// plugins/dqn_plugin/src/lib.rs
//! Simple Q-Learning agent – sample native plugin (simplified version without torch).

use adaptive_expert_platform::agent::{Agent, AgentHealth};
use adaptive_expert_platform::memory::Memory;
use adaptive_expert_platform::plugin::PluginRegistrar;
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use rand::Rng;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;
use tracing::{info, warn, debug};

/// Hyper-parameters for the Q-learning agent (JSON-loadable).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QLearningConfig {
    pub learning_rate: f64,
    pub discount_factor: f64,
    pub epsilon: f64,  // exploration rate
    pub epsilon_decay: f64,
    pub min_epsilon: f64,
    pub state_dim: usize,
    pub action_count: usize,
}

impl Default for QLearningConfig {
    fn default() -> Self {
        Self {
            learning_rate: 0.1,
            discount_factor: 0.95,
            epsilon: 1.0,
            epsilon_decay: 0.995,
            min_epsilon: 0.01,
            state_dim: 4,
            action_count: 2,
        }
    }
}

/// Simple state representation for demonstration
#[derive(Debug, Clone, Hash, Eq, PartialEq)]
struct State {
    values: Vec<i32>,
}

impl State {
    fn from_observation(obs: &[f64]) -> Self {
        // Discretize continuous observations for simple Q-table
        let values = obs.iter()
            .map(|&x| (x * 10.0).round() as i32)
            .collect();
        Self { values }
    }
}

/// Simple Q-Learning agent implementation.
pub struct QLearningAgent {
    config: Mutex<QLearningConfig>,
    q_table: Mutex<HashMap<(State, usize), f64>>,
    last_state: Mutex<Option<State>>,
    last_action: Mutex<Option<usize>>,
    steps: Mutex<u64>,
    total_reward: Mutex<f64>,
    request_count: AtomicU64,
    error_count: AtomicU64,
    start_time: Instant,
}

impl QLearningAgent {
    pub fn new() -> Self {
        Self {
            config: Mutex::new(QLearningConfig::default()),
            q_table: Mutex::new(HashMap::new()),
            last_state: Mutex::new(None),
            last_action: Mutex::new(None),
            steps: Mutex::new(0),
            total_reward: Mutex::new(0.0),
            request_count: AtomicU64::new(0),
            error_count: AtomicU64::new(0),
            start_time: Instant::now(),
        }
    }

    /// Load configuration from JSON string
    fn load_config(&self, config_json: &str) -> Result<()> {
        let config: QLearningConfig = serde_json::from_str(config_json)?;
        *self.config.lock().unwrap() = config.clone();
        info!(?config, "Q-Learning config loaded");
        Ok(())
    }

    /// Get Q-value for state-action pair
    fn get_q_value(&self, state: &State, action: usize) -> f64 {
        let q_table = self.q_table.lock().unwrap();
        *q_table.get(&(state.clone(), action)).unwrap_or(&0.0)
    }

    /// Set Q-value for state-action pair
    fn set_q_value(&self, state: State, action: usize, value: f64) {
        let mut q_table = self.q_table.lock().unwrap();
        q_table.insert((state, action), value);
    }

    /// Choose action using epsilon-greedy strategy
    fn choose_action(&self, state: &State) -> usize {
        let config = self.config.lock().unwrap();
        let mut rng = rand::thread_rng();

        // Epsilon-greedy action selection
        if rng.gen::<f64>() < config.epsilon {
            // Random action (exploration)
            rng.gen_range(0..config.action_count)
        } else {
            // Best action (exploitation)
            (0..config.action_count)
                .max_by(|&a, &b| {
                    self.get_q_value(state, a)
                        .partial_cmp(&self.get_q_value(state, b))
                        .unwrap_or(std::cmp::Ordering::Equal)
                })
                .unwrap_or(0)
        }
    }

    /// Update Q-value using Q-learning update rule
    fn update_q_value(&self, state: State, action: usize, reward: f64, next_state: &State) {
        let config = self.config.lock().unwrap();

        // Find maximum Q-value for next state
        let max_next_q = (0..config.action_count)
            .map(|a| self.get_q_value(next_state, a))
            .fold(f64::NEG_INFINITY, f64::max);

        // Q-learning update: Q(s,a) = Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        let current_q = self.get_q_value(&state, action);
        let target = reward + config.discount_factor * max_next_q;
        let new_q = current_q + config.learning_rate * (target - current_q);

        self.set_q_value(state, action, new_q);

        debug!("Q-update: state={:?}, action={}, reward={:.3}, current_q={:.3}, new_q={:.3}",
               state.values, action, reward, current_q, new_q);
    }

    /// Decay epsilon for reduced exploration over time
    fn decay_epsilon(&self) {
        let mut config = self.config.lock().unwrap();
        config.epsilon = (config.epsilon * config.epsilon_decay).max(config.min_epsilon);
    }

    /// Process a step in the environment
    fn step(&self, observation: Vec<f64>, reward: f64) -> Result<serde_json::Value> {
        let state = State::from_observation(&observation);
        let action = self.choose_action(&state);

        // Update Q-value if we have a previous state-action pair
        if let (Some(last_state), Some(last_action)) = (
            self.last_state.lock().unwrap().clone(),
            *self.last_action.lock().unwrap()
        ) {
            self.update_q_value(last_state, last_action, reward, &state);
        }

        // Update state tracking
        *self.last_state.lock().unwrap() = Some(state.clone());
        *self.last_action.lock().unwrap() = Some(action);

        // Update metrics
        {
            let mut steps = self.steps.lock().unwrap();
            *steps += 1;

            let mut total_reward = self.total_reward.lock().unwrap();
            *total_reward += reward;

            if *steps % 100 == 0 {
                info!("Step {}: Total reward={:.2}, Epsilon={:.3}",
                      *steps, *total_reward, self.config.lock().unwrap().epsilon);
            }
        }

        self.decay_epsilon();

        Ok(serde_json::json!({
            "action": action,
            "q_value": self.get_q_value(&state, action),
            "epsilon": self.config.lock().unwrap().epsilon,
            "steps": *self.steps.lock().unwrap()
        }))
    }

