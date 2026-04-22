"""
Citadel Integration Middleware - JWT Auth + Event Bus
Wraps Citadel orchestrator with authentication and event publishing
"""
import os
import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Any, Dict
import structlog

logger = structlog.get_logger()
security = HTTPBearer()

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8080")
EVENT_BUS_URL = os.getenv("EVENT_BUS_URL", "http://event-bus:8081")
CITADEL_ORCHESTRATOR_URL = os.getenv("CITADEL_ORCHESTRATOR_URL", "http://localhost:8000")

app = FastAPI(title="Citadel Integration Layer")

# Models
class QueryRequest(BaseModel):
    query: str
    correlation_id: str
    tenant_id: str

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token with Auth Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
        except httpx.RequestError as e:
            logger.error("auth_service_unreachable", error=str(e))
            raise HTTPException(status_code=503, detail="Auth service unavailable")

async def publish_event(event_type: str, payload: Dict[str, Any], correlation_id: str, tenant_id: str):
    """Publish event to Event Bus"""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{EVENT_BUS_URL}/publish",
                json={
                    "event_type": event_type,
                    "payload": payload,
                    "correlation_id": correlation_id,
                    "tenant_id": tenant_id,
                    "source_service": "citadel"
                }
            )
        except httpx.RequestError as e:
            logger.error("event_bus_unreachable", error=str(e))

# Endpoints
@app.post("/query")
async def query(
    req: QueryRequest,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Execute Citadel query with auth and event publishing"""
    
    # Publish query started event
    await publish_event(
        "agent.task.created",
        {"service": "citadel", "query": req.query},
        req.correlation_id,
        req.tenant_id
    )
    
    # Call Citadel orchestrator
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{CITADEL_ORCHESTRATOR_URL}/query",
                json={"query": req.query}
            )
            result = response.json()
            
            # Publish query completed event
            await publish_event(
                "agent.task.completed",
                {"service": "citadel", "result": result},
                req.correlation_id,
                req.tenant_id
            )
            
            return result
            
        except httpx.RequestError as e:
            logger.error("citadel_orchestrator_unreachable", error=str(e))
            raise HTTPException(status_code=503, detail="Citadel orchestrator unavailable")

@app.post("/vector/search")
async def vector_search(
    data: Dict[str, Any],
    user: Dict[str, Any] = Depends(verify_token)
):
    """Vector search with auth"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CITADEL_ORCHESTRATOR_URL}/vector/search",
            json=data
        )
        return response.json()

@app.post("/knowledge-graph/query")
async def kg_query(
    data: Dict[str, Any],
    user: Dict[str, Any] = Depends(verify_token)
):
    """Knowledge graph query with auth"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CITADEL_ORCHESTRATOR_URL}/knowledge-graph/query",
            json=data
        )
        return response.json()

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "citadel-integration"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
