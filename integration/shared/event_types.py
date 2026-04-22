"""
Shared event types for ReliantAI integration layer.
Defines central schemas for all cross-service communication.
"""
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

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
    AUDIT_LOG_RECORDED = "audit.log.recorded"

class EventMetadata(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    correlation_id: str = Field(..., description="Request correlation ID")
    tenant_id: str
    source_service: str
    version: str = "1.0"

class Event(BaseModel):
    metadata: EventMetadata
    payload: Dict[str, Any]

class EventPublishRequest(BaseModel):
    event_type: EventType
    payload: Dict[str, Any]
    correlation_id: str
    tenant_id: str
    source_service: str

class EventResponse(BaseModel):
    event_id: str
    status: str
    channel: str

class SubscriptionRequest(BaseModel):
    channel: str
    event_types: Optional[List[EventType]] = None
