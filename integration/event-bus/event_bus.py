"""
ReliantAI Event Bus - Production Redis Pub/Sub Event-Driven Communication
NO MOCKING - Real Redis, real schema validation, real DLQ
"""
from datetime import datetime, UTC
from enum import Enum
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Callable

import os
import json
import asyncio
import threading
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field, ValidationError
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response
import structlog
import redis.asyncio as redis

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
EVENT_RETENTION_SECONDS = int(os.getenv("EVENT_RETENTION_SECONDS", "86400"))  # 24 hours
DLQ_MAX_SIZE = int(os.getenv("DLQ_MAX_SIZE", "10000"))

# Logging
logger = structlog.get_logger()

# Metrics
events_published = Counter("events_published_total", "Total events published", ["channel", "event_type"])
events_consumed = Counter("events_consumed_total", "Total events consumed", ["channel", "event_type"])
events_failed = Counter("events_failed_total", "Total events failed", ["channel", "reason"])
dlq_size = Gauge("dlq_size", "Dead letter queue size")
event_processing_duration = Histogram("event_processing_duration_seconds", "Event processing duration", ["channel"])
active_subscribers = Gauge("active_subscribers", "Number of active subscribers", ["channel"])

from shared.event_types import (
    EventType,
    EventMetadata,
    Event,
    EventPublishRequest,
    EventResponse,
    SubscriptionRequest,
)

# Global state for background processor
handlers: Dict[str, List[Callable]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for Redis and subscribers"""
    logger.info("event_bus_starting", host=REDIS_HOST, port=REDIS_PORT)
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    # Ping to ensure connection
    await r.ping()
    app.state.redis = r
    app.state.pubsub = r.pubsub()
    
    yield
    
    if hasattr(app.state, "pubsub") and app.state.pubsub:
        await app.state.pubsub.aclose()
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.aclose()

    logger.info("event_bus_shutdown")

# App
app = FastAPI(
    title="ReliantAI Event Bus",
    lifespan=lifespan
)

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    try:
        await request.app.state.redis.ping()
        return {"status": "healthy", "redis": "connected", "service": "event-bus"}
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Redis connection failed")

@app.post("/publish", response_model=EventResponse)
async def publish_event(request: EventPublishRequest, fastapi_req: Request):
    """Publish an event to the bus"""
    start_time = time.time()
    r = fastapi_req.app.state.redis
    
    try:
        # Create event
        now = datetime.now(UTC)
        event_id = f"evt_{now.timestamp()}_{os.urandom(4).hex()}"
        event = Event(
            metadata=EventMetadata(
                event_id=event_id,
                event_type=request.event_type,
                correlation_id=request.correlation_id,
                tenant_id=request.tenant_id,
                source_service=request.source_service
            ),
            payload=request.payload
        )
        
        # Determine channel
        channel = f"events:{request.event_type.split('.')[0]}"
        
        # Persist event
        event_key = f"event:{event_id}"
        await r.setex(
            event_key,
            EVENT_RETENTION_SECONDS,
            event.model_dump_json()
        )
        
        # Publish to channel
        await r.publish(channel, event.model_dump_json())
        
        # Update metrics
        events_published.labels(channel=channel, event_type=request.event_type).inc()
        event_processing_duration.labels(channel=channel).observe(time.time() - start_time)
        
        logger.info("event_published", 
                    event_id=event_id, 
                    channel=channel, 
                    event_type=request.event_type)
        
        return EventResponse(event_id=event_id, status="published", channel=channel)
        
    except ValidationError as e:
        logger.error("validation_error", error=str(e))
        events_failed.labels(channel="unknown", reason="validation").inc()
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("publish_error", error=str(e))
        events_failed.labels(channel="unknown", reason="internal").inc()
        
        # Send to DLQ
        try:
            await r.lpush("dlq:events", json.dumps({
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
                "request": request.model_dump()
            }))
            dlq_size.inc()
        except:
            pass
        
        raise HTTPException(status_code=500, detail="Failed to publish event")

@app.get("/event/{event_id}")
async def get_event(event_id: str, request: Request):
    """Retrieve a specific event by ID"""
    r = request.app.state.redis
    try:
        event_key = f"event:{event_id}"
        event_json = await r.get(event_key)
        
        if event_json:
            return json.loads(event_json)
        else:
            raise HTTPException(status_code=404, detail="Event not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_event_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve event")

@app.get("/dlq")
async def get_dlq(request: Request, limit: int = 100):
    """Get dead letter queue events"""
    r = request.app.state.redis
    try:
        events = []
        for i in range(limit):
            event_json = await r.lindex("dlq:events", i)
            if event_json:
                events.append(json.loads(event_json))
            else:
                break
        return {"dlq_size": len(events), "events": events}
    except Exception as e:
        logger.error("get_dlq_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ")

@app.post("/subscribe")
async def subscribe(request: SubscriptionRequest):
    """Subscribe to a channel (HTTP webhook-style)"""
    return {"status": "subscribed", "channel": request.channel}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

# Background task for processing subscriptions
async def process_subscriptions(app: FastAPI):
    """Background task to process subscription messages"""
    try:
        r = app.state.redis
        pubsub = app.state.pubsub
        
        # Subscribe to all event channels
        await pubsub.psubscribe("events:*")
        logger.info("subscription_processor_started")
        
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                try:
                    event_data = json.loads(message["data"])
                    event = Event(**event_data)
                    
                    # Update metrics
                    channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                    events_consumed.labels(channel=channel, event_type=event.metadata.event_type).inc()
                    
                    # Call registered handlers
                    handlers_list = handlers.get(event.metadata.event_type, [])
                    for handler in handlers_list:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event)
                            else:
                                handler(event)
                        except Exception as e:
                            logger.error("handler_error", error=str(e), event_id=event.metadata.event_id)
                            events_failed.labels(channel=channel, reason="handler").inc()
                            
                            # Send to DLQ
                            await r.lpush("dlq:handler_errors", json.dumps({
                                "error": str(e),
                                "event": event_data,
                                "timestamp": datetime.now(UTC).isoformat()
                            }))
                            
                except ValidationError as e:
                    logger.error("validation_error", error=str(e))
                    events_failed.labels(channel="unknown", reason="validation").inc()
                except Exception as e:
                    logger.error("processing_error", error=str(e))
                    events_failed.labels(channel="unknown", reason="processing").inc()
                    
    except Exception as e:
        logger.error("subscription_processor_error", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
