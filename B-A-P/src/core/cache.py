"""
Async Redis cache connection and management.
"""
import redis.asyncio as aioredis
from typing import Optional, Any
import json
from src.config import get_settings

settings = get_settings()


class CacheManager:
    """Redis cache manager for handling connections and operations."""

    def __init__(self) -> None:
        self.redis: Optional[aioredis.Redis] = None
        self.url = settings.REDIS_URL

    async def connect(self) -> "CacheManager":
        """Connect to Redis and return the cache manager instance."""
        if not self.redis:
            try:
                self.redis = await aioredis.from_url(
                    self.url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Redis: {e}") from e
        return self

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.redis:
            await self.connect()
        redis_instance = self.redis
        if redis_instance is None:
            return None
        value = await redis_instance.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL."""
        if not self.redis:
            await self.connect()
        redis_instance = self.redis
        if redis_instance is None:
            return False
        if not isinstance(value, str):
            value = json.dumps(value)
        if ttl:
            return await redis_instance.setex(key, ttl, value)
        return await redis_instance.set(key, value)

    async def delete(self, key: str) -> int:
        """Delete a key from cache."""
        if not self.redis:
            await self.connect()
        redis_instance = self.redis
        if redis_instance is None:
            return 0
        return await redis_instance.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        if not self.redis:
            await self.connect()
        redis_instance = self.redis
        if redis_instance is None:
            return False
        return await redis_instance.exists(key) > 0

    async def clear(self) -> bool:
        """Clear all keys from cache."""
        if not self.redis:
            await self.connect()
        redis_instance = self.redis
        if redis_instance is None:
            return False
        return await redis_instance.flushdb()


# Global cache manager instance
cache_manager = CacheManager()


async def get_redis() -> CacheManager:
    """Dependency for getting Redis cache in FastAPI."""
    if not cache_manager.redis:
        await cache_manager.connect()
    return cache_manager
