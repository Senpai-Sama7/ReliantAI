"""
ReliantAI Integration Service - Main Entry Point

Unified service mesh providing:
- Health checks
- Service routing
- A2A protocol bridge
- Skill service endpoints
- Metrics
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import structlog

logger = structlog.get_logger()

# Service URLs from environment
MONEY_URL = os.getenv("MONEY_URL", "http://money:8000")
COMPLIANCEONE_URL = os.getenv("COMPLIANCEONE_URL", "http://complianceone:8001")
FINOPS360_URL = os.getenv("FINOPS360_URL", "http://finops360:8002")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@postgres:5432/integration")

app = FastAPI(
    title="ReliantAI Integration Service",
    version="1.0.0",
    description="Service mesh and A2A protocol bridge for ReliantAI platform"
)

# CORS middleware — use shared helper for fail-closed defaults
from shared.security_middleware import create_cors_middleware
create_cors_middleware(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "integration",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "ReliantAI Integration Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "services": {
                "money": "/proxy/money/{path}",
                "complianceone": "/proxy/complianceone/{path}",
                "finops360": "/proxy/finops360/{path}"
            }
        }
    }


@app.api_route("/proxy/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_service(service: str, path: str, request: Request):
    """Proxy requests to backend services. Supports all HTTP methods."""
    service_urls = {
        "money": MONEY_URL,
        "complianceone": COMPLIANCEONE_URL,
        "finops360": FINOPS360_URL,
    }
    target_url = service_urls.get(service)
    if not target_url:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")

    async with httpx.AsyncClient() as client:
        try:
            body = await request.body() if request.method in ("POST", "PUT", "PATCH") else None
            response = await client.request(
                method=request.method,
                url=f"{target_url}/{path}",
                headers={k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")},
                params=request.query_params,
                content=body,
                timeout=30.0,
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.error(f"{service}_proxy_error", error=str(e))
            raise HTTPException(status_code=503, detail=f"{service} service unavailable")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("INTEGRATION_HOST", "0.0.0.0")
    port = int(os.getenv("INTEGRATION_PORT", "8080"))
    
    logger.info("starting_integration_service", host=host, port=port)
    uvicorn.run(app, host=host, port=port)
