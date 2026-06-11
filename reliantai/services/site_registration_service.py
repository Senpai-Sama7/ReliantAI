import json
import os
import re
import uuid

import httpx
import structlog

from ..agents.tools.schema_builder import build_local_business_schema
from ..db import get_db_session
from ..db.models import GeneratedSite, Prospect
from .cache import invalidate_site_cache
from .schema_validation import validate_local_business_schema
from .site_content_builder import build_site_content

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
    """Generate a unique URL-safe slug from business name and city."""
    raw = f"{business_name.lower()}-{city.lower()}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:55]
    return f"{slug}-{str(uuid.uuid4())[:4]}"


def _get_theme(template_id: str) -> dict[str, str]:
    themes = {
        "hvac-reliable-blue": {
            "primary": "#1d4ed8",
            "accent": "#93c5fd",
            "font_display": "Outfit",
            "font_body": "Inter",
        },
        "plumbing-trustworthy-navy": {
            "primary": "#1e3a5f",
            "accent": "#60a5fa",
            "font_display": "Sora",
            "font_body": "Inter",
        },
        "electrical-sharp-gold": {
            "primary": "#1a1a1a",
            "accent": "#fbbf24",
            "font_display": "Outfit",
            "font_body": "Inter",
        },
        "roofing-bold-copper": {
            "primary": "#292524",
            "accent": "#c2713a",
            "font_display": "Sora",
            "font_body": "Inter",
        },
        "painting-clean-minimal": {
            "primary": "#f8fafc",
            "accent": "#3b82f6",
            "font_display": "Playfair Display",
            "font_body": "Inter",
        },
        "landscaping-earthy-green": {
            "primary": "#14532d",
            "accent": "#86efac",
            "font_display": "Outfit",
            "font_body": "Inter",
        },
    }
    return themes.get(template_id, themes["hvac-reliable-blue"])


COPY_PACKAGE_KEYS = frozenset({"hero", "services", "about", "seo", "faq", "reviews"})
REGISTRATION_RESULT_KEYS = frozenset({"slug", "preview_url", "schema_valid"})


def _looks_like_copy_package(data: dict) -> bool:
    return bool(COPY_PACKAGE_KEYS & data.keys())


def _looks_like_registration_result(data: dict) -> bool:
    return REGISTRATION_RESULT_KEYS <= data.keys() and not _looks_like_copy_package(data)


def _resolve_unique_slug(db, prospect, existing: GeneratedSite | None) -> str:
    if existing:
        return existing.slug
    for _ in range(10):
        slug = generate_slug(prospect.business_name, prospect.city)
        if not db.query(GeneratedSite).filter_by(slug=slug).first():
            return slug
    return f"{generate_slug(prospect.business_name, prospect.city)}-{uuid.uuid4().hex[:8]}"


def _parse_task_output(output: object) -> dict | list | None:
    """Best-effort parse of CrewAI task output into structured data."""
    if output is None:
        return None
    if isinstance(output, dict):
        return output
    if isinstance(output, list):
        return output
    model_dump = getattr(output, "model_dump", None)
    if callable(model_dump):
        return model_dump()
    to_dict = getattr(output, "dict", None)
    if callable(to_dict):
        return to_dict()
    if hasattr(output, "raw"):
        output = output.raw
    if not isinstance(output, str):
        return None
    text = output.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    return None


