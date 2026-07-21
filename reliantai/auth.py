"""Authentication and authorization for ReliantAI."""

import hmac
import os

from fastapi import HTTPException, Request


def verify_api_key(request: Request) -> bool:
    """Verify Bearer token against API_SECRET_KEY (constant-time)."""
    api_key = os.environ.get("API_SECRET_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    provided_key = auth_header.removeprefix("Bearer ")
    if not hmac.compare_digest(provided_key.encode("utf-8"), api_key.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True
