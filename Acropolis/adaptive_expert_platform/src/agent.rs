use crate::{memory::Memory, settings::Settings};
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::process::Stdio;
use std::sync::Arc;
use tokio::process::Command;
use tracing::{info, warn, instrument};
use blake3::Hasher;

#[cfg(feature = "with-llama")]
use llama_cpp::{standard_sampler, LlamaModel, LlamaParams, SessionParams};

/// Enhanced Agent trait with better error handling and metadata
#[async_trait]
pub trait Agent: Send + Sync {
    fn name(&self) -> &str;
    fn agent_type(&self) -> &str;
    fn capabilities(&self) -> Vec<String>;
    async fn handle(&self, input: serde_json::Value, memory: Arc<Memory>) -> Result<String>;
    async fn health_check(&self) -> Result<AgentHealth>;
}

/// Agent health information
#[derive(Debug, Clone, Serialize)]
pub struct AgentHealth {
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<String>,
    pub uptime_seconds: u64,
    pub total_requests: u64,
    pub error_count: u64,
    pub average_response_time_ms: f64,
}

impl Default for AgentHealth {
    fn default() -> Self {
        Self {
            status: "healthy".to_string(),
            details: None,
            uptime_seconds: 0,
            total_requests: 0,
            error_count: 0,
            average_response_time_ms: 0.0,
        }
    }
}

// --- Built-in Agents ---

/// Simple echo agent for testing
pub struct EchoAgent {
    request_count: std::sync::atomic::AtomicU64,
    error_count: std::sync::atomic::AtomicU64,
    start_time: std::time::Instant,
}

impl EchoAgent {
    pub fn new() -> Self {
        Self {
            request_count: std::sync::atomic::AtomicU64::new(0),
            error_count: std::sync::atomic::AtomicU64::new(0),
            start_time: std::time::Instant::now(),
        }
    }
}

#[async_trait]
impl Agent for EchoAgent {
    fn name(&self) -> &str { "echo" }

    fn agent_type(&self) -> &str { "utility" }

    fn capabilities(&self) -> Vec<String> {
        vec!["text_echo".to_string(), "testing".to_string()]
    }

    async fn handle(&self, input: serde_json::Value, _memory: Arc<Memory>) -> Result<String> {
        self.request_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        let result = format!("Echo: {}", input.to_string());
        info!("Echo agent processed request");
        Ok(result)
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        let uptime = self.start_time.elapsed().as_secs();
        let requests = self.request_count.load(std::sync::atomic::Ordering::Relaxed);
        let errors = self.error_count.load(std::sync::atomic::Ordering::Relaxed);

        Ok(AgentHealth {
            status: "healthy".to_string(),
            details: None,
            uptime_seconds: uptime,
            total_requests: requests,
            error_count: errors,
            average_response_time_ms: 1.0, // Echo is very fast
        })
    }
}

/// Deterministic hashing-based embedding agent
pub struct HashEmbeddingAgent {
    request_count: std::sync::atomic::AtomicU64,
    error_count: std::sync::atomic::AtomicU64,
    start_time: std::time::Instant,
    dimension: usize,
}

impl HashEmbeddingAgent {
    pub fn new(dimension: usize) -> Self {
        Self {
            request_count: std::sync::atomic::AtomicU64::new(0),
            error_count: std::sync::atomic::AtomicU64::new(0),
            start_time: std::time::Instant::now(),
            dimension,
        }
    }
}

#[async_trait]
impl Agent for HashEmbeddingAgent {
    fn name(&self) -> &str { "hash_embedding" }

    fn agent_type(&self) -> &str { "embedding" }

    fn capabilities(&self) -> Vec<String> {
        vec!["embedding".to_string()]
    }

    async fn handle(&self, input: serde_json::Value, _memory: Arc<Memory>) -> Result<String> {
        self.request_count
            .fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        let text = input
            .get("text")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                self.error_count
                    .fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                anyhow!("Missing 'text' field for embedding agent")
            })?;

        // Produce deterministic pseudo-random embedding based on blake3 hashing
        let mut seed_hasher = Hasher::new();
        seed_hasher.update(text.as_bytes());
        let mut seed = seed_hasher.finalize().as_bytes().to_vec();
        let mut embedding = Vec::with_capacity(self.dimension);

        while embedding.len() < self.dimension {
            let mut h = Hasher::new();
            h.update(&seed);
            let digest = h.finalize();
            seed = digest.as_bytes().to_vec();

            for chunk in seed.chunks(4) {
                if embedding.len() == self.dimension { break; }
                let mut arr = [0u8; 4];
                arr[..chunk.len()].copy_from_slice(chunk);
                let v = u32::from_le_bytes(arr) as f32 / u32::MAX as f32;
                embedding.push(v);
            }
        }

        Ok(serde_json::to_string(&embedding)?)
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        Ok(AgentHealth {
            status: "healthy".to_string(),
            details: None,
            uptime_seconds: self.start_time.elapsed().as_secs(),
            total_requests: self
                .request_count
                .load(std::sync::atomic::Ordering::Relaxed),
            error_count: self
                .error_count
                .load(std::sync::atomic::Ordering::Relaxed),
            average_response_time_ms: 1.0,
        })
    }
}

