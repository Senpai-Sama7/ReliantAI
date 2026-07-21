"""Caching service for generated sites."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover
    redis = None

    class RedisError(Exception):  # type: ignore[no-redef]
        """Fallback when redis package is unavailable."""


log = logging.getLogger(__name__)

SITE_CACHE_TTL = int(os.environ.get("SITE_CACHE_TTL", "3600"))

_redis_client = None


def _get_redis_client():
    """Lazy Redis client. Returns None when unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.environ.get("REDIS_URL")
    if not redis_url or redis is None:
        return None

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        _redis_client = client
    except Exception as exc:
        log.warning("redis_unavailable", extra={"error": str(exc)[:120]})
        _redis_client = None
    return _redis_client


# Public alias used by tests / callers
get_redis_client = _get_redis_client


def get_cached_site(slug: str) -> Optional[dict]:
    """Get cached site content by slug."""
    client = _get_redis_client()
    if not client:
        return None

    try:
        cached = client.get(f"site:{slug}")
        if cached:
            return json.loads(cached)
    except (RedisError, json.JSONDecodeError, TypeError, ValueError) as exc:
        log.warning("cache_get_failed", extra={"slug": slug, "error": str(exc)[:120]})
    return None


def set_cached_site(slug: str, content: dict[str, Any], ttl: int | None = None) -> bool:
    """Cache site content by slug. No-op when TTL is zero or Redis is down."""
    effective_ttl = SITE_CACHE_TTL if ttl is None else ttl
    if effective_ttl <= 0:
        return False

    client = _get_redis_client()
    if not client:
        return False

    try:
        client.setex(f"site:{slug}", effective_ttl, json.dumps(content))
        return True
    except (RedisError, TypeError, ValueError) as exc:
        log.warning("cache_set_failed", extra={"slug": slug, "error": str(exc)[:120]})
        return False


def invalidate_site_cache(slug: str) -> bool:
    """Delete cached site content so the next read hits the DB."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        client.delete(f"site:{slug}")
        return True
    except RedisError as exc:
        log.warning("cache_invalidate_failed", extra={"slug": slug, "error": str(exc)[:120]})
        return False