class SiteRegistrationService:
    @staticmethod
    def register(
        prospect_id: str,
        copy_package: dict,
        research_data: dict,
        competitor_data: list,
    ) -> dict:
        """Register or update a generated site for a prospect."""
        with get_db_session() as db:
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            if not prospect:
                return {"error": "prospect_not_found"}

            existing = db.query(GeneratedSite).filter_by(prospect_id=prospect_id).first()
            previous_slug = existing.slug if existing else None
            slug = _resolve_unique_slug(db, prospect, existing)
            template_id = TEMPLATE_MAP.get(prospect.trade, "hvac-reliable-blue")
            theme = _get_theme(template_id)

            schema = build_local_business_schema(
                business_data={
                    **research_data,
                    "slug": slug,
                    "trade": prospect.trade,
                    "name": research_data.get("name", prospect.business_name),
                    "phone": research_data.get("phone", prospect.phone),
                    "address": research_data.get("address", prospect.address),
                },
                review_data=copy_package.get("reviews", {}),
                competitor_keywords=(
                    competitor_data[0].get("top_keywords", []) if competitor_data else []
                ),
            )

            validation = validate_local_business_schema(schema)
            schema_valid = bool(validation.get("valid"))
            if not schema_valid:
                log.warning("schema_validation_failed", slug=slug, validation=validation)

            site_content = build_site_content(
                copy_package=copy_package,
                research_data=research_data,
                prospect=prospect,
                slug=slug,
                template_id=template_id,
                theme=theme,
                schema_org=schema,
                status="preview_live",
            )

            preview_url = f"https://preview.reliantai.org/{slug}"
            meta_title = site_content["meta_title"]
            meta_description = site_content["meta_description"]

            if existing:
                existing.slug = slug
                existing.template_id = template_id
                existing.preview_url = preview_url
                existing.site_content = site_content
                existing.site_config = site_content["site_config"]
                existing.schema_org_json = schema
                existing.meta_title = meta_title
                existing.meta_description = meta_description
                existing.status = "preview_live"
                if site_content.get("lighthouse_score"):
                    existing.lighthouse_score = site_content["lighthouse_score"]
            else:
                site = GeneratedSite(
                    prospect_id=prospect_id,
                    slug=slug,
                    template_id=template_id,
                    preview_url=preview_url,
                    site_content=site_content,
                    site_config=site_content["site_config"],
                    schema_org_json=schema,
                    meta_title=meta_title,
                    meta_description=meta_description,
                    lighthouse_score=site_content.get("lighthouse_score") or None,
                    status="preview_live",
                )
                db.add(site)

            db.commit()

        if previous_slug and previous_slug != slug:
            invalidate_site_cache(previous_slug)
        invalidate_site_cache(slug)

        SiteRegistrationService._revalidate_preview_cache(slug)
        log.info("site_registered", slug=slug, preview_url=preview_url)
        return {"slug": slug, "preview_url": preview_url, "schema_valid": schema_valid}

    @staticmethod
    def register_from_crew_outputs(prospect_id: str, crew) -> dict:
        """Register a site using outputs from a completed CrewAI crew."""
        copy_package: dict = {}
        research_data: dict = {}
        competitor_data: list = []

        for task in getattr(crew, "tasks", []):
            parsed = _parse_task_output(getattr(task, "output", None))
            if parsed is None:
                continue
            description = (getattr(task, "description", "") or "").lower()

            if isinstance(parsed, dict) and _looks_like_registration_result(parsed):
                continue

            if isinstance(parsed, dict) and _looks_like_copy_package(parsed):
                copy_package = parsed
                continue

            if "competitor" in description:
                if isinstance(parsed, list):
                    competitor_data = parsed
                elif isinstance(parsed, dict):
                    competitor_data = [parsed]
                continue

            if isinstance(parsed, dict) and (
                "research" in description
                or "pagespeed_score" in parsed
                or "profile_completeness" in parsed
            ):
                research_data = parsed

        if not copy_package and not research_data:
            log.warning("crew_outputs_unparseable", prospect_id=prospect_id)
            return {"error": "crew_outputs_unparseable"}

        return SiteRegistrationService.register(
            prospect_id=prospect_id,
            copy_package=copy_package or {},
            research_data=research_data or {},
            competitor_data=competitor_data,
        )

    @staticmethod
    def _revalidate_preview_cache(slug: str) -> None:
        secret = os.environ.get("REVALIDATE_SECRET", "")
        if not secret:
            log.warning("revalidate_skipped", reason="REVALIDATE_SECRET not set", slug=slug)
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    "https://preview.reliantai.org/api/revalidate",
                    json={"slug": slug},
                    headers={"Authorization": f"Bearer {secret}"},
                )
                if response.status_code >= 400:
                    log.warning(
                        "revalidate_failed",
                        slug=slug,
                        status=response.status_code,
                        body=response.text[:200],
                    )
                else:
                    log.info("revalidate_ok", slug=slug, status=response.status_code)
        except Exception as exc:
            log.warning("revalidate_failed", slug=slug, error=str(exc))
