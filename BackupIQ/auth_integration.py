#!/usr/bin/env python3
"""
BackupIQ Auth Integration

Provides JWT authentication integration for BackupIQ API.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import sys
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable

from flask import request, jsonify, g

# Add shared JWT validator to path (resolved relative to this file)
_file_dir = os.path.dirname(os.path.abspath(__file__))
_shared_path = os.path.abspath(os.path.join(_file_dir, '..', 'integration', 'shared'))
_apex_path = os.path.abspath(os.path.join(_file_dir, '..', 'apex', 'apex-agents'))

sys.path.insert(0, _shared_path)
try:
    from jwt_validator import JWTValidator
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("WARNING: JWT validator not available")

# Event publishing
try:
    sys.path.insert(0, _apex_path)
    from event_publisher import EventPublisher, ApexEvent, get_publisher
    EVENT_PUBLISHING_AVAILABLE = True
except ImportError:
    EVENT_PUBLISHING_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize validator
validator = JWTValidator() if JWT_AVAILABLE else None

class BackupIQAuth:
    """
    Authentication handler for BackupIQ.
    
    Provides:
    - JWT token validation
    - Role-based access control
    - Flask decorator integration
    """
    
    def __init__(self, app=None):
        self.app = app
        self.validator = validator
        self.event_publisher = get_publisher() if EVENT_PUBLISHING_AVAILABLE else None
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User dict if valid, None otherwise
            
        Raises:
            RuntimeError: If auth service unavailable in production
        """
        if not self.validator:
            raise RuntimeError("Authentication service unavailable - cannot validate tokens")
        
        try:
            return self.validator.validate_token(token)
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    def require_auth(self, f: Callable) -> Callable:
        """
        Decorator to require authentication.
        
        Usage:
            @app.route('/protected')
            @auth.require_auth
            def protected():
                return jsonify({"user": g.current_user["username"]})
        """
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({"error": "Missing authorization header"}), 401
            
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({"error": "Invalid authorization header format"}), 401
            
            token = parts[1]
            user = self.validate_token(token)
            
            if not user:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Store user in flask g
            g.current_user = user
            
            return f(*args, **kwargs)
        
        return decorated
    
    def require_roles(self, roles: list):
        """
        Decorator to require specific roles.
        
        Usage:
            @app.route('/admin-only')
            @auth.require_roles(['admin'])
            def admin_only():
                return jsonify({"message": "Admin access granted"})
        """
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated(*args, **kwargs):
                # First check auth
                auth_result = self._check_auth()
                if auth_result:
                    return auth_result
                
                # Check roles
                user_roles = g.current_user.get('roles', [])
                if not any(role in user_roles for role in roles):
                    return jsonify({
                        "error": "Insufficient permissions",
                        "required_roles": roles
                    }), 403
                
                return f(*args, **kwargs)
            
            return decorated
        return decorator
    
    def _check_auth(self):
        """Check authentication and return error response if invalid."""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid authorization header format"}), 401
        
        token = parts[1]
        user = self.validate_token(token)
        
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        g.current_user = user
        return None


# Global instance
_auth_instance: Optional[BackupIQAuth] = None


def get_auth() -> BackupIQAuth:
    """Get or create global auth instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = BackupIQAuth()
    return _auth_instance


# Convenience decorators
def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication."""
    return get_auth().require_auth(f)


def require_roles(roles: list):
    """Decorator to require specific roles."""
    return get_auth().require_roles(roles)


# Event publishing functions
def publish_backup_event(event_type: str, backup_data: Dict, user_id: str = None):
    """
    Publish backup-related event.
    
    Args:
        event_type: Type of event (backup.started, backup.completed, backup.failed)
        backup_data: Backup operation data
        user_id: User who initiated the backup
    """
    auth = get_auth()
    if not auth.event_publisher:
        return
    
    event = ApexEvent(
        event_type=event_type,
        data={
            "backup_id": backup_data.get("id"),
            "source": backup_data.get("source"),
            "destination": backup_data.get("destination"),
            "size_bytes": backup_data.get("size_bytes"),
            "duration_seconds": backup_data.get("duration_seconds")
        },
        user_id=user_id
    )
    
    auth.event_publisher.publish(event)
    logger.info(f"Published {event_type} event for backup {backup_data.get('id')}")


def publish_restore_event(event_type: str, restore_data: Dict, user_id: str = None):
    """Publish restore-related event."""
    auth = get_auth()
    if not auth.event_publisher:
        return
    
    event = ApexEvent(
        event_type=event_type,
        data={
            "restore_id": restore_data.get("id"),
            "backup_id": restore_data.get("backup_id"),
            "destination": restore_data.get("destination"),
            "status": restore_data.get("status")
        },
        user_id=user_id
    )
    
    auth.event_publisher.publish(event)


if __name__ == "__main__":
    # Test the auth integration
    print("Testing BackupIQ Auth Integration...")
    
    auth = get_auth()
    print(f"Auth instance created: {auth is not None}")
    print(f"JWT available: {JWT_AVAILABLE}")
    print(f"Event publishing available: {EVENT_PUBLISHING_AVAILABLE}")
    
    print("Test complete")
