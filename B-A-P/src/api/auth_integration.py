"""
B-A-P Auth Integration for FastAPI.
Provides shared JWT validation and event publishing.
"""
import sys
import logging
from collections.abc import Callable
from typing import Any, Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.event_bus import publish_event

# Add shared JWT validator to path
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/shared')
try:
    from jwt_validator import JWTValidator  # type: ignore[import-not-found]
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("JWT validator not available")

logger = logging.getLogger("bap_auth")
validator = JWTValidator() if JWT_AVAILABLE else None
EVENT_PUBLISHING_AVAILABLE = True

security = HTTPBearer(auto_error=False)

def get_current_user_from_shared_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict[str, Any]:
    """FastAPI dependency to get current user from shared JWT validator."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not validator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    
    user = validator.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return dict(user)

def require_roles(allowed_roles: list[str]) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """FastAPI dependency factory for role-based access control."""
    def role_checker(user: dict[str, Any] = Depends(get_current_user_from_shared_auth)) -> dict[str, Any]:
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required roles: {allowed_roles}"
            )
        return user
    return role_checker

async def publish_bap_event(
    event_type: str,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, str] | None:
    """Publish a B-A-P business event."""
    payload = dict(data)
    if user_id:
        payload.setdefault("user_id", user_id)

    return await publish_event(
        event_type=event_type,
        payload=payload,
        correlation_id=payload.get("job_id") or payload.get("dataset_id"),
        tenant_id=payload.get("tenant_id"),
        source_service="bap",
    )
