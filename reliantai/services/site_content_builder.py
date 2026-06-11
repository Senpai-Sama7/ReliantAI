"""Normalize agent copy_package + research data into ISR SiteContent shape."""

from __future__ import annotations

from typing import Any

TRADE_AEO_DEFAULTS: dict[str, dict[str, Any]] = {
    "hvac": {
        "local_business_type": "HVACBusiness",
        "primary_category": "HVAC contractor",
        "secondary_categories": ["Air conditioning contractor", "Heating contractor"],
    },
    "plumbing": {
        "local_business_type": "Plumber",
        "primary_category": "Plumber",
        "secondary_categories": ["Drain cleaning service", "Water heater repair"],
    },
    "electrical": {
        "local_business_type": "Electrician",
        "primary_category": "Electrician",
        "secondary_categories": ["Electrical installation", "Panel upgrade"],
    },
    "roofing": {
        "local_business_type": "RoofingContractor",
        "primary_category": "Roofing contractor",
        "secondary_categories": ["Roof repair", "Storm damage repair"],
    },
    "painting": {
        "local_business_type": "HousePainter",
        "primary_category": "Painting contractor",
        "secondary_categories": ["Interior painting", "Exterior painting"],
    },
    "landscaping": {
        "local_business_type": "LandscapingBusiness",
        "primary_category": "Landscaper",
        "secondary_categories": ["Lawn care", "Landscape design"],
    },
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _normalize_lighthouse_score(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _phone_href(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 10:
        return f"tel:+1{digits}"
    if digits:
        return f"tel:+{digits}"
    return "tel:"


def _normalize_reviews(copy_reviews: Any, research_data: dict) -> dict:
    if isinstance(copy_reviews, dict):
        reviews = copy_reviews.get("reviews", [])
        aggregate_line = copy_reviews.get(
            "aggregate_line",
            f"{research_data.get('rating', 0)} stars across "
            f"{research_data.get('review_count', 0)} reviews",
        )
        return {"reviews": reviews or [], "aggregate_line": aggregate_line}

    research_reviews = research_data.get("reviews", [])
    if isinstance(research_reviews, list) and research_reviews:
        return {
            "reviews": research_reviews[:5],
            "aggregate_line": (
                f"{research_data.get('rating', 0)} stars across "
                f"{research_data.get('review_count', 0)} reviews"
            ),
        }

    return {"reviews": [], "aggregate_line": ""}


def _normalize_about(copy_about: Any) -> dict:
    if not isinstance(copy_about, dict):
        return {"story": "", "trust_points": [], "certifications": []}

    story = copy_about.get("story") or copy_about.get("owner_story", "")
    trust_points = copy_about.get("trust_points", [])
    certifications = copy_about.get("certifications", [])
    return {
        "story": story,
        "trust_points": trust_points if isinstance(trust_points, list) else [],
        "certifications": certifications if isinstance(certifications, list) else [],
    }


def _normalize_hero(copy_hero: Any, phone: str) -> dict:
    hero = copy_hero if isinstance(copy_hero, dict) else {}
    return {
        "headline": hero.get("headline", ""),
        "subheadline": hero.get("subheadline", ""),
        "trust_bar": hero.get("trust_bar", [])[:3],
        "cta_primary": hero.get("cta_primary", "Call Now"),
        "cta_primary_url": hero.get("cta_primary_url", _phone_href(phone)),
        "cta_secondary": hero.get("cta_secondary", "View Services"),
        "cta_secondary_url": hero.get("cta_secondary_url", "#services"),
    }


def build_site_content(
    *,
    copy_package: dict,
    research_data: dict,
    prospect: Any,
    slug: str,
    template_id: str,
    theme: dict,
    schema_org: dict,
    status: str = "preview_live",
    lighthouse_score: int | None = None,
) -> dict:
    """Build a SiteContent-compatible dict for ISR templates."""
    trade = prospect.trade
    phone = (
        research_data.get("phone")
        or getattr(prospect, "phone", None)
        or ""
    )
    business_name = (
        research_data.get("name")
        or getattr(prospect, "business_name", "")
    )
    city = research_data.get("city") or getattr(prospect, "city", "")
    state = research_data.get("state") or getattr(prospect, "state", "")

    aeo_defaults = TRADE_AEO_DEFAULTS.get(trade, TRADE_AEO_DEFAULTS["hvac"])
    seo = copy_package.get("seo", {}) if isinstance(copy_package.get("seo"), dict) else {}
    meta_title = seo.get("title", f"{business_name} - {city}")
    meta_description = seo.get("description", "")

    score = _normalize_lighthouse_score(lighthouse_score)
    if score is None:
        score = _normalize_lighthouse_score(research_data.get("pagespeed_score"))

    business_reviews = _normalize_reviews(
        copy_package.get("reviews"),
        research_data,
    )

    return {
        "business": {
            "business_name": business_name,
            "trade": trade,
            "city": city,
            "state": state,
            "phone": phone,
            "email": research_data.get("email") or getattr(prospect, "email", None),
            "address": research_data.get("address") or getattr(prospect, "address", ""),
            "google_rating": _safe_float(
                research_data.get("rating")
                or getattr(prospect, "google_rating", None)
            ),
            "review_count": _safe_int(
                research_data.get("review_count")
                or getattr(prospect, "review_count", None)
            ),
            "website_url": (
                research_data.get("website")
                or research_data.get("website_url")
                or getattr(prospect, "website_url", None)
            ),
            "owner_name": research_data.get("owner_name"),
            "owner_title": research_data.get("owner_title"),
            "years_in_business": research_data.get("years_in_business"),
            "service_area": research_data.get("service_area") or f"{city}, {state}",
            "reviews": business_reviews.get("reviews", []),
        },
        "hero": _normalize_hero(copy_package.get("hero"), phone),
        "services": copy_package.get("services", []) if isinstance(copy_package.get("services"), list) else [],
        "about": _normalize_about(copy_package.get("about")),
        "reviews": business_reviews,
        "faq": copy_package.get("faq", []) if isinstance(copy_package.get("faq"), list) else [],
        "seo": {
            "title": meta_title,
            "description": meta_description,
            "keywords": seo.get("keywords", []) if isinstance(seo.get("keywords"), list) else [],
        },
        "aeo_signals": {
            "local_business_type": aeo_defaults["local_business_type"],
            "primary_category": aeo_defaults["primary_category"],
            "secondary_categories": aeo_defaults["secondary_categories"],
            "area_served": [city, f"{city}, {state}"],
        },
        "schema_org": schema_org,
        "site_config": {
            "template_id": template_id,
            "trade": trade,
            "theme": theme,
        },
        "status": status,
        "slug": slug,
        "meta_title": meta_title,
        "meta_description": meta_description,
        "lighthouse_score": score if score is not None else 0,
    }
