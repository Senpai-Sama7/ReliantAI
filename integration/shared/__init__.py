"""
ReliantAI Shared Library
Common utilities for integration across all projects.
"""

from .jwt_validator import (
    JWTValidator,
    get_current_user,
    require_roles,
    ServiceAccount,
    create_service_account,
    validate_service_token,
    flask_auth_required,
    flask_require_roles,
)

__all__ = [
    "JWTValidator",
    "get_current_user",
    "require_roles",
    "ServiceAccount",
    "create_service_account",
    "validate_service_token",
    "flask_auth_required",
    "flask_require_roles",
]

__version__ = "1.0.0"
