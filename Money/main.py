"""
FastAPI production server for HVAC AI Dispatch
Endpoints:
  POST /dispatch      — API dispatch (JSON body, bearer token or x-api-key auth)
  POST /sms           — Twilio SMS webhook (incoming customer texts)
  POST /whatsapp      — Twilio WhatsApp webhook
  GET  /health        — liveness probe
  GET  /run/{id}      — async job status
  GET  /dispatches    — recent dispatch history

Deploy: uvicorn main:app --host 0.0.0.0 --port 8000
"""

import asyncio
import hashlib
import hmac
import json
import os
import re
import sys
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

# Resolve workspace shared code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from integration.shared.event_types import EventPublishRequest, EventType
from integration.shared.event_bus_client import publish_sync as _event_bus_publish_sync

import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    PlainTextResponse,
    HTMLResponse,
    RedirectResponse,
    FileResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from twilio.request_validator import RequestValidator

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from config import DISPATCH_API_KEY, TWILIO_TOKEN, ENV, setup_logging
from database import (
    init_db,
    save_dispatch,
    update_dispatch_status,
    get_dispatch,
    get_recent_dispatches,
    log_message,
    log_customer_event,
)
from metrics import get_metrics_response, DISPATCH_JOB_DURATION
from billing import router as billing_router, validate_api_key, check_dispatch_quota, PRICING

logger = setup_logging("hvac_api")
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8080").rstrip(
    "/"
)

# ── Session auth ──────────────────────────────────────────────
_SESSION_SECRET = os.environ.get("SESSION_SECRET", DISPATCH_API_KEY)
_SESSION_MAX_AGE = 86400  # 24 hours
_ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
_ADMIN_PASS = os.environ.get("ADMIN_PASS", DISPATCH_API_KEY)
_signer = URLSafeTimedSerializer(_SESSION_SECRET)
_SESSION_COOKIE = "dispatch_session"
_LOGIN_CSRF_COOKIE = "dispatch_login_csrf"
_LOGIN_CSRF_SALT = "dispatch-login-csrf"
_LOGIN_CSRF_MAX_AGE = 3600


def _create_session_cookie(username: str) -> str:
    return _signer.dumps({"u": username})


def _create_login_csrf_token() -> str:
    return _signer.dumps({"t": uuid.uuid4().hex}, salt=_LOGIN_CSRF_SALT)


def _get_session_user(request: Request) -> str | None:
    token = request.cookies.get(_SESSION_COOKIE)
    if not token:
        return None
    try:
        data = _signer.loads(token, max_age=_SESSION_MAX_AGE)
        return data.get("u")
    except (BadSignature, SignatureExpired):
        return None


def _validate_login_csrf_token(
    form_token: str | None, cookie_token: str | None
) -> bool:
    if not form_token or not cookie_token:
        return False
    if not hmac.compare_digest(form_token, cookie_token):
        return False
    try:
        data = _signer.loads(
            form_token, salt=_LOGIN_CSRF_SALT, max_age=_LOGIN_CSRF_MAX_AGE
        )
    except (BadSignature, SignatureExpired):
        return False
    return bool(data.get("t")) if isinstance(data, dict) else False


def _render_login_page(request: Request, error: str | None, status_code: int = 200):
    csrf_token = _create_login_csrf_token()
    response = _templates.TemplateResponse(
        request,
        "login.html",
        {"error": error, "csrf_token": csrf_token},
        status_code=status_code,
    )
    response.set_cookie(
        _LOGIN_CSRF_COOKIE,
        csrf_token,
        max_age=_LOGIN_CSRF_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=ENV == "production",
    )
    return response


# ── Lifespan management (startup/shutdown) ───────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown."""
    # Startup
    # Validate production config (blocks deployment with placeholder values)
    try:
        from shared.security_middleware import validate_production_config
        validate_production_config()
    except RuntimeError as e:
        logger.error(f"Production configuration validation failed: {e}")
        raise
    init_db()
    try:
        from hvac_dispatch_crew import warmup_node
        warmup_node()
        logger.info("Agent warm-up complete — first dispatch will have no cold-start penalty")
    except Exception as e:
        logger.warning(
            f"Agent warm-up failed at startup: {e}. "
            "First dispatch request will incur agent initialization latency."
        )
    logger.info("HVAC AI Dispatch API started — database initialized")
    
    yield
    
    # Shutdown
    logger.info("HVAC AI Dispatch API shutting down")


