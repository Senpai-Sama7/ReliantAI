//! Batch processing functionality for running pre-configured tasks.
//!
//! This module provides the ability to run multiple agent tasks in batch mode
//! from configuration files, with progress tracking, error handling, and
//! result aggregation.

use crate::{
    orchestrator::Orchestrator,
    settings::Settings,
    memory::{Memory, redis_store::InMemoryEmbeddingCache},
    agent::{EchoAgent, PythonToolAgent},
};
use anyhow::{Result, anyhow, Context};
use serde::{Deserialize, Serialize};
use std::{path::PathBuf, sync::Arc, time::Instant};
use tokio::sync::mpsc;
use tracing::{info, warn, error, instrument};
use serde_json::Value;

/// Batch job configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchConfig {
    /// Job metadata
    pub job: JobMetadata,

    /// List of tasks to execute
    pub tasks: Vec<TaskConfig>,

    /// Global settings for the batch job
    pub settings: BatchSettings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobMetadata {
    pub name: String,
    pub description: Option<String>,
    pub version: String,

    #[serde(default)]
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskConfig {
    /// Unique task identifier
    pub id: String,

    /// Agent name to execute
    pub agent: String,

    /// Input data for the agent
    pub input: Value,

    /// Task-specific settings
    #[serde(default)]
    pub settings: TaskSettings,

    /// Dependencies on other tasks (task IDs)
    #[serde(default)]
    pub depends_on: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskSettings {
    /// Maximum execution time in seconds
    #[serde(default = "default_task_timeout")]
    pub timeout_seconds: u64,

    /// Number of retries on failure
    #[serde(default)]
    pub retries: u32,

    /// Whether task failure should stop the entire batch
    #[serde(default)]
    pub critical: bool,

    /// Whether to continue on failure
    #[serde(default = "default_continue_on_error")]
    pub continue_on_error: bool,
}

impl Default for TaskSettings {
    fn default() -> Self {
        Self {
            timeout_seconds: default_task_timeout(),
            retries: 0,
            critical: false,
            continue_on_error: default_continue_on_error(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchSettings {
    /// Maximum concurrent tasks
    #[serde(default = "default_max_concurrent")]
    pub max_concurrent_tasks: usize,

    /// Overall batch timeout in seconds
    #[serde(default = "default_batch_timeout")]
    pub timeout_seconds: u64,

    /// Output file for results
    pub output_file: Option<PathBuf>,

    /// Whether to fail fast on first error
    #[serde(default)]
    pub fail_fast: bool,
}

impl Default for BatchSettings {
    fn default() -> Self {
        Self {
            max_concurrent_tasks: default_max_concurrent(),
            timeout_seconds: default_batch_timeout(),
            output_file: None,
            fail_fast: false,
        }
    }
}

/// Result of a single task execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResult {
    pub task_id: String,
    pub agent: String,
    pub status: TaskStatus,
    pub output: Option<Value>,
    pub error: Option<String>,
    pub duration_ms: u64,
    pub retries_used: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum TaskStatus {
    Pending,
    Running,
    Success,
    Failed,
    Skipped,
    Timeout,
}

/// Complete batch execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchResult {
    pub job_name: String,
    pub status: BatchStatus,
    pub total_tasks: usize,
    pub successful_tasks: usize,
    pub failed_tasks: usize,
    pub skipped_tasks: usize,
    pub total_duration_ms: u64,
    pub task_results: Vec<TaskResult>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum BatchStatus {
    Success,
    PartialSuccess,
    Failed,
}

/// Execute a batch job from configuration file
#[instrument(skip(settings))]
pub async fn run(config_path: PathBuf, settings: Settings) -> Result<()> {
    info!("Starting batch execution from config: {:?}", config_path);

    // Load batch configuration
    let config = load_batch_config(&config_path)
        .context("Failed to load batch configuration")?;

    info!("Loaded batch job: {} (version: {})", config.job.name, config.job.version);

    // Store output file path before moving config
    let output_file = config.settings.output_file.clone();

    // Initialize orchestrator and memory
    let orchestrator = Arc::new(initialize_orchestrator(&settings).await
        .context("Failed to initialize orchestrator")?);

    // Execute batch job
    let start_time = Instant::now();
    let result = execute_batch(orchestrator, config).await
        .context("Batch execution failed")?;

    let total_duration = start_time.elapsed();
    info!("Batch execution completed in {:?}", total_duration);

    // Print summary
    print_batch_summary(&result);

    // Save results if output file specified
    if let Some(ref output_file_path) = output_file {
        save_batch_results(&result, output_file_path)
            .context("Failed to save batch results")?;
    }

    // Return error code if batch failed
    match result.status {
        BatchStatus::Success => Ok(()),
        BatchStatus::PartialSuccess => {
            warn!("Batch completed with some failures");
            Ok(())
        }
        BatchStatus::Failed => {
            error!("Batch execution failed");
            Err(anyhow!("Batch execution failed: {}",
                result.error.unwrap_or_else(|| "Unknown error".to_string())))
        }
    }
}

/// Load batch configuration from TOML file
fn load_batch_config(config_path: &PathBuf) -> Result<BatchConfig> {
    let contents = std::fs::read_to_string(config_path)
        .with_context(|| format!("Failed to read config file: {:?}", config_path))?;

    let config: BatchConfig = toml::from_str(&contents)
        .with_context(|| format!("Failed to parse TOML config: {:?}", config_path))?;

    // Validate configuration
    validate_batch_config(&config)?;

    Ok(config)
}

/// Validate batch configuration
fn validate_batch_config(config: &BatchConfig) -> Result<()> {
    if config.tasks.is_empty() {
        return Err(anyhow!("Batch configuration must contain at least one task"));
    }

    // Check for duplicate task IDs
    let mut task_ids = std::collections::HashSet::new();
    for task in &config.tasks {
        if !task_ids.insert(&task.id) {
            return Err(anyhow!("Duplicate task ID: {}", task.id));
        }
    }

    // Validate dependencies
    for task in &config.tasks {
        for dep in &task.depends_on {
            if !task_ids.contains(dep) {
                return Err(anyhow!("Task {} depends on non-existent task: {}", task.id, dep));
            }
        }
    }

    Ok(())
}

/// Initialize orchestrator with built-in agents
async fn initialize_orchestrator(settings: &Settings) -> Result<Orchestrator> {
    let cache = Arc::new(InMemoryEmbeddingCache::new());
    let echo_agent = Arc::new(EchoAgent::new());
    let memory = Arc::new(Memory::new(
        echo_agent.clone(),
        echo_agent.clone(),
        cache,
    ));

    let orchestrator = Orchestrator::new(settings, memory).await?;

    // Register built-in agents
    orchestrator.register_agent("echo".to_string(), echo_agent).await?;
    orchestrator.register_agent("python_tool".to_string(), Arc::new(PythonToolAgent::new(settings))).await?;

    info!("Orchestrator initialized with built-in agents");
    Ok(orchestrator)
}

/// Execute batch job with dependency resolution and concurrency control
async fn execute_batch(orchestrator: Arc<Orchestrator>, config: BatchConfig) -> Result<BatchResult> {
    let start_time = Instant::now();
    let total_tasks = config.tasks.len();

    let mut task_results = Vec::new();
    let mut completed_tasks = std::collections::HashSet::new();
    let mut remaining_tasks: std::collections::HashMap<String, TaskConfig> =
        config.tasks.into_iter().map(|t| (t.id.clone(), t)).collect();

    // Execute tasks in dependency order
    while !remaining_tasks.is_empty() {
        // Find tasks that can be executed (all dependencies completed)
        let ready_tasks: Vec<_> = remaining_tasks
            .values()
            .filter(|task| {
                task.depends_on.iter().all(|dep| completed_tasks.contains(dep))
            })
            .cloned()
            .collect();

        if ready_tasks.is_empty() {
            return Err(anyhow!("Circular dependency detected or missing dependencies"));
        }

        // Execute ready tasks with concurrency limit
        let semaphore = Arc::new(tokio::sync::Semaphore::new(config.settings.max_concurrent_tasks));
        let mut handles = Vec::new();

        for task in ready_tasks {
            let permit = semaphore.clone().acquire_owned().await?;
            let task_clone = task.clone();
            let orchestrator_clone = orchestrator.clone();

            let handle = tokio::spawn(async move {
                let _permit = permit; // Keep permit until task completes
                execute_single_task(orchestrator_clone.as_ref(), task_clone).await
            });

            handles.push((task.id.clone(), handle));
        }

        // Wait for all tasks in this batch to complete
        for (task_id, handle) in handles {
            let result = handle.await??;

            // Check if we should fail fast
            if config.settings.fail_fast && result.status == TaskStatus::Failed {
                error!("Failing fast due to task failure: {}", task_id);
                return Ok(BatchResult {
                    job_name: config.job.name,
                    status: BatchStatus::Failed,
                    total_tasks,
                    successful_tasks: task_results.iter().filter(|r: &&TaskResult| r.status == TaskStatus::Success).count(),
                    failed_tasks: task_results.iter().filter(|r| r.status == TaskStatus::Failed).count() + 1,
                    skipped_tasks: remaining_tasks.len() - 1,
                    total_duration_ms: start_time.elapsed().as_millis() as u64,
                    task_results,
                    error: Some(format!("Failed fast on task: {}", task_id)),
                });
            }

            if result.status == TaskStatus::Success {
                completed_tasks.insert(task_id.clone());
            }

            task_results.push(result);
            remaining_tasks.remove(&task_id);
        }
    }

    // Calculate final status
    let successful_tasks = task_results.iter().filter(|r| r.status == TaskStatus::Success).count();
    let failed_tasks = task_results.iter().filter(|r| r.status == TaskStatus::Failed).count();
    let skipped_tasks = task_results.iter().filter(|r| r.status == TaskStatus::Skipped).count();

    let status = if failed_tasks == 0 {
        BatchStatus::Success
    } else if successful_tasks > 0 {
        BatchStatus::PartialSuccess
    } else {
        BatchStatus::Failed
    };

    Ok(BatchResult {
        job_name: config.job.name,
        status,
        total_tasks,
        successful_tasks,
        failed_tasks,
        skipped_tasks,
        total_duration_ms: start_time.elapsed().as_millis() as u64,
        task_results,
        error: None,
    })
}

/// Execute a single task with retry logic
async fn execute_single_task(orchestrator: &Orchestrator, task: TaskConfig) -> Result<TaskResult> {
    let start_time = Instant::now();
    let mut retries_used = 0;

    loop {
        info!("Executing task: {} (attempt {})", task.id, retries_used + 1);

                let (tx, mut rx) = mpsc::channel(1);
        let task_tuple = (task.agent.clone(), task.input.clone(), tx);

        // Execute with timeout
        let execution_result = tokio::time::timeout(
            std::time::Duration::from_secs(task.settings.timeout_seconds),
            async {
                orchestrator.dispatch(task_tuple).await?;
                rx.recv().await.ok_or_else(|| anyhow!("No response received"))
            }
        ).await;

        match execution_result {
            Ok(Ok(Ok(output))) => {
                info!("Task {} completed successfully", task.id);
                return Ok(TaskResult {
                    task_id: task.id,
                    agent: task.agent,
                    status: TaskStatus::Success,
                    output: Some(output),
                    error: None,
                    duration_ms: start_time.elapsed().as_millis() as u64,
                    retries_used,
                });
            }
            Ok(Ok(Err(e))) => {
                warn!("Task {} failed: {}", task.id, e);

                if retries_used < task.settings.retries {
                    retries_used += 1;
                    warn!("Retrying task {} (attempt {})", task.id, retries_used + 1);
                    continue;
                }

                return Ok(TaskResult {
                    task_id: task.id,
                    agent: task.agent,
                    status: TaskStatus::Failed,
                    output: None,
                    error: Some(e.to_string()),
                    duration_ms: start_time.elapsed().as_millis() as u64,
                    retries_used,
                });
            }
            Ok(Err(e)) => {
                error!("Task {} dispatch failed: {}", task.id, e);
                return Ok(TaskResult {
                    task_id: task.id,
                    agent: task.agent,
                    status: TaskStatus::Failed,
                    output: None,
                    error: Some(e.to_string()),
                    duration_ms: start_time.elapsed().as_millis() as u64,
                    retries_used,
                });
            }
            Err(_) => {
                warn!("Task {} timed out", task.id);

                if retries_used < task.settings.retries {
                    retries_used += 1;
                    warn!("Retrying task {} after timeout (attempt {})", task.id, retries_used + 1);
                    continue;
                }

                return Ok(TaskResult {
                    task_id: task.id,
                    agent: task.agent,
                    status: TaskStatus::Timeout,
                    output: None,
                    error: Some("Task execution timed out".to_string()),
                    duration_ms: start_time.elapsed().as_millis() as u64,
                    retries_used,
                });
            }
        }
    }
}

/// Print batch execution summary
fn print_batch_summary(result: &BatchResult) {
    println!("\n=== Batch Execution Summary ===");
    println!("Job: {}", result.job_name);
    println!("Status: {:?}", result.status);
    println!("Total Tasks: {}", result.total_tasks);
    println!("Successful: {}", result.successful_tasks);
    println!("Failed: {}", result.failed_tasks);
    println!("Skipped: {}", result.skipped_tasks);
    println!("Duration: {}ms", result.total_duration_ms);

    if result.failed_tasks > 0 {
        println!("\nFailed Tasks:");
        for task in &result.task_results {
            if task.status == TaskStatus::Failed || task.status == TaskStatus::Timeout {
                println!("  - {} ({}): {}",
                    task.task_id,
                    task.agent,
                    task.error.as_deref().unwrap_or("Unknown error")
                );
            }
        }
    }
    println!("===============================\n");
}

/// Save batch results to JSON file
fn save_batch_results(result: &BatchResult, output_file: &PathBuf) -> Result<()> {
    let json = serde_json::to_string_pretty(result)
        .context("Failed to serialize batch results")?;

    std::fs::write(output_file, json)
        .with_context(|| format!("Failed to write results to: {:?}", output_file))?;

    info!("Batch results saved to: {:?}", output_file);
    Ok(())
}

// Default value functions
fn default_task_timeout() -> u64 { 30 }
fn default_continue_on_error() -> bool { false }
fn default_max_concurrent() -> usize { 4 }
fn default_batch_timeout() -> u64 { 3600 }

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use tempfile::tempdir;
    use std::fs;

    #[test]
    fn test_batch_config_validation() {
        // Valid config
        let config = BatchConfig {
            job: JobMetadata {
                name: "test_job".to_string(),
                description: None,
                version: "1.0".to_string(),
                tags: vec![],
            },
            tasks: vec![
                TaskConfig {
                    id: "task1".to_string(),
                    agent: "echo".to_string(),
                    input: json!("test"),
                    settings: TaskSettings::default(),
                    depends_on: vec![],
                }
            ],
            settings: BatchSettings::default(),
        };

        assert!(validate_batch_config(&config).is_ok());

        // Invalid config - duplicate task IDs
        let mut invalid_config = config.clone();
        invalid_config.tasks.push(TaskConfig {
            id: "task1".to_string(), // Duplicate ID
            agent: "echo".to_string(),
            input: json!("test"),
            settings: TaskSettings::default(),
            depends_on: vec![],
        });

        assert!(validate_batch_config(&invalid_config).is_err());
    }

    #[tokio::test]
    async fn test_batch_config_loading() {
        let temp_dir = tempdir().unwrap();
        let config_path = temp_dir.path().join("test_batch.toml");

        let config_content = r#"
[job]
name = "test_batch"
version = "1.0"
description = "Test batch job"

[settings]
max_concurrent_tasks = 2
timeout_seconds = 60

[[tasks]]
id = "echo_task"
agent = "echo"
input = "Hello, World!"

[tasks.settings]
timeout_seconds = 10
retries = 1
"#;

        fs::write(&config_path, config_content).unwrap();

        let config = load_batch_config(&config_path).unwrap();
        assert_eq!(config.job.name, "test_batch");
        assert_eq!(config.tasks.len(), 1);
        assert_eq!(config.tasks[0].id, "echo_task");
        assert_eq!(config.settings.max_concurrent_tasks, 2);
    }
}
