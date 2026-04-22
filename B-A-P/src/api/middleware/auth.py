"""
Authentication middleware and dependencies.
"""
import os
from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any
from src.api import auth_integration
from src.utils.logger import get_logger

logger = get_logger()

# Public paths that don't require authentication
PUBLIC_PATHS = [
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
]
class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for handling authentication on protected routes."""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and verify authentication."""
        # Skip auth for public paths
        if request.url.path == "/" or any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)
        
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid authentication credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header.replace("Bearer ", "")
        if not auth_integration.validator:
            return JSONResponse(
                status_code=503,
                content={"detail": "Authentication service unavailable"},
            )

        try:
            user = auth_integration.validator.validate_token(token)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers or {"WWW-Authenticate": "Bearer"},
            )
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Store user in request state for downstream use
        request.state.user = user
        
        response = await call_next(request)
        return response

def get_current_user(
    user: Dict[str, Any] = Depends(auth_integration.get_current_user_from_shared_auth)
) -> Dict[str, Any]:
    """Get the current user from JWT token (using shared auth integration)."""
    return user

def get_current_user_optional(
    request: Request
) -> Optional[Dict[str, Any]]:
    """Get the current user from request state if authenticated."""
    return getattr(request.state, "user", None)
