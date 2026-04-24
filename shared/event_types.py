"""
Shared event types for ReliantAI integration layer.
Defines central schemas for all cross-service communication.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    LEAD_CREATED = "lead.created"
    LEAD_QUALIFIED = "lead.qualified"
    DISPATCH_REQUESTED = "dispatch.requested"
    DISPATCH_COMPLETED = "dispatch.completed"
    DOCUMENT_PROCESSED = "document.processed"
    AGENT_TASK_CREATED = "agent.task.created"
    AGENT_TASK_COMPLETED = "agent.task.completed"
    ANALYTICS_RECORDED = "analytics.recorded"
    SAGA_STARTED = "saga.started"
    SAGA_COMPLETED = "saga.completed"
    SAGA_FAILED = "saga.failed"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    AUDIT_LOG_RECORDED = "audit.log"


class EventMetadata(BaseModel):
    # SECURITY FIX: Added max_length constraints to prevent memory exhaustion attacks.
    # Previously all strings were unbounded, allowing very long strings to be sent.
    event_id: str = Field(..., max_length=64, description="Unique event identifier")
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    correlation_id: str = Field(
        ..., max_length=128, description="Request correlation ID"
    )
    tenant_id: str = Field(..., max_length=64)
    source_service: str = Field(..., max_length=64)
    version: str = Field(default="1.0", max_length=16)


class Event(BaseModel):
    metadata: EventMetadata
    payload: Dict[str, Any] = Field(default_factory=dict)


class EventPublishRequest(BaseModel):
    # SECURITY FIX: Added max_length constraints to prevent memory exhaustion.
    event_type: EventType
    payload: Dict[str, Any] = Field(
        default_factory=dict
    )  # 64KB max payload - enforced via custom validator below
    correlation_id: str = Field(..., max_length=128)
    tenant_id: str = Field(..., max_length=64)
    source_service: str = Field(..., max_length=64)

    @field_validator("payload")
    @classmethod
    def validate_payload_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payload size (serialized JSON must be under 64KB)."""
        import json
        try:
            serialized = json.dumps(v, separators=(",", ":"))
            if len(serialized.encode("utf-8")) > 65536:
                raise ValueError("Payload exceeds 64KB limit")
        except (TypeError, ValueError) as e:
            if "Payload exceeds" in str(e):
                raise
            raise ValueError(f"Payload cannot be serialized: {e}")
        return v


class EventResponse(BaseModel):
    event_id: str = Field(..., max_length=64)
    status: str = Field(..., max_length=32)
    channel: str = Field(..., max_length=128)


class SubscriptionRequest(BaseModel):
    channel: str = Field(..., max_length=128)
    event_types: Optional[List[EventType]] = Field(default_factory=list, max_length=100)
