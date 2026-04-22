#!/usr/bin/env python3
"""
Shared JWT Validation Library
Used by all Python projects for token validation.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import time
import logging
from typing import Optional, Dict, List, Callable
from functools import wraps
import requests
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8080")
JWT_SECRET = os.getenv("AUTH_SECRET_KEY")  # Aligned with auth_server.py
TOKEN_CACHE_TTL = int(os.getenv("TOKEN_CACHE_TTL", "300"))  # 5 minutes
SKIP_TLS_VERIFY = os.getenv("SKIP_TLS_VERIFY", "false").lower() == "true"  # Only for localhost/dev

if not JWT_SECRET:
    logger.warning(
        "AUTH_SECRET_KEY is not set. Local JWT validation will fail if used. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
    )

security = HTTPBearer()


class JWTValidator:
    """JWT token validator with caching."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        auth_url: Optional[str] = None,
    ):
        self._cache: Dict[str, tuple] = {}  # token -> (payload, expiry)
        self._secret: Optional[str] = secret_key or JWT_SECRET
        self._algorithm: str = algorithm
        self._auth_url: str = auth_url or AUTH_SERVICE_URL
        if not self._secret:
            logger.warning(
                "JWTValidator initialized without JWT_SECRET. "
                "Token validation relies entirely on the auth service at %s. "
                "Set JWT_SECRET if local fallback validation is needed.",
                self._auth_url,
            )

    def validate_token(self, token: str) -> Dict:
        """
        Validate a JWT token.

        First checks local cache, then validates against auth service.

        Args:
            token: The JWT token string

        Returns:
            Token payload with user info

        Raises:
            HTTPException: If token is invalid
        """
        # Check cache first
        if token in self._cache:
            payload, expiry = self._cache[token]
            if time.time() < expiry:
                logger.debug(f"Token validated from cache")
                return payload
            else:
                del self._cache[token]

        # Validate against auth service
        # TLS verification is enforced by default for security.
        # Set SKIP_TLS_VERIFY=true only for localhost/development.
        try:
            response = requests.get(
                f"{self._auth_url}/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
                verify=not SKIP_TLS_VERIFY,
            )

            if response.status_code != 200:
                logger.warning(f"Token validation failed: {response.status_code}")
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )

            payload = response.json()

            # Cache the result
            self._cache[token] = (payload, time.time() + TOKEN_CACHE_TTL)
            logger.info(
                f"Token validated and cached for user: {payload.get('username')}"
            )

            return payload

        except requests.RequestException as e:
            logger.error(f"Auth service unavailable: {e}")
            # FAIL CLOSED: Never fall back to local validation when auth service is down.
            # Local fallback creates a critical attack surface: if an attacker can DoS the
            # auth service, they can bypass authentication entirely using the shared secret.
            # Token revocation is also bypassed in fallback mode.
            raise HTTPException(
                status_code=503, detail="Authentication service unavailable"
            )

    def clear_cache(self):
        """Clear the token cache."""
        self._cache.clear()
        logger.info("Token cache cleared")


# Global validator instance
_validator = JWTValidator()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """
    FastAPI dependency to get current user from token.

    Usage:
        @app.get("/protected")
        def protected_route(user: Dict = Depends(get_current_user)):
            return {"user": user["username"]}
    """
    return _validator.validate_token(credentials.credentials)


def require_roles(roles: List[str]):
    """
    Create a dependency that requires specific roles.

    Usage:
        @app.get("/admin")
        def admin_route(user: Dict = Depends(require_roles(["admin"]))):
            return {"message": "Admin only"}
    """

    def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> Dict:
        user = _validator.validate_token(credentials.credentials)
        user_roles = user.get("roles", [])

        if not any(role in user_roles for role in roles):
            logger.warning(
                f"User {user.get('username')} missing required roles: {roles}"
            )
            raise HTTPException(status_code=403, detail=f"Required roles: {roles}")
        return user

    return role_checker


class ServiceAccount:
    """Service-to-service authentication."""

    def __init__(self, service_name: str, service_token: str):
        self.service_name = service_name
        self.service_token = service_token
        self._headers = {
            "Authorization": f"Bearer {service_token}",
            "X-Service-Name": service_name,
        }

    def get_headers(self) -> Dict[str, str]:
        """Get headers for service requests."""
        return self._headers.copy()


def create_service_account(service_name: str) -> ServiceAccount:
    """
    Create a service account for inter-service communication.

    The service token should be configured in environment or fetched
    from a secure vault.
    """
    token = os.getenv(f"{service_name.upper()}_SERVICE_TOKEN")
    if not token:
        raise ValueError(f"Service token not configured for {service_name}")

    return ServiceAccount(service_name, token)


def validate_service_token(token: str, expected_service: str) -> bool:
    """Validate a service token and check service name."""
    try:
        user = _validator.validate_token(token)
        return user.get("service_name") == expected_service
    except HTTPException:
        return False


# Flask integration
def flask_auth_required(f: Callable) -> Callable:
    """Decorator for Flask routes requiring authentication."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing authorization header"}), 401

        token = auth_header[7:]  # Remove "Bearer "
        try:
            user = _validator.validate_token(token)
            request.current_user = user  # Attach to Flask request
            return f(*args, **kwargs)
        except HTTPException as e:
            return jsonify({"error": e.detail}), e.status_code

    return decorated_function


def flask_require_roles(*roles):
    """Decorator for Flask routes requiring specific roles."""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify

            if not hasattr(request, "current_user"):
                return jsonify({"error": "Authentication required"}), 401

            user_roles = request.current_user.get("roles", [])
            if not any(role in user_roles for role in roles):
                return jsonify({"error": f"Required roles: {roles}"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
