//! Logging and telemetry initialization with conditional OpenTelemetry support.

use anyhow::Result;
use tracing_subscriber::{layer::SubscriberExt, EnvFilter, Registry};

#[cfg(feature = "with-observability")]
use {
    opentelemetry::{sdk::Resource, global as otel_global},
    opentelemetry_otlp::{self as otlp, WithExportConfig},
    tracing_opentelemetry,
};

/// Initialize logging and telemetry based on configuration
pub fn init(_otlp_endpoint: Option<&str>) -> Result<()> {
    let filter = EnvFilter::try_from_default_env()
        .or_else(|_| EnvFilter::try_new("info"))?;

    #[cfg(feature = "with-observability")]
    if let Some(endpoint) = otlp_endpoint {
        init_with_otlp(endpoint, filter)
    } else {
        init_console_only(filter)
    }

    #[cfg(not(feature = "with-observability"))]
    init_console_only(filter)
}

#[cfg(feature = "with-observability")]
fn init_with_otlp(endpoint: &str, filter: EnvFilter) -> Result<()> {
    let tracer = otlp::new_pipeline()
        .tracing()
        .with_exporter(otlp::new_exporter().tonic().with_endpoint(endpoint))
        .with_trace_config(opentelemetry::sdk::trace::config().with_resource(
            Resource::new(vec![opentelemetry::KeyValue::new("service.name", "adaptive_expert_platform")])
        ))
        .install_batch(opentelemetry::runtime::Tokio)?;

    let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);

    let subscriber = Registry::default()
        .with(filter)
        .with(tracing_subscriber::fmt::layer().with_target(false))
        .with(telemetry);

    tracing::subscriber::set_global_default(subscriber)?;

    // Set up global text map propagator
    otel_global::set_text_map_propagator(opentelemetry::sdk::propagation::TraceContextPropagator::new());

    tracing::info!("Telemetry initialized with OTLP endpoint: {}", endpoint);
    Ok(())
}

fn init_console_only(filter: EnvFilter) -> Result<()> {
    let subscriber = Registry::default()
        .with(filter)
        .with(tracing_subscriber::fmt::layer().with_target(false));

    tracing::subscriber::set_global_default(subscriber)?;
    tracing::info!("Console logging initialized");
    Ok(())
}
