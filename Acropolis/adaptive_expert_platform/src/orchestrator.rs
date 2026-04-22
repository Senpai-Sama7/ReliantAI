//! Core coordinator that routes tasks to agents (built-in or from plugins).

use std::collections::HashMap;
use std::sync::Arc;
use anyhow::Result;
use serde_json::Value;
use tokio::sync::{mpsc, Mutex, Semaphore};
use tracing::{info, warn, error, instrument};
use uuid::Uuid;

use crate::{
    agent::Agent,
    plugin::{self, PluginEvent, PluginSecurityConfig},
    settings::Settings,
    memory::Memory,
    lifecycle::{LifecycleManager, LifecycleConfig},
    monitoring::{MonitoringSystem, MonitoringConfig},
    cache::{MultiTierCache, MultiTierCacheConfig},
    websocket::{WebSocketServer, WebSocketConfig},
    mesh::{AgentMesh, MeshConfig},
};

type Task = (String, Value, mpsc::Sender<Result<Value>>);

pub struct Orchestrator {
    agents: Arc<Mutex<HashMap<String, Arc<dyn Agent>>>>,
    agent_instances: Arc<Mutex<HashMap<String, Uuid>>>,
    memory: Arc<Memory>,
    plugin_security_config: PluginSecurityConfig,
    task_semaphore: Arc<Semaphore>,
    max_concurrent_tasks: usize,
    _bus: mpsc::Sender<PluginEvent>,
    
    // Advanced systems
    lifecycle_manager: Arc<LifecycleManager>,
    monitoring_system: Arc<MonitoringSystem>,
    cache_system: Arc<MultiTierCache>,
    websocket_server: Arc<WebSocketServer>,
    agent_mesh: Option<Arc<AgentMesh>>,
}

impl Orchestrator {
    #[instrument(skip(settings))]
    pub async fn new(settings: &Settings, memory: Arc<Memory>) -> Result<Self> {
        let (bus_tx, mut bus_rx) = mpsc::channel(16);
        let agents = Arc::new(Mutex::new(HashMap::new()));
        let agent_instances = Arc::new(Mutex::new(HashMap::new()));

        // Initialize plugin security configuration from settings
        let plugin_security_config = PluginSecurityConfig::from_security_config(&settings.security);
        
        // Initialize task throttling semaphore
        let max_concurrent_tasks = settings.orchestrator.max_concurrent_tasks;
        let task_semaphore = Arc::new(Semaphore::new(max_concurrent_tasks));
        
        info!("Orchestrator configured with max {} concurrent tasks", max_concurrent_tasks);

        // Initialize advanced systems
        let lifecycle_manager = Arc::new(LifecycleManager::new(LifecycleConfig::default()));
        let monitoring_config = MonitoringConfig {
            enable_prometheus: settings.observability.enable_metrics,
            prometheus_port: settings.observability.metrics_port,
            ..MonitoringConfig::default()
        };
        let monitoring_system = Arc::new(MonitoringSystem::new(monitoring_config));
        let cache_system = Arc::new(MultiTierCache::new(MultiTierCacheConfig::default()).await?);
        let websocket_server = Arc::new(WebSocketServer::new(WebSocketConfig::default()));
        
        // Initialize agent mesh if enabled (optional)
        let agent_mesh = if settings.orchestrator.enable_mesh_networking.unwrap_or(false) {
            let bind_address: std::net::SocketAddr = format!("{}:{}", settings.server.host, settings.server.port).parse()?;
            let mesh_config = MeshConfig {
                bind_address,
                ..MeshConfig::default()
            };
            Some(Arc::new(AgentMesh::new(mesh_config).await?))
        } else {
            None
        };

        // Start all systems
        lifecycle_manager.start().await?;
        monitoring_system.start().await?;
        websocket_server.start().await?;
        
        if let Some(ref _mesh) = agent_mesh {
            // Note: mesh.start() would need &mut self, so this would need refactoring
            info!("Agent mesh networking enabled");
        }

        info!("All orchestrator subsystems initialized successfully");

        // ---------- secure hot-reload loop ----------
        let agents_reload = agents.clone();
        let security_config_clone = plugin_security_config.clone();

        tokio::spawn(async move {
            while let Some(evt) = bus_rx.recv().await {
                match evt {
                    PluginEvent::Reload(path) => {
                        info!("Processing plugin reload: {:?}", path);

                        match unsafe { plugin::Plugin::load(&path, &security_config_clone) } {
                            Ok(lib) => {
                                match unsafe { lib.instantiate() } {
                                    Ok(agent) => {
                                        let name = agent.name().to_string();
                                        let metadata = lib.metadata();

                                        agents_reload.lock().await.insert(name.clone(), Arc::from(agent));
                                        info!(
                                            "Successfully reloaded plugin '{}' from {:?} (hash: {})",
                                            name, path, &metadata.hash[..16]
                                        );
                                    }
                                    Err(e) => {
                                        error!("Failed to instantiate plugin agent from {:?}: {}", path, e);
                                    }
                                }
                            }
                            Err(e) => {
                                error!("Failed to load plugin from {:?}: {}", path, e);
                            }
                        }
                    }
                    PluginEvent::SecurityViolation(msg) => {
                        warn!("Plugin security violation: {}", msg);
                        // TODO: Implement security incident logging/alerting
                    }
                }
            }
        });

                // start watcher task with security configuration
        let security_config_for_watcher = plugin_security_config.clone();
        let plugin_dir = settings.plugin_dir.clone();
        let bus_tx_clone = bus_tx.clone();

        tokio::spawn(async move {
            if let Err(e) = plugin::hot_reload::watch(
                plugin_dir,
                bus_tx_clone,
                security_config_for_watcher,
            ).await {
                error!("Plugin hot-reload watcher failed: {}", e);
            }
        });

        Ok(Self {
            agents,
            agent_instances,
            memory,
            plugin_security_config,
            task_semaphore,
            max_concurrent_tasks,
            _bus: bus_tx,
            lifecycle_manager,
            monitoring_system,
            cache_system,
            websocket_server,
            agent_mesh,
        })
    }

