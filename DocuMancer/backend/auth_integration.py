"""
DocuMancer Auth Integration.
Connects DocuMancer FastAPI backend to the shared JWT validator.
"""
import os
import sys
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Add shared integration directory to path
SHARED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "integration", "shared"))
if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)

# Import shared validator
try:
    from jwt_validator import JWTValidator
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

# Configuration
JWT_SECRET = os.environ.get("AUTH_SECRET_KEY") or os.environ.get("JWT_SECRET_KEY")
AUTH_ALGORITHM = "HS256"

# Initialize global validator
validator = JWTValidator(secret_key=JWT_SECRET, algorithm=AUTH_ALGORITHM) if JWT_AVAILABLE else None

security = HTTPBearer(auto_error=False)

def get_current_user_from_shared_auth(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    """FastAPI dependency to get the current user from the shared JWT validator."""
    if not JWT_AVAILABLE or not validator:
        raise HTTPException(status_code=503, detail="JWT validation service unavailable")

    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user = validator.validate_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def require_roles(required_roles: List[str]):
    """FastAPI dependency factory for role-based access control."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user_from_shared_auth)):
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=403, 
                detail=f"User does not have required roles: {required_roles}"
            )
        return user
    return role_checker
