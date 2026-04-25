import hmac
import os
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .db import get_db_session

log = structlog.get_logger()
security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    api_key = os.environ.get("API_SECRET_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")
    provided = credentials.credentials.encode("utf-8")
    expected = api_key.encode("utf-8")
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify DB on startup
    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
        log.info("db_connection_ok")
    except Exception as e:
        log.error("db_connection_failed", error=str(e))
    yield


app = FastAPI(
    title="ReliantAI Platform API",
    version="2.0.0",
    lifespan=lifespan,
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

# ─── HEALTH ──────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    db_ok = False
    redis_ok = False

    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass

    try:
        import redis as redis_lib
        r = redis_lib.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        if r is not None:
            r.ping()
            redis_ok = True
    except Exception:
        pass

    return {"status": "ok", "db": db_ok, "redis": redis_ok}


# ─── ROUTERS (placeholder imports — populated as phases complete) ─────

from .api.v2 import prospects as prospects_router
from .api.v2 import generated_sites as generated_sites_router
from .api.v2 import webhooks as webhooks_router

app.include_router(prospects_router.router)
app.include_router(generated_sites_router.router)
app.include_router(webhooks_router.router)
