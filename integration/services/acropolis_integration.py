"""
Acropolis Integration Middleware - JWT Auth + Event Bus
Wraps Acropolis adaptive expert platform with authentication
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
ACROPOLIS_URL = os.getenv("ACROPOLIS_URL", "http://localhost:8003")

app = FastAPI(title="Acropolis Integration Layer")

# Models
class ExpertRequest(BaseModel):
    task: str
    domain: str
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
                    "source_service": "acropolis"
                }
            )
        except httpx.RequestError as e:
            logger.error("event_bus_unreachable", error=str(e))

# Endpoints
@app.post("/expert/execute")
async def execute_expert(
    req: ExpertRequest,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Execute Acropolis expert task with auth and event publishing"""
    
    # Publish task started event
    await publish_event(
        "agent.task.created",
        {"service": "acropolis", "task": req.task, "domain": req.domain},
        req.correlation_id,
        req.tenant_id
    )
    
    # Call Acropolis
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{ACROPOLIS_URL}/expert/execute",
                json={"task": req.task, "domain": req.domain}
            )
            result = response.json()
            
            # Publish task completed event
            await publish_event(
                "agent.task.completed",
                {"service": "acropolis", "result": result},
                req.correlation_id,
                req.tenant_id
            )
            
            return result
            
        except httpx.RequestError as e:
            logger.error("acropolis_unreachable", error=str(e))
            raise HTTPException(status_code=503, detail="Acropolis unavailable")

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "acropolis-integration"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