    /// Get agent statistics
    fn get_stats(&self) -> serde_json::Value {
        let q_table = self.q_table.lock().unwrap();
        let config = self.config.lock().unwrap();

        serde_json::json!({
            "steps": *self.steps.lock().unwrap(),
            "total_reward": *self.total_reward.lock().unwrap(),
            "epsilon": config.epsilon,
            "q_table_size": q_table.len(),
            "learning_rate": config.learning_rate,
            "discount_factor": config.discount_factor
        })
    }
}

#[async_trait]
impl Agent for QLearningAgent {
    fn name(&self) -> &str {
        "qlearning"
    }

    fn agent_type(&self) -> &str {
        "reinforcement"
    }

    fn capabilities(&self) -> Vec<String> {
        vec!["configure".to_string(), "step".to_string(), "stats".to_string()]
    }

    async fn handle(&self, input: serde_json::Value, _memory: Arc<Memory>) -> Result<String> {
        self.request_count.fetch_add(1, Ordering::Relaxed);
        // Parse input to determine action
        let result = match input.get("action").and_then(|v| v.as_str()) {
            Some("configure") => {
                let config_str = input.get("config")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| anyhow!("Missing 'config' field for configure action"))?;

                self.load_config(config_str)?;
                Ok("Configuration loaded successfully".to_string())
            }
            Some("step") => {
                let observation = input.get("observation")
                    .and_then(|v| v.as_array())
                    .ok_or_else(|| anyhow!("Missing 'observation' array for step action"))?
                    .iter()
                    .map(|v| v.as_f64().unwrap_or(0.0))
                    .collect::<Vec<f64>>();

                let reward = input.get("reward")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.0);

                let result = self.step(observation, reward)?;
                Ok(serde_json::to_string(&result)?)
            }
            Some("stats") => {
                let stats = self.get_stats();
                Ok(serde_json::to_string(&stats)?)
            }
            Some("reset") => {
                *self.last_state.lock().unwrap() = None;
                *self.last_action.lock().unwrap() = None;
                *self.steps.lock().unwrap() = 0;
                *self.total_reward.lock().unwrap() = 0.0;
                info!("Agent reset");
                Ok("Agent reset successfully".to_string())
            }
            _ => {
                Err(anyhow!("Unknown action. Supported actions: configure, step, stats, reset"))
            }
        };

        if result.is_err() {
            self.error_count.fetch_add(1, Ordering::Relaxed);
        }

        result
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        Ok(AgentHealth {
            status: "healthy".to_string(),
            details: None,
            uptime_seconds: self.start_time.elapsed().as_secs(),
            total_requests: self.request_count.load(Ordering::Relaxed),
            error_count: self.error_count.load(Ordering::Relaxed),
            average_response_time_ms: 0.0,
        })
    }
}

/// Mandatory C-ABI entry-point so the platform can `dlopen` this plugin.
#[no_mangle]
pub extern "C" fn register_plugin(registrar: &mut PluginRegistrar) {
    registrar.register_agent("qlearning", || Box::new(QLearningAgent::new()));
    info!("Q-Learning agent registered successfully");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_qlearning_configure() {
        let agent = QLearningAgent::new();
        let config = serde_json::json!({
            "action": "configure",
            "config": r#"{"learning_rate": 0.2, "discount_factor": 0.9, "epsilon": 0.5}"#
        });

        let result = agent.handle(config, Arc::new(create_dummy_memory())).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_qlearning_step() {
        let agent = QLearningAgent::new();
        let step_input = serde_json::json!({
            "action": "step",
            "observation": [1.0, 2.0, -1.0, 0.5],
            "reward": 10.0
        });

        let result = agent.handle(step_input, Arc::new(create_dummy_memory())).await;
        assert!(result.is_ok());

        let response: serde_json::Value = serde_json::from_str(&result.unwrap()).unwrap();
        assert!(response.get("action").is_some());
        assert!(response.get("q_value").is_some());
    }

    #[tokio::test]
    async fn test_qlearning_stats() {
        let agent = QLearningAgent::new();
        let stats_input = serde_json::json!({
            "action": "stats"
        });

        let result = agent.handle(stats_input, Arc::new(create_dummy_memory())).await;
        assert!(result.is_ok());

        let response: serde_json::Value = serde_json::from_str(&result.unwrap()).unwrap();
        assert!(response.get("steps").is_some());
        assert!(response.get("epsilon").is_some());
    }

    fn create_dummy_memory() -> adaptive_expert_platform::memory::Memory {
        use adaptive_expert_platform::memory::redis_store::InMemoryEmbeddingCache;
        use adaptive_expert_platform::agent::EchoAgent;
        use std::sync::Arc;

        let cache = Arc::new(InMemoryEmbeddingCache::new());
        let echo_agent = Arc::new(EchoAgent);
        adaptive_expert_platform::memory::Memory::new(echo_agent.clone(), echo_agent, cache)
    }
}
