"""ReliantAI Platform API - FastAPI entry point."""

import hmac
import os
import time
from collections import OrderedDict
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .db import get_db_session

log = structlog.get_logger()

# Rate Limiter (bounded, per-IP, LRU eviction)
# Memory-safe: caps total tracked IPs at RATE_LIMIT_MAX_IPS and evicts
# the least-recently-seen IP when the cap is hit. Stale entries older
# than RATE_LIMIT_WINDOW are pruned on every check.

_rate_limit_buckets: OrderedDict[str, list[float]] = OrderedDict()
_RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "100"))
_RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
_RATE_LIMIT_MAX_IPS = int(os.environ.get("RATE_LIMIT_MAX_IPS", "10000"))


def _rate_limit_check(client_ip: str) -> bool:
    """Return True if the request is within the rate limit."""
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW

    # Prune stale entries from the oldest bucket first
    stale_keys = [
        ip for ip, timestamps in _rate_limit_buckets.items()
        if not timestamps or timestamps[-1] < window_start
    ]
    for ip in stale_keys:
        del _rate_limit_buckets[ip]

    # Evict LRU IP if we are over the cap
    while len(_rate_limit_buckets) >= _RATE_LIMIT_MAX_IPS:
        _rate_limit_buckets.popitem(last=False)

    # Get or create bucket for this IP
    if client_ip in _rate_limit_buckets:
        bucket = _rate_limit_buckets[client_ip]
        _rate_limit_buckets.move_to_end(client_ip)
    else:
        bucket = []
        _rate_limit_buckets[client_ip] = bucket

    # Prune old timestamps within this bucket
    bucket[:] = [t for t in bucket if t > window_start]

    if len(bucket) >= _RATE_LIMIT_MAX:
        return False

    bucket.append(now)
    return True


def verify_api_key(request: Request):
    """Verify Bearer token against API_SECRET_KEY using constant-time comparison."""
    api_key = os.environ.get("API_SECRET_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")
    provided = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not provided:
        raise HTTPException(status_code=401, detail="Missing API key")
    if not hmac.compare_digest(provided.encode("utf-8"), api_key.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        log.info("db_connection_ok")
    except Exception as e:
        log.error("db_connection_failed", error=str(e))
    yield


app = FastAPI(
    title="ReliantAI Platform API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.environ.get("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.environ.get("ENVIRONMENT") != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://reliantai.org",
        "https://www.reliantai.org",
        "https://preview.reliantai.org",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/ready", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_limit_check(client_ip):
        log.warning("rate_limit_exceeded", client_ip=client_ip, path=request.url.path)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(_RATE_LIMIT_WINDOW)},
        )
    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health():
    db_ok = False
    redis_ok = False
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis as redis_lib
            r = redis_lib.from_url(redis_url)
            if r is not None:
                r.ping()
                redis_ok = True
        except Exception:
            pass
    return {"status": "ok", "db": db_ok, "redis": redis_ok}


# ─── ROUTERS ─────────────────────────────────────────────────────────

from .api.v2 import prospects_router, generated_sites_router, webhooks_router

app.include_router(prospects_router)
app.include_router(generated_sites_router)
app.include_router(webhooks_router)


@app.get("/ready")
async def readiness():
    """Kubernetes-style readiness probe."""
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")
