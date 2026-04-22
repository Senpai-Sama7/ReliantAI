"""
Authentication middleware and dependencies.
"""
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Process the request and verify authentication."""
        # Skip auth entirely for public paths - even if auth service is unavailable
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
        # If auth service is unavailable, allow request to proceed without auth
        # This ensures the app can still serve requests when auth service is down
        if not auth_integration.validator:
            logger.warning("Auth service unavailable, allowing request to proceed without authentication")
            # Store no user - downstream code should handle optional auth
            return await call_next(request)

        try:
            user = auth_integration.validator.validate_token(token)
        except HTTPException as exc:
            # If auth service returns 503, allow request to proceed without auth
            # This is a resilience pattern - fail open when auth service is down
            if exc.status_code == 503:
                logger.warning("Auth service unavailable (503), allowing request to proceed without authentication")
                return await call_next(request)
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
    user: dict[str, Any] = Depends(auth_integration.get_current_user_from_shared_auth)
) -> dict[str, Any]:
    """Get the current user from JWT token (using shared auth integration)."""
    return user


def get_current_user_optional(request: Request) -> dict[str, Any] | None:
    """Get the current user from request state if authenticated."""
    return getattr(request.state, "user", None)
