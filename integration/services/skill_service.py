"""
Skill Service — FastAPI HTTP endpoints for the 3 core skills.

Mount at /skills/ in the integration gateway or standalone.
Requires JWT authentication via the integration auth layer.
"""

from __future__ import annotations

import os
import sys
import time
import asyncio
import threading
import httpx
from pathlib import Path
from typing import Annotated
from collections import defaultdict

# Ensure skill_integration is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()
security = HTTPBearer()

from skill_integration import (
    diagnose_async,
    qualify_prospects_async,
    generate_outreach,
    generate_proposal_package_async,
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8080")

# ─────────────────────────────────────────────────────────────────────────────
# Revenue Metrics — thread-safe counters using simple dict + lock
# ─────────────────────────────────────────────────────────────────────────────

_metrics_lock = threading.Lock()
_metrics = {
    "calls": 0,
    "errors": 0,
    "total_latency_ms": 0.0,
    "hot_leads": 0,
    "warm_leads": 0,
    "cold_leads": 0,
    "proposals_generated": 0,
    "proposal_pipeline_value": 0.0,
    "outreach_generated": 0,
}


def _record_metric(
    latency_ms: float,
    ok: bool,
    hot: int = 0,
    warm: int = 0,
    cold: int = 0,
    proposal_value: float = 0.0,
    is_proposal: bool = False,
    is_outreach: bool = False,
) -> None:
    with _metrics_lock:
        _metrics["calls"] += 1
        if not ok:
            _metrics["errors"] += 1
        _metrics["total_latency_ms"] += latency_ms
        _metrics["hot_leads"] += hot
        _metrics["warm_leads"] += warm
        _metrics["cold_leads"] += cold
        if is_proposal:
            _metrics["proposals_generated"] += 1
            _metrics["proposal_pipeline_value"] += proposal_value
        if is_outreach:
            _metrics["outreach_generated"] += 1


def _get_metrics_snapshot() -> dict:
    with _metrics_lock:
        calls = _metrics["calls"]
        errors = _metrics["errors"]
        total_latency = _metrics["total_latency_ms"]
        return {
            "calls": calls,
            "errors": errors,
            "error_rate": round(errors / max(calls, 1) * 100, 2),
            "avg_latency_ms": round(total_latency / max(calls, 1), 2),
            "hot_leads": _metrics["hot_leads"],
            "warm_leads": _metrics["warm_leads"],
            "cold_leads": _metrics["cold_leads"],
            "proposals_generated": _metrics["proposals_generated"],
            "proposal_pipeline_value_usd": _metrics["proposal_pipeline_value"],
            "outreach_generated": _metrics["outreach_generated"],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────


class DiagnoseRequest(BaseModel):
    context: str = Field(..., min_length=1, description="Project situation to diagnose")


class ProspectRequest(BaseModel):
    criteria: str = Field(..., min_length=1)
    skills: list[str] = Field(..., min_length=1)
    raw_opportunities: str = Field(..., min_length=1)


class OutreachRequest(BaseModel):
    criteria: str = Field(..., min_length=1)
    skills: list[str] = Field(..., min_length=1)
    raw_opportunities: str = Field(..., min_length=1)
    your_name: str = Field(default="")


class ProposalRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    project_title: str = Field(..., min_length=1)
    description: str = Field(default="")
    budget_usd: float = Field(..., gt=0)
    timeline_weeks: int = Field(..., gt=0)
    skills: list[str] = Field(default=[])


class SkillResponse(BaseModel):
    ok: bool = True
    result: dict | str


# ─────────────────────────────────────────────────────────────────────────────
# Auth Dependency (reuse from integration auth)
# ─────────────────────────────────────────────────────────────────────────────


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify JWT token with Auth Service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {credentials.credentials}"},
                timeout=5.0,
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401 or response.status_code == 403:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            else:
                logger.error("auth_service_error", status=response.status_code)
                raise HTTPException(status_code=503, detail="Auth service error")
        except httpx.RequestError as e:
            logger.error("auth_service_unreachable", error=str(e))
            raise HTTPException(status_code=503, detail="Auth service unavailable")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("auth_unexpected_error", error=str(e))
            raise HTTPException(status_code=500, detail="Auth check failed")


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiting
# ─────────────────────────────────────────────────────────────────────────────


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            # Remove old requests outside the window
            self._requests[key] = [
                t for t in self._requests[key] if now - t < self.window_seconds
            ]
            if len(self._requests[key]) >= self.max_requests:
                return False
            self._requests[key].append(now)
            return True


_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ReliantAI Skill Service",
    description="HTTP API for the 3 core revenue skills",
    version="1.0.0",
)


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


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all skill endpoints."""
    from fastapi.responses import JSONResponse

    # Skip rate limiting for health and metrics endpoints
    if request.url.path in ("/skills/health", "/skills/metrics"):
        return await call_next(request)

    # Use client IP + endpoint path as rate limit key
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{request.url.path}"

    if not _rate_limiter.is_allowed(key):
        logger.warn("rate_limit_exceeded", ip=client_ip, path=request.url.path)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
        )

    return await call_next(request)


@app.post("/skills/diagnose", response_model=SkillResponse)
async def api_diagnose(
    body: DiagnoseRequest, _auth: Annotated[dict, Depends(require_auth)]
) -> SkillResponse:
    """Strategic Execution Advisor — diagnose a situation and get ranked actions."""
    start = time.monotonic()
    ok = False
    try:
        result = await diagnose_async(body.context)
        ok = True
        return SkillResponse(ok=True, result=result)
    except Exception as e:
        logger.error(
            "skill_diagnose_failed", error=str(e), context_len=len(body.context)
        )
        raise HTTPException(status_code=500, detail="Diagnosis failed")
    finally:
        latency_ms = (time.monotonic() - start) * 1000
        _record_metric(latency_ms, ok)


@app.post("/skills/prospect", response_model=SkillResponse)
async def api_prospect(
    body: ProspectRequest, _auth: Annotated[dict, Depends(require_auth)]
) -> SkillResponse:
    """Autonomous Prospect Engine — qualify raw opportunities into a pipeline."""
    start = time.monotonic()
    ok = False
    try:
        result = await qualify_prospects_async(
            body.criteria,
            body.skills,
            body.raw_opportunities,
        )
        ok = True
        hot = int(result.get("hot_count", 0))
        warm = int(result.get("warm_count", 0))
        cold = int(result.get("cold_count", 0))
        pipeline_value = float(result.get("pipeline_value", 0))
        _record_metric(
            (time.monotonic() - start) * 1000,
            ok,
            hot=hot,
            warm=warm,
            cold=cold,
        )
        logger.info(
            "prospect_completed",
            hot=hot,
            warm=warm,
            cold=cold,
            pipeline_value=pipeline_value,
            qualified_rate=result.get("qualified_rate", 0),
        )
        return SkillResponse(ok=True, result=result)
    except Exception as e:
        _record_metric((time.monotonic() - start) * 1000, ok)
        logger.error("skill_prospect_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Prospect failed")


@app.post("/skills/outreach", response_model=SkillResponse)
async def api_outreach(
    body: OutreachRequest, _auth: Annotated[dict, Depends(require_auth)]
) -> SkillResponse:
    """Autonomous Prospect Engine — generate personalized outreach for HOT/WARM leads."""
    start = time.monotonic()
    ok = False
    try:
        # Run blocking sync call in thread pool to avoid blocking the event loop
        result = await asyncio.to_thread(
            generate_outreach,
            body.criteria,
            body.skills,
            body.raw_opportunities,
            body.your_name,
        )
        ok = True
        _record_metric((time.monotonic() - start) * 1000, ok, is_outreach=True)
        logger.info("outreach_completed", recipient=body.your_name)
        return SkillResponse(ok=True, result=result)
    except Exception as e:
        _record_metric((time.monotonic() - start) * 1000, ok, is_outreach=True)
        logger.error("skill_outreach_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Outreach failed")


@app.post("/skills/proposal", response_model=SkillResponse)
async def api_proposal(
    body: ProposalRequest, _auth: Annotated[dict, Depends(require_auth)]
) -> SkillResponse:
    """Proposal-to-Contract Pipeline — generate full proposal package."""
    start = time.monotonic()
    ok = False
    try:
        result = await generate_proposal_package_async(
            body.client_name,
            body.company,
            body.project_title,
            body.description,
            body.budget_usd,
            body.timeline_weeks,
            body.skills,
        )
        ok = True
        _record_metric(
            (time.monotonic() - start) * 1000,
            ok,
            is_proposal=True,
            proposal_value=body.budget_usd,
        )
        logger.info(
            "proposal_completed",
            company=body.company,
            budget_usd=body.budget_usd,
            timeline_weeks=body.timeline_weeks,
            skills=body.skills,
        )
        return SkillResponse(ok=True, result=result)
    except Exception as e:
        _record_metric(
            (time.monotonic() - start) * 1000,
            ok,
            is_proposal=True,
            proposal_value=body.budget_usd,
        )
        logger.error("skill_proposal_failed", error=str(e), company=body.company)
        raise HTTPException(status_code=500, detail="Proposal failed")


@app.get("/skills/health")
async def health():
    return {"ok": True, "service": "skill-service"}


@app.get("/skills/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    snap = _get_metrics_snapshot()
    lines = [
        "# HELP skill_service_calls_total Total skill service calls",
        "# TYPE skill_service_calls_total counter",
        f'skill_service_calls_total{{service="skill-service"}} {snap["calls"]}',
        "# HELP skill_service_errors_total Total errors",
        "# TYPE skill_service_errors_total counter",
        f'skill_service_errors_total{{service="skill-service"}} {snap["errors"]}',
        "# HELP skill_service_error_rate Error rate percentage",
        "# TYPE skill_service_error_rate gauge",
        f'skill_service_error_rate{{service="skill-service"}} {snap["error_rate"]}',
        "# HELP skill_service_avg_latency_ms Average latency in ms",
        "# TYPE skill_service_avg_latency_ms gauge",
        f'skill_service_avg_latency_ms{{service="skill-service"}} {snap["avg_latency_ms"]}',
        "# HELP skill_hot_leads_total HOT leads identified",
        "# TYPE skill_hot_leads_total counter",
        f'skill_hot_leads_total{{service="skill-service"}} {snap["hot_leads"]}',
        "# HELP skill_warm_leads_total WARM leads identified",
        "# TYPE skill_warm_leads_total counter",
        f'skill_warm_leads_total{{service="skill-service"}} {snap["warm_leads"]}',
        "# HELP skill_cold_leads_total COLD leads identified",
        "# TYPE skill_cold_leads_total counter",
        f'skill_cold_leads_total{{service="skill-service"}} {snap["cold_leads"]}',
        "# HELP skill_proposals_generated_total Proposals generated",
        "# TYPE skill_proposals_generated_total counter",
        f'skill_proposals_generated_total{{service="skill-service"}} {snap["proposals_generated"]}',
        "# HELP skill_proposal_pipeline_value_usd Total pipeline value USD",
        "# TYPE skill_proposal_pipeline_value_usd gauge",
        f'skill_proposal_pipeline_value_usd{{service="skill-service"}} {snap["proposal_pipeline_value_usd"]}',
        "# HELP skill_outreach_generated_total Outreach messages generated",
        "# TYPE skill_outreach_generated_total counter",
        f'skill_outreach_generated_total{{service="skill-service"}} {snap["outreach_generated"]}',
    ]
    return "\n".join(lines)


# Mount in integration gateway with: router.include_router(skill_service.app, prefix="/api")
