#!/usr/bin/env python3
"""Regression tests for BackupIQ auth hardening."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask import Flask

import auth_integration


@pytest.fixture(autouse=True)
def reset_auth_singleton():
    auth_integration._auth_instance = None
    yield
    auth_integration._auth_instance = None


def test_validate_token_fails_closed_when_validator_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_integration, "validator", None)
    auth = auth_integration.BackupIQAuth()

    with pytest.raises(RuntimeError, match="Authentication service unavailable"):
        auth.validate_token("token")


def test_require_auth_rejects_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_validator = MagicMock()
    mock_validator.validate_token.return_value = None
    monkeypatch.setattr(auth_integration, "validator", mock_validator)

    app = Flask(__name__)
    auth = auth_integration.BackupIQAuth(app)

    @app.get("/protected")
    @auth.require_auth
    def protected():
        return {"ok": True}

    client = app.test_client()
    response = client.get("/protected", headers={"Authorization": "Bearer bad-token"})

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid or expired token"
