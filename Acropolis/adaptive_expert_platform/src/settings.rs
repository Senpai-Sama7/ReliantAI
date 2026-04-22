//! Enhanced configuration management with environment variable support and validation.

use anyhow::{anyhow, Result};
use config::{Config, Environment};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use tracing::warn;

/// Enhanced server configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub max_connections: usize,
    pub request_timeout_seconds: u64,
    pub enable_cors: bool,
    pub cors_origins: Vec<String>,
    pub rate_limit_per_minute: u32,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port: 8080,
            max_connections: 1_000,
            request_timeout_seconds: 30,
            enable_cors: true,
            cors_origins: vec!["*".to_string()],
            rate_limit_per_minute: 1_000,
        }
    }
}

/// Enhanced logging configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingConfig {
    pub level: String,
    pub format: String, // "json" or "text"
    pub output: String, // "stdout", "stderr", or file path
    pub enable_timestamps: bool,
    pub enable_thread_ids: bool,
    pub enable_target: bool,
}

impl Default for LoggingConfig {
    fn default() -> Self {
        Self {
            level: "info".to_string(),
            format: "text".to_string(),
            output: "stdout".to_string(),
            enable_timestamps: true,
            enable_thread_ids: true,
            enable_target: false,
        }
    }
}

/// Enhanced orchestrator configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestratorConfig {
    pub max_concurrent_tasks: usize,
    pub task_timeout_seconds: u64,
    pub enable_hot_reload: bool,
    pub plugin_scan_interval_seconds: u64,
    pub max_plugin_size_mb: usize,
    pub enable_agent_health_checks: bool,
    pub health_check_interval_seconds: u64,
    pub enable_mesh_networking: Option<bool>,
}

impl Default for OrchestratorConfig {
    fn default() -> Self {
        Self {
            max_concurrent_tasks: 10,
            task_timeout_seconds: 300,
            enable_hot_reload: true,
            plugin_scan_interval_seconds: 30,
            max_plugin_size_mb: 50,
            enable_agent_health_checks: true,
            health_check_interval_seconds: 60,
            enable_mesh_networking: Some(false),
        }
    }
}

/// Enhanced plugin configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginConfig {
    pub directory: PathBuf,
    pub allowed_extensions: Vec<String>,
    pub require_signatures: bool,
    pub signature_public_key_path: Option<PathBuf>,
    pub max_plugin_size_mb: usize,
    pub enable_sandboxing: bool,
    pub sandbox_timeout_seconds: u64,
}

impl Default for PluginConfig {
    fn default() -> Self {
        Self {
            directory: PathBuf::from("plugins"),
            allowed_extensions: vec![".so".to_string(), ".dll".to_string(), ".dylib".to_string()],
            require_signatures: true,
            signature_public_key_path: None,
            max_plugin_size_mb: 50,
            enable_sandboxing: true,
            sandbox_timeout_seconds: 30,
        }
    }
}

/// Enhanced memory configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryConfig {
    pub provider: String, // "in_memory", "redis", "postgres"
    pub url: Option<String>,
    pub max_fragments: usize,
    pub embedding_dim: usize,
    pub similarity_threshold: f32,
    pub cache_size: usize,
    pub enable_persistence: bool,
    pub persistence_path: Option<PathBuf>,
}

impl Default for MemoryConfig {
    fn default() -> Self {
        Self {
            provider: "in_memory".to_string(),
            url: None,
            max_fragments: 10_000,
            embedding_dim: 384,
            similarity_threshold: 0.1,
            cache_size: 1_000,
            enable_persistence: false,
            persistence_path: None,
        }
    }
}

/// Enhanced LLM configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmConfig {
    pub provider: String, // "llama", "openai", "anthropic"
    pub models: HashMap<String, LlmModelConfig>,
    pub default_model: String,
    pub max_tokens: usize,
    pub temperature: f32,
    pub enable_streaming: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmModelConfig {
    pub path: String,
    pub context_size: usize,
    pub max_tokens: usize,
    pub temperature: f32,
    pub top_p: f32,
    pub top_k: usize,
}

