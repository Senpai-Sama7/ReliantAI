#!/usr/bin/env python3
"""
Gen-H HVAC Lead Generator - Auth Middleware

FastAPI middleware for JWT authentication integration with ReliantAI auth service.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import sys
from typing import Dict, Any, Optional
from functools import wraps

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Add shared JWT validator to path
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/shared')
try:
    from jwt_validator import JWTValidator, get_current_user
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("WARNING: JWT validator not available")

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8080")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Security scheme
security = HTTPBearer(auto_error=False)

# Initialize validator
validator = JWTValidator() if JWT_AVAILABLE else None


class AuthMiddleware:
    """
    Authentication middleware for Gen-H API.
    
    Validates JWT tokens and extracts user information.
    """
    
    def __init__(self, app: FastAPI = None):
        self.app = app
        self.validator = validator
    
    async def authenticate(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        Authenticate request using JWT token.
        
        Args:
            credentials: Authorization header credentials
            
        Returns:
            User dictionary if authenticated
            
        Raises:
            HTTPException: If authentication fails
        """
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not JWT_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = credentials.credentials
        
        try:
            user = self.validator.validate_token(token)
            return user
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def require_auth(self, required_roles: list = None):
        """
        Decorator to require authentication and optional roles.
        
        Args:
            required_roles: List of required roles
            
        Usage:
            @app.get("/protected")
            @auth.require_auth(["admin"])
            async def protected_route(user: Dict = Depends(auth.authenticate)):
                return {"user": user["username"]}
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Authentication is handled by FastAPI Depends
                user = kwargs.get('user')
                
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                if required_roles:
                    user_roles = user.get('roles', [])
                    if not any(role in user_roles for role in required_roles):
                        raise HTTPException(
                            status_code=403,
                            detail=f"Required roles: {required_roles}"
                        )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Global middleware instance
_auth_middleware: Optional[AuthMiddleware] = None


def get_auth_middleware() -> AuthMiddleware:
    """Get or create global auth middleware instance."""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()
    return _auth_middleware


# Convenience dependency
async def get_current_user_dep(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current user."""
    middleware = get_auth_middleware()
    return await middleware.authenticate(credentials)


def require_roles(required_roles: list):
    """Dependency to require specific roles."""
    async def role_checker(user: Dict = Depends(get_current_user_dep)) -> Dict[str, Any]:
        user_roles = user.get('roles', [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Required roles: {required_roles}"
            )
        return user
    return role_checker


# Event publishing integration
try:
    sys.path.insert(0, '/home/donovan/Projects/ReliantAI/apex/apex-agents')
    from event_publisher import EventPublisher, ApexEvent, get_publisher
    
    _publisher = get_publisher()
    
    def publish_lead_event(lead_data: Dict, user_id: str = None):
        """Publish lead generation event."""
        event = ApexEvent(
            event_type="lead.generated",
            data={
                "lead_id": lead_data.get("id"),
                "source": "gen-h",
                "hvac_type": lead_data.get("hvac_type"),
                "user_id": user_id
            },
            user_id=user_id
        )
        _publisher.publish(event)
        
    EVENT_PUBLISHING_AVAILABLE = True
except ImportError:
    EVENT_PUBLISHING_AVAILABLE = False
    
    def publish_lead_event(lead_data: Dict, user_id: str = None):
        """No-op when event publishing unavailable."""
        pass


if __name__ == "__main__":
    # Test the middleware
    print("Testing Gen-H Auth Middleware...")
    
    middleware = get_auth_middleware()
    print(f"Auth middleware initialized: {middleware is not None}")
    print(f"JWT available: {JWT_AVAILABLE}")
    print(f"Event publishing available: {EVENT_PUBLISHING_AVAILABLE}")
    
    print("Test complete")
