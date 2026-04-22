"""Shared auth-service integration tests for Money API authentication."""

from __future__ import annotations

from typing import Any

import requests


def _fake_response(status_code: int, payload: dict[str, Any] | None = None) -> Any:
    class Response:
        def __init__(self) -> None:
            self.status_code = status_code

        def json(self) -> dict[str, Any]:
            return payload or {}

    return Response()


class TestSharedAuthIntegration:
    def test_dispatch_accepts_valid_bearer_token(self, client, monkeypatch):
        captured: dict[str, Any] = {}

        def fake_get(url: str, headers: dict[str, str], timeout: int) -> Any:
            captured["url"] = url
            captured["headers"] = headers
            captured["timeout"] = timeout
            return _fake_response(
                200,
                {
                    "valid": True,
                    "user_id": "money-user",
                    "username": "money-user",
                    "tenant_id": "tenant-alpha",
                    "role": "admin",
                    "roles": ["admin"],
                },
            )

        monkeypatch.setattr("main.requests.get", fake_get)

        response = client.post(
            "/dispatch",
            json={"customer_message": "AC not cooling", "outdoor_temp_f": 95.0},
            headers={"Authorization": "Bearer shared-token"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "complete"
        assert captured == {
            "url": "http://localhost:8080/verify",
            "headers": {"Authorization": "Bearer shared-token"},
            "timeout": 5,
        }

    def test_dispatch_rejects_invalid_bearer_token(self, client, monkeypatch):
        monkeypatch.setattr("main.requests.get", lambda *args, **kwargs: _fake_response(401))

        response = client.post(
            "/dispatch",
            json={"customer_message": "AC not cooling"},
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired token"

    def test_dispatch_returns_503_when_auth_service_is_unavailable(self, client, monkeypatch):
        def fake_get(*args, **kwargs):
            raise requests.RequestException("auth down")

        monkeypatch.setattr("main.requests.get", fake_get)

        response = client.post(
            "/dispatch",
            json={"customer_message": "AC not cooling"},
            headers={"Authorization": "Bearer live-token"},
        )

        assert response.status_code == 503
        assert response.json()["detail"] == "Auth Service unavailable"
