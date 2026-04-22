"""Apex HTTP Event Bus integration for cross-cutting events via the shared integration bus.

This complements the existing Kafka-based event_publisher.py by providing an HTTP-based
alternative for events that need to be visible across all ReliantAI services.

Usage:
    from http_event_bus import publish_cross_cutting_event
    
    # Publish an event that can be consumed by B-A-P, Money, Citadel, etc.
    publish_cross_cutting_event(
        event_type="workflow.completed",
        payload={"workflow_id": "abc123", "result": {...}},
        trace_id="trace-123",
        user_id="user-456"
    )
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

# Add ReliantAI root to sys.path for integration.shared
_RELIANT_ROOT = Path(__file__).resolve().parents[2]
if str(_RELIANT_ROOT) not in sys.path:
    sys.path.insert(0, str(_RELIANT_ROOT))

from integration.shared.event_bus_client import (  # noqa: E402
    publish_sync,
    get_event_sync,
)

APEX_SERVICE_NAME = "apex-agents"


def publish_cross_cutting_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: str | None = None,
    tenant_id: str | None = None,
    use_kafka_also: bool = False,
) -> dict[str, str] | None:
    """Publish an event to the shared HTTP event bus for cross-cutting visibility.
    
    This sends events to the centralized integration event bus (via Kong gateway)
    where they can be consumed by B-A-P, Money, Citadel, and other services.
    
    Args:
        event_type: Type of event (e.g., "workflow.completed")
        payload: Event data/payload
        trace_id: Distributed tracing ID
        user_id: User ID for attribution
        correlation_id: Optional correlation ID (generated if not provided)
        tenant_id: Optional tenant ID
        use_kafka_also: If True, also publish to Kafka (hybrid mode)
        
    Returns:
        Event response dict with event_id, or None if EVENT_BUS_URL not configured
    """
    event_bus_url = os.getenv("EVENT_BUS_URL", "").rstrip("/")
    if not event_bus_url:
        # Graceful degradation - log but don't fail
        print(f"[Apex HTTP Bus] EVENT_BUS_URL not set, skipping HTTP publish for {event_type}")
        return None

    body = {
        "event_type": event_type,
        "payload": {
            **payload,
            "_apex_metadata": {
                "trace_id": trace_id,
                "user_id": user_id,
            }
        },
        "correlation_id": correlation_id or f"{event_type}-{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id or os.getenv("DEFAULT_TENANT_ID", "apex-default"),
        "source_service": APEX_SERVICE_NAME,
    }
    
    try:
        response = publish_sync(body, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        print(f"[Apex HTTP Bus] Published {event_type}: {data.get('event_id', 'unknown')}")
        
        # Optionally also publish to Kafka for backwards compatibility
        if use_kafka_also:
            from event_publisher import publish_workflow_completed, publish_workflow_started
            # Route to appropriate Kafka publisher based on event type
            if event_type == "workflow.completed" and "workflow_id" in payload:
                publish_workflow_completed(
                    workflow_id=payload["workflow_id"],
                    output=payload.get("result", {}),
                    trace_id=trace_id,
                    user_id=user_id
                )
            elif event_type == "workflow.started" and "workflow_id" in payload:
                publish_workflow_started(
                    workflow_id=payload["workflow_id"],
                    task=payload.get("task", ""),
                    trace_id=trace_id,
                    user_id=user_id
                )
        
        return data
    except Exception as exc:
        print(f"[Apex HTTP Bus] Failed to publish {event_type}: {exc}", file=sys.stderr)
        return None


def get_event(event_id: str) -> dict[str, Any] | None:
    """Retrieve an event from the HTTP event bus by ID."""
    event_bus_url = os.getenv("EVENT_BUS_URL", "").rstrip("/")
    if not event_bus_url:
        return None
    
    try:
        return get_event_sync(event_id, timeout=5.0)
    except Exception as exc:
        print(f"[Apex HTTP Bus] Failed to get event {event_id}: {exc}", file=sys.stderr)
        return None


# Convenience functions for common cross-cutting events

def publish_workflow_completed_cross_cutting(
    workflow_id: str,
    output: dict[str, Any],
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_kafka_also: bool = False,
) -> dict[str, str] | None:
    """Publish workflow completion to HTTP bus for cross-service visibility."""
    return publish_cross_cutting_event(
        event_type="workflow.completed",
        payload={
            "workflow_id": workflow_id,
            "result": output,
        },
        trace_id=trace_id,
        user_id=user_id,
        use_kafka_also=use_kafka_also,
    )


def publish_hitl_required_cross_cutting(
    decision_id: str,
    task_summary: str,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_kafka_also: bool = False,
) -> dict[str, str] | None:
    """Publish HITL requirement to HTTP bus for cross-service visibility."""
    return publish_cross_cutting_event(
        event_type="hitl.required",
        payload={
            "decision_id": decision_id,
            "task_summary": task_summary,
        },
        trace_id=trace_id,
        user_id=user_id,
        use_kafka_also=use_kafka_also,
    )


def publish_agent_status_cross_cutting(
    agent_id: str,
    status: str,  # "started", "completed", "failed"
    agent_type: str,
    result: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_kafka_also: bool = False,
) -> dict[str, str] | None:
    """Publish agent status change to HTTP bus for cross-service visibility."""
    payload = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "status": status,
    }
    if result:
        payload["result"] = result
    if error:
        payload["error"] = error
        
    return publish_cross_cutting_event(
        event_type=f"agent.{status}",
        payload=payload,
        trace_id=trace_id,
        user_id=user_id,
        use_kafka_also=use_kafka_also,
    )
