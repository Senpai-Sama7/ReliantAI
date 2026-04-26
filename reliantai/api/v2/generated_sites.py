import os
import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ...db import get_db_session
from ...db.models import GeneratedSite

# Optional Redis cache
try:
    import redis
    redis_client = redis.Redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379"),
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True
    )
    CACHE_TTL = int(os.environ.get("SITE_CACHE_TTL", "3600"))  # 1 hour default
except (ImportError, redis.ConnectionError):
    redis_client = None
    CACHE_TTL = 0

router = APIRouter(prefix="/api/v2/generated-sites", tags=["generated-sites"])


def _get_cache_key(slug: str) -> str:
    """Generate cache key for site slug."""
    return f"site:{slug}"


@router.get("/{slug}")
def get_generated_site(slug: str) -> Dict[str, Any]:
    """Retrieve generated site content by slug.
    
    Args:
        slug: Unique slug identifier for the site.
    
    Returns:
        Dict containing site content, status, metadata, and configuration.
    
    Raises:
        HTTPException: If site not found (404).
    """
    cache_key = _get_cache_key(slug)
    
    # Try cache first
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except redis.RedisError:
            pass  # Fall through to DB
    
    with get_db_session() as db:
        site = db.query(GeneratedSite).filter_by(slug=slug).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        content = site.site_content or {}
        content["status"] = site.status
        content["slug"] = site.slug
        content["meta_title"] = site.meta_title
        content["meta_description"] = site.meta_description
        content["lighthouse_score"] = site.lighthouse_score
        content["site_config"] = site.site_config
        content["schema_org"] = site.schema_org_json
        
        # Cache the result
        if redis_client and CACHE_TTL > 0:
            try:
                redis_client.setex(cache_key, CACHE_TTL, json.dumps(content))
            except redis.RedisError:
                pass  # Cache failure shouldn't break the request
        
        return content
