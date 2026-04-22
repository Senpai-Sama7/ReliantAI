"""
Tests for B-A-P Auth Integration.
Verifies JWT validation and event publishing for the Analytics Platform.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from jose import jwt

from src.api import auth_integration
from src.api.auth_integration import (
    get_current_user_from_shared_auth,
    require_roles,
    publish_bap_event,
    JWT_AVAILABLE,
)


def _install_validator(monkeypatch: pytest.MonkeyPatch, validator: object) -> None:
    monkeypatch.setattr(auth_integration, "validator", validator)


class TestBAPAuthIntegration:
    """Test suite for B-A-P auth integration."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful user retrieval from shared auth."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        mock_user = {"username": "testuser", "roles": ["user"]}
        
        with patch("src.api.auth_integration.validator") as mock_validator:
            mock_validator.validate_token.return_value = mock_user
            
            user = get_current_user_from_shared_auth(mock_credentials)
            
            assert user == mock_user
            mock_validator.validate_token.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test failure with invalid token."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"
        
        with patch("src.api.auth_integration.validator") as mock_validator:
            mock_validator.validate_token.return_value = None
            
            with pytest.raises(HTTPException) as excinfo:
                get_current_user_from_shared_auth(mock_credentials)
            
            assert excinfo.value.status_code == 401
            assert "Invalid or expired token" in excinfo.value.detail

    def test_require_roles_success(self):
        """Test role check - success."""
        mock_user = {"username": "admin", "roles": ["admin", "user"]}
        role_checker = require_roles(["admin"])
        
        # Should not raise
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

    @pytest.mark.asyncio
    async def test_publish_bap_event(self):
        """Test event publishing for B-A-P."""
        event_data = {"pipeline_id": "pip_001", "status": "started"}

        with patch("src.api.auth_integration.publish_event", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = {"event_id": "evt-123", "channel": "events:pipeline"}

            result = await publish_bap_event("pipeline.started", event_data, "user_001")

            assert result == {"event_id": "evt-123", "channel": "events:pipeline"}
            mock_publish.assert_awaited_once_with(
                event_type="pipeline.started",
                payload={"pipeline_id": "pip_001", "status": "started", "user_id": "user_001"},
                correlation_id=None,
                tenant_id=None,
                source_service="bap",
            )


@pytest.mark.asyncio
async def test_protected_route_requires_bearer_token(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
):
    """Protected B-A-P routes reject unauthenticated requests when bypass is disabled."""
    monkeypatch.setenv("DEV_MODE", "false")

    response = await async_client.get("/api/data/datasets")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid authentication credentials"


@pytest.mark.asyncio
async def test_protected_route_accepts_valid_locally_verified_token(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
):
    """Middleware accepts a valid bearer token through the shared validator."""
    if not JWT_AVAILABLE:
        pytest.skip("Shared JWT validator unavailable")

    monkeypatch.setenv("DEV_MODE", "false")
    validator = auth_integration.JWTValidator(
        secret_key="test-shared-secret",
        auth_url="http://127.0.0.1:9",
    )
    _install_validator(monkeypatch, validator)

    token = jwt.encode(
        {
            "sub": "bap-user",
            "tenant_id": "tenant-alpha",
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "test-shared-secret",
        algorithm="HS256",
    )

    response = await async_client.get(
        "/api/data/datasets",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_route_rejects_expired_token(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
):
    """Middleware returns 401 for expired bearer tokens."""
    if not JWT_AVAILABLE:
        pytest.skip("Shared JWT validator unavailable")

    monkeypatch.setenv("DEV_MODE", "false")
    validator = auth_integration.JWTValidator(
        secret_key="test-shared-secret",
        auth_url="http://127.0.0.1:9",
    )
    _install_validator(monkeypatch, validator)

    expired_token = jwt.encode(
        {
            "sub": "bap-user",
            "tenant_id": "tenant-alpha",
            "role": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        "test-shared-secret",
        algorithm="HS256",
    )

    response = await async_client.get(
        "/api/data/datasets",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_protected_route_fails_closed_when_validator_missing(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
):
    """Middleware must not allow requests through when the shared validator is unavailable."""
    monkeypatch.setenv("DEV_MODE", "false")
    monkeypatch.setattr(auth_integration, "validator", None)

    response = await async_client.get(
        "/api/data/datasets",
        headers={"Authorization": "Bearer arbitrary-token"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Authentication service unavailable"


@pytest.mark.asyncio
async def test_live_shared_auth_flow(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
):
    """Exercise the real auth-service login flow against B-A-P when a live auth URL is supplied."""
    live_auth_url = os.getenv("LIVE_AUTH_SERVICE_URL")
    if not live_auth_url:
        pytest.skip("Set LIVE_AUTH_SERVICE_URL to run the live cross-service auth flow test")
    if not JWT_AVAILABLE:
        pytest.skip("Shared JWT validator unavailable")

    monkeypatch.setenv("DEV_MODE", "false")
    _install_validator(monkeypatch, auth_integration.JWTValidator(auth_url=live_auth_url))

    username = f"bap_live_{uuid.uuid4().hex[:8]}"
    password = "Sup3rSecure!"
    tenant_id = "tenant-live"

    async with httpx.AsyncClient(base_url=live_auth_url, timeout=10.0) as auth_client:
        register_response = await auth_client.post(
            "/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": password,
                "tenant_id": tenant_id,
                "role": "admin",
            },
        )
        assert register_response.status_code == 201

        token_response = await auth_client.post(
            "/token",
            data={"username": username, "password": password},
        )
        assert token_response.status_code == 200
        access_token = token_response.json()["access_token"]

    response = await async_client.get(
        "/api/data/datasets",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
