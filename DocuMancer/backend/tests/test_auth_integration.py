"""
Tests for DocuMancer Auth Integration.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from auth_integration import (
    get_current_user_from_shared_auth,
    require_roles,
    JWT_AVAILABLE
)

class TestDocuMancerAuth:
    """Test suite for DocuMancer auth integration."""

    def test_get_current_user_success(self):
        """Test successful user retrieval."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        mock_user = {"username": "doc_user", "roles": ["user"]}
        
        with patch("auth_integration.validator") as mock_validator:
            mock_validator.validate_token.return_value = mock_user
            
            user = get_current_user_from_shared_auth(mock_credentials)
            
            assert user == mock_user
            mock_validator.validate_token.assert_called_once_with("valid_token")

    def test_get_current_user_invalid_token(self):
        """Test failure with invalid token."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"
        
        with patch("auth_integration.validator") as mock_validator:
            mock_validator.validate_token.return_value = None
            
            with pytest.raises(HTTPException) as excinfo:
                get_current_user_from_shared_auth(mock_credentials)
            
            assert excinfo.value.status_code == 401
            assert "Invalid or expired token" in excinfo.value.detail

    def test_require_roles_success(self):
        """Test role check - success."""
        mock_user = {"username": "admin", "roles": ["admin"]}
        role_checker = require_roles(["admin"])
        
        result = role_checker(mock_user)
        assert result == mock_user

    def test_require_roles_failure(self):
        """Test role check - failure."""
        mock_user = {"username": "user", "roles": ["user"]}
        role_checker = require_roles(["admin"])
        
        with pytest.raises(HTTPException) as excinfo:
            role_checker(mock_user)
        
        assert excinfo.value.status_code == 403
        assert "User does not have required roles" in excinfo.value.detail

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