/// Simple reranking agent that orders candidates by length similarity to the query
pub struct LengthRerankAgent {
    request_count: std::sync::atomic::AtomicU64,
    error_count: std::sync::atomic::AtomicU64,
    start_time: std::time::Instant,
}

impl LengthRerankAgent {
    pub fn new() -> Self {
        Self {
            request_count: std::sync::atomic::AtomicU64::new(0),
            error_count: std::sync::atomic::AtomicU64::new(0),
            start_time: std::time::Instant::now(),
        }
    }
}

#[async_trait]
impl Agent for LengthRerankAgent {
    fn name(&self) -> &str { "length_rerank" }

    fn agent_type(&self) -> &str { "rerank" }

    fn capabilities(&self) -> Vec<String> {
        vec!["rerank".to_string()]
    }

    async fn handle(&self, input: serde_json::Value, _memory: Arc<Memory>) -> Result<String> {
        self.request_count
            .fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        let query = input
            .get("query")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                self.error_count
                    .fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                anyhow!("Missing 'query' field for rerank agent")
            })?;

        let candidates = input
            .get("candidates")
            .and_then(|v| v.as_array())
            .ok_or_else(|| {
                self.error_count
                    .fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                anyhow!("Missing 'candidates' field for rerank agent")
            })?;

        let mut cand_strings: Vec<String> = candidates
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect();

        cand_strings.sort_by_key(|c| {
            let diff = c.len() as i64 - query.len() as i64;
            diff.abs()
        });

        Ok(serde_json::to_string(&cand_strings)?)
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        Ok(AgentHealth {
            status: "healthy".to_string(),
            details: None,
            uptime_seconds: self.start_time.elapsed().as_secs(),
            total_requests: self
                .request_count
                .load(std::sync::atomic::Ordering::Relaxed),
            error_count: self
                .error_count
                .load(std::sync::atomic::Ordering::Relaxed),
            average_response_time_ms: 1.0,
        })
    }
}

/// Enhanced Python tool agent with better security
pub struct PythonToolAgent {
    request_count: std::sync::atomic::AtomicU64,
    error_count: std::sync::atomic::AtomicU64,
    start_time: std::time::Instant,
    allowed_directories: Vec<String>,
    script_allowlist_hashes: HashMap<String, String>,
    max_execution_time: std::time::Duration,
}

#[derive(Deserialize)]
struct PythonToolInput {
    script_path: String,
    args: Vec<String>,
    timeout_seconds: Option<u64>,
}

impl PythonToolAgent {
    pub fn new(settings: &Settings) -> Self {
        Self {
            request_count: std::sync::atomic::AtomicU64::new(0),
            error_count: std::sync::atomic::AtomicU64::new(0),
            start_time: std::time::Instant::now(),
            // Scripts must be in a dedicated, non-tmp directory
            allowed_directories: vec!["./python_scripts".to_string()],
            script_allowlist_hashes: settings.security.script_allowlist_hashes.clone(),
            max_execution_time: std::time::Duration::from_secs(300), // 5 minutes
        }
    }

    fn validate_script_path(&self, path: &str) -> Result<()> {
        let path = std::path::Path::new(path);

        // Check if path is within allowed directories
        let is_allowed = self.allowed_directories.iter().any(|allowed| {
            path.starts_with(allowed)
        });

        if !is_allowed {
            return Err(anyhow!("Script path '{}' is not in allowed directories", path.display()));
        }

        // Check if file exists and is readable
        if !path.exists() {
            return Err(anyhow!("Script file '{}' does not exist", path.display()));
        }

        if !path.is_file() {
            return Err(anyhow!("Path '{}' is not a file", path.display()));
        }

        Ok(())
    }

