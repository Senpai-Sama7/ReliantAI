"""
Unified Audit Log publisher for ReliantAI.
"""
import httpx
import os
import uuid
import structlog
from typing import Dict, Any, Optional

from .event_types import EventType, EventPublishRequest
from .event_bus_client import get_event_bus_url, publish_request_headers

logger = structlog.get_logger()

async def emit_audit(
    action: str,
    actor: str,
    target: Optional[str] = None,
    tenant_id: str = "system",
    source_service: str = "unknown",
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an event and push it over HTTP to the Event Bus.
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
        
    payload = {
        "action": action,
        "actor": actor,
        "target": target,
        "details": details or {}
    }
    
    # Log locally
    logger.info("audit_event", **payload, tenant_id=tenant_id, source_service=source_service, correlation_id=correlation_id)
    
    # Push to event bus
    try:
        event = EventPublishRequest(
            event_type=EventType.AUDIT_LOG_RECORDED,
            payload=payload,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            source_service=source_service
        )
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{get_event_bus_url()}/publish",
                json=event.model_dump(),
                headers=publish_request_headers(),
            )
            response.raise_for_status()
    except Exception as e:
        logger.error("failed_to_emit_audit_event", error=str(e), action=action, correlation_id=correlation_id)
