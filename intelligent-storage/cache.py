"""Caching layer for Intelligent Storage Nexus using Redis with fallback to in-memory dict.

Phase 3C: Query & embedding cache layer
- Embedding cache: 1 hour TTL
- Search result cache: 5 minute TTL
- Fallback to Python dict if Redis unavailable
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import Redis, fallback to dict if unavailable
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory dict fallback")


class CacheManager:
    """Manages caching with Redis (preferred) or in-memory dict (fallback)."""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        embedding_ttl: int = 3600,  # 1 hour
        search_ttl: int = 300,  # 5 minutes
        max_memory_entries: int = 10000,
    ):
        self.embedding_ttl = embedding_ttl
        self.search_ttl = search_ttl
        self.max_memory_entries = max_memory_entries
        self._redis: Optional[Any] = None
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._using_redis = False

        # Try to connect to Redis
        if REDIS_AVAILABLE:
            try:
                self._redis = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=False,  # We'll handle serialization
                    socket_connect_timeout=2,
                )
                self._using_redis = True
                logger.info(f"✅ Cache: Redis connected ({redis_host}:{redis_port})")
            except Exception as e:
                logger.warning(
                    f"⚠️  Cache: Redis connection failed: {e}, using memory fallback"
                )
                self._redis = None
        else:
            logger.info("✅ Cache: Using in-memory dict fallback")

    def _make_key(self, prefix: str, data: str) -> str:
        """Create a cache key from prefix and data hash."""
        hash_val = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{hash_val}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes."""
        return json.dumps(value).encode("utf-8")

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to value."""
        return json.loads(data.decode("utf-8"))

    def _prune_memory_cache(self) -> None:
        """Prune expired memory-cache entries and enforce max size."""
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._memory_cache.items() if now >= expiry
        ]
        for key in expired_keys:
            self._memory_cache.pop(key, None)

        if len(self._memory_cache) <= self.max_memory_entries:
            return

        # Drop oldest-expiring entries first to bound memory use.
        sorted_items = sorted(self._memory_cache.items(), key=lambda item: item[1][1])
        overflow = len(self._memory_cache) - self.max_memory_entries
        for key, _ in sorted_items[:overflow]:
            self._memory_cache.pop(key, None)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text.

        Returns:
            Cached embedding vector or None if not found.
        """
        key = self._make_key("emb", text)

        if self._using_redis and self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    logger.debug(f"Cache HIT for embedding: {text[:50]}...")
                    return self._deserialize(data)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
        else:
            # Memory fallback
            if key in self._memory_cache:
                value, expiry = self._memory_cache[key]
                if time.time() < expiry:
                    logger.debug(f"Memory Cache HIT for embedding: {text[:50]}...")
                    return value
                else:
                    # Expired
                    del self._memory_cache[key]

        logger.debug(f"Cache MISS for embedding: {text[:50]}...")
        return None

    async def set_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache embedding for text with TTL."""
        key = self._make_key("emb", text)

        if self._using_redis and self._redis:
            try:
                data = self._serialize(embedding)
                await self._redis.setex(key, self.embedding_ttl, data)
                logger.debug(f"Cached embedding: {text[:50]}...")
            except Exception as e:
                logger.debug(f"Redis set error: {e}")
        else:
            # Memory fallback
            expiry = time.time() + self.embedding_ttl
            self._memory_cache[key] = (embedding, expiry)
            self._prune_memory_cache()

    async def get_search_result(
        self, query: str, limit: int, weights: Optional[Tuple[float, ...]] = None
    ) -> Optional[Dict]:
        """Get cached search result.

        Args:
            query: Search query string
            limit: Result limit
            weights: Optional weights tuple for cache key

        Returns:
            Cached search result or None if not found.
        """
        # Create cache key from query params
        cache_data = f"{query}:{limit}:{weights}"
        key = self._make_key("search", cache_data)

        if self._using_redis and self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    logger.info(f"Cache HIT for search: '{query}' (limit={limit})")
                    return self._deserialize(data)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
        else:
            # Memory fallback
            if key in self._memory_cache:
                value, expiry = self._memory_cache[key]
                if time.time() < expiry:
                    logger.info(
                        f"Memory Cache HIT for search: '{query}' (limit={limit})"
                    )
                    return value
                else:
                    del self._memory_cache[key]

        logger.info(f"Cache MISS for search: '{query}' (limit={limit})")
        return None

    async def set_search_result(
        self,
        query: str,
        limit: int,
        result: Dict,
        weights: Optional[Tuple[float, ...]] = None,
    ) -> None:
        """Cache search result with TTL."""
        cache_data = f"{query}:{limit}:{weights}"
        key = self._make_key("search", cache_data)

        if self._using_redis and self._redis:
            try:
                data = self._serialize(result)
                await self._redis.setex(key, self.search_ttl, data)
                logger.debug(f"Cached search result: '{query}'")
            except Exception as e:
                logger.debug(f"Redis set error: {e}")
        else:
            # Memory fallback
            expiry = time.time() + self.search_ttl
            self._memory_cache[key] = (result, expiry)
            self._prune_memory_cache()

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Cache: Redis connection closed")


# Global cache instance
cache_manager: Optional[CacheManager] = None


async def init_cache(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
) -> CacheManager:
    """Initialize the global cache manager."""
    global cache_manager
    cache_manager = CacheManager(
        redis_host=redis_host,
        redis_port=redis_port,
        redis_db=redis_db,
    )
    return cache_manager


async def close_cache() -> None:
    """Close the global cache manager."""
    global cache_manager
    if cache_manager:
        await cache_manager.close()
        cache_manager = None


def get_cache() -> Optional[CacheManager]:
    """Get the global cache manager instance."""
    return cache_manager
