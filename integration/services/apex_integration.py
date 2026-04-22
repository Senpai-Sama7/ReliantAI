"""
Apex Integration Middleware - JWT Auth + Event Bus
Wraps existing Apex API with authentication and event publishing
"""

import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Any, Dict
import structlog

logger = structlog.get_logger()
security = HTTPBearer()

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8080")
EVENT_BUS_URL = os.getenv("EVENT_BUS_URL", "http://event-bus:8081")
APEX_AGENTS_URL = os.getenv("APEX_AGENTS_URL", "http://localhost:8001")


def _event_bus_headers() -> dict[str, str]:
    h: dict[str, str] = {"Content-Type": "application/json"}
    key = (os.getenv("EVENT_BUS_API_KEY") or "").strip()
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


app = FastAPI(title="Apex Integration Layer")


# Models
class WorkflowRequest(BaseModel):
    input_data: Dict[str, Any]
    correlation_id: str
    tenant_id: str


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Verify JWT token with Auth Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {credentials.credentials}"},
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
        except httpx.RequestError as e:
            logger.error("auth_service_unreachable", error=str(e))
            raise HTTPException(status_code=503, detail="Auth service unavailable")


async def publish_event(
    event_type: str, payload: Dict[str, Any], correlation_id: str, tenant_id: str
):
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
                    "source_service": "apex",
                },
                headers=_event_bus_headers(),
            )
        except httpx.RequestError as e:
            logger.error("event_bus_unreachable", error=str(e))


# Endpoints
@app.post("/workflow/run")
async def run_workflow(
    req: WorkflowRequest, user: Dict[str, Any] = Depends(verify_token)
):
    """Run Apex workflow with auth and event publishing"""

    # Publish workflow started event
    await publish_event(
        "agent.task.created",
        {"workflow": "apex_full", "input": req.input_data},
        req.correlation_id,
        req.tenant_id,
    )

    # Call Apex agents API
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{APEX_AGENTS_URL}/workflow/run", json=req.input_data
            )
            result = response.json()

            # Publish workflow completed event
            await publish_event(
                "agent.task.completed",
                {"workflow": "apex_full", "result": result},
                req.correlation_id,
                req.tenant_id,
            )

            return result

        except httpx.RequestError as e:
            logger.error("apex_agents_unreachable", error=str(e))
            raise HTTPException(status_code=503, detail="Apex agents unavailable")


@app.post("/agents/layer1/analyze")
async def layer1_analyze(
    data: Dict[str, Any], user: Dict[str, Any] = Depends(verify_token)
):
    """Layer 1 analysis with auth"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{APEX_AGENTS_URL}/agents/layer1/analyze", json=data
        )
        return response.json()


@app.post("/agents/layer2/calibration-gate")
async def layer2_calibration(
    data: Dict[str, Any], user: Dict[str, Any] = Depends(verify_token)
):
    """Layer 2 calibration with auth"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{APEX_AGENTS_URL}/agents/layer2/calibration-gate", json=data
        )
        return response.json()


@app.post("/agents/layer3/dispatch")
async def layer3_dispatch(
    data: Dict[str, Any], user: Dict[str, Any] = Depends(verify_token)
):
    """Layer 3 dispatch with auth"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{APEX_AGENTS_URL}/agents/layer3/dispatch", json=data
        )
        return response.json()


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "apex-integration"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
