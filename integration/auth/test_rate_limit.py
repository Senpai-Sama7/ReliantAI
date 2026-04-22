"""Rate limit tests for auth endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import auth_server
from auth_server import User, Role, hash_password, store_user
from memory_redis import MemoryRedis


TEST_IP = "203.0.113.10"


@pytest_asyncio.fixture(autouse=True)
async def cleanup_services():
    """Ensure each rate limit test starts with clean globals."""
    await auth_server.shutdown_services()
    yield
    await auth_server.shutdown_services()


@pytest_asyncio.fixture
async def auth_client(tmp_path: Path):
    """Start the auth app against an isolated SQLite database and in-memory Redis."""
    cache = MemoryRedis()
    await auth_server.initialize_services(
        redis_factory=lambda *args, **kwargs: cache,
        db_path=tmp_path / "auth.db",
    )

    transport = ASGITransport(app=auth_server.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, cache


@pytest.mark.asyncio
async def test_register_rate_limit_returns_429_and_retry_after(auth_client):
    """The sixth registration attempt in one minute from the same IP should be rejected."""
    client, cache = auth_client
    headers = {"x-forwarded-for": TEST_IP}

    for attempt in range(5):
        response = await client.post(
            "/register",
            headers=headers,
            json={
                "username": f"register-user-{attempt}",
                "email": f"register-user-{attempt}@example.com",
                "password": "register-pass-123",
                "tenant_id": "tenant-register",
                "role": "technician",
            },
        )
        assert response.status_code == 201

    rate_limited = await client.post(
        "/register",
        headers=headers,
        json={
            "username": "register-user-overflow",
            "email": "register-user-overflow@example.com",
            "password": "register-pass-123",
            "tenant_id": "tenant-register",
            "role": "technician",
        },
    )

    assert rate_limited.status_code == 429
    assert rate_limited.headers["Retry-After"].isdigit()
    assert 1 <= int(rate_limited.headers["Retry-After"]) <= 60
    assert await cache.zcard(f"rate_limit:register:{TEST_IP}") == 5


@pytest.mark.asyncio
async def test_token_rate_limit_returns_429_and_retry_after(auth_client):
    """The eleventh token request in one minute from the same IP should be rejected."""
    client, cache = auth_client
    headers = {"x-forwarded-for": TEST_IP}

    await store_user(
        User(
            username="token-user",
            email="token-user@example.com",
            tenant_id="tenant-token",
            role=Role.ADMIN,
            hashed_password=hash_password("token-pass-123"),
        )
    )

    for _ in range(10):
        response = await client.post(
            "/token",
            headers=headers,
            data={"username": "token-user", "password": "token-pass-123"},
        )
        assert response.status_code == 200

    rate_limited = await client.post(
        "/token",
        headers=headers,
        data={"username": "token-user", "password": "token-pass-123"},
    )

    assert rate_limited.status_code == 429
    assert rate_limited.headers["Retry-After"].isdigit()
    assert 1 <= int(rate_limited.headers["Retry-After"]) <= 60
    assert await cache.zcard(f"rate_limit:token:{TEST_IP}") == 10
