//! Comprehensive monitoring and metrics system

use anyhow::Result;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use dashmap::DashMap;
use tracing::{info, instrument};

#[cfg(feature = "with-metrics")]
use {
    prometheus::Registry,
    metrics::{counter, histogram, gauge},
};

/// System health status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum HealthStatus {
    Healthy,
    Warning,
    Critical,
    Unknown,
}

/// Metric data point
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricPoint {
    pub timestamp: u64,
    pub value: f64,
    pub labels: HashMap<String, String>,
}

/// Time series metric
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeSeries {
    pub name: String,
    pub metric_type: MetricType,
    pub points: Vec<MetricPoint>,
    pub retention_duration: Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MetricType {
    Counter,
    Gauge,
    Histogram,
    Summary,
}

/// Agent performance metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentMetrics {
    pub agent_name: String,
    pub total_requests: u64,
    pub successful_requests: u64,
    pub failed_requests: u64,
    pub average_response_time_ms: f64,
    pub p50_response_time_ms: f64,
    pub p95_response_time_ms: f64,
    pub p99_response_time_ms: f64,
    pub current_concurrent_requests: u32,
    pub max_concurrent_requests: u32,
    pub memory_usage_bytes: u64,
    pub cpu_usage_percent: f64,
    pub last_updated: SystemTime,
}

impl Default for AgentMetrics {
    fn default() -> Self {
        Self {
            agent_name: String::new(),
            total_requests: 0,
            successful_requests: 0,
            failed_requests: 0,
            average_response_time_ms: 0.0,
            p50_response_time_ms: 0.0,
            p95_response_time_ms: 0.0,
            p99_response_time_ms: 0.0,
            current_concurrent_requests: 0,
            max_concurrent_requests: 0,
            memory_usage_bytes: 0,
            cpu_usage_percent: 0.0,
            last_updated: SystemTime::now(),
        }
    }
}

/// System-wide metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub uptime_seconds: u64,
    pub total_memory_bytes: u64,
    pub used_memory_bytes: u64,
    pub cpu_cores: u32,
    pub cpu_usage_percent: f64,
    pub disk_usage_percent: f64,
    pub network_bytes_in: u64,
    pub network_bytes_out: u64,
    pub active_connections: u32,
    pub goroutines: u32,
    pub heap_size_bytes: u64,
    pub gc_count: u64,
    pub last_gc_duration_ms: f64,
}

/// Health check configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheckConfig {
    pub name: String,
    pub enabled: bool,
    pub interval_seconds: u64,
    pub timeout_seconds: u64,
    pub failure_threshold: u32,
    pub success_threshold: u32,
    pub endpoint: Option<String>,
    pub expected_status: Option<u16>,
    pub command: Option<Vec<String>>,
    pub custom_check: Option<String>,
}

/// Health check result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheckResult {
    pub check_name: String,
    pub status: HealthStatus,
    pub message: Option<String>,
    pub duration_ms: u64,
    pub timestamp: SystemTime,
    pub metadata: HashMap<String, serde_json::Value>,
}

