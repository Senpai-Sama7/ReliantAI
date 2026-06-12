"""Redis cache helpers for generated site content."""

from __future__ import annotations

import json
import os
from typing import Any

try:
    import redis

    RedisError = redis.RedisError
except ImportError:
    redis = None  # type: ignore[assignment]
    _redis_client = None

    class RedisError(Exception):
        pass

else:
    try:
        _redis_client = redis.Redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
    except RedisError:
        _redis_client = None

SITE_CACHE_TTL = int(os.environ.get("SITE_CACHE_TTL", "3600"))


def site_cache_key(slug: str) -> str:
    return f"site:{slug}"


def get_cached_site(slug: str) -> dict[str, Any] | None:
    if not _redis_client:
        return None
    try:
        cached = _redis_client.get(site_cache_key(slug))
        if cached:
            return json.loads(cached)
    except (RedisError, json.JSONDecodeError):
        pass
    return None


def set_cached_site(slug: str, content: dict[str, Any]) -> None:
    if not _redis_client or SITE_CACHE_TTL <= 0:
        return
    try:
        _redis_client.setex(site_cache_key(slug), SITE_CACHE_TTL, json.dumps(content))
    except RedisError:
        pass


def invalidate_site_cache(slug: str) -> None:
    if not _redis_client:
        return
    try:
        _redis_client.delete(site_cache_key(slug))
    except RedisError:
        pass
