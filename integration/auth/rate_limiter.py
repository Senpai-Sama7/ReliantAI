"""Redis-backed sliding window rate limiting for auth endpoints."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import math
import time
from typing import Any
import uuid


@dataclass
class RateLimitDecision:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int


class SlidingWindowRateLimiter:
    """Per-identifier sliding window limiter backed by Redis sorted sets."""

    def __init__(self, redis_client: Any, prefix: str = "rate_limit"):
        self.redis_client = redis_client
        self.prefix = prefix
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock_factory_lock = asyncio.Lock()

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create lock for key in thread-safe manner."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def check(
        self,
        scope: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Allow or reject a request based on the recent request count."""
        key = self._key(scope, identifier)

        # Get or create lock atomically
        async with self._lock_factory_lock:
            lock = self._get_lock(key)

        async with lock:
            now = time.time()
            cutoff = now - window_seconds

            await self.redis_client.zremrangebyscore(key, 0, cutoff)
            current_count = await self.redis_client.zcard(key)

            if current_count >= limit:
                oldest_entry = await self.redis_client.zrange(key, 0, 0, withscores=True)
                retry_after = window_seconds
                if oldest_entry:
                    oldest_score = float(oldest_entry[0][1])
                    retry_after = max(1, math.ceil(window_seconds - (now - oldest_score)))
                await self.redis_client.expire(key, window_seconds)
                return RateLimitDecision(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after=retry_after,
                )

            member = f"{now:.6f}:{uuid.uuid4().hex}"
            await self.redis_client.zadd(key, {member: now})
            await self.redis_client.expire(key, window_seconds)

            return RateLimitDecision(
                allowed=True,
                limit=limit,
                remaining=max(limit - current_count - 1, 0),
                retry_after=0,
            )

    def _key(self, scope: str, identifier: str) -> str:
        return f"{self.prefix}:{scope}:{identifier}"
