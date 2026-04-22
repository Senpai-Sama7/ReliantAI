"""Additional auth rate-limiter edge-case tests."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

AUTH_DIR = Path(__file__).resolve().parents[1] / "auth"
sys.path.insert(0, str(AUTH_DIR))

from memory_redis import MemoryRedis  # noqa: E402
from rate_limiter import SlidingWindowRateLimiter  # noqa: E402


@pytest.mark.asyncio
async def test_rate_limiter_trims_expired_requests_and_formats_key() -> None:
    cache = MemoryRedis()
    limiter = SlidingWindowRateLimiter(cache, prefix="edge")
    key = limiter._key("token", "203.0.113.5")

    await cache.zadd(key, {"expired": time.time() - 120})

    decision = await limiter.check("token", "203.0.113.5", limit=2, window_seconds=60)

    assert key == "edge:token:203.0.113.5"
    assert decision.allowed is True
    assert decision.remaining == 1
    assert await cache.zcard(key) == 1


@pytest.mark.asyncio
async def test_rate_limiter_defaults_retry_after_when_oldest_entry_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = MemoryRedis()
    limiter = SlidingWindowRateLimiter(cache, prefix="edge")
    key = limiter._key("register", "198.51.100.8")

    await cache.zadd(key, {"existing": time.time()})

    async def empty_zrange(*args, **kwargs):
        return []

    monkeypatch.setattr(cache, "zrange", empty_zrange)

    decision = await limiter.check("register", "198.51.100.8", limit=1, window_seconds=60)

    assert decision.allowed is False
    assert decision.remaining == 0
    assert decision.retry_after == 60
