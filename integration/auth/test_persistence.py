"""Persistence tests for the auth service user store."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio

import auth_server
from auth_server import Role, User, get_user, hash_password, store_user
from memory_redis import MemoryRedis


@pytest_asyncio.fixture(autouse=True)
async def cleanup_services():
    """Ensure each test starts and ends with a clean auth service state."""
    await auth_server.shutdown_services()
    yield
    await auth_server.shutdown_services()


async def initialize_test_services(db_path: Path) -> MemoryRedis:
    """Start auth dependencies with an isolated SQLite database and in-memory cache."""
    cache = MemoryRedis()
    await auth_server.initialize_services(
        redis_factory=lambda *args, **kwargs: cache,
        db_path=db_path,
    )
    return cache


@pytest.mark.asyncio
async def test_store_user_persists_to_sqlite_and_cache(tmp_path):
    """New users should be durable in SQLite and immediately present in cache."""
    db_path = tmp_path / "auth.db"
    cache = await initialize_test_services(db_path)

    user = User(
        username="persisted-user",
        email="persisted@example.com",
        tenant_id="tenant-1",
        role=Role.ADMIN,
        hashed_password=hash_password("correct-horse-battery"),
    )

    await store_user(user)

    stored = await auth_server.user_store.get_user(user.username)
    cached = await cache.hgetall(f"user:{user.username}")
    sqlite_metadata = await auth_server.user_store.ping()

    assert stored is not None
    assert stored["email"] == user.email
    assert cached["tenant_id"] == user.tenant_id
    assert sqlite_metadata["journal_mode"].lower() == "wal"
    assert sqlite_metadata["user_count"] == "1"

    await auth_server.shutdown_services()


@pytest.mark.asyncio
async def test_get_user_rehydrates_cache_after_cache_loss(tmp_path):
    """Cache misses should fall back to SQLite and repopulate Redis."""
    db_path = tmp_path / "auth.db"
    cache = await initialize_test_services(db_path)

    user = User(
        username="rehydrate-user",
        email="rehydrate@example.com",
        tenant_id="tenant-2",
        role=Role.OPERATOR,
        hashed_password=hash_password("another-secure-password"),
    )

    await store_user(user)
    await cache.delete(f"user:{user.username}")

    reloaded = await get_user(user.username)
    cached = await cache.hgetall(f"user:{user.username}")

    assert reloaded is not None
    assert reloaded.username == user.username
    assert cached["email"] == user.email

    await auth_server.shutdown_services()


@pytest.mark.asyncio
async def test_startup_hydrates_users_from_sqlite(tmp_path):
    """Service startup should reload persisted users into Redis from SQLite."""
    db_path = tmp_path / "auth.db"
    first_cache = await initialize_test_services(db_path)

    await store_user(
        User(
            username="startup-user",
            email="startup@example.com",
            tenant_id="tenant-3",
            role=Role.TECHNICIAN,
            hashed_password=hash_password("startup-password"),
        )
    )

    assert await first_cache.hgetall("user:startup-user")
    await auth_server.shutdown_services()

    second_cache = await initialize_test_services(db_path)
    cached = await second_cache.hgetall("user:startup-user")

    assert cached["username"] == "startup-user"
    assert cached["role"] == Role.TECHNICIAN.value

    await auth_server.shutdown_services()
