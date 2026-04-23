"""
ReliantAI Platform — Shared OpenTelemetry Instrumentation

Provides automatic distributed tracing for FastAPI services via OpenTelemetry.

Usage:
    from shared.tracing import configure_tracing, trace_span
    configure_tracing(service_name="money")

    # Automatic FastAPI instrumentation (recommended)
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)

    # Manual span creation
    @trace_span("process_dispatch")
    async def process_dispatch(dispatch_id: str):
        ...

Environment:
    OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317  # or tempo:4317
    OTEL_SERVICE_NAME=money
    OTEL_TRACES_SAMPLER=parentbased_traceidratio
    OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling in production
"""

import os
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable, Optional

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.propagate import set_global_textmap, extract, inject
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False


DEFAULT_OTEL_ENDPOINT = "http://jaeger:4317"
DEFAULT_SAMPLER_RATE = "1.0"  # 100% in dev, override in production


def configure_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    otel_endpoint: Optional[str] = None,
    sampler_rate: Optional[str] = None,
) -> Optional[Any]:
    """
    Configure OpenTelemetry tracing for a service.

    Args:
        service_name:     Identifies the service in trace UI (e.g. "money").
        service_version:  Semantic version string.
        otel_endpoint:    OTLP gRPC endpoint. Defaults to env OTEL_EXPORTER_OTLP_ENDPOINT.
        sampler_rate:     Trace sampling ratio (0.0-1.0). Defaults to env OTEL_TRACES_SAMPLER_ARG.

    Returns:
        TracerProvider instance, or None if opentelemetry is not installed.
    """
    if not _HAS_OTEL:
        # Graceful degradation: log but don't crash
        import logging
        logging.getLogger("tracing").warning(
            "OpenTelemetry not installed. Tracing disabled. "
            "Install: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi"
        )
        return None

    endpoint = otel_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_OTEL_ENDPOINT)
    rate = sampler_rate or os.getenv("OTEL_TRACES_SAMPLER_ARG", DEFAULT_SAMPLER_RATE)

    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": os.getenv("ENV", "development"),
        "host.name": os.getenv("HOSTNAME", "unknown"),
    })

    provider = TracerProvider(resource=resource)

    # OTLP exporter (gRPC)
    try:
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    except Exception as e:
        import logging
        logging.getLogger("tracing").warning(f"Failed to create OTLP exporter: {e}")
        return None

    trace.set_tracer_provider(provider)
    set_global_textmap(TraceContextTextMapPropagator())

    import logging
    logging.getLogger("tracing").info(
        f"OpenTelemetry configured: service={service_name} endpoint={endpoint} sampler={rate}"
    )
    return provider


def get_tracer(service_name: str) -> Optional[Any]:
    """Return a tracer for the service, or None if OTel is unavailable."""
    if not _HAS_OTEL:
        return None
    return trace.get_tracer(service_name)


def trace_span(span_name: str, attributes: Optional[dict] = None):
    """
    Decorator to wrap a function in an OpenTelemetry span.

    Usage:
        @trace_span("db_query", {"table": "dispatches"})
        async def fetch_dispatch(dispatch_id: str):
            ...
    """
    def decorator(func: Callable):
        if not _HAS_OTEL:
            return func

        tracer = trace.get_tracer(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                # Add function arguments as attributes (sanitized)
                for idx, arg in enumerate(args):
                    if isinstance(arg, (str, int, float, bool)):
                        span.set_attribute(f"arg.{idx}", arg)
                for k, v in kwargs.items():
                    if isinstance(v, (str, int, float, bool)):
                        span.set_attribute(f"arg.{k}", v)
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_current_trace_id() -> Optional[str]:
    """Return the current trace ID as a hex string, or None if no active span."""
    if not _HAS_OTEL:
        return None
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        return format(ctx.trace_id, "032x")
    return None


def get_current_span_id() -> Optional[str]:
    """Return the current span ID as a hex string, or None if no active span."""
    if not _HAS_OTEL:
        return None
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        return format(ctx.span_id, "016x")
    return None


def inject_trace_context(headers: dict) -> dict:
    """
    Inject the current trace context into HTTP headers for outgoing requests.

    Usage:
        headers = inject_trace_context({"Content-Type": "application/json"})
        async with aiohttp.ClientSession() as session:
            await session.get(url, headers=headers)
    """
    if not _HAS_OTEL:
        return headers
    inject(headers)
    return headers


# Import asyncio for trace_span decorator
import asyncio
