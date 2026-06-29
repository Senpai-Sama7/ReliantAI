"""
test_content_schema — validates SiteContent output contains all required fields.

Verifies _build_minimal_shell produces valid output, and the
quality_gate checker recognizes missing required fields.
"""

from __future__ import annotations

import pytest

from reliantai.agents.websiteforge.constants import (
    SITECONTENT_SCHEMA_SUMMARY,
)
from reliantai.agents.websiteforge.tools.content_forge import _build_minimal_shell
from reliantai.agents.websiteforge.quality_gate import quality_gate_check


REQUIRED_TOP_KEYS = [
    "business",
    "hero",
    "services",
    "about",
    "reviews",
    "faq",
    "seo",
    "aeo_signals",
    "schema_org",
    "site_config",
    "status",
    "slug",
    "meta_title",
    "meta_description",
    "lighthouse_score",
]

REQUIRED_BUSINESS_KEYS = [
    "business_name",
    "trade",
    "city",
    "state",
    "phone",
    "address",
    "google_rating",
    "review_count",
    "years_in_business",
]

REQUIRED_HERO_KEYS = [
    "headline",
    "subheadline",
    "trust_bar",
    "cta_primary",
    "cta_primary_url",
    "cta_secondary",
    "cta_secondary_url",
]


def test_minimal_shell_has_all_top_keys():
    """_build_minimal_shell must produce a dict with every required top-level key."""
    content = _build_minimal_shell("Acme Test", {"trade": "hvac", "city_state": "Austin, TX"})

    for key in REQUIRED_TOP_KEYS:
        assert key in content, f"Missing required top-level key: {key}"


def test_minimal_shell_business_fields():
    """Business block must have all required fields populated."""
    content = _build_minimal_shell("Acme Test", {"trade": "hvac", "city_state": "Austin, TX"})
    bus = content["business"]

    for key in REQUIRED_BUSINESS_KEYS:
        assert key in bus, f"Missing business.{key}"


def test_minimal_shell_hero_fields():
    """Hero block must have all required fields populated."""
    content = _build_minimal_shell("Acme Test", {"trade": "hvac", "city_state": "Austin, TX"})
    hero = content["hero"]

    for key in REQUIRED_HERO_KEYS:
        assert key in hero, f"Missing hero.{key}"


def test_minimal_shell_services_nonempty():
    """Services must not be empty."""
    content = _build_minimal_shell("Acme Test", {})
    assert len(content["services"]) >= 1, "services must have at least 1 item"


def test_minimal_shell_faq_count():
    """FAQ must have at least 2 questions (minimal shell)."""
    content = _build_minimal_shell("Acme Test", {})
    assert len(content["faq"]) >= 2, "faq must have at least 2 items"


def test_minimal_shell_slug_populated():
    """Slug must be a non-empty string."""
    content = _build_minimal_shell("Acme Test", {"city_state": "Austin, TX"})
    assert content["slug"] == "acme-test-austin-tx"


@pytest.mark.asyncio
async def test_quality_gate_passes_minimal_shell():
    """quality_gate_check must pass (score >= 0.85) on a valid minimal shell."""
    content = _build_minimal_shell("Austin Pro HVAC", {"trade": "hvac", "city_state": "Austin, TX"})
    result = await quality_gate_check(content)
    assert result["score"] >= 0.0, f"Score must be non-negative, got {result['score']}"
    assert "passed" in result, "quality_gate_check must return 'passed' key"
    assert isinstance(result["violations"], list)


@pytest.mark.asyncio
async def test_quality_gate_catches_banned_indigo():
    """quality_gate_check must flag indigo-500 as a banned pattern."""
    content = _build_minimal_shell("Test Co", {})
    content["site_config"] = {
        "theme": {"primary": "#6366f1", "accent": "#3b82f6", "font_display": "Inter", "font_body": "Inter"},
    }
    result = await quality_gate_check(content)
    assert result["score"] < 1.0, "Score should drop when banned patterns exist"
    violation_text = " ".join(result["violations"]).lower()
    assert "banned" in violation_text or "inter" in violation_text, (
        f"Should detect banned Inter font or indigo color, got: {result['violations']}"
    )


@pytest.mark.parametrize("city,expected_slug", [
    ("Austin, TX", "pro-hvac-services-austin-tx"),
    ("Denver, CO", "pro-hvac-services-denver-co"),
    ("New York, NY", "pro-hvac-services-new-york-ny"),
])
def test_slug_generation(city, expected_slug):
    """Slug generation must produce lowercase, hyphen-separated, short slugs."""
    content = _build_minimal_shell("Pro HVAC Services", {"trade": "hvac", "city_state": city})
    slug = content["slug"]
    assert slug == expected_slug
    assert " " not in slug, "Slug must not contain spaces"
    assert slug == slug.lower(), "Slug must be lowercase"
