"""API v2 generated sites router."""

from typing import Any, FrozenSet

from fastapi import APIRouter, HTTPException

from reliantai.db import get_db_session
from reliantai.db.models import GeneratedSite
from reliantai.lib.slug import is_valid_slug
from reliantai.services.cache import get_cached_site, set_cached_site

router = APIRouter(prefix="/api/v2/generated-sites", tags=["generated-sites"])

# Only these statuses are served on the public ISR endpoint.
# Expired / draft / archived rows must 404 so previews cannot leak after expiry.
PUBLIC_SITE_STATUSES: FrozenSet[str] = frozenset(
    {"preview_live", "live", "published"}
)


def _is_public_payload(payload: dict[str, Any]) -> bool:
    status = payload.get("status")
    return isinstance(status, str) and status in PUBLIC_SITE_STATUSES


@router.get("/{slug}")
def get_generated_site(slug: str) -> dict[str, Any]:
    """Retrieve generated site content by slug (public, no auth)."""
    if not is_valid_slug(slug):
        raise HTTPException(status_code=400, detail="Invalid slug")

    cached = get_cached_site(slug)
    if cached and _is_public_payload(cached):
        return cached

    with get_db_session() as db:
        site = db.query(GeneratedSite).filter_by(slug=slug).first()
        if not site or site.status not in PUBLIC_SITE_STATUSES:
            raise HTTPException(status_code=404, detail="Site not found")

        content = dict(site.site_content or {})
        content.setdefault("status", site.status)
        content.setdefault("slug", site.slug)
        content.setdefault("meta_title", site.meta_title)
        content.setdefault("meta_description", site.meta_description)
        content.setdefault("lighthouse_score", site.lighthouse_score or 0)
        content.setdefault("site_config", site.site_config or {})
        content.setdefault("schema_org", site.schema_org_json or {})

        set_cached_site(slug, content)
        return content
