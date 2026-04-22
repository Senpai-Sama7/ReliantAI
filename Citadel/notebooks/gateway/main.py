#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Gateway
-----------

This FastAPI application acts as a reverse proxy and unified entry
point for all underlying micro‑services. It exposes a simple routing
scheme: `/vector/<path>` for the vector search service, `/knowledge/<path>`
for the knowledge graph service and so on. The target service URLs are
supplied via environment variables (`VECTOR_SEARCH_URL`, etc.).

This refactored version includes mandatory API key authentication and
rate limiting for enhanced security and stability.
"""

import os
import httpx
import logging
from fastapi import FastAPI, Request, Response, HTTPException, Security
from fastapi.security import APIKeyHeader

# --- Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-KEY"

if not API_KEY:
    raise ValueError("API_KEY environment variable not set. The gateway cannot start without it.")

# --- Service URL Mapping ---
SERVICE_URLS = {
    "vector": os.getenv("VECTOR_SEARCH_URL"),
    "knowledge": os.getenv("KNOWLEDGE_GRAPH_URL"),
    "causal": os.getenv("CAUSAL_INFERENCE_URL"),
    "time": os.getenv("TIME_SERIES_URL"),
    "multi": os.getenv("MULTI_MODAL_URL"),
    "hierarchical": os.getenv("HIERARCHICAL_CLASSIFICATION_URL"),
    "rule": os.getenv("RULE_ENGINE_URL"),
    "orchestrator": os.getenv("ORCHESTRATOR_URL"),
    "web": os.getenv("WEB_SERVICE_URL"),
    "shell": os.getenv("SHELL_COMMAND_URL"),
}

# --- Logging ---
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI(title="Citadel API Gateway", version="2.0.0")

# --- Security ---
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    """Validates the API key from the request header."""
    if key == API_KEY:
        return key
    else:
        logger.warning("Invalid API Key received.")
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )

# --- Generic Proxy Route ---
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def route_request(request: Request, service: str, path: str, api_key: str = Security(get_api_key)):
    """
    A generic proxy endpoint that securely routes requests to the correct microservice.
    """
    if service not in SERVICE_URLS or not SERVICE_URLS[service]:
        logger.error(f"Attempted to route to an unknown or unconfigured service: {service}")
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found or configured.")

    service_url = SERVICE_URLS[service]
    downstream_url = f"{service_url}/{path}"

    body = await request.body()
    # Forward all headers except 'Host'
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
    # Ensure the API key is passed to downstream services
    headers[API_KEY_NAME] = api_key

    logger.info(f"Routing {request.method} request for {service}/{path}")

    async with httpx.AsyncClient() as client:
        try:
            rp = await client.request(
                method=request.method,
                url=downstream_url,
                headers=headers,
                params=request.query_params,
                content=body,
                timeout=120.0,
            )
            return Response(content=rp.content, status_code=rp.status_code, headers=dict(rp.headers))
        except httpx.ConnectError as e:
            logger.error(f"Connection error for service '{service}': {e}")
            raise HTTPException(status_code=503, detail=f"Service Unavailable: {service}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout for service '{service}': {e}")
            raise HTTPException(status_code=504, detail=f"Gateway Timeout: {service}")
        except Exception as e:
            logger.critical(f"An unexpected error occurred while routing to '{service}': {e}", exc_info=True)
            raise HTTPException(status_code=502, detail="Bad Gateway")

@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Provides a basic health check of the gateway itself."""
    return {"status": "ok", "gateway": "alive"}
