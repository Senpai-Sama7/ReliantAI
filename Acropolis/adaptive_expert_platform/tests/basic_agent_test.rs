//! Comprehensive integration tests for the Adaptive Expert Platform.
//!
//! These tests exercise the core orchestrator functionality, security features,
//! plugin management, memory systems, and agent interactions. They include
//! performance benchmarks, security validation, and edge case testing.

use adaptive_expert_platform::{
    agent::{Agent, EchoAgent, PythonToolAgent},
    orchestrator::Orchestrator,
    plugin::{PluginSecurityConfig, Plugin},
    memory::{Memory, redis_store::InMemoryEmbeddingCache},
    settings::Settings,
};
use anyhow::Result;
use tracing::warn;
use std::{sync::Arc, time::Duration};
use serde_json::json;
use tempfile::tempdir;
use std::fs::File;
use std::io::Write;
use tracing_test::traced_test;

/// Helper function to create a test orchestrator with memory
async fn create_test_orchestrator() -> Result<Orchestrator> {
    let mut settings = Settings::default();
    settings.observability.enable_metrics = false;
    let cache = Arc::new(InMemoryEmbeddingCache::new());
    let echo_agent = Arc::new(EchoAgent::new());
    let memory = Arc::new(Memory::new(
        echo_agent.clone(),
        echo_agent.clone(),
        cache,
    ));

    Orchestrator::new(&settings, memory).await
}

/// Helper function to create test plugin security config
fn create_test_security_config() -> PluginSecurityConfig {
    let mut config = PluginSecurityConfig::default();
    // For testing only: provide expected plugin hashes or disable signatures
    // In production, signatures should ALWAYS be enabled
    config.require_signatures = false; // ONLY for testing - never in production
    config.max_plugin_size = 1024 * 1024; // 1MB for testing

    warn!("Plugin signature verification DISABLED for testing - this is insecure for production");
    config
}

#[tokio::test]
#[traced_test]
async fn test_echo_agent_basic_functionality() {
    let orchestrator = create_test_orchestrator().await.unwrap();

    // Register echo agent
    let agent = Arc::new(EchoAgent::new());
    orchestrator.register_agent("echo".to_string(), agent).await.unwrap();

    // Test basic echo functionality
    let (tx, mut rx) = tokio::sync::mpsc::channel(1);
    let task = ("echo".to_string(), json!("hello world"), tx);

    orchestrator.dispatch(task).await.unwrap();
    let result = rx.recv().await.unwrap().unwrap();

    assert!(result.as_str().unwrap().contains("hello world"));
}

#[tokio::test]
#[traced_test]
async fn test_orchestrator_concurrent_dispatch() {
    let orchestrator = Arc::new(create_test_orchestrator().await.unwrap());

    // Register multiple agents
    let echo_agent = Arc::new(EchoAgent::new());
    orchestrator.register_agent("echo1".to_string(), echo_agent.clone()).await.unwrap();
    orchestrator.register_agent("echo2".to_string(), echo_agent.clone()).await.unwrap();
    orchestrator.register_agent("echo3".to_string(), echo_agent).await.unwrap();

    // Dispatch multiple concurrent tasks
    let mut handles = Vec::new();

    for i in 0..10 {
        let orch = orchestrator.clone();
        let handle = tokio::spawn(async move {
            let (tx, mut rx) = tokio::sync::mpsc::channel(1);
            let agent_name = format!("echo{}", (i % 3) + 1);
            let task = (agent_name, json!(format!("message {}", i)), tx);

            orch.dispatch(task).await.unwrap();
            rx.recv().await.unwrap()
        });
        handles.push(handle);
    }

    // Wait for all tasks to complete
    let results = futures::future::join_all(handles).await;
    assert_eq!(results.len(), 10);

    // Verify all tasks succeeded
    for result in results {
        assert!(result.unwrap().is_ok());
    }
}

#[tokio::test]
#[traced_test]
async fn test_orchestrator_timeout_handling() {
    let orchestrator = create_test_orchestrator().await.unwrap();

    // Test dispatching to non-existent agent
    let (tx, mut rx) = tokio::sync::mpsc::channel(1);
    let task = ("nonexistent".to_string(), json!("test"), tx);

    orchestrator.dispatch(task).await.unwrap();
    let result = rx.recv().await.unwrap();
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("Unknown agent"));
}

