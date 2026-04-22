from __future__ import annotations

import json

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from cache import CacheManager
from control_auth import CONTROL_API_KEY_ENV, require_control_api_key


def _build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(CONTROL_API_KEY_ENV, "intelligent-storage-super-secret")
    app = FastAPI()

    @app.post("/control")
    async def control(_: None = Depends(require_control_api_key)):
        return {"status": "ok"}

    return TestClient(app)


def test_control_auth_rejects_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)

    response = client.post("/control")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid control API key"


def test_control_auth_accepts_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)

    response = client.post(
        "/control",
        headers={"X-ISN-Control-Key": "intelligent-storage-super-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_cache_manager_uses_json_serialization() -> None:
    cache = CacheManager()
    payload = {"results": [{"id": 1, "path": "alpha.py"}], "total": 1}

    encoded = cache._serialize(payload)
    decoded = cache._deserialize(encoded)

    assert decoded == payload
    with pytest.raises((UnicodeDecodeError, json.JSONDecodeError)):
        cache._deserialize(b"\x80\x04K.")
