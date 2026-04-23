"""
ReliantAI Platform — Shared Structured JSON Logging Configuration

Usage in any Python service:
    from shared.logging_config import configure_logging, get_logger
    configure_logging(service_name="money", log_level="INFO")
    logger = get_logger()
    logger.info("dispatch_created", dispatch_id=dispatch_id, customer=customer_name)

In production (ENV=production), logs are emitted as structured JSON on stdout.
In development, logs are pretty-printed with colors.
"""

import os
import sys
import logging
import structlog
from typing import Optional


def configure_logging(
    service_name: str,
    log_level: Optional[str] = None,
    json_output: Optional[bool] = None,
) -> None:
    """
    Configure structlog and stdlib logging for the service.

    Args:
        service_name:  Identifier used in every log record (e.g. "money").
        log_level:     "DEBUG", "INFO", "WARNING", "ERROR". Defaults to env LOG_LEVEL or "INFO".
        json_output:   True  → JSON lines (production).
                       False → pretty console (development).
                       None  → inferred from ENV env var.
    """
    level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    is_production = (json_output is None and os.getenv("ENV", "development").lower() == "production") or json_output is True

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if is_production:
        # Production: compact JSON, no colors
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ExtraAdder(),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
        )
    else:
        # Development: pretty console with colors
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ExtraAdder(),
                structlog.dev.ConsoleRenderer(colors=True),
            ],
        )

    # stdlib handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # structlog configuration
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Inject service name into every log record via stdlib adapter
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record

    logging.setLogRecordFactory(record_factory)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger instance."""
    return structlog.get_logger(name)
