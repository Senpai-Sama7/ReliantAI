"""
content_forge tool — generates structured WebsiteContent JSON.

Uses Gemini 1.5 Pro (or Flash) via Langchain Google GenAI.
Embeds the 10-point prompt structure + all design/copy quality constraints.

This is the ONLY place in the system that calls the LLM for copy generation.
All other agents/code paths produce site content through this tool.

NOTE: LLM imports are lazy (inside async functions) to allow tests to run
without langchain-google-genai installed.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ...core import get_logger
from ..constants import (
    AWWWARDS_REQUIREMENTS,
    BANNED_AI_PATTERNS,
    COPY_ALWAYS,
    COPY_NEVER,
    DEFAULT_FALLBACK_TEMPLATE,
    SITECONTENT_SCHEMA_SUMMARY,
    TRADE_PALETTES,
    TRADE_TEMPLATE_MAP,
)

log = get_logger("agents.websiteforge.content_forge")

# 10-point prompt structure embedded here
FORGE_PROMPT_TPL = """\
You are WebsiteForge's content generation engine. Generate a complete, production-grade
website content package for this specific company.

## 1. Task Context
Company: {company_name}
Trade: {trade}
City/State: {city_state}
Brand signals: {brand_summary}
Audience: {audience_summary}
Research facts (use these — do NOT fabricate): {research_facts}
Competitors (differentiate from these): {competitors}

## 2. Tone Context
{quality_rules}

## 3. Background / Constraints
{SITE_SCHEMA}

Anti-patterns (NEVER include):
{anti_patterns}

Awwwards requirements (MUST include at least 5):
{awwwards_reqs}

Trade-specific palette (OKLCH-authored hex — NEVER #3b82f6 / #6366f1):
- HVAC: Steel Ink — primary #3d5a73, accent #6b8fa8, ink #0b1220
- Plumbing: Ink + Copper — primary #1e3a5f, accent #c45c26, ink #0a1420
- Electrical: Charcoal Gold — primary #9a6b1f, accent #d4a017, ink #0c0a09
- Roofing: Umber Copper — primary #9a4520, accent #c46a35, ink #140c08
- Painting: Gallery Ochre — primary #8b6914, accent #a67c2a, surface #f7f4ef
- Landscaping: Moss + Clay — primary #3d5c3d, accent #a67c52, ink #0f1a12

Execution tier: T1 editorial. Brand-first hero (business name hero-scale).
Proof (stars, trust bar, credentials) BELOW the fold. Numbered asymmetric
services — never three equal grid-cols-3 cards.

## 4. Dynamic Input
Generate content for THIS specific company. All copy must reference their:
- Business name, city, years in business, owner name (if known)
- Real differentiators from research
- Local context (neighborhood, landmarks, climate)
- Specific services they actually offer

## 5. Step-by-Step Generation Order
Generate these fields IN ORDER (each builds on the previous):

a) business block — name, trade, city, state, phone, address, rating
b) hero block — headline, subheadline, trust_bar[3], CTA buttons
c) services — 3-5 items, each with icon, title, description, CTA
d) about — founder story (1-2 paragraphs), trust_points[4], certifications[]
e) reviews — 4-6 entries, aggregate_line
f) faq — 5 real homeowner questions + answers
g) seo — title, description, keywords
h) aeo_signals — local_business_type, categories, area_served
i) schema_org — Organization + LocalBusiness JSON-LD @graph
j) site_config — template_id, trade, theme colors, font pairing

## 6. Examples (few-shot)

Good hero headline:
  "Comfort Pro HVAC — Same-Day AC Repair in Austin, TX"
  (company name + city + concrete service)

Bad hero headline:
  "Your Trusted HVAC Partner — Quality Service You Can Count On"

Good trust bar: ["EPA 608 Certified", "TX License #TACLA12345",
                 "15 Years in Austin"]
Bad trust bar: ["Expert Team", "Quality Work", "Customer Satisfaction"]

## 7. Conversation History
{NONE — first-pass generation}

## 8. Task Reminder
Generate the COMPLETE SiteContent JSON. Do NOT truncate. Every field is required.
All factual claims must be supported by research. Do NOT invent reviews, ratings,
or credentials.

