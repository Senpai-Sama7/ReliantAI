from fastapi import APIRouter, HTTPException

from ...db import get_db_session
from ...db.models import GeneratedSite

router = APIRouter(prefix="/api/v2/generated-sites", tags=["generated-sites"])


@router.get("/{slug}")
def get_generated_site(slug: str):
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
        return content