#[tokio::test]
#[traced_test]
async fn test_orchestrator_agent_management() {
    let orchestrator = create_test_orchestrator().await.unwrap();

    // Initially no agents
    let agents = orchestrator.list_agents().await;
    assert!(agents.is_empty());

    // Register an agent
    let agent = Arc::new(EchoAgent::new());
    orchestrator.register_agent("test_echo".to_string(), agent).await.unwrap();

    // Verify agent is registered
    let agents = orchestrator.list_agents().await;
    assert_eq!(agents.len(), 1);
    assert!(agents.iter().any(|(name, _)| name == "test_echo"));
}

#[tokio::test]
#[traced_test]
async fn test_python_tool_agent() {
    let settings = Settings::default();
    let agent = PythonToolAgent::new(&settings);
    let cache = Arc::new(InMemoryEmbeddingCache::new());
    let echo_agent = Arc::new(EchoAgent::new());
    let memory = Arc::new(Memory::new(echo_agent.clone(), echo_agent, cache));

    // Create a simple Python script
    std::fs::create_dir_all("./python_scripts").unwrap();
    let unique_id = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let script_rel_path = format!("./python_scripts/test_script_{unique_id}.py");
    let mut file = File::create(&script_rel_path).unwrap();
    writeln!(file, "print('Hello from Python!')").unwrap();

    // Test execution
    let input = json!({
        "script_path": script_rel_path,
        "args": []
    });

    let result = agent.handle(input, memory).await.unwrap();
    assert!(result.contains("Hello from Python!"));
    std::fs::remove_file(&script_rel_path).unwrap();
}

#[tokio::test]
#[traced_test]
async fn test_python_tool_agent_error_handling() {
    let settings = Settings::default();
    let agent = PythonToolAgent::new(&settings);
    let cache = Arc::new(InMemoryEmbeddingCache::new());
    let echo_agent = Arc::new(EchoAgent::new());
    let memory = Arc::new(Memory::new(echo_agent.clone(), echo_agent, cache));

    // Test with invalid Python script
    std::fs::create_dir_all("./python_scripts").unwrap();
    let unique_id = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let script_rel_path = format!("./python_scripts/bad_script_{unique_id}.py");
    let mut file = File::create(&script_rel_path).unwrap();
    writeln!(file, "this is not valid python syntax!!!").unwrap();

    let input = json!({
        "script_path": script_rel_path,
        "args": []
    });

    let result = agent.handle(input, memory).await;
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("failed"));
    std::fs::remove_file(&script_rel_path).unwrap();
}

#[tokio::test]
#[traced_test]
async fn test_plugin_security_validation() {
    let config = create_test_security_config();

    // Test with valid file extension
    let temp_dir = tempdir().unwrap();
    let plugin_path = temp_dir.path().join("test.so");
    let mut file = File::create(&plugin_path).unwrap();
    writeln!(file, "fake plugin content").unwrap();

    // This should fail because it's not a real plugin
    let result = unsafe { Plugin::load(&plugin_path, &config) };
    assert!(result.is_err()); // Should fail to load as it's not a real shared library

    // Test with invalid file extension
    let bad_path = temp_dir.path().join("test.txt");
    File::create(&bad_path).unwrap();

    let result = unsafe { Plugin::load(&bad_path, &config) };
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("not allowed"));
}

#[tokio::test]
#[traced_test]
async fn test_plugin_size_limits() {
    let mut config = create_test_security_config();
    config.max_plugin_size = 10; // Very small limit

    let temp_dir = tempdir().unwrap();
    let plugin_path = temp_dir.path().join("large.so");
    let mut file = File::create(&plugin_path).unwrap();

    // Write more than the limit
    for _ in 0..20 {
        writeln!(file, "x").unwrap();
    }

    let result = unsafe { Plugin::load(&plugin_path, &config) };
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("too large"));
}

#[tokio::test]
#[traced_test]
async fn test_memory_system_basic() {
    let cache = Arc::new(InMemoryEmbeddingCache::new());
    let echo_agent = Arc::new(EchoAgent::new());
    let memory = Memory::new(echo_agent.clone(), echo_agent, cache);

    // Test adding memory
    let result = memory.add_memory("test content").await;
    // This will fail because EchoAgent doesn't return proper embeddings,
    // but we're testing the error handling
    assert!(result.is_err());
}

