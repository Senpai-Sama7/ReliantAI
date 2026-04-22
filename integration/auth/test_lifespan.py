"""Lifespan tests for the auth service."""

from __future__ import annotations

import pytest

import auth_server
from auth_server import app, lifespan
from memory_redis import MemoryRedis


@pytest.mark.asyncio
async def test_lifespan_initializes_and_cleans_up_services(tmp_path, monkeypatch):
    """FastAPI lifespan should initialize and then release all auth dependencies."""
    await auth_server.shutdown_services()
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setattr(auth_server.redis, "from_url", lambda *args, **kwargs: MemoryRedis())

    async with lifespan(app):
        assert auth_server.redis_client is not None
        assert auth_server.user_store is not None
        assert auth_server.rate_limiter is not None

    assert auth_server.redis_client is None
    assert auth_server.user_store is None
    assert auth_server.rate_limiter is None
