"""
Design-quality constants — pinned system-layer context.

These are NEVER modified by the agent at runtime. They are the non-negotiable
contract that every generated site MUST satisfy.

Sources:
  - reliantai-client-sites/lib/design-quality-standards.ts
  - reliableai/agents/quality_standards.py
  - Playbook: 5-Layer System — System Layer < 400 tokens
"""

from __future__ import annotations

# ─── TYPE SYSTEM PINNED RULES ───────────────────────────────────────────────
# These are the output schema rules. Baked into system prompt as constraints.
# Update ONLY when SiteContent schema changes.

SITECONTENT_SCHEMA_SUMMARY = """
  SiteContent = {
    business: { business_name, trade, city, state, phone, email, address,
                google_rating, review_count, website_url, owner_name,
                owner_title, years_in_business, service_area, reviews[] },
    hero:     { headline, subheadline, trust_bar[], cta_primary, cta_primary_url,
                cta_secondary, cta_secondary_url },
    services: [{ icon, title, description, cta_text }],
    about:    { story, trust_points[], certifications[] },
    reviews:  { reviews[], aggregate_line },
    faq:      [{ question, answer }],
    seo:      { title, description, keywords[] },
    aeo_signals: { local_business_type, primary_category, secondary_categories[],
                   area_served[] },
    schema_org:   JSON-LD @graph (Organization, LocalBusiness, WebSite, WebPage),
    site_config:  { template_id, trade, theme: { primary, accent, font_display, font_body } },
    status, slug, meta_title, meta_description, lighthouse_score
  }
  Required fields: business.*, hero.*, services[3-5], about.*, reviews.*,
                   faq[5], seo.*, aeo_signals.*, schema_org, site_config, status, slug
""".strip()

# ─── AWWWARDS QUALITY BAR ────────────────────────────────────────────────────
# Banned patterns — presence of any one is an automatic rejection.
BANNED_AI_PATTERNS = [
    "Inter, Geist, system-ui, or default sans as display type",
    "Indigo-500 (#6366f1) or generic blue-500 (#3b82f6) as primary brand color",
    "Multi-stop gradients (from-X via-Y to-Z) on heroes or sections",
    "Purple-to-blue or blue-to-violet hero gradients",
    "Centered full-viewport hero with vague headline ('Build the future', 'Elevate your X')",
    "Three equal feature cards in a symmetric 3-column grid",
    "backdrop-blur on navbars, cards, or overlays (glassmorphism cliché)",
    "animate-ping dots or pulsing status indicators",
    "Concentric circle / orb decorations with no semantic content",
    "blur-3xl glow blobs as the only visual interest",
    "transition-all duration-300 ease-in-out on every interactive element",
    "Uniform rounded-xl (16px) everywhere",
    "shadow-lg on every card and button",
    "Word-by-word headline reveal animation",
    "min-h-screen (100vh) hero — use min-h-[85vh] with asymmetric layout",
    "Stock-photo placeholders or generic AI imagery",
    "Vague trust badges: 'Quality Service', 'Expert Team'",
    "FAQ as default fifth section with generic questions",
    "Emoji in professional copy or outreach SMS",
    "Exclamation-heavy marketing copy ('Amazing!', 'Best in town!')",
]

AWWWARDS_REQUIREMENTS = [
    "Real specificity in copy: city names, years, license types, review themes",
    "Restrained color palette: 1 primary + 1 accent + neutrals",
]

HTML_AWWWARDS_REQUIREMENTS = [
    "Distinctive typography pairing: serif or editorial display + humanist sans body",
    "Asymmetric layout: grid-cols-[2fr_3fr] or [3fr_5fr], off-center hero",
    "Solid section backgrounds with at most ONE subtle radial accent",
    "Intentional border-radius variation (buttons ≠ cards ≠ panels)",
    "Purposeful motion: cubic-bezier(0.22, 1, 0.36, 1) on state changes only",
    "Editorial typography: tight display tracking, generous body line-height (1.6–1.75)",
    "Visual hierarchy through size/weight contrast — not color alone",
    "One signature layout moment per template",
]

# ─── COPY QUALITY BAR ────────────────────────────────────────────────────────
COPY_NEVER = [
    "Vague headlines: 'Your Trusted Partner', 'Quality You Can Count On'",
    "Empty superlatives: 'best', 'leading', 'premier' without proof",
    "Generic trust bars: 'Expert Team', 'Quality Work', 'Customer Satisfaction'",
    "Robotic FAQ that could apply to any business in any city",
    "Copy without business name, city, or concrete differentiator",
    "More than 1 exclamation mark per page",
    "Emoji, ALL CAPS, or 'Hey there!' openers",
    "Services described identically",
    "Invented reviews sounding like marketing",
    "Subheadlines >2 sentences or <8 words",
]

COPY_ALWAYS = [
    "Headline = business name + city + concrete outcome",
    "Subheadline = specific benefit + proof point (years, rating, response time, license)",
    "Trust bar (3 items): certifications, licenses, guarantees with specifics",
    "Services (3-5): trade-specific, 1-2 sentences each with concrete detail",
    "About: founder name, founding year, one specific moment or philosophy",
    "Trust points: numbers not adjectives",
    "FAQ (5): real homeowner questions, answers cite local context",
    "SEO title ≤60 chars, description ≤155 chars",
    "Voice: confident, direct, warm — like a neighbor who happens to be an expert",
]

# ─── ADAPTIVE RENDERING RULES ────────────────────────────────────────────────
# When to render standalone HTML vs full Next.js ISR site.
HTML_SITE_THRESHOLD = {
    "max_pages": 1,
    "max_interactive_routes": 0,
    "requires_backend": False,
    "requires_auth": False,
}

FULL_ISR_THRESHOLD = {
    "requires_backend": True,
    "requires_auth": True,
    "multi_slug": True,
    "max_pages": None,  # unlimited
}

TRADE_TEMPLATE_MAP = {
    "hvac": "hvac-reliable-blue",
    "plumbing": "plumbing-trustworthy-navy",
    "electrical": "electrical-sharp-gold",
    "roofing": "roofing-bold-copper",
    "painting": "painting-clean-minimal",
    "landscaping": "landscaping-earthy-green",
}

DEFAULT_FALLBACK_TEMPLATE = "hvac-reliable-blue"
