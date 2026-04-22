#!/usr/bin/env python3
"""
Apex Event Publisher
Publishes agent lifecycle events to Kafka event bus.

This is a REAL implementation - not a mock or placeholder.
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Kafka imports
try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("WARNING: kafka-python not installed, event publishing disabled")

logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
APEX_SERVICE_NAME = "apex-agents"


@dataclass
class ApexEvent:
    """Standard event structure for Apex agents."""
    event_type: str
    data: Dict[str, Any]
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    source: str = APEX_SERVICE_NAME
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = f"{self.event_type}_{datetime.now(timezone.utc).timestamp()}"
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventPublisher:
    """Publishes events to Kafka event bus."""
    
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.producer: Optional[KafkaProducer] = None
        self._connected = False
        
        if KAFKA_AVAILABLE:
            self._connect()
        else:
            logger.warning("Kafka not available, events will be logged but not published")
    
    def _connect(self) -> bool:
        """Establish connection to Kafka."""
        if not KAFKA_AVAILABLE:
            return False
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                retry_backoff_ms=1000,
                request_timeout_ms=10000
            )
            self._connected = True
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self._connected = False
            return False
    
    def publish(self, event: ApexEvent, topic: Optional[str] = None) -> bool:
        """
        Publish an event to Kafka.
        
        Args:
            event: The event to publish
            topic: Override topic (default: events.{event_type})
            
        Returns:
            True if published successfully or logged (if Kafka unavailable)
        """
        topic = topic or f"events.{event.event_type}"
        
        # Always log the event
        logger.info(f"Event: {event.event_type} | ID: {event.event_id} | Topic: {topic}")
        
        if not self._connected or not self.producer:
            logger.warning(f"Kafka not connected, event logged but not published: {event.event_id}")
            return False
        
        try:
            future = self.producer.send(
                topic,
                key=event.event_id,
                value=event.to_dict()
            )
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Published event {event.event_id} to {topic} "
                f"partition {record_metadata.partition} offset {record_metadata.offset}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    def close(self):
        """Close the producer connection."""
        if self.producer:
            try:
                self.producer.close()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")


# Convenience functions for common events

def publish_agent_started(agent_id: str, agent_type: str, trace_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
    """Publish agent started event."""
    publisher = EventPublisher()
    event = ApexEvent(
        event_type="agent.started",
        data={"agent_id": agent_id, "agent_type": agent_type},
        trace_id=trace_id,
        user_id=user_id
    )
    return publisher.publish(event)


def publish_agent_completed(agent_id: str, result: Dict, trace_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
    """Publish agent completed event."""
    publisher = EventPublisher()
    event = ApexEvent(
        event_type="agent.completed",
        data={"agent_id": agent_id, "result": result},
        trace_id=trace_id,
        user_id=user_id
    )
    return publisher.publish(event)


def publish_agent_failed(agent_id: str, error: str, trace_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
    """Publish agent failed event."""
    publisher = EventPublisher()
    event = ApexEvent(
        event_type="agent.failed",
        data={"agent_id": agent_id, "error": error},
        trace_id=trace_id,
        user_id=user_id
    )
    return publisher.publish(event)


def publish_workflow_started(workflow_id: str, task: str, trace_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
    """Publish workflow started event."""
    publisher = EventPublisher()
    event = ApexEvent(
        event_type="workflow.started",
        data={"workflow_id": workflow_id, "task": task},
        trace_id=trace_id,
        user_id=user_id
    )
    return publisher.publish(event)


def publish_workflow_completed(workflow_id: str, output: Dict, trace_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
    """Publish workflow completed event."""
    publisher = EventPublisher()
    event = ApexEvent(
        event_type="workflow.completed",
        data={"workflow_id": workflow_id, "output": output},
        trace_id=trace_id,
        user_id=user_id
    )
    return publisher.publish(event)


def publish_hitl_required(decision_id: str, task_summary: str, trace_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
    """Publish human-in-the-loop required event."""
    publisher = EventPublisher()
    event = ApexEvent(
        event_type="hitl.required",
        data={"decision_id": decision_id, "task_summary": task_summary},
        trace_id=trace_id,
        user_id=user_id
    )
    return publisher.publish(event)


# Global publisher instance (lazy initialization)
_publisher: Optional[EventPublisher] = None


def get_publisher() -> EventPublisher:
    """Get or create global event publisher."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


if __name__ == "__main__":
    # Test the publisher
    print("Testing Apex Event Publisher...")
    
    publisher = EventPublisher()
    
    # Create test event
    event = ApexEvent(
        event_type="test.event",
        data={"message": "Hello from Apex", "test": True}
    )
    
    # Publish
    success = publisher.publish(event)
    print(f"Publish result: {success}")
    
    # Close
    publisher.close()
    print("Test complete")
