"""ReliantAI Platform API - FastAPI entry point."""

import os
import time
from collections import OrderedDict
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .db import get_db_session

log = structlog.get_logger()

_rate_limit_buckets: OrderedDict[str, list[float]] = OrderedDict()
_RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "100"))
_RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
_RATE_LIMIT_MAX_IPS = int(os.environ.get("RATE_LIMIT_MAX_IPS", "10000"))


def _client_ip(request: Request) -> str:
    """Prefer left-most X-Forwarded-For hop only when TRUST_PROXY=1."""
    if os.environ.get("TRUST_PROXY", "").lower() in {"1", "true", "yes"}:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def _rate_limit_check(client_ip: str) -> bool:
    """Return True if the request is within the rate limit."""
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW

    stale_keys = [
        ip for ip, timestamps in _rate_limit_buckets.items()
        if not timestamps or timestamps[-1] < window_start
    ]
    for ip in stale_keys:
        del _rate_limit_buckets[ip]

    while len(_rate_limit_buckets) >= _RATE_LIMIT_MAX_IPS:
        _rate_limit_buckets.popitem(last=False)

    if client_ip in _rate_limit_buckets:
        bucket = _rate_limit_buckets[client_ip]
        _rate_limit_buckets.move_to_end(client_ip)
    else:
        bucket = []
        _rate_limit_buckets[client_ip] = bucket

    bucket[:] = [t for t in bucket if t > window_start]

    if len(bucket) >= _RATE_LIMIT_MAX:
        return False

    bucket.append(now)
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


# Docs only when explicitly local/dev — unset ENVIRONMENT must not expose OpenAPI.
_ENV = os.environ.get("ENVIRONMENT", "production").lower()
_DOCS_ENABLED = _ENV in {"dev", "development", "local", "test"}

app = FastAPI(
    title="ReliantAI Platform API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if _DOCS_ENABLED else None,
    redoc_url="/redoc" if _DOCS_ENABLED else None,
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
    client_ip = _client_ip(request)
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
    except Exception as exc:
        log.warning("health_db_check_failed", error=str(exc)[:120])
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis as redis_lib
            r = redis_lib.from_url(redis_url)
            if r is not None:
                r.ping()
                redis_ok = True
        except Exception as exc:
            log.warning("health_redis_check_failed", error=str(exc)[:120])
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
