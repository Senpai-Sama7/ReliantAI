"""Caching service for generated sites."""

import os
import json
from typing import Optional, Any

try:
    import redis
except ImportError:
    redis = None


_redis_client = None


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.environ.get("REDIS_URL")
        if redis_url and redis:
            try:
                _redis_client = redis.from_url(redis_url)
                _redis_client.ping()
            except Exception:
                _redis_client = None
    return _redis_client


def get_cached_site(slug: str) -> Optional[dict]:
    """Get cached site content by slug."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        cached = client.get(f"site:{slug}")
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    
    return None


def set_cached_site(slug: str, content: dict, ttl: int = 3600) -> bool:
    """Cache site content by slug."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.setex(f"site:{slug}", ttl, json.dumps(content))
        return True
    except Exception:
        return False
