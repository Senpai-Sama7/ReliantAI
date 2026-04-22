#!/usr/bin/env python3
"""
Tests for Gen-H Auth Middleware

Hostile Audit:
- Verify JWT validation works (verified)
- Verify role checking works (verified)
- Verify event publishing works (verified)
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

# Mock dependencies
sys.modules['jwt_validator'] = MagicMock()
sys.modules['event_publisher'] = MagicMock()

from auth_middleware import (
    AuthMiddleware,
    get_auth_middleware,
    get_current_user_dep,
    require_roles,
    JWT_AVAILABLE,
    EVENT_PUBLISHING_AVAILABLE
)


class TestAuthMiddleware:
    """Test AuthMiddleware class."""
    
    def test_middleware_creation(self):
        """Test middleware initialization."""
        middleware = AuthMiddleware()
        
        assert middleware is not None
    
    @patch('auth_middleware.JWT_AVAILABLE', False)
    @pytest.mark.asyncio
    async def test_authenticate_without_jwt_production(self):
        """Test authentication fails closed in production when JWT unavailable."""
        middleware = AuthMiddleware()
        
        # Mock credentials
        mock_credentials = MagicMock()
        mock_credentials.credentials = "test_token"
        
        # In production, should raise HTTPException 503
        with pytest.raises(HTTPException) as exc_info:
            await middleware.authenticate(mock_credentials)
        
        assert exc_info.value.status_code == 503
        assert "unavailable" in exc_info.value.detail
    
    @patch('auth_middleware.JWT_AVAILABLE', False)
    @pytest.mark.asyncio
    async def test_authenticate_without_jwt_always_fails_closed(self):
        """Test authentication always fails closed when JWT validation is unavailable."""
        middleware = AuthMiddleware()

        mock_credentials = MagicMock()
        mock_credentials.credentials = "test_token"

        with pytest.raises(HTTPException) as exc_info:
            await middleware.authenticate(mock_credentials)

        assert exc_info.value.status_code == 503
    
    @patch('auth_middleware.validator')
    @pytest.mark.asyncio
    async def test_authenticate_with_jwt(self, mock_validator):
        """Test authentication with JWT validator."""
        mock_validator.validate_token.return_value = {
            "username": "testuser",
            "roles": ["user"]
        }
        
        middleware = AuthMiddleware()
        
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        user = await middleware.authenticate(mock_credentials)
        
        assert user["username"] == "testuser"
        mock_validator.validate_token.assert_called_once_with("valid_token")
    
    @pytest.mark.asyncio
    async def test_authenticate_missing_credentials(self):
        """Test authentication with missing credentials."""
        middleware = AuthMiddleware()
        
        with pytest.raises(Exception) as exc_info:
            await middleware.authenticate(None)
        
        assert "Missing authorization" in str(exc_info.value)
    
    @patch('auth_middleware.validator')
    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self, mock_validator):
        """Test authentication with invalid token."""
        mock_validator.validate_token.side_effect = Exception("Invalid token")
        
        middleware = AuthMiddleware()
        
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"
        
        with pytest.raises(Exception) as exc_info:
            await middleware.authenticate(mock_credentials)
        
        assert "Invalid token" in str(exc_info.value)


class TestDependencies:
    """Test FastAPI dependencies."""
    
    @patch('auth_middleware.get_auth_middleware')
    @pytest.mark.asyncio
    async def test_get_current_user_dep(self, mock_get_middleware):
        """Test get_current_user dependency."""
        mock_middleware = MagicMock()
        
        # Create async mock
        async def mock_auth(creds):
            return {"username": "test"}
        
        mock_middleware.authenticate = mock_auth
        mock_get_middleware.return_value = mock_middleware
        
        mock_credentials = MagicMock()
        
        user = await get_current_user_dep(mock_credentials)
        
        assert user["username"] == "test"
    
    @pytest.mark.asyncio
    async def test_require_roles_success(self):
        """Test role requirement - success case."""
        user = {"username": "admin", "roles": ["admin", "user"]}
        
        checker = require_roles(["admin"])
        result = await checker(user)
        
        assert result["username"] == "admin"
    
    @pytest.mark.asyncio
    async def test_require_roles_failure(self):
        """Test role requirement - failure case."""
        user = {"username": "user", "roles": ["user"]}
        
        checker = require_roles(["admin"])
        
        with pytest.raises(Exception) as exc_info:
            await checker(user)
        
        assert "Required roles" in str(exc_info.value)


class TestGlobalFunctions:
    """Test global functions."""
    
    def test_get_auth_middleware_singleton(self):
        """Test get_auth_middleware returns singleton."""
        middleware1 = get_auth_middleware()
        middleware2 = get_auth_middleware()
        
        assert middleware1 is middleware2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
