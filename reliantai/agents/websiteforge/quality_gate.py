"""
Quality gate — ACE Reflector for WebsiteForge.

Evaluates generated SiteContent against the Awwwards bar + anti-AI-slop rules.
Returns a score (0.0-1.0) + list of violations.

Per Playbook ACE Framework: Generator → Reflector → Curator.
This IS the Reflector. Checks output against success criterion
(gate_score >= 0.85, zero banned patterns) and returns structured feedback.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .constants import AWWWARDS_REQUIREMENTS, HTML_AWWWARDS_REQUIREMENTS, BANNED_AI_PATTERNS, COPY_NEVER, COPY_ALWAYS
from ..core import get_logger

log = get_logger("agents.websiteforge.quality_gate")

# Patterns that signal obvious AI-slop in generated text
_TEXT_PATTERNS = {
    "emoji_in_copy": re.compile(r"[\U0001F300-\U0001F9FF\u2600-\u27BF]", re.S),
    "multiple_exclamations": re.compile(r"!!+"),
    "inter_display_font": re.compile(
        r"\b(?:Inter|Geist|Outfit|system-ui|Arial|Helvetica)\b", re.S
    ),
    "indigo_500": re.compile(r"#6366f1|indigo-?500|\bIndigo\b", re.I),
    "blue_500": re.compile(r"#3b82f6|blue-?500", re.I),
    "gradient_hero": re.compile(
        r"from-(?:indigo|blue|purple|violet|slate)-(?:50|100|200).*?to-", re.S
    ),
    "backdrop_blur": re.compile(r"backdrop-blur|backdropFilter.*blur", re.I),
    "animate_ping": re.compile(r"animate-ping|animatePing", re.I),
    "blur_3xl_glow": re.compile(r"blur-3xl", re.I),
    "min_h_screen": re.compile(r"min-h-screen|min-height:\s*100vh", re.I),
    "three_equal_cards": re.compile(r"grid-cols-3", re.I),
    "generic_headlines": re.compile(
        r"\b(?:Your Trusted Partner|Quality You Can Count On|Excellence in Service|"
        r"Build the Future|Elevate Your|We Are|Your Premier)\b",
        re.I,
    ),
    "vague_trust": re.compile(
        r"\b(?:Expert Team|Quality Work|Customer Satisfaction|Best in Town)\b", re.I
    ),
    "buzzwords": re.compile(
        r"\b(?:seamless|cutting-edge|unlock|elevate|robust|best-in-class|leverage|"
        r"delve|holistic|transformative|empower)\b",
        re.I,
    ),
    "ai_not_just_frame": re.compile(
        r"it'?s not just\b.{0,40}\bit'?s\b",
        re.I,
    ),
    "stock_opener": re.compile(
        r"in today'?s (?:fast-paced|digital|modern) world|a rich tapestry of",
        re.I,
    ),
    "all_caps": re.compile(r"\b[A-Z]{6,}\b(?!\s*(?:HVAC|LLC|INC|CORP|LTD|CO\.)\b)"),
    "ai_imagery": re.compile(
        r"(?:placeholder|placeholder\.com|via\.placeholder|unsplash\.it)", re.I
    ),
    "word_by_word_anim": re.compile(r"staggerChildren.*1", re.S),
}

_COPY_PATTERNS = {
    "empty_superlative": re.compile(
        r"\b(?:best|leading|premier|top-rated)\b(?!\s+(?:in|for|rated|price|value|quality))",
        re.I,
    ),
    "robotic_faq": re.compile(r"\b(?:Q:|Question:)\s*\d+", re.I),
    "business_name_missing": re.compile(
        r"\b(?:your business|your company)\b", re.I
    ),
}

_REQUIREMENT_PATTERNS = {
    "asymmetric_layout": re.compile(r"grid-cols-\[2?fr.*?3?fr\]|grid-cols-\[3?fr.*?5?fr\]", re.S),
    "typography_variety": re.compile(
        r"(?:Instrument Serif|Playfair Display|DM Serif|Cormorant|Fraunces)", re.I
    ),
    "humanist_sans": re.compile(
        r"(?:DM Sans|Plus Jakarta|Manrope|Space Grotesk|General Sans)", re.I
    ),
    "radius_variation": re.compile(
        r"(?:rounded-sm|rounded-md|rounded-lg|rounded-xl)", re.S
    ),
    "premium_ease": re.compile(
        r"cubic-bezier\(0\.22,\s*1,\s*0\.36,\s*1\)", re.S
    ),
    "line_height": re.compile(r"leading-(?:relaxed|6|7)|line-height:\s*(?:1\.6|1\.65|1\.7)", re.S),
    "solid_bg": re.compile(
        r"bg-(?:white|slate-50|stone-50|gray-50|zinc-50|neutral-50|#f[fa][fa]|#fff)",
        re.S,
    ),
}


async def quality_gate_check(site_content: dict[str, Any]) -> dict[str, Any]:
    """
    Score content against the Awwwards bar.
    Returns: {score: float, violations: list[str], passed: bool, details: dict}
    """
    violations: list[str] = []
    details: dict[str, Any] = {}
    score = 1.0

    # ── Text extraction for scanning ─────────────────────────────────────
    all_text = _extract_all_text(site_content)
    hero_html = json.dumps(site_content.get("hero", {}))
    services_json = json.dumps(site_content.get("services", []))
    about_json = json.dumps(site_content.get("about", {}))
    faq_json = json.dumps(site_content.get("faq", []))
    all_json = json.dumps(site_content)

    # Build scoped texts for pattern matching (exclude reviews to avoid false
    # positives like "best HVAC" from customer reviews or "quality work")
    copy_check_text = " ".join([
        site_content.get("business", {}).get("business_name", ""),
        site_content.get("business", {}).get("city", ""),
        site_content.get("hero", {}).get("headline", ""),
        site_content.get("hero", {}).get("subheadline", ""),
        " ".join(site_content.get("hero", {}).get("trust_bar", [])),
        site_content.get("about", {}).get("story", ""),
        " ".join(site_content.get("about", {}).get("trust_points", [])),
        json.dumps(site_content.get("services", [])),
    ])
    copy_check_text += " " + hero_html + " " + services_json + " " + about_json + " " + faq_json

    # ── BANNED AI PATTERNS (hard rejection)
    # Design anti-patterns (Inter font, indigo color, min-h-screen, etc.) are in
    # site_config / CSS — check via full JSON which carries all structure.
    # Text anti-patterns (emoji, exclamations, generic headlines) are checked
    # on copy-only text to avoid false positives in customer reviews.
    design_check_json = all_json.replace(json.dumps(site_content.get("reviews", {})), "")
    text_only = copy_check_text

    for pattern_name, pattern in _TEXT_PATTERNS.items():
        if pattern.search(design_check_json) or pattern.search(text_only):
            violations.append(f"BANNED pattern found: {pattern_name}")
            score -= 0.15

    # ── COPY PATTERNS (hero/about/services only, never reviews/faq answers) ──
    for pattern_name, pattern in _COPY_PATTERNS.items():
        if pattern.search(copy_check_text):
            violations.append(f"COPY violation: {pattern_name}")
            score -= 0.08

    # ── COPY NEVER checks ────────────────────────────────────────────────
    has_name = bool(site_content.get("business", {}).get("business_name"))
    if not has_name:
        violations.append("COPY_NEVER: Missing business name")

    city = site_content.get("business", {}).get("city", "")
    headline = site_content.get("hero", {}).get("headline", "")
    if city and city.lower() not in headline.lower():
        violations.append("COPY_ALWAYS: Headline must include city")
        score -= 0.05

    # ── AWWWARDS REQUIREMENTS (content-detectable, small penalty) ────────
    content_hits = 0
    content_total = len(AWWWARDS_REQUIREMENTS)
    for req in AWWWARDS_REQUIREMENTS:
        if _check_requirement(req, hero_html, services_json, about_json, all_json):
            content_hits += 1
        else:
            score -= 0.02

    score = max(0.0, min(1.0, score))

    details = {
        "awwwards_content_hits": content_hits,
        "awwwards_content_total": content_total,
        "all_text_length": len(all_text),
        "hero_present": bool(site_content.get("hero", {}).get("headline")),
        "services_count": len(site_content.get("services", [])),
        "faq_count": len(site_content.get("faq", [])),
        "reviews_count": len(site_content.get("reviews", {}).get("reviews", [])),
        "schema_present": bool(site_content.get("schema_org")),
    }

    passed = score >= 0.85 and not any(
        v.startswith("BANNED") for v in violations
    )

    log.info(
        "quality_gate",
        score=round(score, 3),
        passed=passed,
        violations=len(violations),
        req_hits=content_hits,
        details=details,
    )

    return {
        "score": round(score, 3),
        "violations": violations,
        "passed": passed,
        "details": details,
    }



# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _extract_all_text(content: dict[str, Any]) -> str:
    """Flatten SiteContent into a single string for pattern matching."""
    parts: list[str] = []
    parts.append(content.get("business", {}).get("business_name", ""))
    parts.append(content.get("business", {}).get("city", ""))
    parts.append(content.get("hero", {}).get("headline", ""))
    parts.append(content.get("hero", {}).get("subheadline", ""))
    parts.extend(content.get("hero", {}).get("trust_bar", []))
    parts.append(content.get("about", {}).get("story", ""))
    parts.extend(content.get("about", {}).get("trust_points", []))
    for svc in content.get("services", []):
        parts.append(svc.get("title", ""))
        parts.append(svc.get("description", ""))
    for item in content.get("faq", []):
        parts.append(item.get("question", ""))
        parts.append(item.get("answer", ""))
    for review in content.get("reviews", {}).get("reviews", []):
        parts.append(review.get("text", ""))
    return " ".join(parts)


def _check_requirement(req: str, hero: str, services: str, about: str, all_json: str) -> bool:
    """Check if one Awwwards requirement is met in the output."""
    req_lower = req.lower()

    if "asymmetric layout" in req_lower:
        return bool(_REQUIREMENT_PATTERNS["asymmetric_layout"].search(hero))
    if "distinctive typography" in req_lower:
        return bool(
            _REQUIREMENT_PATTERNS["typography_variety"].search(all_json)
        )
    if "solid section backgrounds" in req_lower:
        return bool(_REQUIREMENT_PATTERNS["solid_bg"].search(services))
    if "border-radius variation" in req_lower:
        return bool(_REQUIREMENT_PATTERNS["radius_variation"].search(all_json))
    if "purposeful motion" in req_lower or "cubic-bezier" in req_lower:
        return bool(_REQUIREMENT_PATTERNS["premium_ease"].search(all_json))
    if "editorial typography" in req_lower:
        return bool(_REQUIREMENT_PATTERNS["line_height"].search(all_json))
    if "real specificity" in req_lower:
        return any(
            word in all_json for word in ["years", "license", "certified", "established"]
        )
    if "visual hierarchy" in req_lower:
        return "text-" in all_json or "font-" in all_json
    if "signature layout moment" in req_lower:
        return any(
            term in all_json for term in ["offset", "masonry", "bento", "split-screen"]
        )
    if "restrained color palette" in req_lower:
        # Check for NOT having rainbow / multi-color usage
        return not bool(re.search(r"(red|green|blue|yellow|purple|orange)-[4-9]00", all_json))
    return True  # Unknown requirement — pass by default
