"""
Verbose telemetry logging for all agent operations.

Every action, decision, error, and retry is logged with full context.
Supports structured logging to stderr, file, and optional OTLP export.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from typing import Any

import structlog


def setup_logging(
    level: str | None = None,
    log_file: str | None = None,
    json_format: bool = True,
) -> None:
    """Configure structured logging for the entire agents package."""
    log_level = (level or os.environ.get("AGENTS_LOG_LEVEL", "INFO")).upper()

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(
            file=open(log_file, "a") if log_file else sys.stderr
        ),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level),
        handlers=[logging.StreamHandler(sys.stderr if not log_file else open(log_file, "a"))],
    )


def get_logger(name: str) -> Any:
    """Get a structured logger with the given name."""
    return structlog.get_logger(name)


class Telemetry:
    """Context manager and decorator for instrumenting agent operations."""

    def __init__(self, operation: str, agent: str, **context: Any):
        self.operation = operation
        self.agent = agent
        self.context = context
        self.start_time: float = 0
        self.logger = get_logger(f"agents.telemetry.{agent}")

    def __enter__(self) -> Telemetry:
        self.start_time = time.monotonic()
        self.logger.info(
            "operation_start",
            operation=self.operation,
            agent=self.agent,
            **self.context,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration = time.monotonic() - self.start_time
        if exc_val:
            self.logger.error(
                "operation_failed",
                operation=self.operation,
                agent=self.agent,
                duration_ms=round(duration * 1000, 2),
                error_type=exc_type.__name__ if exc_type else None,
                error=str(exc_val),
                **self.context,
            )
        else:
            self.logger.info(
                "operation_complete",
                operation=self.operation,
                agent=self.agent,
                duration_ms=round(duration * 1000, 2),
                **self.context,
            )

    @contextmanager
    def step(self, step_name: str, **extra: Any):
        """Track a sub-step within an operation."""
        step_start = time.monotonic()
        self.logger.info(
            "step_start",
            operation=self.operation,
            step=step_name,
            agent=self.agent,
            **extra,
        )
        try:
            yield
            self.logger.info(
                "step_complete",
                operation=self.operation,
                step=step_name,
                agent=self.agent,
                duration_ms=round((time.monotonic() - step_start) * 1000, 2),
                **extra,
            )
        except Exception as e:
            self.logger.error(
                "step_failed",
                operation=self.operation,
                step=step_name,
                agent=self.agent,
                duration_ms=round((time.monotonic() - step_start) * 1000, 2),
                error=str(e),
                **extra,
            )
            raise
