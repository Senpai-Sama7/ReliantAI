//! Julia runtime integration with enhanced security and proper dependency handling.

#[cfg(feature = "with-julia")]
mod julia_impl {
    use crate::{agent::Agent, memory::Memory, settings::Settings};
    use anyhow::{anyhow, Result};
    use async_trait::async_trait;
    use jlrs::prelude::*;
    use serde_json::Value;
    use sha2::{Digest, Sha256};
    use std::collections::HashMap;
    use std::sync::Arc;
    use tokio::sync::{mpsc::Sender, oneshot::channel};
    use tracing::{info, error, warn};

    pub struct JuliaTask {
        pub function_name: String,
        pub json_config: Value,
        pub response: oneshot::Sender<Result<String>>,
    }

    /// Validate the integrity of the model file by checking its hash
    fn validate_model_integrity(path: &str, allowlist: &HashMap<String, String>) -> Result<()> {
        if allowlist.is_empty() {
            warn!("Script allowlist is empty. Skipping integrity check for {}", path);
            return Ok(());
        }

        let expected_hash = allowlist.get(path)
            .ok_or_else(|| anyhow!("Model '{}' is not in the allowlist", path))?;

        let file_content = std::fs::read(path)?;
        let mut hasher = Sha256::new();
        hasher.update(&file_content);
        let actual_hash = format!("{:x}", hasher.finalize());

        if actual_hash != *expected_hash {
            return Err(anyhow!(
                "Model integrity check failed for '{}'. Expected hash: {}, Actual hash: {}",
                path,
                expected_hash,
                actual_hash
            ));
        }

        Ok(())
    }

    /// Initialize Julia runtime in a dedicated thread with bounded queue for concurrency control
    fn init_julia(settings: Settings) -> Result<Sender<JuliaTask>> {
        let (tx, mut rx) = tokio::sync::mpsc::channel::<JuliaTask>(100);
        let (init_tx, init_rx) = std::sync::mpsc::channel::<Result<()>>();

        std::thread::spawn(move || {
            let julia_res = RuntimeBuilder::new().start();
            let mut julia = match julia_res {
                Ok(julia) => {
                    if init_tx.send(Ok(())).is_err() {
                        error!("Failed to send Julia init success signal");
                        return;
                    }
                    julia
                }
                Err(e) => {
                    error!("Failed to initialize Julia runtime: {}", e);
                    let _ = init_tx.send(Err(anyhow!("Failed to initialize Julia: {}", e)));
                    return;
                }
            };
            let mut frame = StackFrame::new();

            info!("Julia runtime initialized in dedicated thread");

            // Load common Julia modules
            if let Err(e) = julia.scope(|mut frame| {
                let include = Module::main(&mut frame).function(&mut frame, "include")?;
                // Load model files if they exist
                for model_path in &["models/julia/causal_model.jl", "models/julia/ltn_logic.jl"] {
                    if std::path::Path::new(model_path).exists() {
                        // Validate integrity before loading
                        if let Err(e) = validate_model_integrity(model_path, &settings.security.script_allowlist_hashes) {
                            error!("Integrity check failed for Julia model '{}': {}", model_path, e);
                            continue;
                        }
                        include.call1(&mut frame, Value::new(&mut frame, model_path))?;
                        info!("Loaded Julia model: {}", model_path);
                    }
                }
                Ok(())
            }) {
                error!("Failed to load Julia models: {}", e);
            }

            // Main loop for processing Julia tasks
            while let Some(task) = rx.blocking_recv() {
                let result = julia.scope(|mut frame| {
                    let func = Module::main(&mut frame).function(&mut frame, &task.function_name)?;
                    let config_val = Value::new(&mut frame, task.json_config);
                    let result = func.call1(&mut frame, config_val)?;
                    Ok(result.display_string(&mut frame)?)
                });

                let response = match result {
                    Ok(output) => Ok(output),
                    Err(e) => Err(anyhow!("Julia execution error: {}", e)),
                };

                if let Err(_) = task.response.send(response) {
                    error!("Failed to send Julia task response");
                }
            }
        });

        let init_timeout = std::time::Duration::from_secs(30);
        match init_rx.recv_timeout(init_timeout) {
            Ok(Ok(_)) => Ok(tx),
            Ok(Err(e)) => Err(e),
            Err(_) => Err(anyhow!("Julia runtime initialization timed out after {:?}", init_timeout)),
        }
    }

    /// Allowed Julia function names for security
    const ALLOWED_JULIA_FUNCTIONS: &[&str] = &[
        "main",
        "run_model", 
        "predict",
        "train_model",
        "causal_analysis",
        "ltn_inference",
        "clip_encode",
        "process_data",
    ];

    /// Julia agent that processes tasks via the runtime
    pub struct JuliaAgent {
        sender: Sender<JuliaTask>,
    }

    impl JuliaAgent {
        pub fn new(settings: &Settings) -> Result<Self> {
            let sender = init_julia(settings.clone())?;
            Ok(Self { sender })
        }
    }

    #[async_trait]
    impl Agent for JuliaAgent {
        fn name(&self) -> &str {
            "julia"
        }

        fn agent_type(&self) -> &str {
            "language_model"
        }

        fn capabilities(&self) -> Vec<String> {
            vec!["julia_execute".to_string()]
        }

        async fn health_check(&self) -> Result<crate::agent::AgentHealth> {
            if self.sender.is_closed() {
                let mut health = crate::agent::AgentHealth::default();
                health.status = "unhealthy".to_string();
                health.details = Some("Julia runtime thread has terminated.".to_string());
                return Ok(health);
            }
            Ok(crate::agent::AgentHealth::default())
        }

        async fn handle(&self, input: Value, _memory: Arc<Memory>) -> Result<String> {
            let function_name = input.get("function")
                .and_then(|v| v.as_str())
                .unwrap_or("main")
                .to_string();

            // Validate function name against allowlist
            if !ALLOWED_JULIA_FUNCTIONS.contains(&function_name.as_str()) {
                return Err(anyhow!(
                    "Julia function '{}' not allowed. Permitted functions: {:?}", 
                    function_name, 
                    ALLOWED_JULIA_FUNCTIONS
                ));
            }

            let config = input.get("config")
                .cloned()
                .unwrap_or(input);

            let (response_tx, response_rx) = oneshot::channel();
            let task = JuliaTask {
                function_name,
                json_config: config,
                response: response_tx,
            };

            // Send with timeout to handle backpressure gracefully
            match tokio::time::timeout(
                std::time::Duration::from_secs(5),
                self.sender.send(task)
            ).await {
                Ok(Ok(())) => {},
                Ok(Err(_)) => return Err(anyhow!("Julia runtime channel closed")),
                Err(_) => return Err(anyhow!("Julia task queue full - request timed out")),
            }

            response_rx.await
                .map_err(|_| anyhow!("Julia task response channel closed"))?
        }
    }
}

#[cfg(feature = "with-julia")]
pub use julia_impl::JuliaAgent;

#[cfg(not(feature = "with-julia"))]
pub struct JuliaAgent;

#[cfg(not(feature = "with-julia"))]
impl JuliaAgent {
    pub fn new() -> Result<Self, anyhow::Error> {
        Err(anyhow::anyhow!("Julia support not compiled in. Enable 'with-julia' feature."))
    }
}
