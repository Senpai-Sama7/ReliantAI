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

from fastapi import FastAPI, HTTPException
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/proxy/money/{path:path}")
async def proxy_money(path: str):
    """Proxy requests to Money service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MONEY_URL}/{path}")
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.error("money_proxy_error", error=str(e))
            raise HTTPException(status_code=503, detail="Money service unavailable")


@app.get("/proxy/complianceone/{path:path}")
async def proxy_complianceone(path: str):
    """Proxy requests to ComplianceOne service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{COMPLIANCEONE_URL}/{path}")
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.error("complianceone_proxy_error", error=str(e))
            raise HTTPException(status_code=503, detail="ComplianceOne service unavailable")


@app.get("/proxy/finops360/{path:path}")
async def proxy_finops360(path: str):
    """Proxy requests to FinOps360 service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FINOPS360_URL}/{path}")
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.error("finops360_proxy_error", error=str(e))
            raise HTTPException(status_code=503, detail="FinOps360 service unavailable")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("INTEGRATION_HOST", "0.0.0.0")
    port = int(os.getenv("INTEGRATION_PORT", "8080"))
    
    logger.info("starting_integration_service", host=host, port=port)
    uvicorn.run(app, host=host, port=port)