impl Default for LlmConfig {
    fn default() -> Self {
        let mut models = HashMap::new();
        models.insert("default".to_string(), LlmModelConfig {
            path: "models/llama-2-7b.gguf".to_string(),
            context_size: 2_048,
            max_tokens: 512,
            temperature: 0.7,
            top_p: 0.9,
            top_k: 40,
        });

        Self {
            provider: "llama".to_string(),
            models,
            default_model: "default".to_string(),
            max_tokens: 512,
            temperature: 0.7,
            enable_streaming: false,
        }
    }
}

/// Enhanced security configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConfig {
    pub enable_authentication: bool,
    pub jwt_secret: Option<String>,
    pub jwt_expiry_hours: usize,
    pub api_key_header: String,
    pub allowed_origins: Vec<String>,
    pub enable_rate_limiting: bool,
    pub rate_limit_per_minute: u32,
    pub enable_cors: bool,
    pub max_request_size_mb: usize,
    pub enable_plugin_signatures: bool,
    pub plugin_allowlist_hashes: Vec<String>,
    pub script_allowlist_hashes: HashMap<String, String>,
    pub max_plugin_size_mb: usize,
    pub enable_resource_limits: bool,
    pub max_execution_time_seconds: u64,
    pub max_memory_mb: usize,
    pub enable_security_headers: bool,
    pub session_timeout_minutes: u64,
    pub max_login_attempts: u32,
    pub lockout_duration_minutes: u64,
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            enable_authentication: true, // Secure by default
            jwt_secret: None, // Must be provided in production
            jwt_expiry_hours: 8, // 8 hour JWT expiry
            api_key_header: "X-API-Key".to_string(),
            allowed_origins: vec!["https://localhost:3000".to_string()], // Restrictive by default
            enable_rate_limiting: true,
            rate_limit_per_minute: 100, // More restrictive default
            enable_cors: false, // Disabled by default for security
            max_request_size_mb: 5, // Smaller default size
            enable_plugin_signatures: true, // Always require signatures
            plugin_allowlist_hashes: vec![], // Empty by default - must be configured
            script_allowlist_hashes: HashMap::new(),
            max_plugin_size_mb: 10, // Smaller plugin size limit
            enable_resource_limits: true,
            max_execution_time_seconds: 30,
            max_memory_mb: 512,
            enable_security_headers: true,
            session_timeout_minutes: 480, // 8 hours
            max_login_attempts: 5,
            lockout_duration_minutes: 15,
        }
    }
}

/// Enhanced observability configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObservabilityConfig {
    pub enable_metrics: bool,
    pub metrics_port: u16,
    pub enable_tracing: bool,
    pub tracing_sampler: f64, // 0.0 to 1.0
    pub enable_profiling: bool,
    pub profiling_port: u16,
    pub otlp_endpoint: Option<String>,
    pub jaeger_endpoint: Option<String>,
}

impl Default for ObservabilityConfig {
    fn default() -> Self {
        Self {
            enable_metrics: true,
            metrics_port: 9090,
            enable_tracing: true,
            tracing_sampler: 0.1,
            enable_profiling: false,
            profiling_port: 6060,
            otlp_endpoint: None,
            jaeger_endpoint: None,
        }
    }
}

/// Main settings structure with all configuration sections
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub server: ServerConfig,
    pub logging: LoggingConfig,
    pub orchestrator: OrchestratorConfig,
    pub plugins: PluginConfig,
    pub memory: MemoryConfig,
    pub llm: LlmConfig,
    pub security: SecurityConfig,
    pub observability: ObservabilityConfig,
    pub db_path: Option<String>,

    // Legacy fields for backward compatibility
    pub plugin_dir: PathBuf,
    pub otlp_endpoint: Option<String>,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            server: ServerConfig::default(),
            logging: LoggingConfig::default(),
            orchestrator: OrchestratorConfig::default(),
            plugins: PluginConfig::default(),
            memory: MemoryConfig::default(),
            llm: LlmConfig::default(),
            security: SecurityConfig::default(),
            observability: ObservabilityConfig::default(),
            db_path: None,

            // Legacy fields
            plugin_dir: PathBuf::from("plugins"),
            otlp_endpoint: None,
        }
    }
}

