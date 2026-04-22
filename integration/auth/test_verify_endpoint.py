"""Endpoint tests for the auth-service /verify contract."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import auth_server
from memory_redis import MemoryRedis


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Run the auth service against a temporary SQLite DB and in-memory Redis."""

    async def fake_from_url(*args, **kwargs):
        return MemoryRedis()

    monkeypatch.setattr(auth_server.redis, "from_url", fake_from_url)
    monkeypatch.setenv(auth_server.AUTH_DB_PATH_ENV, str(tmp_path / "auth.db"))

    with TestClient(auth_server.app) as test_client:
        yield test_client


def _register_and_login(client: TestClient) -> str:
    username = "verify_user"
    password = "Sup3rSecure!"
    register = client.post(
        "/register",
        json={
            "username": username,
            "email": "verify_user@example.com",
            "password": password,
            "tenant_id": "tenant-verify",
            "role": "operator",
        },
    )
    assert register.status_code == 201

    token_response = client.post("/token", data={"username": username, "password": password})
    assert token_response.status_code == 200
    return token_response.json()["access_token"]


def test_verify_accepts_get_and_returns_shared_identity_fields(client: TestClient) -> None:
    token = _register_and_login(client)

    response = client.get("/verify", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["user_id"] == "verify_user"
    assert payload["username"] == "verify_user"
    assert payload["tenant_id"] == "tenant-verify"
    assert payload["role"] == "operator"
    assert payload["roles"] == ["operator"]


def test_verify_accepts_post_and_returns_shared_identity_fields(client: TestClient) -> None:
    token = _register_and_login(client)

    response = client.post("/verify", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["username"] == "verify_user"
    assert payload["roles"] == ["operator"]
