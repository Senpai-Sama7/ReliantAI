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
import time
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ReliantAI Health Aggregator", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration ───────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:9000")
MCP_BRIDGE_URL = os.environ.get("MCP_BRIDGE_URL", "http://mcp-bridge:8083")

# Service registry — all services that expose /health
SERVICES = [
    {"name": "money", "url": "http://money:8000/health", "critical": True},
    {"name": "complianceone", "url": "http://complianceone:8001/health", "critical": True},
    {"name": "finops360", "url": "http://finops360:8002/health", "critical": True},
    {"name": "growthengine", "url": "http://growthengine:8003/health", "critical": False},
    {"name": "reliant-os-backend", "url": "http://reliant-os-backend:8004/health", "critical": True},
    {"name": "integration", "url": "http://integration:8080/health", "critical": True},
    {"name": "event-bus", "url": "http://event-bus:8081/health", "critical": True},
    {"name": "orchestrator", "url": "http://orchestrator:9000/health", "critical": True},
    {"name": "ops-intelligence", "url": "http://ops-intelligence:8050/health", "critical": False},
    {"name": "gen-h", "url": "http://gen-h:8040/health", "critical": False},
    {"name": "sentinel", "url": "http://sentinel:8060/health", "critical": False},
    {"name": "apex", "url": "http://apex:8070/health", "critical": False},
    {"name": "cyberarchitect", "url": "http://cyberarchitect:8090/health", "critical": False},
    {"name": "primus", "url": "http://primus:8088/health", "critical": False},
    {"name": "acropolis", "url": "http://acropolis:8089/health", "critical": False},
    {"name": "citadelaplus", "url": "http://citadelaplus:8086/health", "critical": False},
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
async def heal_service(service: str):
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
                "last_check": datetime.utcnow().isoformat(),
                "details": data,
                "critical": svc["critical"],
            }
        else:
            return {
                "name": svc["name"],
                "healthy": False,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "last_check": datetime.utcnow().isoformat(),
                "error": f"HTTP {response.status_code}",
                "critical": svc["critical"],
            }
    except httpx.TimeoutException:
        return {
            "name": svc["name"],
            "healthy": False,
            "status_code": None,
            "latency_ms": 10000,
            "last_check": datetime.utcnow().isoformat(),
            "error": "Timeout",
            "critical": svc["critical"],
        }
    except Exception as e:
        return {
            "name": svc["name"],
            "healthy": False,
            "status_code": None,
            "latency_ms": 0,
            "last_check": datetime.utcnow().isoformat(),
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
            _last_check = datetime.utcnow()
            
            # Store in Redis
            try:
                r = aioredis.from_url(REDIS_URL)
                await r.setex("health:aggregate", 60, json.dumps({
                    "timestamp": _last_check.isoformat(),
                    "services": _health_state,
                }))
                await r.close()
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
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.publish("events:health", json.dumps(event))
        await r.close()
    except Exception:
        pass

# ── Self-Healing ────────────────────────────────────────────────

async def _evaluate_self_heal():
    """Evaluate if any services need self-healing and trigger Orchestrator."""
    for svc in SERVICES:
        state = _health_state.get(svc["name"], {})
        if not state.get("healthy", False):
            # Check if we've been unhealthy for > 2 minutes
            last_healthy = state.get("last_healthy")
            if last_healthy is None:
                # First time seeing unhealthy — mark timestamp
                state["last_healthy"] = None
                state["first_unhealthy"] = datetime.utcnow().isoformat()
            else:
                first_unhealthy = datetime.fromisoformat(state.get("first_unhealthy", datetime.utcnow().isoformat()))
                if (datetime.utcnow() - first_unhealthy).total_seconds() > 120:
                    await _self_heal(svc["name"])

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
                    "timestamp": datetime.utcnow().isoformat(),
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
                    "timestamp": datetime.utcnow().isoformat(),
                }
    except Exception as e:
        return {
            "service": service,
            "action": "none",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    return {
        "service": service,
        "action": "none",
        "status": "orchestrator_unavailable",
        "timestamp": datetime.utcnow().isoformat(),
    }

# ── Startup ─────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    asyncio.create_task(_health_check_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
