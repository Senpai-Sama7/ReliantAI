"""
ReliantAI Health Aggregator
============================
Aggregates health status from all platform services, computes system-wide health score,
and triggers self-healing actions through the Orchestrator when services are unhealthy.

Design: Polls all service /health endpoints every 30s, maintains rolling health state in Redis,
publishes health change events to the event bus. Self-healing loop runs every 60s.
"""

import asyncio
import json
import os
import secrets as _secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader

app = FastAPI(title="ReliantAI Health Aggregator", version="1.0.0")

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost,http://localhost:3000,http://localhost:8085")
_origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
if "*" not in _origins:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

HEAL_API_KEY = os.environ.get("HEAL_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:9000")
MCP_BRIDGE_URL = os.environ.get("MCP_BRIDGE_URL", "http://mcp-bridge:8083")

_redis_pool: aioredis.Redis | None = None

async def _get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis_pool

async def verify_heal_api_key(api_key: str = Security(_api_key_header)) -> str:
    if not HEAL_API_KEY:
        raise HTTPException(status_code=503, detail="Heal API key not configured. Set HEAL_API_KEY environment variable.")
    if not api_key or not _secrets.compare_digest(api_key, HEAL_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key for heal endpoint")
    return api_key

# Service registry — all services that expose /health
SERVICES = [
    {"name": "money", "url": "http://money:8000/health", "critical": True},
    {"name": "complianceone", "url": "http://complianceone:8001/health", "critical": True},
    {"name": "finops360", "url": "http://finops360:8002/health", "critical": True},
    {"name": "growthengine", "url": "http://growthengine:8003/health", "critical": False},
    {"name": "reliant-os-backend", "url": "http://reliant-os-backend:8004/health", "critical": True},
    {"name": "integration", "url": "http://integration:8080/health", "critical": True},
    {"name": "event-bus", "url": "http://event-bus:8081/health", "critical": True},
    {"name": "mcp-bridge", "url": "http://mcp-bridge:8083/health", "critical": True},
    {"name": "orchestrator", "url": "http://orchestrator:9000/health", "critical": True},
    {"name": "nginx", "url": "http://nginx:80/health", "critical": True},
]

# ── State ───────────────────────────────────────────────────────
_health_state: Dict[str, Dict] = {}
_last_check: Optional[datetime] = None

# ── Core Endpoints ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "health-aggregator"}

@app.get("/health/aggregate")
async def aggregate_health():
    """Return current aggregated health status for all services."""
    healthy = sum(1 for s in _health_state.values() if s.get("healthy", False))
    total = len(SERVICES)
    critical_healthy = sum(
        1 for svc in SERVICES
        if svc["critical"] and _health_state.get(svc["name"], {}).get("healthy", False)
    )
    critical_total = sum(1 for svc in SERVICES if svc["critical"])
    
    return {
        "timestamp": _last_check.isoformat() if _last_check else None,
        "overall": "healthy" if healthy == total else "degraded" if critical_healthy == critical_total else "critical",
        "score": f"{healthy}/{total}",
        "critical_score": f"{critical_healthy}/{critical_total}",
        "services": _health_state,
    }

@app.get("/health/{service}")
async def service_health(service: str):
    """Get detailed health for a specific service."""
    if service not in _health_state:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    return _health_state[service]

@app.post("/health/heal/{service}")
async def heal_service(service: str, _auth: str = Depends(verify_heal_api_key)):
    """Trigger self-healing for a specific service."""
    result = await _self_heal(service)
    return result

# ── Health Check Loop ───────────────────────────────────────────

async def _check_service(client: httpx.AsyncClient, svc: Dict) -> Dict:
    """Check health of a single service."""
    start = time.time()
    try:
        response = await client.get(svc["url"], timeout=10.0)
        latency_ms = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "name": svc["name"],
                "healthy": True,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "details": data,
                "critical": svc["critical"],
            }
        else:
            return {
                "name": svc["name"],
                "healthy": False,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": f"HTTP {response.status_code}",
                "critical": svc["critical"],
            }
    except httpx.TimeoutException:
        return {
            "name": svc["name"],
            "healthy": False,
            "status_code": None,
            "latency_ms": 10000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "error": "Timeout",
            "critical": svc["critical"],
        }
    except Exception as e:
        return {
            "name": svc["name"],
            "healthy": False,
            "status_code": None,
            "latency_ms": 0,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "critical": svc["critical"],
        }

async def _health_check_loop():
    """Main health check loop — runs every 30 seconds."""
    global _health_state, _last_check
    
    await asyncio.sleep(5)  # Initial delay for services to start
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                tasks = [_check_service(client, svc) for svc in SERVICES]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            new_state = {}
            for result in results:
                if isinstance(result, Exception):
                    continue
                new_state[result["name"]] = result
                
                # Publish state change to event bus
                prev = _health_state.get(result["name"], {})
                if prev.get("healthy") != result["healthy"]:
                    await _publish_health_event(result["name"], result["healthy"], result.get("error"))
            
            _health_state = new_state
            _last_check = datetime.now(timezone.utc)
            
            try:
                r = await _get_redis()
                await r.setex("health:aggregate", 60, json.dumps({
                    "timestamp": _last_check.isoformat(),
                    "services": _health_state,
                }))
            except Exception:
                pass
            
            # Check if self-healing needed
            await _evaluate_self_heal()
            
        except Exception as e:
            print(f"[Health Aggregator] Error in health loop: {e}")
        
        await asyncio.sleep(30)

async def _publish_health_event(service: str, healthy: bool, error: Optional[str]):
    """Publish health state change to event bus."""
    event = {
        "event_type": "health.status_changed",
        "source": "health-aggregator",
        "service": service,
        "healthy": healthy,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        r = await _get_redis()
        await r.publish("events:health", json.dumps(event))
    except Exception:
        pass

# ── Self-Healing ────────────────────────────────────────────────

async def _evaluate_self_heal():
    """Evaluate if any services need self-healing and trigger Orchestrator."""
    for svc_name, state in _health_state.items():
        if not state.get("healthy", False):
            # Check if we've been unhealthy for > 2 minutes
            first_unhealthy = state.get("first_unhealthy")
            if first_unhealthy is None:
                # First time seeing unhealthy — mark timestamp
                state["first_unhealthy"] = datetime.now(timezone.utc).isoformat()
            else:
                # Already marked — check duration
                try:
                    unhealthy_since = datetime.fromisoformat(first_unhealthy)
                    if (datetime.now(timezone.utc) - unhealthy_since).total_seconds() > 120:
                        await _self_heal(svc_name)
                except Exception:
                    pass

async def _self_heal(service: str) -> Dict:
    """Trigger self-healing through the Orchestrator."""
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Try restart
            response = await client.post(
                f"{ORCHESTRATOR_URL}/services/{service}/restart",
                timeout=30.0
            )
            if response.status_code == 200:
                return {
                    "service": service,
                    "action": "restart",
                    "status": "triggered",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            
            # Step 2: If restart not available, try scale to 1
            response = await client.post(
                f"{ORCHESTRATOR_URL}/services/{service}/scale",
                params={"target_instances": 1},
                timeout=30.0
            )
            if response.status_code == 200:
                return {
                    "service": service,
                    "action": "scale",
                    "status": "triggered",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
    except Exception as e:
        return {
            "service": service,
            "action": "none",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    return {
        "service": service,
        "action": "none",
        "status": "orchestrator_unavailable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ── Startup ─────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    asyncio.create_task(_health_check_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
