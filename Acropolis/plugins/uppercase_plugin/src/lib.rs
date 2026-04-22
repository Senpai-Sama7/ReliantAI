// plugins/uppercase_plugin/src/lib.rs
//! A minimal Agent that turns text (or a list of texts) into UPPER-CASE.
//!
//! ### Supported JSON commands
//! ```jsonc
//! { "action": "uppercase", "text": "hello" }
//! { "action": "uppercase_many", "texts": ["foo", "bar"] }
//! ```

use adaptive_expert_platform::agent::{Agent, AgentHealth};
use adaptive_expert_platform::memory::Memory;
use adaptive_expert_platform::plugin::PluginRegistrar;
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use serde::Deserialize;
use std::sync::Arc;
use tracing::{info, warn};

#[derive(Deserialize)]
#[serde(rename_all = "snake_case")]
#[serde(tag = "action")]
enum Request {
    Uppercase { text: String },
    UppercaseMany { texts: Vec<String> },
}

pub struct UppercaseAgent;

impl UppercaseAgent {
    pub fn new() -> Self {
        Self
    }

    fn process(&self, req: Request) -> String {
        match req {
            Request::Uppercase { text } => text.to_uppercase(),
            Request::UppercaseMany { texts } => {
                texts.into_iter().map(|s| s.to_uppercase()).collect::<Vec<_>>().join(" ")
            }
        }
    }
}

#[async_trait]
impl Agent for UppercaseAgent {
    fn name(&self) -> &str {
        "uppercase_agent"
    }

    fn agent_type(&self) -> &str {
        "utility"
    }

    fn capabilities(&self) -> Vec<String> {
        vec!["uppercase".to_string()]
    }

    async fn handle(&self, input: serde_json::Value, _memory: Arc<Memory>) -> Result<String> {
        // Handle both structured JSON and simple string inputs
        let request = if let Ok(req) = serde_json::from_value::<Request>(input.clone()) {
            req
        } else if let Some(text) = input.as_str() {
            // Fallback for simple string input
            Request::Uppercase { text: text.to_string() }
        } else {
            return Err(anyhow!("Invalid input format. Expected JSON with 'action' field or simple string"));
        };

        let result = self.process(request);
        info!("Processed uppercase request, output length: {}", result.len());
        Ok(result)
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        Ok(AgentHealth::default())
    }
}

/// Mandatory C-ABI entry-point so the platform can `dlopen` this plugin.
#[no_mangle]
pub extern "C" fn register_plugin(registrar: &mut PluginRegistrar) {
    registrar.register_agent("uppercase_agent", || Box::new(UppercaseAgent::new()));
    info!("Uppercase agent registered successfully");
}
