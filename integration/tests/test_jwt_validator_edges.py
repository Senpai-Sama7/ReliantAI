"""Additional JWT validator edge-case tests for integration coverage."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from shared import jwt_validator


def test_get_current_user_delegates_to_global_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        jwt_validator._validator,
        "validate_token",
        lambda token: {"username": "edge-user", "token": token},
    )

    credentials = SimpleNamespace(credentials="edge-token")
    result = jwt_validator.get_current_user(credentials)

    assert result == {"username": "edge-user", "token": "edge-token"}


def test_validate_service_token_returns_false_when_validation_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_invalid(token: str):
        raise HTTPException(status_code=401, detail="invalid")

    monkeypatch.setattr(jwt_validator._validator, "validate_token", raise_invalid)

    assert jwt_validator.validate_service_token("bad-token", "money") is False
