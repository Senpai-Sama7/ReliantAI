"""
Apex Agents Auth Integration.

Provides JWT authentication by validating tokens against the Auth Service.
Uses the shared JWT validator from integration/shared/jwt_validator.py.
"""

import os
import sys
from pathlib import Path

_RELIINTAI_ROOT = Path(__file__).parent.parent.parent.parent
_SHARED_DIR = _RELIINTAI_ROOT / "integration" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict

try:
    from jwt_validator import JWTValidator

    _secret = os.getenv("AUTH_SECRET_KEY", "")
    _auth_url = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8080")
    _validator = JWTValidator(secret_key=_secret, auth_url=_auth_url)
    AUTH_ENABLED = True
except Exception:
    _validator = None
    AUTH_ENABLED = False

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """FastAPI dependency — extract and validate JWT, return user payload."""
    if not AUTH_ENABLED or _validator is None:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    try:
        return _validator.validate_token(credentials.credentials)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """Alias for get_current_user — used as FastAPI dependency."""
    return get_current_user(credentials)


class AuthIntegration:
    """Compatibility shim — the auth service is the external JWT issuer."""

    def __init__(self):
        self.enabled = AUTH_ENABLED

    def verify_token(self, token: str) -> Dict:
        if not AUTH_ENABLED or _validator is None:
            raise HTTPException(status_code=503, detail="Auth service unavailable")
        return _validator.validate_token(token)