impl Settings {
    /// Load settings from configuration files and environment variables
    pub fn load() -> Result<Self> {
        let config = Config::builder()
            // Start with default settings
            .add_source(config::File::from_str(
                include_str!("../config.toml"),
                config::FileFormat::Toml,
            ))
            // Add local config file if it exists
            .add_source(config::File::with_name("config").required(false))
            // Add environment variables with AEP_ prefix
            .add_source(
                Environment::with_prefix("AEP")
                    .separator("__")
                    .list_separator(",")
                    .try_parsing(true)
            )
            .build()?;

        let mut settings: Settings = config.try_deserialize()?;

        // Apply environment variable overrides for critical settings
        Self::apply_env_overrides(&mut settings)?;

        // Validate settings
        settings.validate()?;

        Ok(settings)
    }

    /// Apply environment variable overrides
    fn apply_env_overrides(settings: &mut Settings) -> Result<()> {
        // Server settings
        if let Ok(host) = std::env::var("AEP_SERVER_HOST") {
            settings.server.host = host;
        }
        if let Ok(port) = std::env::var("AEP_SERVER_PORT") {
            settings.server.port = port.parse()?;
        }

        // Plugin settings
        if let Ok(plugin_dir) = std::env::var("AEP_PLUGIN_DIR") {
            settings.plugin_dir = PathBuf::from(plugin_dir);
            settings.plugins.directory = settings.plugin_dir.clone();
        }

        // Observability settings
        if let Ok(otlp_endpoint) = std::env::var("AEP_OTLP_ENDPOINT") {
            settings.otlp_endpoint = Some(otlp_endpoint.clone());
            settings.observability.otlp_endpoint = Some(otlp_endpoint);
        }

        // Security settings
        if let Ok(jwt_secret) = std::env::var("AEP_JWT_SECRET") {
            settings.security.jwt_secret = Some(jwt_secret);
        }

        // Memory settings
        if let Ok(memory_url) = std::env::var("AEP_MEMORY_URL") {
            settings.memory.url = Some(memory_url);
        }

        // LLM settings
        if let Ok(model_path) = std::env::var("AEP_LLM_MODEL_PATH") {
            if let Some(default_model) = settings.llm.models.get_mut(&settings.llm.default_model) {
                default_model.path = model_path;
            }
        }

        Ok(())
    }

    /// Validate settings for consistency and security
    pub fn validate(&self) -> Result<()> {
        // Server validation
        if self.server.port == 0 {
            return Err(anyhow!("Server port cannot be 0"));
        }
        if self.server.max_connections == 0 {
            return Err(anyhow!("Max connections cannot be 0"));
        }

        // Plugin validation
        if !self.plugins.directory.exists() {
            warn!("Plugin directory does not exist: {:?}", self.plugins.directory);
        }

        // Memory validation
        if self.memory.provider == "redis" && self.memory.url.is_none() {
            return Err(anyhow!("Redis provider requires AEP_MEMORY_URL environment variable"));
        }

        // Security validation
        if self.security.enable_authentication && self.security.jwt_secret.is_none() {
            return Err(anyhow!("Authentication enabled but no JWT secret provided"));
        }

        // LLM validation
        if self.llm.provider == "llama" {
            let default_model = self.llm.models.get(&self.llm.default_model)
                .ok_or_else(|| anyhow!("Default LLM model not found"))?;

            if !std::path::Path::new(&default_model.path).exists() {
                warn!("LLM model file does not exist: {}", default_model.path);
            }
        }

        Ok(())
    }

    /// Get a configuration value by path (e.g., "server.port")
    pub fn get<T: serde::de::DeserializeOwned>(&self, path: &str) -> Result<T> {
        let value = serde_json::to_value(self)?;
        let value = value.pointer(path)
            .ok_or_else(|| anyhow!("Configuration path not found: {}", path))?;

        Ok(serde_json::from_value(value.clone())?)
    }

    /// Check if a feature is enabled
    pub fn is_feature_enabled(&self, feature: &str) -> bool {
        match feature {
            "authentication" => self.security.enable_authentication,
            "rate_limiting" => self.security.enable_rate_limiting,
            "cors" => self.security.enable_cors,
            "metrics" => self.observability.enable_metrics,
            "tracing" => self.observability.enable_tracing,
            "profiling" => self.observability.enable_profiling,
            "hot_reload" => self.orchestrator.enable_hot_reload,
            "health_checks" => self.orchestrator.enable_agent_health_checks,
            "sandboxing" => self.plugins.enable_sandboxing,
            "persistence" => self.memory.enable_persistence,
            "streaming" => self.llm.enable_streaming,
            _ => false,
        }
    }
}