# ── App setup ─────────────────────────────────────────────────
app = FastAPI(
    title="Houston HVAC AI Dispatch API",
    version="2.0.0",
    description="Multi-agent AI dispatcher for Houston HVAC shops",
    lifespan=lifespan,
)

# Include billing router
app.include_router(billing_router)

_templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

# ── Static Files (Unified Frontend) ──────────────────────────
# Check if frontend is built and mount static files
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")

if os.path.exists(frontend_assets):
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")
    logger.info(f"✅ Mounted frontend assets from {frontend_assets}")
else:
    logger.warning(
        "⚠️ Frontend not built. Run: cd frontend && npm install && npm run build"
    )


_cors_raw = os.environ.get("CORS_ORIGINS", "")
_cors_origins = (
    [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else []
)

# SECURITY FIX: In production, require explicit CORS_ORIGINS configuration
# Do NOT default to localhost origins in production
if ENV == "dev":
    # In dev, allow localhost origins
    if not _cors_origins:
        _cors_origins.extend(
            [
                "http://localhost:5173",  # Vite dev server
                "http://localhost:3000",  # Common dev port
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
        )
elif not _cors_origins:
    # In production, fail explicitly if CORS_ORIGINS not set
    logger.warning(
        "SECURITY WARNING: CORS_ORIGINS not set in production! API will reject all cross-origin requests."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,  # Important for session cookies
    allow_methods=["POST", "GET", "PUT", "DELETE", "OPTIONS"],
    # SECURITY FIX: Removed wildcard "*" from allow_headers. Only explicit headers allowed.
    allow_headers=["x-api-key", "content-type", "authorization"],
    expose_headers=["Content-Length", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enterprise security headers interceptor."""
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# In-memory job store (supplement to PostgreSQL — keeps async status)
job_store: dict = {}
# Anti-DDoS rudimentary rate-limiter store mapping {phone_number: float_timestamp}
rate_limit_store: dict = {}
# MAX STORE LIMITS (Prevent Memory DoS)
MAX_STORE_SIZE = 1000
MAX_MSG_LENGTH = 1000
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_COUNT = 60
_rate_counters = defaultdict(deque)


def _api_key_configured() -> bool:
    return bool(DISPATCH_API_KEY and DISPATCH_API_KEY != "change-me-in-env")


def _prune_stores():
    """FIFO + TTL pruning to keep memory footprint constant."""
    while len(job_store) > MAX_STORE_SIZE:
        job_store.pop(next(iter(job_store)))
    while len(rate_limit_store) > MAX_STORE_SIZE:
        rate_limit_store.pop(next(iter(rate_limit_store)))
    # Evict stale rate-counter buckets (empty deques or all entries expired)
    now = time.time()
    stale = [
        k
        for k, dq in _rate_counters.items()
        if not dq or (now - dq[-1]) > RATE_LIMIT_WINDOW
    ]
    for k in stale:
        del _rate_counters[k]


def _rate_limit(bucket: str) -> None:
    now = time.time()
    queue = _rate_counters[bucket]
    while queue and now - queue[0] > RATE_LIMIT_WINDOW:
        queue.popleft()
    if len(queue) >= RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    queue.append(now)


def _rate_bucket(request: Request, suffix: str) -> str:
    key = (
        request.headers.get("authorization")
        or request.headers.get("x-api-key")
        or request.client.host
    )
    return f"{suffix}:{key}"


def _get_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise HTTPException(
                    status_code=503, detail="Auth Service unavailable (Circuit Open)"
                )

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except requests.RequestException as exc:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
            logger.error(
                "auth_service_unavailable auth_service_url=%s error=%s",
                AUTH_SERVICE_URL,
                exc,
            )
            raise HTTPException(
                status_code=503, detail="Auth Service unavailable"
            ) from exc


auth_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)


def _verify_bearer_token(token: str) -> dict[str, Any]:
    response = auth_circuit_breaker.call(
        requests.get,
        f"{AUTH_SERVICE_URL}/verify",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.json()


async def _authorize_request(x_api_key: str | None, request: Request | None = None) -> None:
    # Accept valid session cookie as alternative to API key or bearer auth
    if request and _get_session_user(request):
        return

    if request:
        bearer_token = _get_bearer_token(request)
        if bearer_token:
            request.state.current_user = _verify_bearer_token(bearer_token)
            return

    header_value = x_api_key or ""
    if not header_value:
        raise HTTPException(
            status_code=401, detail="Missing authentication credentials"
        )
    if not _api_key_configured():
        raise HTTPException(
            status_code=503, detail="DISPATCH_API_KEY is not configured"
        )
    if not hmac.compare_digest(header_value, DISPATCH_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


def _advance_dispatch_workflow(sm, run_id: str, result: dict | None = None) -> None:
    """Advance a dispatch through the synchronous workflow states."""
    from state_machine import DispatchState

    current_state = sm.get_current_state(run_id)
    if current_state is None:
        sm.transition(
            run_id,
            DispatchState.RECEIVED,
            actor="system",
            run_id=run_id,
            payload={"channel": "api"},
        )

    workflow_states = [
        DispatchState.TRIAGED,
        DispatchState.QUALIFIED,
        DispatchState.SCHEDULED,
        DispatchState.CONFIRMED,
        DispatchState.DISPATCHED,
    ]

    for state in workflow_states:
        if sm.get_current_state(run_id) == state.value:
            continue
        sm.transition(
            run_id,
            state,
            actor="hvac_crew",
            run_id=run_id,
            payload=result if state == DispatchState.DISPATCHED else None,
        )


def _publish_dispatch_completed_event(
    dispatch_id: str, result: dict
) -> dict[str, str] | None:
    """Publish dispatch completion metadata to the shared event bus when configured."""
    event_bus_url = os.getenv("EVENT_BUS_URL", "").rstrip("/")
    if not event_bus_url:
        return None

    payload_data = EventPublishRequest(
        event_type=EventType.DISPATCH_COMPLETED,
        payload={
            "dispatch_id": dispatch_id,
            "status": "complete",
            "result": result,
        },
        correlation_id=dispatch_id,
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "money-default"),
        source_service=os.getenv("MONEY_SERVICE_NAME", "money-dispatch"),
    ).model_dump(mode="json")

    response = _event_bus_publish_sync(payload_data, timeout=5.0)
    response.raise_for_status()
    event_response = response.json()
    logger.info(
        "Dispatch completion event published",
        extra={
            "dispatch_id": dispatch_id,
            "event_id": event_response.get("event_id"),
            "channel": event_response.get("channel"),
        },
    )
    return {
        "event_id": str(event_response["event_id"]),
        "channel": str(event_response["channel"]),
    }


# ── Pydantic models ──────────────────────────────────────────


class DispatchRequest(BaseModel):
    customer_message: str = Field(..., min_length=1, max_length=MAX_MSG_LENGTH)
    outdoor_temp_f: float = Field(default=80.0, ge=-50.0, le=150.0)
    async_mode: bool = False


class DispatchResponse(BaseModel):
    run_id: str
    status: str
    result: Optional[dict] = None
    timestamp: str


class ErrorResponse(BaseModel):
    detail: str


# ── Helpers ───────────────────────────────────────────────────


def _validate_twilio_signature(request: Request, params: dict) -> bool:
    """Verify Twilio webhook signature to prevent spoofing."""
    validator = RequestValidator(TWILIO_TOKEN)
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    # Render/proxies may change scheme; use forwarded proto if available
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_proto:
        url = url.replace("http://", f"{forwarded_proto}://", 1)
    return validator.validate(url, params, signature)


def _twilio_skip_allowed() -> bool:
    skip = os.environ.get("SKIP_TWILIO_VALIDATION", "false").lower() == "true"
    if skip and ENV == "production":
        raise HTTPException(
            status_code=403, detail="Twilio validation may not be skipped in production"
        )
    return skip


def _execute_job(run_id: str, message: str, temp: float):
    """Background task runner with state machine tracking."""
    from state_machine import get_state_machine

    sm = get_state_machine()
    start_time = time.time()

    try:
        job_store[run_id]["status"] = "running"

        from hvac_dispatch_crew import run_hvac_crew

        result = run_hvac_crew(customer_message=message, outdoor_temp_f=temp)

        _advance_dispatch_workflow(sm, run_id, result)

        event_bus_event = _publish_dispatch_completed_event(run_id, result)
        if event_bus_event:
            result = {
                **result,
                "event_bus_event_id": event_bus_event["event_id"],
                "event_bus_channel": event_bus_event["channel"],
            }

        sm.record_event(
            run_id,
            "dispatch_completed",
            actor="hvac_crew",
            run_id=run_id,
            payload=result,
        )

        job_store[run_id].update({"status": "complete", "result": result})
        update_dispatch_status(run_id, "complete", result)
        _broadcast_dispatch_event("dispatch_completed", {"run_id": run_id, "status": "complete",
                                                          "result": result})

        if DISPATCH_JOB_DURATION:
            DISPATCH_JOB_DURATION.labels(status="success").observe(
                time.time() - start_time
            )

    except Exception as exc:
        logger.error("Job %s failed: %s", run_id, exc)
        if DISPATCH_JOB_DURATION:
            DISPATCH_JOB_DURATION.labels(status="error").observe(
                time.time() - start_time
            )
        sm.record_event(
            run_id, "error", actor="system", run_id=run_id, payload={"error": str(exc)}
        )
        job_store[run_id].update({"status": "error", "error": str(exc)})
        update_dispatch_status(run_id, "error", {"error": str(exc)})
        _broadcast_dispatch_event("dispatch_error", {"run_id": run_id, "status": "error",
                                                      "error": str(exc)})


def _twiml_response(body: str) -> PlainTextResponse:
    """Return a hardened TwiML <Response><Message> for Twilio using ElementTree (Prevents Injection)."""
    # Truncate for safety
    body = body[:MAX_MSG_LENGTH]

    response_el = ET.Element("Response")
    message_el = ET.SubElement(response_el, "Message")
    message_el.text = body

    xml_str = ET.tostring(response_el, encoding="unicode", xml_declaration=False)
    # Add manual decl
    header = '<?xml version="1.0" encoding="UTF-8"?>'
    return PlainTextResponse(content=f"{header}{xml_str}", media_type="application/xml")


# ── API Endpoints ─────────────────────────────────────────────


@app.get("/health")
def health():
    db_ok = True
    try:
        from database import get_pool

        conn = get_pool().getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        finally:
            get_pool().putconn(conn)
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "HVAC AI Dispatch",
        "time": datetime.now(timezone.utc).isoformat(),
        "api_key_configured": _api_key_configured(),
        "database": "connected" if db_ok else "error",
    }


@app.get("/metrics")
async def metrics(request: Request, x_api_key: str = Header(default=None)):
    """Expose Prometheus metrics."""
    await _authorize_request(x_api_key, request)
    return get_metrics_response()


@app.post(
    "/dispatch",
    response_model=DispatchResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def dispatch(
    payload: DispatchRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    x_api_key: str = Header(default=None),
):
    """API-driven dispatch with customer API key validation and billing."""
    # Validate customer API key for multi-tenant billing
    customer = None
    if x_api_key:
        try:
            customer = await validate_api_key(x_api_key)
        except HTTPException as e:
            # Re-raise billing/authentication errors (not validation failures)
            if e.status_code in (401, 403, 429):
                raise
            # Fall back to legacy admin API key auth for other errors
            await _authorize_request(x_api_key, request)
    else:
        await _authorize_request(x_api_key, request)

    # Rate limit after authentication
    _rate_limit(_rate_bucket(request, "dispatch"))
    
    # Check dispatch quota if customer is authenticated
    if customer:
        if not check_dispatch_quota(customer):
            raise HTTPException(
                status_code=429,
                detail="Monthly dispatch quota exceeded. Please upgrade your plan."
            )

    run_id = str(uuid.uuid4())
    _prune_stores()
    job_store[run_id] = {"status": "queued", "result": None}
    ts = datetime.now(timezone.utc).isoformat()

    save_dispatch(
        dispatch_id=run_id,
        issue_summary=payload.customer_message,
        status="queued",
    )
    _broadcast_dispatch_event("dispatch_created", {"run_id": run_id, "status": "queued",
                                                    "issue": payload.customer_message[:120]})

    # Log customer event for revenue tracking
    if customer:
        # Calculate revenue impact based on plan
        plan_config = PRICING.get(customer.get("plan", "free"), {})
        dispatch_value = plan_config.get("price", 0) / max(plan_config.get("dispatches_per_month", 1), 1)
        
        log_customer_event(
            customer_id=customer["id"],
            event_type="dispatch_created",
            event_data={
                "dispatch_id": run_id,
                "plan": customer.get("plan"),
                "message": payload.customer_message[:100],
            },
            revenue_impact=dispatch_value,
        )

    if payload.async_mode:
        background_tasks.add_task(
            _execute_job, run_id, payload.customer_message, payload.outdoor_temp_f
        )
        return DispatchResponse(run_id=run_id, status="queued", timestamp=ts)
    else:
        _execute_job(run_id, payload.customer_message, payload.outdoor_temp_f)
        job = job_store[run_id]
        return DispatchResponse(
            run_id=run_id,
            status=job["status"],
            result=job.get("result"),
            timestamp=ts,
        )


@app.get("/run/{run_id}", response_model=DispatchResponse)
async def get_run(run_id: str, request: Request, x_api_key: str = Header(default=None)):
    _rate_limit(_rate_bucket(request, "run"))
    await _authorize_request(x_api_key, request)
    job = job_store.get(run_id)
    if not job:
        # Try database fallback
        db_record = get_dispatch(run_id)
        if db_record:
            return DispatchResponse(
                run_id=run_id,
                status=db_record.get("status", "unknown"),
                timestamp=db_record.get("updated_at", ""),
            )
        raise HTTPException(status_code=404, detail="Run not found")
    return DispatchResponse(
        run_id=run_id,
        status=job["status"],
        result=job.get("result"),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/dispatches")
async def list_dispatches(
    request: Request, limit: int = 50, x_api_key: str = Header(default=None)
):
    """Return recent dispatch history from database."""
    _rate_limit(_rate_bucket(request, "dispatches"))
    await _authorize_request(x_api_key, request)
    return get_recent_dispatches(limit)


@app.get("/api/dispatch/{dispatch_id}/timeline")
async def get_dispatch_timeline(
    dispatch_id: str, request: Request, x_api_key: str = Header(default=None)
):
    """Get full event timeline for a dispatch (event sourcing)."""
    _rate_limit(_rate_bucket(request, "timeline"))
    await _authorize_request(x_api_key, request)

    from state_machine import get_state_machine

    sm = get_state_machine()

    timeline = sm.get_timeline(dispatch_id)
    current_state = sm.get_current_state(dispatch_id)
    time_in_state = sm.get_time_in_state(dispatch_id)

    return {
        "dispatch_id": dispatch_id,
        "current_state": current_state,
        "time_in_state_seconds": time_in_state,
        "event_count": len(timeline),
        "events": timeline,
    }


@app.get("/api/dispatch/funnel")
async def get_dispatch_funnel(request: Request, x_api_key: str = Header(default=None)):
    """Get dispatch pipeline funnel counts."""
    _rate_limit(_rate_bucket(request, "funnel"))
    await _authorize_request(x_api_key, request)

    from state_machine import get_state_machine

    sm = get_state_machine()

    counts = sm.funnel_counts()

    # Calculate conversion rates
    total = sum(counts.values())
    active = (
        total
        - counts.get("cancelled", 0)
        - counts.get("escalated", 0)
        - counts.get("followed_up", 0)
    )

    return {
        "total_dispatches": total,
        "active_dispatches": active,
        "state_counts": counts,
        "terminal_counts": {
            "completed": counts.get("followed_up", 0),
            "cancelled": counts.get("cancelled", 0),
            "escalated": counts.get("escalated", 0),
        },
    }


# ── Enhanced Dashboard API Endpoints ────────────────────────


@app.get("/api/metrics")
async def get_dashboard_metrics(request: Request, x_api_key: str = Header(default=None)):
    """Server-side dispatch metrics — single DB query, no client-side aggregation."""
    _rate_limit(_rate_bucket(request, "metrics"))
    await _authorize_request(x_api_key, request)
    from database import get_dispatch_metrics
    return get_dispatch_metrics()


@app.get("/api/dispatches/search")
async def search_dispatches_api(
    request: Request,
    q: str = "",
    status: str = "",
    urgency: str = "",
    limit: int = 50,
    offset: int = 0,
    x_api_key: str = Header(default=None),
):
    """Full-text search + filter dispatches. Supports q, status, urgency params."""
    _rate_limit(_rate_bucket(request, "search"))
    await _authorize_request(x_api_key, request)
    from database import search_dispatches
    results = search_dispatches(query=q, status=status, urgency=urgency, limit=min(limit, 200), offset=offset)
    return {"results": results, "count": len(results), "offset": offset}


_ALLOWED_STATUS_VALUES = frozenset({"pending", "queued", "complete", "cancelled", "escalated", "in_progress"})


class DispatchUpdateBody(BaseModel):
    status: Optional[str] = Field(default=None, max_length=32)
    tech_name: Optional[str] = Field(default=None, max_length=120)
    eta: Optional[str] = Field(default=None, max_length=64)


@app.patch("/api/dispatch/{dispatch_id}/status")
async def update_dispatch_status_api(
    dispatch_id: str,
    body: DispatchUpdateBody,
    request: Request,
    x_api_key: str = Header(default=None),
):
    """
    Manually override dispatch status, tech assignment, or ETA.
    Accepts a JSON body: {status?, tech_name?, eta?}.
    Used by dashboard operators to correct AI assignments.
    """
    _rate_limit(_rate_bucket(request, "update"))
    await _authorize_request(x_api_key, request)

    from database import update_dispatch_fields

    updates: dict = {}
    if body.status:
        if body.status.lower() not in _ALLOWED_STATUS_VALUES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Allowed: {sorted(_ALLOWED_STATUS_VALUES)}",
            )
        updates["status"] = body.status.lower()
    if body.tech_name:
        updates["tech_name"] = body.tech_name
    if body.eta:
        updates["eta"] = body.eta

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    updated = update_dispatch_fields(dispatch_id, **updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return updated


# In-memory set of SSE queues — each connected browser gets one.
# Protected by a lock because _execute_job runs in a background thread while
# stream_dispatches runs in the async event loop; concurrent mutation of a
# plain set is not thread-safe in CPython under heavy load.
_sse_clients: set = set()
_sse_lock = threading.Lock()


def _broadcast_dispatch_event(event_type: str, data: dict) -> None:
    """Push a server-sent event to all connected dashboard clients."""
    payload = json.dumps({"type": event_type, "data": data})
    dead: set = set()
    with _sse_lock:
        snapshot = list(_sse_clients)
    for q in snapshot:
        try:
            q.put_nowait(payload)
        except Exception:
            dead.add(q)
    if dead:
        with _sse_lock:
            _sse_clients.difference_update(dead)


@app.get("/api/stream/dispatches")
async def stream_dispatches(request: Request, x_api_key: str = Header(default=None)):
    """
    Server-Sent Events stream — push live dispatch updates to the dashboard.
    Clients reconnect automatically on disconnect (EventSource spec).
    """
    await _authorize_request(x_api_key, request)

    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    with _sse_lock:
        _sse_clients.add(queue)

    async def event_generator():
        try:
            # Send current metrics on connect so dashboard loads instantly
            from database import get_dispatch_metrics
            metrics = get_dispatch_metrics()
            yield f"event: metrics\ndata: {json.dumps(metrics)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=25)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"  # keep-alive ping every 25s
        finally:
            with _sse_lock:
                _sse_clients.discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Twilio Webhook Endpoints ─────────────────────────────────


async def _handle_twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str,
    Body: str,
    MessageSid: str,
    channel: str,
) -> PlainTextResponse:
    """Shared handler for SMS and WhatsApp Twilio webhooks."""
    import importlib
    from state_machine import get_state_machine, DispatchState
    from response_templates import generate_dispatch_response
    from triage import triage_urgency_local

    form_data = await request.form()
    params = {k: v for k, v in form_data.items()}

    skip_validation = _twilio_skip_allowed()
    if not skip_validation and not _validate_twilio_signature(request, params):
        logger.warning("Invalid Twilio signature from %s", From)
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Anti-spam: drop messages from the same number faster than 5 seconds
    now_time = time.time()
    if now_time - rate_limit_store.get(From, 0.0) < 5.0:
        logger.warning("Rate limit hit from %s, dropping %s", From, channel)
        return _twiml_response("")
    rate_limit_store[From] = now_time

    # Sanitize: truncate + strip HTML to prevent XSS echoing
    Body = re.sub(r"<[^>]+>", "[REDACTED]", Body[:MAX_MSG_LENGTH])

    logger.info("%s received from %s: %s", channel.upper(), From, Body[:100])
    log_message(direction="inbound", phone=From, body=Body, sms_sid=MessageSid, channel=channel)

    run_id = str(uuid.uuid4())
    _prune_stores()
    job_store[run_id] = {"status": "queued", "result": None}
    save_dispatch(dispatch_id=run_id, customer_phone=From, issue_summary=Body, status="queued")

    sm = get_state_machine()
    sm.transition(
        run_id,
        DispatchState.RECEIVED,
        actor="customer",
        payload={"channel": channel, "phone": From},
    )

    background_tasks.add_task(_execute_job, run_id, Body, 95.0)  # Default Houston summer temp

    triage_result = triage_urgency_local(Body, 95.0)
    urgency = triage_result.get("urgency_level", "standard").lower()
    response_text = generate_dispatch_response(Body, urgency, outdoor_temp=95.0)
    return _twiml_response(response_text)


@app.post("/sms")
async def sms_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(default=""),
    To: str = Form(default=""),
):
    """
    Twilio SMS webhook — customer texts in, AI responds.
    Configure in Twilio Console: Phone Numbers → Messaging → Webhook URL.
    """
    return await _handle_twilio_webhook(request, background_tasks, From, Body, MessageSid, "sms")


@app.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(default=""),
    To: str = Form(default=""),
):
    """
    Twilio WhatsApp webhook — same logic as SMS but logged as 'whatsapp' channel.
    Configure in Twilio Console: Messaging → WhatsApp Sandbox → Webhook URL.
    """
    return await _handle_twilio_webhook(request, background_tasks, From, Body, MessageSid, "whatsapp")


# ── Premium Admin Dashboard (De-AI'd FAANG Refactor) ──────────


# ── Login / Logout ────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if _get_session_user(request):
        return RedirectResponse(url="/admin", status_code=302)
    return _render_login_page(request, error=None)


@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str | None = Form(default=None),
):
    cookie_token = request.cookies.get(_LOGIN_CSRF_COOKIE)
    if not _validate_login_csrf_token(csrf_token, cookie_token):
        return _render_login_page(
            request, "Invalid or expired CSRF token", status_code=403
        )
    if hmac.compare_digest(username, _ADMIN_USER) and hmac.compare_digest(
        password, _ADMIN_PASS
    ):
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(
            _SESSION_COOKIE,
            _create_session_cookie(username),
            max_age=_SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=ENV == "production",
        )
        response.delete_cookie(_LOGIN_CSRF_COOKIE)
        return response
    return _render_login_page(request, "Invalid username or password", status_code=401)


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(_SESSION_COOKIE)
    response.delete_cookie(_LOGIN_CSRF_COOKIE)
    return response


@app.get("/legacy-admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Secure admin dashboard — session cookie auth with login redirect."""
    if not _get_session_user(request):
        return RedirectResponse(url="/login", status_code=302)
    recent = get_recent_dispatches(50)

    # Real metrics from DB data
    total = len(recent)
    emergency_count = sum(
        1 for d in recent if d.get("urgency", "").lower() == "emergency"
    )
    completed_count = sum(
        1 for d in recent if d.get("status", "").lower() == "complete"
    )
    emergency_pct = round((emergency_count / total * 100) if total else 0, 1)

    # Jinja2 auto-escapes all template variables — no manual escaping needed
    safe_dispatches = []
    for d in recent:
        safe_dispatches.append(
            {
                "status": str(d.get("status", "queued")),
                "customer_phone": str(d.get("customer_phone") or "N/A"),
                "dispatch_id": str(d.get("dispatch_id", "")),
                "issue_summary": str(d.get("issue_summary", "")),
            }
        )

    return _templates.TemplateResponse(
        request,
        "admin.html",
        {
            "dispatches": safe_dispatches,
            "total_dispatches": total,
            "emergency_count": emergency_count,
            "completed_count": completed_count,
            "emergency_pct": emergency_pct,
            "pid": os.getpid(),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        },
    )


# ── Sales Intelligence Integration Endpoints ─────────────────


@app.get("/integrations/status")
async def integrations_status(request: Request, x_api_key: str = Header(default="")):
    """Status of all integration connections"""
    await _authorize_request(x_api_key, request)

    from integrations import (
        SalesIntelligenceConnector,
    )

    return {
        "sales_intelligence": SalesIntelligenceConnector().check_connection(),
        "hubspot": {"connected": bool(os.environ.get("HUBSPOT_API_KEY"))},
        "google_sheets": {"connected": bool(os.environ.get("GOOGLE_SHEETS_ID"))},
        "slack": {"connected": bool(os.environ.get("SLACK_WEBHOOK_URL"))},
    }


@app.post("/webhooks/make/sales-lead")
async def make_webhook_sales_lead(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_timestamp: str = Header(default=""),
    x_webhook_signature: str = Header(default=""),
):
    """
    Webhook receiver for Make.com (Integromat) automations

    Your Sales Intelligence System runs on Make/Rube and sends:
    - Email lead data from Gmail scanner
    - Lead scores and urgency classification
    - HubSpot contact IDs

    Security: HMAC-SHA256 signature verification with timestamp skew enforcement
    """
    from integrations import (
        MakeWebhookReceiver,
        create_dispatch_from_sales_lead,
        NotificationRouter,
        WebhookVerifier,
    )

    # Make.com ingress is fail-closed: the HMAC secret must be configured.
    webhook_secret = os.environ.get("MAKE_WEBHOOK_SECRET", "").strip()
    if len(webhook_secret) < 16:
        logger.error("MAKE_WEBHOOK_SECRET missing or too short; rejecting webhook")
        raise HTTPException(
            status_code=503,
            detail="MAKE_WEBHOOK_SECRET is not configured",
        )

    raw_body = await request.body()
    verifier = WebhookVerifier(webhook_secret)
    result = verifier.verify(raw_body, x_webhook_timestamp, x_webhook_signature)

    if not result.valid:
        logger.warning(f"Make.com webhook verification failed: {result.error}")
        raise HTTPException(status_code=401, detail=f"Invalid webhook: {result.error}")

    logger.info(f"Make.com webhook verified (skew: {result.skew_seconds}s)")
    payload = await request.json()

    # Preserve the legacy payload-secret check as a second gate while the Make
    # automation migrates fully to signed requests.
    if not MakeWebhookReceiver.validate_webhook(payload, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    # Parse the Make.com payload
    lead_data = MakeWebhookReceiver.parse_make_payload(payload)
    logger.info(f"Received sales lead from Make: {lead_data.get('sender_email')}")

    # Create dispatch from lead
    dispatch_id = create_dispatch_from_sales_lead(lead_data)
    lead_data["dispatch_id"] = dispatch_id
    lead_data["dispatch_status"] = "queued"

    # Route notifications based on score
    notifier = NotificationRouter()
    notifier.route_lead_notification(lead_data)

    return {
        "status": "received",
        "dispatch_id": dispatch_id,
        "lead_score": lead_data.get("lead_score", {}).get("score", 0),
    }


@app.post("/webhooks/hubspot/contact-updated")
async def hubspot_webhook_contact_updated(
    request: Request, x_hubspot_signature: str = Header(default="")
):
    """
    Webhook for HubSpot contact updates
    Keeps ReliantAI in sync when contacts are updated in HubSpot
    """
    hubspot_secret = os.environ.get("HUBSPOT_WEBHOOK_SECRET", "").strip()
    if len(hubspot_secret) < 16:
        logger.error("HUBSPOT_WEBHOOK_SECRET missing or too short; rejecting webhook")
        raise HTTPException(
            status_code=503,
            detail="HUBSPOT_WEBHOOK_SECRET is not configured",
        )

    if not x_hubspot_signature:
        raise HTTPException(status_code=401, detail="Missing HubSpot webhook signature")

    raw_body = await request.body()
    expected_signature = hmac.new(
        hubspot_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(x_hubspot_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid HubSpot webhook signature")

    payload = json.loads(raw_body.decode("utf-8"))
    logger.info(f"HubSpot webhook received: {payload}")

    return {"status": "acknowledged"}


# ── Static File Serving for Unified Frontend ─────────────────


# Serve index.html for the root path (SPA entry point)
@app.get("/", response_class=HTMLResponse)
def serve_index(request: Request):
    """Serve the unified React SPA at root"""
    index_path = os.path.join(frontend_dist, "index.html")

    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # Fallback to API info page if frontend not built
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head><title>HVAC Dispatch API Server</title></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🛠️ HVAC Dispatch API Server</h1>
            <p>The frontend has not been built yet.</p>
            <h2>API Endpoints Available:</h2>
            <ul>
                <li><code>GET /health</code> - Health check</li>
                <li><code>GET /dispatches</code> - List dispatches</li>
                <li><code>POST /dispatch</code> - Create dispatch</li>
            </ul>
            <p>To build the frontend: <code>cd frontend && npm install && npm run build</code></p>
        </body>
        </html>
        """
        )
