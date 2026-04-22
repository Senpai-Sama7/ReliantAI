"""Shared async event-bus publishing for B-A-P cross-service integrations."""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx

from src.utils.logger import get_logger

logger = get_logger()


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

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{event_bus_url}/publish",
                json={
                    "event_type": event_type,
                    "payload": payload,
                    "correlation_id": correlation_id or f"{event_type}-{uuid.uuid4().hex[:12]}",
                    "tenant_id": tenant_id or os.getenv("DEFAULT_TENANT_ID", "bap-default"),
                    "source_service": source_service,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error(
            f"Failed to publish {event_type} event: {exc}",
            event_type=event_type,
            source_service=source_service,
        )
        return None

    body = response.json()
    logger.info(
        f"Published {event_type} event",
        event_type=event_type,
        event_id=body.get("event_id"),
        channel=body.get("channel"),
    )
    return {
        "event_id": str(body["event_id"]),
        "channel": str(body["channel"]),
    }