#[tokio::test]
#[traced_test]
async fn test_settings_validation() {
    let mut settings = Settings::default();
    settings.security.jwt_secret = Some("test-jwt-secret".to_string());

    // Should pass validation with defaults
    assert!(settings.validate().is_ok());

    // Test invalid server port
    settings.server.port = 0;
    assert!(settings.validate().is_err());

    // Test redis configuration validation
    settings.server.port = 8080;
    settings.memory.provider = "redis".to_string();
    settings.memory.url = None;
    assert!(settings.validate().is_err());

    // Fix redis configuration
    settings.memory.url = Some("redis://localhost:6379".to_string());
    assert!(settings.validate().is_ok());
}

#[tokio::test]
#[traced_test]
async fn test_orchestrator_performance_basic() {
    let orchestrator = create_test_orchestrator().await.unwrap();
    let echo_agent = Arc::new(EchoAgent::new());
    orchestrator.register_agent("echo".to_string(), echo_agent).await.unwrap();

    let start = std::time::Instant::now();
    let mut handles = Vec::new();

    // Dispatch 100 concurrent tasks
    for i in 0..100 {
        let (tx, rx) = tokio::sync::mpsc::channel(1);
        let task = ("echo".to_string(), json!(format!("message {}", i)), tx);

        orchestrator.dispatch(task).await.unwrap();
        handles.push(rx);
    }

    // Wait for all to complete
    for mut rx in handles {
        let _ = rx.recv().await.unwrap();
    }

    let duration = start.elapsed();
    println!("100 concurrent echo tasks completed in: {:?}", duration);

    // Should complete within reasonable time (adjust based on CI environment)
    assert!(duration < Duration::from_secs(5));
}

#[tokio::test]
#[traced_test]
async fn test_error_propagation() {
    // Test that errors are properly propagated through the system
    let orchestrator = create_test_orchestrator().await.unwrap();

    // Register echo agent
    let echo_agent = Arc::new(EchoAgent::new());
    orchestrator.register_agent("echo".to_string(), echo_agent).await.unwrap();

    // Test with malformed JSON (agent should handle this)
    let (tx, mut rx) = tokio::sync::mpsc::channel(1);
    let task = ("echo".to_string(), json!(null), tx);

    orchestrator.dispatch(task).await.unwrap();
    let result = rx.recv().await.unwrap();

    // Echo agent should handle null input gracefully
    assert!(result.is_ok());
}

#[tokio::test]
#[traced_test]
async fn test_json_input_validation() {
    let agent = EchoAgent::new();
    let cache = Arc::new(InMemoryEmbeddingCache::new());
    let echo_agent_arc = Arc::new(EchoAgent::new());
    let memory = Arc::new(Memory::new(
        echo_agent_arc.clone(),
        echo_agent_arc,
        cache,
    ));

    // Test various JSON input types
    let inputs = vec![
        json!("string input"),
        json!({"key": "value"}),
        json!([1, 2, 3]),
        json!(42),
        json!(true),
        json!(null),
    ];

    for input in inputs {
        let result: Result<String, _> = agent.handle(input, memory.clone()).await;
        assert!(result.is_ok());
    }
}

// Benchmark tests
#[cfg(test)]
mod benchmarks {
    use super::*;
    use std::time::Instant;

    #[tokio::test]
    async fn bench_orchestrator_throughput() {
        let orchestrator = create_test_orchestrator().await.unwrap();
        let echo_agent = Arc::new(EchoAgent::new());
        orchestrator.register_agent("echo".to_string(), echo_agent).await.unwrap();

        let num_requests = 1000;
        let start = Instant::now();

        let mut handles = Vec::with_capacity(num_requests);

        for i in 0..num_requests {
            let (tx, rx) = tokio::sync::mpsc::channel(1);
            let task = ("echo".to_string(), json!(format!("msg{}", i)), tx);

            orchestrator.dispatch(task).await.unwrap();
            handles.push(rx);
        }

        // Wait for all completions
        for mut rx in handles {
            let _ = rx.recv().await.unwrap();
        }

        let duration = start.elapsed();
        let throughput = num_requests as f64 / duration.as_secs_f64();

        println!("Throughput: {:.2} requests/second", throughput);
        assert!(throughput > 100.0); // Expect at least 100 req/s
    }
}
