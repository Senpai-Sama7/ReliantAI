"""Shared async event-bus publishing for B-A-P cross-service integrations."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any

# Repo root (ReliantAI/) so ``integration.shared`` resolves under Poetry/runtime.
_RELIANT_ROOT = Path(__file__).resolve().parents[3]
if str(_RELIANT_ROOT) not in sys.path:
    sys.path.insert(0, str(_RELIANT_ROOT))

from integration.shared.event_bus_client import (  # noqa: E402
    publish_async,
    should_verify_tls,
)

# Try to import B-A-P logger, fall back to standard logging
try:
    from src.utils.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger("bap.event_bus")
    logger.setLevel(logging.INFO)


async def publish_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    correlation_id: str | None = None,
    tenant_id: str | None = None,
    source_service: str = "bap",
) -> dict[str, str] | None:
    """Publish an event to the shared integration event bus when configured."""
    event_bus_url = os.getenv("EVENT_BUS_URL", "").rstrip("/")
    if not event_bus_url:
        return None

    body = {
        "event_type": event_type,
        "payload": payload,
        "correlation_id": correlation_id or f"{event_type}-{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id or os.getenv("DEFAULT_TENANT_ID", "bap-default"),
        "source_service": source_service,
    }
    url = f"{event_bus_url}/publish"
    verify = should_verify_tls(url)
    try:
        response = await publish_async(body, timeout=5.0, verify=verify)
        response.raise_for_status()
    except Exception as exc:
        logger.error(f"Failed to publish {event_type} event: {exc}")
        return None

    data = response.json()
    logger.info(f"Published {event_type} event: {data.get('event_id', 'unknown')}")
    return {
        "event_id": str(data["event_id"]),
        "channel": str(data["channel"]),
    }
