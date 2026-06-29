"""Redis cache helpers for generated site content.

Lazy initialization: the Redis client is created on first use, not at module
import time. This prevents connection errors when the module is imported
before REDIS_URL is set (e.g., in tests).
"""

from __future__ import annotations

import json
import os
from typing import Any

import structlog

try:
    import redis

    RedisError = redis.RedisError
except ImportError:
    redis = None  # type: ignore[assignment]

    class RedisError(Exception):
        pass

log = structlog.get_logger()

SITE_CACHE_TTL = int(os.environ.get("SITE_CACHE_TTL", "3600"))

_redis_client: Any = None


def _get_redis_client() -> Any:
    """Lazy-initialize and return the Redis client, or None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if redis is None:
        return None
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        return None
    try:
        _redis_client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        # Verify connection works
        _redis_client.ping()
    except RedisError:
        _redis_client = None
    return _redis_client


def site_cache_key(slug: str) -> str:
    return f"site:{slug}"


def get_cached_site(slug: str) -> dict[str, Any] | None:
    client = _get_redis_client()
    if not client:
        return None
    try:
        cached = client.get(site_cache_key(slug))
        if cached:
            return json.loads(cached)
    except (RedisError, json.JSONDecodeError) as exc:
        log.warning("cache_get_failed", slug=slug, error=str(exc))
    return None


def set_cached_site(slug: str, content: dict[str, Any]) -> None:
    if SITE_CACHE_TTL <= 0:
        return
    client = _get_redis_client()
    if not client:
        return
    try:
        client.setex(site_cache_key(slug), SITE_CACHE_TTL, json.dumps(content))
    except RedisError as exc:
        log.warning("cache_set_failed", slug=slug, error=str(exc))


def invalidate_site_cache(slug: str) -> None:
    client = _get_redis_client()
    if not client:
        return
    try:
        client.delete(site_cache_key(slug))
    except RedisError as exc:
        log.warning("cache_invalidate_failed", slug=slug, error=str(exc))
