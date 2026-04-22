#!/usr/bin/env python3
"""
Unit tests for JWT Validator
Level 1 Verification - Must pass before proceeding
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from shared.jwt_validator import (
    JWTValidator, 
    get_current_user, 
    require_roles,
    create_service_account,
    validate_service_token,
    flask_auth_required,
    flask_require_roles
)


class TestJWTValidator:
    """Test JWT validation functionality."""
    
    def test_validate_token_success(self):
        """Test successful token validation."""
        validator = JWTValidator()
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {"username": "test", "roles": ["user"]}
            )
            
            result = validator.validate_token("valid_token")
            
            assert result["username"] == "test"
            assert "user" in result["roles"]
    
    def test_validate_token_invalid(self):
        """Test invalid token rejection."""
        validator = JWTValidator()
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(status_code=401)
            
            with pytest.raises(HTTPException) as exc:
                validator.validate_token("invalid_token")
            
            assert exc.value.status_code == 401
            assert "Invalid" in exc.value.detail
    
    def test_token_caching(self):
        """Test that valid tokens are cached."""
        validator = JWTValidator()
        validator.TOKEN_CACHE_TTL = 300  # 5 minutes
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {"username": "test"}
            )
            
            # First call should hit auth service
            validator.validate_token("token123")
            assert mock_get.call_count == 1
            
            # Second call should use cache
            result = validator.validate_token("token123")
            assert mock_get.call_count == 1  # No additional call
            assert result["username"] == "test"
    
    def test_cache_expiry(self):
        """Test that cache expires correctly."""
        validator = JWTValidator()
        validator._cache["token123"] = ({"username": "test"}, time.time() - 1)  # Expired
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {"username": "test"}
            )
            
            validator.validate_token("token123")
            
            # Should hit service because cache expired
            assert mock_get.call_count == 1
    
    def test_validate_locally_with_secret(self):
        """Test local validation when secret is configured."""
        validator = JWTValidator()
        validator._secret = "test_secret"
        
        from jose import jwt
        token = jwt.encode({"username": "test", "exp": int(time.time()) + 3600}, "test_secret", algorithm="HS256")
        
        result = validator._validate_locally(token)
        
        assert result["username"] == "test"
    
    def test_validate_locally_invalid_secret(self):
        """Test local validation fails with wrong secret."""
        validator = JWTValidator()
        validator._secret = "wrong_secret"
        
        from jose import jwt
        token = jwt.encode({"username": "test", "exp": int(time.time()) + 3600}, "test_secret", algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc:
            validator._validate_locally(token)
        
        assert exc.value.status_code == 401
    
    def test_clear_cache(self):
        """Test cache clearing."""
        validator = JWTValidator()
        validator._cache["token1"] = ({"user": "test"}, time.time() + 300)
        
        assert len(validator._cache) == 1
        
        validator.clear_cache()
        
        assert len(validator._cache) == 0


class TestRequireRoles:
    """Test role-based access control."""
    
    def test_require_roles_success(self):
        """Test role check with valid role."""
        validator = JWTValidator()
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {"username": "admin", "roles": ["admin", "user"]}
            )
            
            checker = require_roles(["admin"])
            
            # Mock credentials
            mock_credentials = Mock()
            mock_credentials.credentials = "valid_token"
            
            # Should not raise
            result = checker(mock_credentials)
            assert result["username"] == "admin"
    
    def test_require_roles_failure(self):
        """Test role check with invalid role."""
        with patch('shared.jwt_validator._validator.validate_token') as mock_validate:
            mock_validate.return_value = {"username": "user", "roles": ["user"]}
            
            checker = require_roles(["admin"])
            
            # Mock credentials
            mock_credentials = Mock()
            mock_credentials.credentials = "valid_token"
            
            with pytest.raises(HTTPException) as exc:
                checker(mock_credentials)
            
            assert exc.value.status_code == 403
            assert "admin" in exc.value.detail


class TestServiceAccount:
    """Test service account functionality."""
    
    def test_create_service_account(self):
        """Test creating service account."""
        import os
        os.environ["MONEY_SERVICE_TOKEN"] = "test_token_123"
        
        account = create_service_account("money")
        
        assert account.service_name == "money"
        assert account.service_token == "test_token_123"
        assert account.get_headers()["Authorization"] == "Bearer test_token_123"
        assert account.get_headers()["X-Service-Name"] == "money"
    
    def test_create_service_account_missing_token(self):
        """Test creating service account without token fails."""
        import os
        if "MISSING_SERVICE_TOKEN" in os.environ:
            del os.environ["MISSING_SERVICE_TOKEN"]
        
        with pytest.raises(ValueError) as exc:
            create_service_account("missing_service")
        
        assert "not configured" in str(exc.value)
    
    def test_validate_service_token_success(self):
        """Test service token validation."""
        with patch('shared.jwt_validator._validator.validate_token') as mock_validate:
            mock_validate.return_value = {"service_name": "test_service"}
            
            result = validate_service_token("token", "test_service")
            
            assert result is True
    
    def test_validate_service_token_wrong_service(self):
        """Test service token validation with wrong service."""
        with patch('shared.jwt_validator._validator.validate_token') as mock_validate:
            mock_validate.return_value = {"service_name": "other_service"}
            
            result = validate_service_token("token", "test_service")
            
            assert result is False


class TestFlaskIntegration:
    """Test Flask integration decorators."""
    
    def test_flask_auth_required_success(self):
        """Test Flask auth decorator with valid token."""
        mock_func = Mock(return_value="success")
        decorated = flask_auth_required(mock_func)
        
        # Mock Flask request and jsonify inside the decorator
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        
        with patch.dict('sys.modules', {'flask': MagicMock(request=mock_request, jsonify=Mock(return_value=({"error": "test"}, 401)))}):
            with patch('shared.jwt_validator._validator.validate_token') as mock_validate:
                mock_validate.return_value = {"username": "test"}
                
                result = decorated()
                
                assert result == "success"
                assert mock_request.current_user == {"username": "test"}
    
    def test_flask_auth_required_missing_header(self):
        """Test Flask auth decorator without header."""
        mock_func = Mock(return_value="success")
        decorated = flask_auth_required(mock_func)
        
        mock_request = MagicMock()
        mock_request.headers = {}
        
        with patch.dict('sys.modules', {'flask': MagicMock(request=mock_request, jsonify=Mock(return_value=({"error": "Missing"}, 401)))}):
            result = decorated()
            
            # Should return 401 response
            assert isinstance(result, tuple)
            assert result[1] == 401
    
    def test_flask_require_roles_success(self):
        """Test Flask roles decorator with valid role."""
        mock_func = Mock(return_value="success")
        decorated = flask_require_roles("admin")(mock_func)
        
        mock_request = MagicMock()
        mock_request.current_user = {"roles": ["admin"]}
        
        with patch.dict('sys.modules', {'flask': MagicMock(request=mock_request, jsonify=Mock())}):
            result = decorated()
            
            assert result == "success"
    
    def test_flask_require_roles_failure(self):
        """Test Flask roles decorator without required role."""
        mock_func = Mock(return_value="success")
        decorated = flask_require_roles("admin")(mock_func)
        
        mock_request = MagicMock()
        mock_request.current_user = {"roles": ["user"]}
        
        with patch.dict('sys.modules', {'flask': MagicMock(request=mock_request, jsonify=Mock(return_value=({"error": "Forbidden"}, 403)))}):
            result = decorated()
            
            # Should return 403 response
            assert isinstance(result, tuple)
            assert result[1] == 403


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_auth_service_timeout(self):
        """Test handling of auth service timeout."""
        validator = JWTValidator()
        validator._secret = None
        
        with patch('requests.get') as mock_get:
            from requests.exceptions import Timeout
            mock_get.side_effect = Timeout("Connection timed out")
            
            # Without fallback secret, should raise 503
            with pytest.raises(HTTPException) as exc:
                validator.validate_token("token")
            
            assert exc.value.status_code == 503
    
    def test_auth_service_connection_error(self):
        """Test handling of auth service connection error."""
        validator = JWTValidator()
        validator._secret = "fallback_secret"
        
        with patch('requests.get') as mock_get:
            from requests.exceptions import ConnectionError
            mock_get.side_effect = ConnectionError("Connection refused")
            
            # With fallback secret, should try local validation
            from jose import jwt
            token = jwt.encode({"username": "test", "exp": int(time.time()) + 3600}, 
                               "fallback_secret", algorithm="HS256")
            
            result = validator.validate_token(token)
            assert result["username"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