/// Alert configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertConfig {
    pub name: String,
    pub enabled: bool,
    pub metric_name: String,
    pub condition: AlertCondition,
    pub threshold: f64,
    pub duration_seconds: u64,
    pub severity: AlertSeverity,
    pub channels: Vec<AlertChannel>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AlertCondition {
    GreaterThan,
    LessThan,
    Equal,
    NotEqual,
    GreaterThanOrEqual,
    LessThanOrEqual,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum AlertSeverity {
    Info,
    Warning,
    Critical,
    Emergency,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AlertChannel {
    Email(String),
    Slack(String),
    Webhook(String),
    PagerDuty(String),
}

/// Active alert
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub id: Uuid,
    pub config: AlertConfig,
    pub triggered_at: SystemTime,
    pub resolved_at: Option<SystemTime>,
    pub current_value: f64,
    pub message: String,
    pub status: AlertStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AlertStatus {
    Firing,
    Resolved,
    Silenced,
}

/// Comprehensive monitoring system
pub struct MonitoringSystem {
    // Core components
    metrics_store: Arc<MetricsStore>,
    health_checker: Arc<HealthChecker>,
    alert_manager: Arc<AlertManager>,
    
    // Configuration
    config: MonitoringConfig,
    
    // Runtime state
    system_start_time: Instant,
    agent_metrics: Arc<DashMap<String, AgentMetrics>>,
    
    // Prometheus integration
    #[cfg(feature = "with-metrics")]
    prometheus_registry: Arc<Registry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitoringConfig {
    pub metrics_retention_hours: u64,
    pub health_check_interval_seconds: u64,
    pub metrics_collection_interval_seconds: u64,
    pub enable_prometheus: bool,
    pub prometheus_port: u16,
    pub enable_alerts: bool,
    pub alert_evaluation_interval_seconds: u64,
    pub max_alert_history: usize,
}

impl Default for MonitoringConfig {
    fn default() -> Self {
        Self {
            metrics_retention_hours: 168, // 7 days
            health_check_interval_seconds: 30,
            metrics_collection_interval_seconds: 15,
            enable_prometheus: true,
            prometheus_port: 9090,
            enable_alerts: true,
            alert_evaluation_interval_seconds: 60,
            max_alert_history: 10000,
        }
    }
}

impl MonitoringSystem {
    /// Create a new monitoring system
    pub fn new(config: MonitoringConfig) -> Self {
        let metrics_store = Arc::new(MetricsStore::new());
        let health_checker = Arc::new(HealthChecker::new());
        let alert_manager = Arc::new(AlertManager::new());
        
        #[cfg(feature = "with-metrics")]
        let prometheus_registry = Arc::new(Registry::new());
        
        Self {
            metrics_store,
            health_checker,
            alert_manager,
            config,
            system_start_time: Instant::now(),
            agent_metrics: Arc::new(DashMap::new()),
            
            #[cfg(feature = "with-metrics")]
            prometheus_registry,
        }
    }

    /// Start the monitoring system
    #[instrument(skip(self))]
    pub async fn start(&self) -> Result<()> {
        info!("Starting comprehensive monitoring system");

        // Start metrics collection
        self.start_metrics_collection().await;
        
        // Start health checks
        self.start_health_checks().await;
        
        // Start alert evaluation
        if self.config.enable_alerts {
            self.start_alert_evaluation().await;
        }
        
        // Start Prometheus exporter
        #[cfg(feature = "with-metrics")]
        if self.config.enable_prometheus {
            self.start_prometheus_exporter().await?;
        }

        info!("Monitoring system started successfully");
        Ok(())
    }

    /// Record agent request metrics
    #[instrument(skip(self))]
    pub async fn record_agent_request(
        &self,
        agent_name: &str,
        success: bool,
        duration: Duration,
    ) {
        let mut metrics = self.agent_metrics
            .entry(agent_name.to_string())
            .or_insert_with(|| {
                let mut m = AgentMetrics::default();
                m.agent_name = agent_name.to_string();
                m
            });

        metrics.total_requests += 1;
        if success {
            metrics.successful_requests += 1;
        } else {
            metrics.failed_requests += 1;
        }

        let duration_ms = duration.as_millis() as f64;
        metrics.average_response_time_ms = 
            (metrics.average_response_time_ms + duration_ms) / 2.0;
        
        metrics.last_updated = SystemTime::now();

        // Record Prometheus metrics
        #[cfg(feature = "with-metrics")]
        {
            counter!("agent_requests_total", "agent" => agent_name.to_string())
                .increment(1);
            
            if success {
                counter!("agent_requests_successful_total", "agent" => agent_name.to_string())
                    .increment(1);
            } else {
                counter!("agent_requests_failed_total", "agent" => agent_name.to_string())
                    .increment(1);
            }
            
            histogram!("agent_request_duration_seconds", "agent" => agent_name.to_string())
                .record(duration.as_secs_f64());
        }
    }

    /// Get agent metrics
    pub async fn get_agent_metrics(&self, agent_name: &str) -> Option<AgentMetrics> {
        self.agent_metrics.get(agent_name).map(|entry| entry.clone())
    }

    /// Get all agent metrics
    pub async fn get_all_agent_metrics(&self) -> HashMap<String, AgentMetrics> {
        self.agent_metrics
            .iter()
            .map(|entry| (entry.key().clone(), entry.value().clone()))
            .collect()
    }

    /// Get system metrics
    pub async fn get_system_metrics(&self) -> SystemMetrics {
        SystemMetrics {
            uptime_seconds: self.system_start_time.elapsed().as_secs(),
            total_memory_bytes: get_total_memory(),
            used_memory_bytes: get_used_memory(),
            cpu_cores: num_cpus::get() as u32,
            cpu_usage_percent: get_cpu_usage(),
            disk_usage_percent: get_disk_usage(),
            network_bytes_in: get_network_bytes_in(),
            network_bytes_out: get_network_bytes_out(),
            active_connections: get_active_connections(),
            goroutines: get_goroutine_count(),
            heap_size_bytes: get_heap_size(),
            gc_count: get_gc_count(),
            last_gc_duration_ms: get_last_gc_duration(),
        }
    }

    /// Add health check
    pub async fn add_health_check(&self, config: HealthCheckConfig) -> Result<()> {
        self.health_checker.add_check(config).await
    }

    /// Get health status
    pub async fn get_health_status(&self) -> HealthStatus {
        self.health_checker.get_overall_status().await
    }

    /// Get all health check results
    pub async fn get_health_checks(&self) -> Vec<HealthCheckResult> {
        self.health_checker.get_all_results().await
    }

    /// Add alert configuration
    pub async fn add_alert(&self, config: AlertConfig) -> Result<()> {
        self.alert_manager.add_alert(config).await
    }

    /// Get active alerts
    pub async fn get_active_alerts(&self) -> Vec<Alert> {
        self.alert_manager.get_active_alerts().await
    }

    /// Start metrics collection loop
    async fn start_metrics_collection(&self) {
        let interval = self.config.metrics_collection_interval_seconds;
        let agent_metrics = self.agent_metrics.clone();
        
        tokio::spawn(async move {
            let mut collection_interval = tokio::time::interval(
                Duration::from_secs(interval)
            );
            
            loop {
                collection_interval.tick().await;
                
                // Collect system metrics
                Self::collect_system_metrics(&agent_metrics).await;
            }
        });
    }

    /// Collect system-wide metrics
    async fn collect_system_metrics(agent_metrics: &DashMap<String, AgentMetrics>) {
        // Update system-level metrics
        #[cfg(feature = "with-metrics")]
        {
            gauge!("system_memory_used_bytes").set(get_used_memory() as f64);
            gauge!("system_cpu_usage_percent").set(get_cpu_usage());
            gauge!("system_active_connections").set(get_active_connections() as f64);
        }

        // Update agent-specific metrics
        for mut entry in agent_metrics.iter_mut() {
            let metrics = entry.value_mut();
            metrics.memory_usage_bytes = get_agent_memory_usage(&metrics.agent_name);
            metrics.cpu_usage_percent = get_agent_cpu_usage(&metrics.agent_name);
        }
    }

    /// Start health check loop
    async fn start_health_checks(&self) {
        let health_checker = self.health_checker.clone();
        let interval = self.config.health_check_interval_seconds;
        
        tokio::spawn(async move {
            let mut check_interval = tokio::time::interval(
                Duration::from_secs(interval)
            );
            
            loop {
                check_interval.tick().await;
                health_checker.run_all_checks().await;
            }
        });
    }

    /// Start alert evaluation loop
    async fn start_alert_evaluation(&self) {
        let alert_manager = self.alert_manager.clone();
        let metrics_store = self.metrics_store.clone();
        let interval = self.config.alert_evaluation_interval_seconds;
        
        tokio::spawn(async move {
            let mut eval_interval = tokio::time::interval(
                Duration::from_secs(interval)
            );
            
            loop {
                eval_interval.tick().await;
                alert_manager.evaluate_alerts(&metrics_store).await;
            }
        });
    }

    /// Start Prometheus metrics exporter
    #[cfg(feature = "with-metrics")]
    async fn start_prometheus_exporter(&self) -> Result<()> {
        use axum::{
            body::Body,
            extract::State,
            http::{header, StatusCode},
            response::Response,
            routing::get,
            Router,
        };
        use prometheus::Encoder;
        use tokio::net::TcpListener;
        use tracing::error;

        async fn metrics_handler(State(registry): State<Arc<Registry>>) -> Response<Body> {
            let encoder = prometheus::TextEncoder::new();
            let metric_families = registry.gather();
            let mut buffer = Vec::new();

            match encoder.encode(&metric_families, &mut buffer) {
                Ok(()) => Response::builder()
                    .status(StatusCode::OK)
                    .header(header::CONTENT_TYPE, "text/plain; version=0.0.4")
                    .body(Body::from(buffer))
                    .expect("metrics response body should be valid"),
                Err(e) => Response::builder()
                    .status(StatusCode::INTERNAL_SERVER_ERROR)
                    .body(Body::from(format!("Error encoding metrics: {e}")))
                    .expect("metrics response body should be valid"),
            }
        }

        let registry = self.prometheus_registry.clone();
        let port = self.config.prometheus_port;
        let listener = TcpListener::bind(("0.0.0.0", port)).await?;
        let app = Router::new()
            .route("/metrics", get(metrics_handler))
            .with_state(registry);

        tokio::spawn(async move {
            if let Err(e) = axum::serve(listener, app).await {
                error!("Prometheus metrics server error: {}", e);
            }
        });

        info!("Prometheus metrics exporter started on port {}", port);
        Ok(())
    }
}

/// Metrics storage system
pub struct MetricsStore {
    time_series: Arc<RwLock<HashMap<String, TimeSeries>>>,
}

impl MetricsStore {
    pub fn new() -> Self {
        Self {
            time_series: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn record_metric(&self, name: String, value: f64, labels: HashMap<String, String>) {
        let mut store = self.time_series.write().await;
        let series = store.entry(name.clone()).or_insert_with(|| TimeSeries {
            name: name.clone(),
            metric_type: MetricType::Gauge,
            points: Vec::new(),
            retention_duration: Duration::from_secs(7 * 24 * 3600), // 7 days
        });

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        series.points.push(MetricPoint {
            timestamp,
            value,
            labels,
        });

        // Clean up old points
        let cutoff = timestamp - series.retention_duration.as_secs();
        series.points.retain(|point| point.timestamp > cutoff);
    }
}

/// Health checking system
pub struct HealthChecker {
    checks: Arc<RwLock<HashMap<String, HealthCheckConfig>>>,
    results: Arc<RwLock<HashMap<String, HealthCheckResult>>>,
}

impl HealthChecker {
    pub fn new() -> Self {
        Self {
            checks: Arc::new(RwLock::new(HashMap::new())),
            results: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn add_check(&self, config: HealthCheckConfig) -> Result<()> {
        let mut checks = self.checks.write().await;
        checks.insert(config.name.clone(), config);
        Ok(())
    }

    pub async fn run_all_checks(&self) {
        let checks = self.checks.read().await.clone();

        for (name, config) in &checks {
            if config.enabled {
                let result = self.run_check(config).await;
                let mut results = self.results.write().await;
                results.insert(name.clone(), result);
            }
        }
    }

    async fn run_check(&self, config: &HealthCheckConfig) -> HealthCheckResult {
        let start_time = Instant::now();
        
        // Simulate health check
        let status = if rand::random::<f64>() > 0.1 {
            HealthStatus::Healthy
        } else {
            HealthStatus::Warning
        };

        HealthCheckResult {
            check_name: config.name.clone(),
            status,
            message: Some("Health check completed".to_string()),
            duration_ms: start_time.elapsed().as_millis() as u64,
            timestamp: SystemTime::now(),
            metadata: HashMap::new(),
        }
    }

    pub async fn get_overall_status(&self) -> HealthStatus {
        let results = self.results.read().await;
        
        if results.values().any(|r| r.status == HealthStatus::Critical) {
            HealthStatus::Critical
        } else if results.values().any(|r| r.status == HealthStatus::Warning) {
            HealthStatus::Warning
        } else if results.is_empty() {
            HealthStatus::Unknown
        } else {
            HealthStatus::Healthy
        }
    }

    pub async fn get_all_results(&self) -> Vec<HealthCheckResult> {
        let results = self.results.read().await;
        results.values().cloned().collect()
    }
}

/// Alert management system
pub struct AlertManager {
    configs: Arc<RwLock<HashMap<String, AlertConfig>>>,
    active_alerts: Arc<RwLock<HashMap<Uuid, Alert>>>,
}

impl AlertManager {
    pub fn new() -> Self {
        Self {
            configs: Arc::new(RwLock::new(HashMap::new())),
            active_alerts: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn add_alert(&self, config: AlertConfig) -> Result<()> {
        let mut configs = self.configs.write().await;
        configs.insert(config.name.clone(), config);
        Ok(())
    }

    pub async fn evaluate_alerts(&self, _metrics_store: &MetricsStore) {
        // Alert evaluation logic would go here
        // For now, this is a placeholder
    }

    pub async fn get_active_alerts(&self) -> Vec<Alert> {
        let alerts = self.active_alerts.read().await;
        alerts.values().cloned().collect()
    }
}

// System metric collection functions (platform-specific)
fn get_total_memory() -> u64 { 8_000_000_000 } // 8GB simulated
fn get_used_memory() -> u64 { 4_000_000_000 } // 4GB simulated
fn get_cpu_usage() -> f64 { 45.0 } // 45% simulated
fn get_disk_usage() -> f64 { 60.0 } // 60% simulated
fn get_network_bytes_in() -> u64 { 1_000_000 }
fn get_network_bytes_out() -> u64 { 500_000 }
fn get_active_connections() -> u32 { 150 }
fn get_goroutine_count() -> u32 { 42 }
fn get_heap_size() -> u64 { 100_000_000 }
fn get_gc_count() -> u64 { 25 }
fn get_last_gc_duration() -> f64 { 5.2 }
fn get_agent_memory_usage(_agent_name: &str) -> u64 { 50_000_000 }
fn get_agent_cpu_usage(_agent_name: &str) -> f64 { 15.0 }
