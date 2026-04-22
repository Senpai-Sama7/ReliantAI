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
from .event_bus_client import (
    get_event_bus_url,
    publish_sync,
    publish_async,
    get_event_sync,
    publish_request_headers,
    should_verify_tls,
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
    "get_event_bus_url",
    "publish_sync",
    "publish_async",
    "get_event_sync",
    "publish_request_headers",
    "should_verify_tls",
]

__version__ = "1.0.0"
