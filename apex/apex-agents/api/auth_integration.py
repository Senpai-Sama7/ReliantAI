"""
APEX Auth Integration
Integrates APEX agents API with shared JWT authentication.
"""

import os
import sys
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

# Add shared JWT validator to path
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/shared')

# Try to import JWT validator
try:
    from jwt_validator import JWTValidator, get_current_user as _get_current_user
    AUTH_ENABLED = True
except ImportError as e:
    print(f"WARNING: JWT validator not available: {e}")
    AUTH_ENABLED = False

# Global validator instance
_validator = None

def get_validator() -> Optional[JWTValidator]:
    """Get or create JWT validator instance."""
    global _validator
    if _validator is None and AUTH_ENABLED:
        _validator = JWTValidator()
    return _validator


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from JWT token.
    
    Usage:
        @app.get("/protected")
        def protected_route(user: Dict = Depends(get_current_user)):
            return {"user": user["username"]}
    """
    return await require_authenticated_user(credentials)


async def require_authenticated_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """Require shared-auth-backed authentication and fail closed if unavailable."""
    if not AUTH_ENABLED:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authentication credentials")

    validator = get_validator()
    if validator is None:
        raise HTTPException(status_code=503, detail="JWT validator not initialized")

    return validator.validate_token(credentials.credentials)


async def get_current_user_optional() -> Dict[str, Any]:
    """Get current user if auth is enabled, otherwise return anonymous."""
    if not AUTH_ENABLED:
        return {"username": "anonymous", "roles": []}
    
    # For optional auth, we'd need the request context
    # This is a placeholder for future implementation
    return {"username": "anonymous", "roles": []}


class AuthIntegration:
    """Auth integration helper for APEX."""
    
    def __init__(self):
        self.enabled = AUTH_ENABLED
        self.validator = get_validator()
    
    def require_auth(self):
        """Get auth dependency if enabled."""
        return Depends(require_authenticated_user)


# Convenience instance
auth = AuthIntegration()
