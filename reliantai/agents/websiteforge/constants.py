"""
Design-quality constants — pinned system-layer context.

These are NEVER modified by the agent at runtime. They are the non-negotiable
contract that every generated site MUST satisfy.

Sources:
  - docs/design/MASTER-GUIDE-anti-ai-slop-cinematic-websites.md
  - https://context-engineering-site.vercel.app
  - reliantai-client-sites/lib/design-quality-standards.ts
  - reliantai/agents/quality_standards.py
"""

from __future__ import annotations

# ─── TYPE SYSTEM PINNED RULES ───────────────────────────────────────────────
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

# Execution tier for local-business ISR / HTML landings
EXECUTION_TIER = "T1"  # editorial motion — CSS reveals, no pins/WebGL

# Trade palettes — OKLCH-authored hex. NEVER Tailwind blue-500 (#3b82f6) / indigo-500.
TRADE_PALETTES = {
    "hvac": {
        "primary": "#3d5a73",
        "accent": "#6b8fa8",
        "ink": "#0b1220",
        "label": "Steel Ink",
    },
    "plumbing": {
        "primary": "#1e3a5f",
        "accent": "#c45c26",
        "ink": "#0a1420",
        "label": "Ink + Copper",
    },
    "electrical": {
        "primary": "#9a6b1f",
        "accent": "#d4a017",
        "ink": "#0c0a09",
        "label": "Charcoal Gold",
    },
    "roofing": {
        "primary": "#9a4520",
        "accent": "#c46a35",
        "ink": "#140c08",
        "label": "Umber Copper",
    },
    "painting": {
        "primary": "#8b6914",
        "accent": "#a67c2a",
        "ink": "#1a1614",
        "label": "Gallery Ochre",
    },
    "landscaping": {
        "primary": "#3d5c3d",
        "accent": "#a67c52",
        "ink": "#0f1a12",
        "label": "Moss + Clay",
    },
}

# ─── AWWWARDS / ANTI-SLOP BAR ────────────────────────────────────────────────
BANNED_AI_PATTERNS = [
    "Inter, Geist, Roboto, Outfit, or system-ui as the only / display typeface",
    "Indigo-500 (#6366f1) or Tailwind blue-500 (#3b82f6) as primary brand color",
    "Any unmodified Tailwind blue-*/indigo-*/violet-* as the site identity",
    "Multi-stop gradients (from-X via-Y to-Z) on heroes or sections",
    "Purple-to-blue, blue-to-violet, or purple-to-pink hero gradients",
    "Centered full-viewport hero with vague headline ('Build the future', 'Elevate your X')",
    "Three equal feature cards in a symmetric grid-cols-3",
    "Lucide Zap / Shield / Rocket stamped as a three-icon feature row",
    "backdrop-blur on navbars, cards, or overlays (glassmorphism cliché)",
    "animate-ping dots or pulsing status indicators",
    "Concentric circle / orb decorations with no semantic content",
    "blur-3xl glow blobs as the only visual interest",
    "transition-all duration-300 ease-in-out on every interactive element",
    "Uniform rounded-xl (16px) everywhere",
    "shadow-lg / colored glow on every card and button",
    "Word-by-word headline reveal animation",
    "min-h-screen (100vh) hero — use min-h-[85svh] with deliberate composition",
    "Cards, stats, or trust chips inside the first viewport hero",
    "Stock-photo placeholders or generic AI imagery / plastic 3D blobs",
    "Vague trust badges: 'Quality Service', 'Expert Team'",
    "FAQ as default fifth section with generic questions",
    "Emoji in professional copy or outreach SMS",
    "Exclamation-heavy marketing copy ('Amazing!', 'Best in town!')",
    "Buzzwords: seamless, cutting-edge, unlock, elevate, robust, best-in-class, leverage, delve, holistic, transformative, empower",
    "AI sentence frame: \"It's not just X — it's Y\"",
    "Em-dash confetti / stock openers ('In today's fast-paced world')",
]

AWWWARDS_REQUIREMENTS = [
    "Real specificity in copy: city names, years, license types, review themes",
    "Restrained color palette: 1 primary + 1 accent + neutrals from TRADE_PALETTES",
    "Brand-first hero: business name is a hero-level signal",
    "Hero budget: brand + headline + one sentence + CTAs + atmosphere; proof below fold",
]

HTML_AWWWARDS_REQUIREMENTS = [
    "Distinctive typography pairing: serif or editorial display + humanist sans body",
    "Asymmetric layout: grid-cols-[2fr_3fr] / [3fr_5fr] / 12-col poster — not centered equal cards",
    "Solid section backgrounds with at most ONE subtle radial accent",
    "Intentional border-radius variation (buttons ≠ cards ≠ panels)",
    "Purposeful motion: cubic-bezier(0.22, 1, 0.36, 1) or CSS scroll-driven reveals",
    "Editorial typography: tight display tracking, generous body line-height (1.6–1.75)",
    "Visual hierarchy through size/weight contrast — not color alone",
    "One signature layout moment per template (numbered services, copper rule, etc.)",
    "OKLCH/custom hex trade palette — never default Tailwind indigo/blue-500",
    "prefers-reduced-motion static path; animate transform/opacity only",
]

# ─── COPY QUALITY BAR ────────────────────────────────────────────────────────
COPY_NEVER = [
    "Vague headlines: 'Your Trusted Partner', 'Quality You Can Count On', 'Elevate Your X'",
    "Empty superlatives: 'best', 'leading', 'premier' without proof",
    "Generic trust bars: 'Expert Team', 'Quality Work', 'Customer Satisfaction'",
    "Buzzwords: seamless, cutting-edge, unlock, elevate, robust, best-in-class, leverage, delve, holistic, transformative, empower",
    "AI frame: \"It's not just X — it's Y\"",
    "Em-dash confetti / 'In today's fast-paced world'",
    "Robotic FAQ that could apply to any business in any city",
    "Copy without business name, city, or concrete differentiator",
    "More than 1 exclamation mark per page",
    "Emoji, ALL CAPS, or 'Hey there!' openers",
    "Services described identically",
    "Invented reviews sounding like marketing",
    "Subheadlines >2 sentences or <8 words",
]

COPY_ALWAYS = [
    "Brand-first: business name is the primary identity; headline = city + concrete outcome",
    "Subheadline = specific benefit + proof point (years, rating, response time, license)",
    "Trust bar (3 items, below fold): certifications, licenses, guarantees with specifics",
    "Services (3-5): trade-specific, 1-2 sentences each with concrete detail",
    "About: founder name, founding year, one specific moment or philosophy",
    "Trust points: numbers not adjectives",
    "FAQ (5): real homeowner questions, answers cite local context",
    "SEO title ≤60 chars, description ≤155 chars",
    "Voice: confident, direct, warm — like a neighbor who happens to be an expert",
    "Minimize em dashes; prefer periods, commas, colons, parentheses",
]

# ─── ADAPTIVE RENDERING RULES ────────────────────────────────────────────────
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
    "max_pages": None,
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