    /// Validate command arguments to prevent shell injection and dangerous patterns
    fn validate_command_args(args: &[String]) -> Result<()> {
        for arg in args {
            // Check for shell metacharacters that could be dangerous
            let dangerous_chars = ['&', '|', ';', '`', '$', '>', '<', '(', ')', '{', '}'];
            if arg.chars().any(|c| dangerous_chars.contains(&c)) {
                return Err(anyhow!(
                    "Command argument '{}' contains potentially dangerous shell metacharacters", 
                    arg
                ));
            }
            
            // Check for common injection patterns
            let dangerous_patterns = ["rm -", "shutdown", "reboot", "../", "sudo", "su ", "chmod"];
            for pattern in &dangerous_patterns {
                if arg.to_lowercase().contains(pattern) {
                    return Err(anyhow!(
                        "Command argument '{}' contains potentially dangerous pattern: {}", 
                        arg, pattern
                    ));
                }
            }
            
            // Limit argument length to prevent buffer overflow attacks
            if arg.len() > 1000 {
                return Err(anyhow!(
                    "Command argument exceeds maximum length of 1000 characters"
                ));
            }
        }
        Ok(())
    }

    /// Validate the integrity of the script file by checking its hash
    fn validate_script_integrity(&self, path: &str) -> Result<()> {
        if self.script_allowlist_hashes.is_empty() {
            warn!("Script allowlist is empty. Skipping integrity check for {}", path);
            return Ok(());
        }

        let expected_hash = self.script_allowlist_hashes.get(path)
            .ok_or_else(|| anyhow!("Script '{}' is not in the allowlist", path))?;

        let file_content = std::fs::read(path)?;
        let mut hasher = Sha256::new();
        hasher.update(&file_content);
        let actual_hash = format!("{:x}", hasher.finalize());

        if actual_hash != *expected_hash {
            return Err(anyhow!(
                "Script integrity check failed for '{}'. Expected hash: {}, Actual hash: {}",
                path,
                expected_hash,
                actual_hash
            ));
        }

        Ok(())
    }
}

#[async_trait]
impl Agent for PythonToolAgent {
    fn name(&self) -> &str { "python_tool" }

    fn agent_type(&self) -> &str { "execution" }

    fn capabilities(&self) -> Vec<String> {
        vec!["python_execution".to_string(), "script_runner".to_string()]
    }

    #[instrument(skip(self, _memory))]
    async fn handle(&self, input: serde_json::Value, _memory: Arc<Memory>) -> Result<String> {
        self.request_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        let parsed_input: PythonToolInput = serde_json::from_value(input)
            .map_err(|e| {
                self.error_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                anyhow!("Invalid Python tool input: {}", e)
            })?;

        // Validate script path and integrity
        self.validate_script_path(&parsed_input.script_path)?;
        self.validate_script_integrity(&parsed_input.script_path)?;

        info!(
            "Executing Python script: {} with args: {:?}",
            parsed_input.script_path,
            parsed_input.args
        );

        // Build command with security constraints and input validation
        Self::validate_command_args(&parsed_input.args)?;
        
        let script_path = std::path::Path::new(&parsed_input.script_path);
        let script_arg = if script_path.is_relative() {
            script_path
                .file_name()
                .ok_or_else(|| anyhow!("Script path '{}' has no file name", script_path.display()))?
                .to_os_string()
        } else {
            script_path.as_os_str().to_os_string()
        };

        let mut cmd = Command::new("python3");
        cmd.arg(script_arg);
        cmd.args(&parsed_input.args);

        // Keep execution anchored to the script directory without duplicating relative segments.
        if let Some(script_dir) = script_path.parent() {
            cmd.current_dir(script_dir);
        }

        // Set up I/O
        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());

        // Execute with proper timeout and cleanup
        let timeout = parsed_input.timeout_seconds
            .map(std::time::Duration::from_secs)
            .unwrap_or(self.max_execution_time);

        // Create child process with kill_on_drop enabled
        cmd.kill_on_drop(true);
        let child = cmd.spawn()
            .map_err(|e| {
                self.error_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                anyhow!("Failed to spawn Python process: {}", e)
            })?;

        // Wait for completion with timeout. kill_on_drop handles cleanup.
        let output = match tokio::time::timeout(timeout, child.wait_with_output()).await {
            Ok(Ok(output)) => output,
            Ok(Err(e)) => {
                self.error_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                return Err(anyhow!("Failed to execute Python script: {}", e));
            }
            Err(_) => {
                // Timeout occurred - child will be killed on drop
                warn!("Python script execution timed out");
                self.error_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                return Err(anyhow!("Python script execution timed out after {:?}", timeout));
            }
        };

        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            info!("Python script executed successfully");
            Ok(stdout.to_string())
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            self.error_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            Err(anyhow!("Python script failed: {}", stderr))
        }
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        let uptime = self.start_time.elapsed().as_secs();
        let requests = self.request_count.load(std::sync::atomic::Ordering::Relaxed);
        let errors = self.error_count.load(std::sync::atomic::Ordering::Relaxed);

        Ok(AgentHealth {
            status: "healthy".to_string(),
            details: None,
            uptime_seconds: uptime,
            total_requests: requests,
            error_count: errors,
            average_response_time_ms: 10.0, // Python execution has overhead
        })
    }
}