    /// Dispatch a task `(agent_name, json_in)`; send result via `resp_tx`.
    #[instrument(skip(self, task), fields(agent_name))]
    pub async fn dispatch(&self, task: Task) -> Result<()> {
        let (name, input, resp_tx) = task;
        tracing::Span::current().record("agent_name", &name);

        // Acquire semaphore permit to limit concurrent tasks
        let permit = match self.task_semaphore.try_acquire() {
            Ok(permit) => permit,
            Err(_) => {
                warn!("Task queue full ({} concurrent tasks), rejecting task for agent '{}'", 
                      self.max_concurrent_tasks, name);
                let error = anyhow::anyhow!("Task queue full - too many concurrent tasks");
                let _ = resp_tx.send(Err(error)).await;
                return Ok(());
            }
        };

        let agent = {
            let map = self.agents.lock().await;
            match map.get(&name) {
                Some(agent) => agent.clone(),
                None => {
                    let error = anyhow::anyhow!("Unknown agent '{}'", name);
                    let _ = resp_tx.send(Err(error)).await;
                    return Ok(());
                }
            }
        }; // Release lock before awaiting

        // Execute agent with timeout and error handling
        let memory_clone = self.memory.clone();
        let start = std::time::Instant::now();
        let result = tokio::time::timeout(
            std::time::Duration::from_secs(30), // 30 second timeout
            agent.handle(input, memory_clone)
        ).await;

        let response = match result {
            Ok(Ok(output)) => Ok(Value::String(output)),
            Ok(Err(e)) => {
                error!("Agent '{}' execution failed: {}", name, e);
                self.monitoring_system
                    .record_agent_request(&name, false, start.elapsed())
                    .await;
                Err(e)
            }
            Err(_) => {
                error!("Agent '{}' execution timed out", name);
                self.monitoring_system
                    .record_agent_request(&name, false, start.elapsed())
                    .await;
                Err(anyhow::anyhow!("Agent execution timed out"))
            }
        };

        if response.is_ok() {
            self.monitoring_system
                .record_agent_request(&name, true, start.elapsed())
                .await;
        }

        // Release permit automatically when it goes out of scope
        drop(permit);

        let _ = resp_tx.send(response).await;
        Ok(())
    }

