module resolves
_INTEGRATION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _INTEGRATION_ROOT not in sys.path:
    sys.path.insert(0, _INTEGRATION_ROOT)

import json
import asyncio
import threading
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from pydantic import BaseModel, Field, ValidationError
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
import redis.asyncio as redis

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
EVENT_RETENTION_SECONDS = int(os.getenv("EVENT_RETENTION_SECONDS", "86400"))  # 24 hours
DLQ_MAX_SIZE = int(os.getenv("DLQ_MAX_SIZE", "10000"))

# Event Bus API Key authentication
EVENT_BUS_API_KEY = os.getenv("EVENT_BUS_API_KEY")
security = HTTPBearer(auto_error=False)

# Logging
logger = structlog.get_logger()

# Metrics
events_published = Counter(
    "events_published_total", "Total events published", ["channel", "event_type"]
)
events_consumed = Counter(
    "events_consumed_total", "Total events consumed", ["channel", "event_type"]
)
events_failed = Counter(
    "events_failed_total", "Total events failed", ["channel", "reason"]
)
dlq_size = Gauge("dlq_size", "Dead letter queue size")
event_processing_duration = Histogram(
    "event_processing_duration_seconds", "Event processing duration", ["channel"]
)
active_subscribers = Gauge(
    "active_subscribers", "Number of active subscribers", ["channel"]
)

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


async def require_event_bus_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> bool:
    """Require valid API key for event bus endpoints."""
    if not EVENT_BUS_API_KEY:
        # If no API key is configured, deny all requests (fail closed)
        raise HTTPException(
            status_code=503,
            detail="Event Bus API key not configured. Set EVENT_BUS_API_KEY environment variable.",
        )
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if credentials.credentials != EVENT_BUS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for Redis and subscribers"""
    logger.info("event_bus_starting", host=REDIS_HOST, port=REDIS_PORT)
    r = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
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
app = FastAPI(title="ReliantAI Event Bus", lifespan=lifespan)


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
async def publish_event(
    request: EventPublishRequest,
    fastapi_req: Request,
    _auth: bool = Depends(require_event_bus_api_key),
):
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
                source_service=request.source_service,
            ),
            payload=request.payload,
        )

        # Determine channel
        channel = f"events:{request.event_type.split('.')[0]}"

        # Persist event
        event_key = f"event:{event_id}"
        await r.setex(event_key, EVENT_RETENTION_SECONDS, event.model_dump_json())

        # Publish to channel
        await r.publish(channel, event.model_dump_json())

        # Update metrics
        events_published.labels(channel=channel, event_type=request.event_type).inc()
        event_processing_duration.labels(channel=channel).observe(
            time.time() - start_time
        )

        logger.info(
            "event_published",
            event_id=event_id,
            channel=channel,
            event_type=request.event_type,
        )

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
            await r.lpush(
                "dlq:events",
                json.dumps(
                    {
                        "error": str(e),
                        "timestamp": datetime.now(UTC).isoformat(),
                        "request": request.model_dump(),
                    }
                ),
            )
            dlq_size.inc()
        except Exception as dlq_err:
            logger.error("dlq_write_failed", error=str(dlq_err))

        raise HTTPException(status_code=500, detail="Failed to publish event")


@app.get("/event/{event_id}")
async def get_event(
    event_id: str,
    request: Request,
    _auth: bool = Depends(require_event_bus_api_key),
):
    """Retrieve a specific event by ID"""
    r = request.app.state.redis
    try:
        event_key = f"event:{event_id}"
        event_json = await r.get(event_key)

        if event_json:
            try:
                return json.loads(event_json)
            except json.JSONDecodeError as e:
                logger.error("json_decode_error", event_id=event_id, error=str(e))
                raise HTTPException(status_code=500, detail="Invalid JSON in event data")
        else:
            raise HTTPException(status_code=404, detail="Event not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_event_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve event")


@app.get("/dlq")
async def get_dlq(
    request: Request,
    limit: int = 100,
    _auth: bool = Depends(require_event_bus_api_key),
):
    """Get dead letter queue events"""
    # SECURITY FIX: Enforce maximum limit to prevent DoS via memory exhaustion.
    # An attacker could request limit=10000000 to cause excessive memory usage.
    limit = min(max(1, limit), 1000)  # Clamp between 1 and 1000
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
async def subscribe(
    request: SubscriptionRequest,
    _auth: bool = Depends(require_event_bus_api_key),
):
    """Subscribe to a channel (HTTP webhook-style)"""
    return {"status": "subscribed", "channel": request.channel}


@app.get("/metrics")
async def metrics(
    _auth: bool = Depends(require_event_bus_api_key),
):
    """Prometheus metrics endpoint — requires API key authentication"""
    return Response(generate_latest(), media_type="text/plain")


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


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
                    channel = (
                        message["channel"].decode()
                        if isinstance(message["channel"], bytes)
                        else message["channel"]
                    )
                    events_consumed.labels(
                        channel=channel, event_type=event.metadata.event_type
                    ).inc()

                    # Call registered handlers
                    handlers_list = handlers.get(event.metadata.event_type, [])
                    for handler in handlers_list:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event)
                            else:
                                handler(event)
                        except Exception as e:
                            logger.error(
                                "handler_error",
                                error=str(e),
                                event_id=event.metadata.event_id,
                            )
                            events_failed.labels(
                                channel=channel, reason="handler"
                            ).inc()

                            # Send to DLQ
                            await r.lpush(
                                "dlq:handler_errors",
                                json.dumps(
                                    {
                                        "error": str(e),
                                        "event": event_data,
                                        "timestamp": datetime.now(UTC).isoformat(),
                                    }
                                ),
                            )

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

    _host = os.getenv("EVENT_BUS_HOST", "127.0.0.1")
    _port = int(os.getenv("EVENT_BUS_PORT", "8081"))
    uvicorn.run(app, host=_host, port=_port)
