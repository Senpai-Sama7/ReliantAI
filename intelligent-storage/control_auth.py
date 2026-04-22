"""Control-plane authentication helpers for Intelligent Storage Nexus."""

from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, WebSocket

CONTROL_API_KEY_ENV = "ISN_CONTROL_API_KEY"
CONTROL_API_HEADER = "X-ISN-Control-Key"


def get_control_api_key() -> str:
    """Return the configured control-plane API key."""
    return os.getenv(CONTROL_API_KEY_ENV, "").strip()


def _ensure_configured() -> str:
    expected = get_control_api_key()
    if len(expected) < 16:
        raise HTTPException(
            status_code=503,
            detail=f"{CONTROL_API_KEY_ENV} is not configured",
        )
    return expected


def _validate_provided_key(provided: Optional[str]) -> None:
    expected = _ensure_configured()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid control API key")


async def require_control_api_key(
    x_isn_control_key: Optional[str] = Header(default=None, alias=CONTROL_API_HEADER),
) -> None:
    """FastAPI dependency for protected control-plane endpoints."""
    _validate_provided_key(x_isn_control_key)


async def authorize_websocket(websocket: WebSocket) -> None:
    """Authorize a websocket connection using the control API key."""
    api_key = websocket.query_params.get("api_key")
    _validate_provided_key(api_key)