    /// Register a built-in agent
    #[instrument(skip(self, agent))]
    pub async fn register_agent(&self, name: String, agent: Arc<dyn Agent>) -> Result<()> {
        info!("Registering built-in agent: {}", name);
        self.agents.lock().await.insert(name.clone(), agent);
        let instance_id = self
            .lifecycle_manager
            .register_agent_instance(&name)
            .await?;
        self.agent_instances.lock().await.insert(name, instance_id);
        Ok(())
    }

    /// Get list of registered agents with their types
    pub async fn list_agents(&self) -> Vec<(String, String)> {
        let agents_map = self.agents.lock().await;
        agents_map.iter()
            .map(|(name, agent)| (name.clone(), agent.agent_type().to_string()))
            .collect()
    }

    /// Remove a registered agent
    #[instrument(skip(self))]
    pub async fn remove_agent(&self, name: &str) -> Result<()> {
        info!("Removing agent: {}", name);
        if self.agents.lock().await.remove(name).is_some() {
            if let Some(id) = self.agent_instances.lock().await.remove(name) {
                let _ = self.lifecycle_manager.shutdown_agent(id).await;
            }
            Ok(())
        } else {
            Err(anyhow::anyhow!("Agent '{}' not found", name))
        }
    }

    /// Get plugin security configuration
    pub fn plugin_security_config(&self) -> &PluginSecurityConfig {
        &self.plugin_security_config
    }

    /// Update plugin security configuration
    pub fn update_plugin_security_config(&mut self, config: PluginSecurityConfig) {
        self.plugin_security_config = config;
    }

    /// Get a clone of the memory system
    pub fn memory(&self) -> Arc<Memory> {
        self.memory.clone()
    }

    /// Get monitoring system handle
    pub fn monitoring(&self) -> Arc<MonitoringSystem> {
        self.monitoring_system.clone()
    }

    /// Gracefully shutdown all running agents
    pub async fn shutdown(&self) -> Result<()> {
        self.lifecycle_manager.shutdown_all().await
    }

    /// Get the number of memory fragments
    pub async fn get_memory_fragment_count(&self) -> usize {
        self.memory.get_fragment_count().await
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::agent::EchoAgent;
    use crate::memory::Memory;
    use crate::memory::redis_store::InMemoryEmbeddingCache;
    use std::sync::Arc;

    #[tokio::test]
    async fn test_orchestrator_agent_registration() {
        let cache = Arc::new(InMemoryEmbeddingCache::new());
        let echo_agent = Arc::new(EchoAgent::new());
        let memory = Arc::new(Memory::new(
            echo_agent.clone(),
            echo_agent.clone(),
            cache,
        ));

        let mut settings = crate::settings::Settings::default();
        settings.observability.enable_metrics = false;
        let orchestrator = Orchestrator::new(&settings, memory).await.unwrap();

        // Register an agent
        let agent = Arc::new(EchoAgent::new());
        orchestrator.register_agent("test_echo".to_string(), agent).await.unwrap();

        // Verify agent is registered
        let agents = orchestrator.list_agents().await;
        assert!(agents.iter().any(|(name, _)| name == "test_echo"));
    }

    #[tokio::test]
    async fn test_orchestrator_dispatch_timeout() {
        let cache = Arc::new(InMemoryEmbeddingCache::new());
        let echo_agent = Arc::new(EchoAgent::new());
        let memory = Arc::new(Memory::new(
            echo_agent.clone(),
            echo_agent.clone(),
            cache,
        ));

        let mut settings = crate::settings::Settings::default();
        settings.observability.enable_metrics = false;
        let orchestrator = Orchestrator::new(&settings, memory).await.unwrap();

        // Test dispatching to non-existent agent
        let (tx, mut rx) = mpsc::channel(1);
        let task = ("nonexistent".to_string(), Value::String("test".to_string()), tx);

        orchestrator.dispatch(task).await.unwrap();
        let result = rx.recv().await.unwrap();
        assert!(result.is_err());
    }
}
