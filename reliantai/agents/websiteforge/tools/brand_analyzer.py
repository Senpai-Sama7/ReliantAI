"""
brand_analyzer — analyze a company's online footprint and audience.

Thin wrapper over researcher.analyze_brand with structured output
suitable for the content_forge prompt.
"""

from __future__ import annotations

from typing import Any

from ...core import get_logger
from .researcher import analyze_brand

log = get_logger("agents.websiteforge.brand_analyzer")


async def run(company_name: str, company_url: str = "") -> dict[str, Any]:
    """
    Analyze a company's brand, audience, and market position.

    Returns:
        {
            "company": str,
            "signals": dict,       # name, homepage_content, top_search_results, city, trade
            "audience": dict,       # detected_from, indicators
            "trade": str,           # detected trade slug
            "facts": list[str],     # citable research facts
            "city": str,            # detected city, state
            "differentiators": list[str],
        }
    """
    log.info("brand_analyzer.start", company=company_name, url=company_url)

    result = await analyze_brand(company_name, company_url)

    signals = result.get("signals", {})
    facts = result.get("facts", [])

    differentiators = _extract_differentiators(signals, facts)

    output = {
        "company": company_name,
        "signals": signals,
        "audience": result.get("audience", {}),
        "trade": result.get("trade", "hvac"),
        "facts": facts,
        "city": result.get("city", ""),
        "differentiators": differentiators,
    }

    log.info(
        "brand_analyzer.complete",
        company=company_name,
        trade=output["trade"],
        city=output["city"],
        differentiators=len(differentiators),
    )
    return output


def _extract_differentiators(
    signals: dict[str, Any], facts: list[str]
) -> list[str]:
    """Extract concrete differentiators from brand signals and research facts."""
    diffs: list[str] = []

    combined = " ".join(facts) + " " + (signals.get("homepage_content") or "")

    import re

    for pattern, label in [
        (r"(\d+)\s+years?", "years_in_business"),
        (r"licensed\s+and\s+insured", "licensed_insured"),
        (r"(\d+)\s+star", "star_rating"),
        (r"family(?:[- ]?owned| business)", "family_owned"),
        (r"24/7|emergency\s+service", "emergency_service"),
        (r"BBB\s+(?:rated|accredited|A\+?)", "bbb_rated"),
        (r"NATE\s+certified", "nate_certified"),
        (r"EPA\s+(?:608|certified)", "epa_certified"),
    ]:
        if re.search(pattern, combined, re.I):
            diffs.append(label)

    return list(set(diffs))
