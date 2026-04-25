import re
import uuid
import httpx
import os
import structlog
from ..db import get_db_session
from ..db.models import GeneratedSite, Prospect
from ..agents.tools.schema_builder import build_local_business_schema
from ..agents.tools.schema_validator import SchemaValidatorTool

log = structlog.get_logger()

TEMPLATE_MAP = {
    "hvac": "hvac-reliable-blue",
    "plumbing": "plumbing-trustworthy-navy",
    "electrical": "electrical-sharp-gold",
    "roofing": "roofing-bold-copper",
    "painting": "painting-clean-minimal",
    "landscaping": "landscaping-earthy-green",
}


def generate_slug(business_name: str, city: str) -> str:
    raw = f"{business_name.lower()}-{city.lower()}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:55]
    return f"{slug}-{str(uuid.uuid4())[:4]}"


def _get_theme(template_id: str) -> dict:
    themes = {
        "hvac-reliable-blue": {"primary": "#1d4ed8", "accent": "#93c5fd", "font_display": "Outfit", "font_body": "Inter"},
        "plumbing-trustworthy-navy": {"primary": "#1e3a5f", "accent": "#60a5fa", "font_display": "Sora", "font_body": "Inter"},
        "electrical-sharp-gold": {"primary": "#1a1a1a", "accent": "#fbbf24", "font_display": "Outfit", "font_body": "Inter"},
        "roofing-bold-copper": {"primary": "#292524", "accent": "#c2713a", "font_display": "Sora", "font_body": "Inter"},
        "painting-clean-minimal": {"primary": "#f8fafc", "accent": "#3b82f6", "font_display": "Playfair Display", "font_body": "Inter"},
        "landscaping-earthy-green": {"primary": "#14532d", "accent": "#86efac", "font_display": "Outfit", "font_body": "Inter"},
    }
    return themes.get(template_id, themes["hvac-reliable-blue"])


class SiteRegistrationService:

    @staticmethod
    def register(
        prospect_id: str,
        copy_package: dict,
        research_data: dict,
        competitor_data: list,
    ) -> dict:
        with get_db_session() as db:
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            if not prospect:
                return {"error": "prospect_not_found"}

            slug = generate_slug(prospect.business_name, prospect.city)
            template_id = TEMPLATE_MAP.get(prospect.trade, "hvac-reliable-blue")

            schema = build_local_business_schema(
                business_data={**research_data, "slug": slug, "trade": prospect.trade},
                review_data=copy_package.get("reviews", {}),
                competitor_keywords=competitor_data[0].get("top_keywords", []) if competitor_data else [],
            )

            validator = SchemaValidatorTool()
            schema_result = validator._run(schema)
            schema_valid = "true" in schema_result.lower() or '"valid": true' in schema_result
            if not schema_valid:
                log.warning("schema_validation_failed", slug=slug)

            preview_url = f"https://preview.reliantai.org/{slug}"

            existing = db.query(GeneratedSite).filter_by(prospect_id=prospect_id).first()
            if existing:
                existing.slug = slug
                existing.template_id = template_id
                existing.preview_url = preview_url
                existing.site_content = {**copy_package, "schema_org": schema}
                existing.site_config = {"template_id": template_id, "trade": prospect.trade, "theme": _get_theme(template_id)}
                existing.schema_org_json = schema
                existing.meta_title = copy_package.get("seo", {}).get("title", f"{prospect.business_name} - {prospect.city}")
                existing.meta_description = copy_package.get("seo", {}).get("description", "")
                existing.status = "preview_live"
            else:
                site = GeneratedSite(
                    prospect_id=prospect_id,
                    slug=slug,
                    template_id=template_id,
                    preview_url=preview_url,
                    site_content={**copy_package, "schema_org": schema},
                    site_config={"template_id": template_id, "trade": prospect.trade, "theme": _get_theme(template_id)},
                    schema_org_json=schema,
                    meta_title=copy_package.get("seo", {}).get("title", f"{prospect.business_name} - {prospect.city}"),
                    meta_description=copy_package.get("seo", {}).get("description", ""),
                    status="preview_live",
                )
                db.add(site)

            db.commit()

        SiteRegistrationService._revalidate_preview_cache(slug)
        log.info("site_registered", slug=slug, preview_url=preview_url)
        return {"slug": slug, "preview_url": preview_url, "schema_valid": schema_valid}

    @staticmethod
    def _revalidate_preview_cache(slug: str):
        try:
            secret = os.environ.get("REVALIDATE_SECRET", "")
            if not secret:
                return
            with httpx.Client(timeout=10.0) as client:
                client.post(
                    "https://preview.reliantai.org/api/revalidate",
                    json={"slug": slug},
                    headers={"Authorization": f"Bearer {secret}"},
                )
        except Exception as e:
            log.warning("revalidate_failed", slug=slug, error=str(e))
