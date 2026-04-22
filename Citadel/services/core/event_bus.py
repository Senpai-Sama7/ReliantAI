"""Citadel shared event-bus integration for cross-service communication."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any

# Add ReliantAI root to sys.path for integration.shared
_RELIANT_ROOT = Path(__file__).resolve().parents[4]
if str(_RELIANT_ROOT) not in sys.path:
    sys.path.insert(0, str(_RELIANT_ROOT))

from integration.shared.event_bus_client import (  # noqa: E402
    publish_sync,
    get_event_sync,
)


def publish_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    correlation_id: str | None = None,
    tenant_id: str | None = None,
    source_service: str = "citadel",
) -> dict[str, str] | None:
    """Publish an event to the shared integration event bus when configured.
    
    Uses synchronous publish for Citadel's synchronous service architecture.
    Returns None if EVENT_BUS_URL not configured (graceful degradation).
    """
    event_bus_url = os.getenv("EVENT_BUS_URL", "").rstrip("/")
    if not event_bus_url:
        return None

    body = {
        "event_type": event_type,
        "payload": payload,
        "correlation_id": correlation_id or f"{event_type}-{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id or os.getenv("DEFAULT_TENANT_ID", "citadel-default"),
        "source_service": source_service,
    }
    
    try:
        response = publish_sync(body, timeout=5.0)
        response.raise_for_status()
    except Exception as exc:
        # Log but don't fail - event bus is best-effort
        print(f"[Citadel Event Bus] Failed to publish {event_type}: {exc}", file=sys.stderr)
        return None

    data = response.json()
    print(f"[Citadel Event Bus] Published {event_type}: {data.get('event_id', 'unknown')}")
    return data


def get_event(event_id: str) -> dict[str, Any] | None:
    """Retrieve an event from the event bus by ID."""
    event_bus_url = os.getenv("EVENT_BUS_URL", "").rstrip("/")
    if not event_bus_url:
        return None
    
    try:
        return get_event_sync(event_id, timeout=5.0)
    except Exception as exc:
        print(f"[Citadel Event Bus] Failed to get event {event_id}: {exc}", file=sys.stderr)
        return None
