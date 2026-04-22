// Prevents a console window from appearing on Windows in release builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use adaptive_expert_platform::agent::{Agent, EchoAgent, LlmAgent, PythonToolAgent};
use adaptive_expert_platform::orchestrator::Orchestrator;
use adaptive_expert_platform::settings::{Settings, Task};
use anyhow::{anyhow, Result};
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::sync::Arc;
use tauri::Manager;
use tokio::sync::Mutex;
use tracing::info;

// The state of our application backend, managed by Tauri.
pub struct AppState {
    orchestrator: Arc<Mutex<Orchestrator>>,
}

// Loads all task configurations from the `configs` directory.
fn load_tasks_from_dir(path: &str) -> Result<HashMap<String, Task>> {
    let mut tasks = HashMap::new();
    if !Path::new(path).exists() {
        info!("'{}' directory not found, skipping task loading.", path);
        return Ok(tasks);
    }
    for entry in fs::read_dir(path)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_file() && path.extension().map_or(false, |e| e == "toml") {
            let task_name = path.file_stem().unwrap().to_str().unwrap().to_string();
            let content = fs::read_to_string(&path)?;
            let task: Task = toml::from_str(&content)?;
            tasks.insert(task_name, task);
        }
    }
    Ok(tasks)
}

// Exposes the `execute_task` function to the JavaScript frontend.
#[tauri::command]
async fn execute_task(
    task_name: String,
    state: tauri::State<'_, AppState>,
) -> Result<String, String> {
    let orchestrator = state.orchestrator.lock().await;
    orchestrator
        .execute_task(&task_name)
        .await
        .map_err(|e| e.to_string())
}

// Exposes a function to get the list of available tasks for the frontend.
#[tauri::command]
async fn list_tasks(state: tauri::State<'_, AppState>) -> Result<Vec<String>, String> {
    let orchestrator = state.orchestrator.lock().await;
    // In a real app, you'd pull the tasks from the orchestrator state.
    // For this example, we reload them.
    let tasks = load_tasks_from_dir("configs").map_err(|e| e.to_string())?;
    Ok(tasks.keys().cloned().collect())
}

fn main() {
    // This is the setup logic for your backend.
    let orchestrator_instance = tokio::runtime::Runtime::new()
        .unwrap()
        .block_on(async {
            let settings = Settings::new().expect("Failed to load settings.");
            tracing_subscriber::fmt()
                .with_max_level(settings.logging.log_level)
                .init();
            info!("Backend starting up for Tauri...");

            // This assumes the 'llama' feature is enabled for the main library
            let mut llm_agents: HashMap<String, Arc<dyn Agent>> = HashMap::new();
            for agent_config in &settings.llm.agents {
                let agent =
                    LlmAgent::new(&agent_config.name, &agent_config.model_path).unwrap();
                llm_agents.insert(agent_config.name.clone(), Arc::new(agent));
            }

            let embedding_agent = llm_agents
                .get("embedding_agent")
                .expect("Core 'embedding_agent' not found.")
                .clone();
            let reranker_agent = llm_agents
                .get("reranker_agent")
                .expect("Core 'reranker_agent' not found.")
                .clone();

            let mut orchestrator = Orchestrator::new(embedding_agent, reranker_agent);

            for (name, agent) in llm_agents {
                orchestrator.register_agent(agent);
                info!("Registered core LLM agent: '{}'", name);
            }

            orchestrator.register_agent(Arc::new(EchoAgent));
            orchestrator.register_agent(Arc::new(PythonToolAgent::new()));

            if let Err(e) = orchestrator.load_plugins(&settings.plugins.native_directory) {
                tracing::error!("Failed to load plugins: {}", e);
            }
            
            let tasks = load_tasks_from_dir("configs").unwrap_or_default();
            for (name, task) in tasks {
                orchestrator.register_task(&name, task);
                info!("Registered task: '{}'", name);
            }
            
            info!("Backend initialization complete.");
            Arc::new(Mutex::new(orchestrator))
        });

    // Build and run the Tauri application.
    tauri::Builder::default()
        .manage(AppState {
            orchestrator: orchestrator_instance,
        })
        .invoke_handler(tauri::generate_handler![execute_task, list_tasks])
        .run(tauri::generate_context!())
        .expect("Error while running Tauri application");
}
