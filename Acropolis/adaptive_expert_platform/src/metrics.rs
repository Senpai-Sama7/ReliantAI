//! Metrics and tracing utilities with conditional OpenTelemetry support.

#[cfg(feature = "with-observability")]
mod metrics_impl {
    use anyhow::Result;
    use opentelemetry::{global, sdk::export::trace::stdout, sdk::trace, KeyValue};
    use opentelemetry_otlp::WithExportConfig;
    use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

    pub fn init_metrics(otlp_endpoint: Option<&str>) -> Result<()> {
        if let Some(endpoint) = otlp_endpoint {
            let tracer = opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint(endpoint)
                .install_batch(tokio)?;

            let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);

            tracing_subscriber::registry()
                .with(telemetry)
                .with(tracing_subscriber::fmt::layer())
                .init();
        }

        Ok(())
    }
}

#[cfg(feature = "with-observability")]
pub use metrics_impl::init_metrics;

#[cfg(not(feature = "with-observability"))]
pub fn init_metrics(_otlp_endpoint: Option<&str>) -> anyhow::Result<()> {
    // No-op when observability features are disabled
    Ok(())
}