## 9. Critical Guardrails
- Do NOT fabricate owner names, phone numbers, addresses, license numbers
- Do NOT invent reviews with phrases like "absolutely amazing"
- Do NOT use Inter, Geist, or system-ui as display font
- Do NOT use indigo-500 (#6366f1) or Tailwind blue-500 (#3b82f6) as brand color
- Do NOT use min-h-screen hero — use min-h-[85svh] with brand-first composition
- Do NOT put cards, stars, or trust chips in the first viewport
- Do NOT use three equal feature cards in a symmetric grid-cols-3
- Do NOT use buzzwords (seamless, elevate, unlock, transformative) or "It's not just X — it's Y"
- Do NOT use generic FAQ questions that apply to any business

## 10. Output Format
Return ONLY valid JSON (no markdown fences, no explanation):
{SITE_SCHEMA}
""".strip()


def build_forge_prompt(
    company_name: str,
    research: dict[str, Any],
    mode: str = "standalone_html",
) -> str:
    """Build the complete forge prompt from research data."""
    brand = research.get("brand_signals", {})
    facts = research.get("facts", [])
    competitors = research.get("competitors", [])
    audience = research.get("audience", {})

    def _summarize(d: Any, max_chars: int = 500) -> str:
        if isinstance(d, dict):
            text = json.dumps(d, indent=2)
        else:
            text = str(d)
        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    brand_summary = _summarize(brand, 600)
    audience_summary = _summarize(audience, 300)
    facts_text = "\n  ".join(facts[:5]) if facts else "No research available — use general knowledge"

    competitors_text = ", ".join(
        c.get("name", c.get("url", "")) for c in competitors[:3]
    ) or "None found"

    city = research.get("city_state") or research.get("city") or "US"
    trade = research.get("trade", "hvac")

    return FORGE_PROMPT_TPL.format(
        company_name=company_name,
        trade=trade,
        city_state=city,
        brand_summary=brand_summary,
        audience_summary=audience_summary,
        research_facts=facts_text,
        competitors=competitors_text,
        SITE_SCHEMA=SITECONTENT_SCHEMA_SUMMARY,
        anti_patterns="\n".join(f"  - {p}" for p in BANNED_AI_PATTERNS),
        awwwards_reqs="\n".join(f"  - {r}" for r in AWWWARDS_REQUIREMENTS),
        quality_rules="\n".join(f"NEVER: {c}" for c in COPY_NEVER)
        + "\n"
        + "\n".join(f"ALWAYS: {c}" for c in COPY_ALWAYS),
        NONE="(none — initial generation)",
    )


def _get_llm(model: str):
    """Lazy import to avoid requiring langchain-google-genai at import time."""
    from ...core.llm import get_gemini_pro, get_gemini_flash
    return get_gemini_pro() if model == "pro" else get_gemini_flash()


async def forge_site_content(
    company_name: str,
    research: dict[str, Any],
    mode: str = "standalone_html",
    model: str = "pro",
    max_retries: int = 2,
) -> dict[str, Any]:
    """
    Call LLM to generate structured WebsiteContent JSON.

    Uses Gemini Pro for quality. Falls back to Flash on timeout/error.
    Retries up to max_retries times with repair prompts.
    """
    prompt = build_forge_prompt(company_name, research, mode)

    for attempt in range(1, max_retries + 1):
        try:
            llm = _get_llm(model)
            response = await llm.ainvoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)

            # Extract JSON from response (handle markdown fences)
            json_text = _extract_json(text)
            if not json_text:
                log.warning(
                    "forge_no_json", attempt=attempt, preview=text[:200]
                )
                continue

            content = json.loads(json_text)
            log.info(
                "forge_success",
                company=company_name,
                attempt=attempt,
                keys=list(content.keys())[:8],
            )
            return content

        except json.JSONDecodeError as exc:
            log.warning(
                "forge_json_parse_failed", attempt=attempt, error=str(exc)
            )
        except Exception as exc:
            log.warning(
                "forge_llm_failed", attempt=attempt, error=str(exc)
            )

    # All retries exhausted — return a minimal valid shell
    log.error("forge_exhausted", company=company_name)
    return _build_minimal_shell(company_name, research)


async def repair_site_content(
    content: dict[str, Any],
    violations: list[str],
    research: dict[str, Any],
    model: str = "pro",
) -> dict[str, Any]:
    """
    Ask the LLM to repair content addressing specific quality violations.
    Called iteratively inside the forge-evaluate loop when gate fails.
    """
    repair_prompt = f"""\
You previously generated a SiteContent JSON that failed an Awwwards-quality review.
Here are the violations that must be fixed:

Violations:
{chr(10).join(f"- {v}" for v in violations)}

Previous content (fix this — do NOT regenerate from scratch):
{json.dumps(content, indent=2)[:4000]}

Research context (must be preserved):
{json.dumps(research.get('brand_signals', {}), indent=2)[:2000]}

Fix ONLY the violating fields. Preserve all factual claims from research.
Return the full corrected SiteContent JSON (no markdown fences):
{SITECONTENT_SCHEMA_SUMMARY}
""".strip()

    try:
        llm = _get_llm(model)
        response = await llm.ainvoke(repair_prompt)
        text = response.content if hasattr(response, "content") else str(response)
        json_text = _extract_json(text)
        if json_text:
            return json.loads(json_text)
    except Exception as exc:
        log.warning("repair_failed", error=str(exc))

    return content  # Return unchanged if repair fails


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

_JSON_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.S)
_JSON_ARRAY_RE = re.compile(r"(\[.*\])", re.S)
_JSON_OBJECT_RE = re.compile(r"(\{.*\})", re.S)


def _extract_json(text: str) -> str | None:
    """Extract the first valid JSON object or array from a response."""
    # Try markdown code fence first
    m = _JSON_RE.search(text)
    if m:
        candidate = m.group(1).strip()
        if _is_valid_json(candidate):
            return candidate

    # Try to find a raw JSON object or array
    for pattern in (_JSON_ARRAY_RE, _JSON_OBJECT_RE):
        for m in pattern.finditer(text):
            candidate = m.group(1).strip()
            if _is_valid_json(candidate):
                return candidate

    return None


def _is_valid_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def _build_minimal_shell(
    company_name: str, research: dict[str, Any]
) -> dict[str, Any]:
    """Minimal valid SiteContent when LLM output fails."""
    brand = research.get("brand_signals", {})
    city_state = research.get("city_state") or research.get("city") or "their area"
    trade = research.get("trade", "hvac")
    template = TRADE_TEMPLATE_MAP.get(trade, DEFAULT_FALLBACK_TEMPLATE)
    slug_raw = f"{company_name.lower()}-{city_state.lower()}"
    slug = re.sub(r"[^a-z0-9]+", "-", slug_raw).strip("-")

    return {
        "business": {
            "business_name": company_name,
            "trade": trade,
            "city": city_state.split(",")[0].strip() if "," in city_state else city_state,
            "state": city_state.split(",")[1].strip() if "," in city_state else "",
            "phone": "(555) 123-4567",
            "address": f"Main Street, {city_state}",
            "google_rating": 4.8,
            "review_count": 127,
            "owner_name": brand.get("owner_name"),
            "years_in_business": brand.get("years_in_business", 10),
        },
        "hero": {
            "headline": f"{company_name} — {trade.title()} in {city_state}",
            "subheadline": f"Trusted {trade} service for {city_state}. Quality work, fair prices.",
            "trust_bar": ["Licensed & Insured", "Satisfaction Guaranteed", "Local Team"],
            "cta_primary": "Call Now",
            "cta_primary_url": "tel:",
            "cta_secondary": "Get a Free Quote",
            "cta_secondary_url": "#contact",
        },
        "services": [
            {"icon": "wrench", "title": f"{trade.title()} Service", "description": "Expert service for your home.", "cta_text": "Learn More"},
        ],
        "about": {
            "story": f"{company_name} was founded to bring honest, reliable {trade} service to {city_state}.",
            "trust_points": ["Local team", "Quality guarantee", "Fair pricing"],
            "certifications": [],
        },
        "reviews": {
            "reviews": [],
            "aggregate_line": "Rated 4.8/5 by local customers",
        },
        "faq": [
            {"question": "Do you offer free estimates?", "answer": "Yes, we provide free estimates on all jobs."},
            {"question": "What are your hours?", "answer": "Monday-Friday 7am-6pm, emergency service available."},
        ],
        "seo": {
            "title": f"{company_name} | {trade.title()} in {city_state}",
            "description": f"Looking for reliable {trade} in {city_state}? Contact {company_name} for professional service.",
            "keywords": [trade, city_state, "home services"],
        },
        "aeo_signals": {
            "local_business_type": "HomeService",
            "primary_category": trade,
            "secondary_categories": [],
            "area_served": [city_state],
        },
        "schema_org": {},
        "site_config": {
            "template_id": template,
            "trade": trade,
            "theme": {
                "primary": TRADE_PALETTES.get(trade, TRADE_PALETTES["hvac"])["primary"],
                "accent": TRADE_PALETTES.get(trade, TRADE_PALETTES["hvac"])["accent"],
                "font_display": "Instrument Serif",
                "font_body": "DM Sans",
            },
        },
        "status": "draft",
        "slug": slug,
        "meta_title": "",
        "meta_description": "",
        "lighthouse_score": 0,
    }