/// Enhanced LLM agent with better model management
#[cfg(feature = "with-llama")]
pub struct LlmAgent {
    name: String,
    model: LlamaModel,
    session_params: SessionParams,
    request_count: std::sync::atomic::AtomicU64,
    error_count: std::sync::atomic::AtomicU64,
    start_time: std::time::Instant,
    max_tokens: usize,
    temperature: f32,
}

#[cfg(feature = "with-llama")]
impl LlmAgent {
    pub fn new(name: &str, model_path: &str) -> Result<Self> {
        let params = LlamaParams::default()
            .with_model_path(model_path)
            .with_n_ctx(2048)
            .with_n_batch(512);

        let model = LlamaModel::load(params)?;
        let session_params = SessionParams::default()
            .with_seed(42);

        Ok(Self {
            name: name.to_string(),
            model,
            session_params,
            request_count: std::sync::atomic::AtomicU64::new(0),
            error_count: std::sync::atomic::AtomicU64::new(0),
            start_time: std::time::Instant::now(),
            max_tokens: 512,
            temperature: 0.7,
        })
    }

    pub fn with_max_tokens(mut self, max_tokens: usize) -> Self {
        self.max_tokens = max_tokens;
        self
    }

    pub fn with_temperature(mut self, temperature: f32) -> Self {
        self.temperature = temperature;
        self
    }
}

#[cfg(feature = "with-llama")]
#[async_trait]
impl Agent for LlmAgent {
    fn name(&self) -> &str { &self.name }

    fn agent_type(&self) -> &str { "llm" }

    fn capabilities(&self) -> Vec<String> {
        vec!["text_generation".to_string(), "completion".to_string(), "reasoning".to_string()]
    }

    #[instrument(skip(self, memory))]
    async fn handle(&self, input: serde_json::Value, memory: Arc<Memory>) -> Result<String> {
        self.request_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        let prompt = input.get("prompt")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                self.error_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                anyhow!("Missing 'prompt' field in LLM input")
            })?;

        // Get relevant context from memory
        let context = memory.search_memory(prompt, 3).await
            .unwrap_or_else(|_| vec![]);

        let enhanced_prompt = if context.is_empty() {
            prompt.to_string()
        } else {
            format!("Context:\n{}\n\nQuestion: {}",
                context.join("\n"), prompt)
        };

        info!("Generating LLM response for prompt: {}", &enhanced_prompt[..enhanced_prompt.len().min(100)]);

        // Generate response using llama.cpp
        let mut session = self.model.create_session(self.session_params.clone())?;

        let sampler = standard_sampler()
            .with_temperature(self.temperature)
            .with_top_p(0.9)
            .with_top_k(40);

        let response = session
            .infer(enhanced_prompt, sampler, |_| {})
            .map_err(|e| {
                self.error_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                anyhow!("LLM inference failed: {}", e)
            })?;

        info!("LLM response generated successfully");
        Ok(response)
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        let uptime = self.start_time.elapsed().as_secs();
        let requests = self.request_count.load(std::sync::atomic::Ordering::Relaxed);
        let errors = self.error_count.load(std::sync::atomic::Ordering::Relaxed);

        Ok(AgentHealth {
            status: "healthy".to_string(),
            uptime_seconds: uptime,
            total_requests: requests,
            error_count: errors,
            average_response_time_ms: 2000.0, // LLM inference takes time
        })
    }
}

/// Agent factory for creating agents by type
pub struct AgentFactory;

impl AgentFactory {
    pub fn create_agent(agent_type: &str, _config: serde_json::Value, settings: &Settings) -> Result<Box<dyn Agent>> {
        match agent_type {
            "echo" => Ok(Box::new(EchoAgent::new())),
            "python" => Ok(Box::new(PythonToolAgent::new(settings))),
            #[cfg(feature = "with-julia")]
            "julia" => {
                use crate::ffi_julia::JuliaAgent;
                Ok(Box::new(JuliaAgent::new(settings)?))
            }
            #[cfg(feature = "with-llama")]
            "llm" => {
                let name = config.get("name")
                    .and_then(|v| v.as_str())
                    .unwrap_or("llm_agent");
                let model_path = config.get("model_path")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| anyhow!("Missing 'model_path' for LLM agent"))?;

                let agent = LlmAgent::new(name, model_path)?;
                Ok(Box::new(agent))
            }
            _ => Err(anyhow!("Unknown agent type: {}", agent_type)),
        }
    }
}
