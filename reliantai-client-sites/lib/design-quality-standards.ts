/**
 * ReliantAI client-site design quality standards.
 *
 * Source of truth for anti-AI-slop craft. Derived from:
 *   - docs/design/MASTER-GUIDE-anti-ai-slop-cinematic-websites.md
 *   - https://context-engineering-site.vercel.app (editorial T1 reference)
 *
 * Local-business ISR sites are EXECUTION TIER T1 (editorial motion).
 * Every template, component, and generation prompt MUST comply.
 */

/** Motion easing — never ease-in-out / transition-all as house default */
export const PREMIUM_EASE = [0.22, 1, 0.36, 1] as const;

export const MOTION = {
  duration: { fast: 0.2, base: 0.45, slow: 0.7 },
  ease: PREMIUM_EASE,
} as const;

/** Border-radius hierarchy — intentional variation, never uniform 16px */
export const RADIUS = {
  button: "rounded-md", // 6px
  card: "rounded-lg", // 8px
  panel: "rounded-xl", // 12px — sparingly
  pill: "rounded-full",
} as const;

/**
 * Universal Router — local business / nonprofit playbook.
 * Primary verb: evaluate + buy. Visit: once-to-few. Content: semi-permanent NAP.
 * Tier: T1 editorial (CSS scroll-driven reveals, one accent moment, no pins).
 */
export const EXECUTION_TIER = "T1" as const;

export const TIER_RULES = {
  T0: "Static craft — CSS transitions only; zero scroll choreography",
  T1: "Editorial motion — CSS scroll-driven reveals, one accent moment, no pins/Lenis",
  T2: "Cinematic scroll — Lenis + GSAP pins/scrub (campaign only)",
  T3: "Immersive world — WebGL/video only when content requires it",
} as const;

/**
 * Trade palettes authored in OKLCH (hex fallbacks).
 * NEVER use unmodified Tailwind blue-500 (#3b82f6) or indigo-500 (#6366f1).
 */
export const TRADE_PALETTES = {
  hvac: {
    /** Steel ink — industrial reliability, not Tailwind blue */
    ink: "#0b1220",
    surface: "#121a2b",
    elevated: "#1a2438",
    primary: "#3d5a73",
    accent: "#6b8fa8",
    primaryOklch: "oklch(42% 0.055 240)",
    accentOklch: "oklch(62% 0.055 230)",
    label: "Steel Ink",
  },
  plumbing: {
    ink: "#0a1420",
    surface: "#111c2c",
    elevated: "#1a283c",
    primary: "#1e3a5f",
    accent: "#c45c26",
    primaryOklch: "oklch(32% 0.06 250)",
    accentOklch: "oklch(58% 0.14 45)",
    label: "Ink + Copper",
  },
  electrical: {
    ink: "#0c0a09",
    surface: "#161210",
    elevated: "#221c18",
    primary: "#9a6b1f",
    accent: "#d4a017",
    primaryOklch: "oklch(52% 0.12 75)",
    accentOklch: "oklch(72% 0.14 85)",
    label: "Charcoal Gold",
  },
  roofing: {
    ink: "#140c08",
    surface: "#1c120c",
    elevated: "#2a1a12",
    primary: "#9a4520",
    accent: "#c46a35",
    primaryOklch: "oklch(48% 0.12 45)",
    accentOklch: "oklch(62% 0.13 50)",
    label: "Umber Copper",
  },
  painting: {
    ink: "#1a1614",
    surface: "#f7f4ef",
    elevated: "#ffffff",
    primary: "#8b6914",
    accent: "#a67c2a",
    primaryOklch: "oklch(52% 0.1 85)",
    accentOklch: "oklch(60% 0.1 75)",
    label: "Gallery Ochre",
  },
  landscaping: {
    ink: "#0f1a12",
    surface: "#152018",
    elevated: "#1e2e22",
    primary: "#3d5c3d",
    accent: "#a67c52",
    primaryOklch: "oklch(42% 0.06 145)",
    accentOklch: "oklch(62% 0.08 65)",
    label: "Moss + Clay",
  },
} as const;

export type TradeId = keyof typeof TRADE_PALETTES;

/**
 * Patterns that signal low-effort / AI-generated sites.
 * NEVER use in templates, prompts, or agent output.
 */
export const BANNED_AI_PATTERNS = [
  "Inter, Geist, Roboto, Outfit, or system-ui as the only / display typeface",
  "Indigo-500 (#6366f1) or Tailwind blue-500 (#3b82f6) as primary brand color",
  "Any unmodified Tailwind blue-*/indigo-*/violet-* as the site identity",
  "Multi-stop gradients (from-X via-Y to-Z) on heroes or sections",
  "Purple-to-blue, blue-to-violet, or purple-to-pink hero gradients",
  "Centered full-viewport hero with vague headline ('Build the future', 'Elevate your X')",
  "Three equal feature cards in a symmetric grid-cols-3 with identical height/padding/radius",
  "Lucide Zap / Shield / Rocket stamped as a three-icon feature row",
  "backdrop-blur on navbars, cards, or overlays (glassmorphism cliché)",
  "animate-ping dots or pulsing status indicators",
  "Concentric circle / orb decorations with no semantic content",
  "blur-3xl glow blobs as the only visual interest",
  "transition-all duration-300 ease-in-out on every interactive element",
  "Uniform rounded-xl (16px) on buttons, cards, and inputs",
  "shadow-lg / colored glow shadows on every card and button",
  "Word-by-word headline reveal animation (overused AI motion)",
  "min-h-screen (100vh) hero — use min-h-[85svh] with deliberate composition",
  "Cards, stats, schedules, or trust chips inside the first viewport hero",
  "Stock-photo placeholders or generic AI imagery / plastic 3D blobs",
  "Vague trust badges without specifics ('Quality Service', 'Expert Team')",
  "FAQ as the default fifth section with generic questions",
  "Emoji in professional copy or outreach SMS",
  "Exclamation-heavy marketing copy ('Amazing!', 'Best in town!')",
  "Buzzwords: seamless, cutting-edge, unlock, elevate, robust, best-in-class, leverage, delve, holistic, transformative, empower",
  "AI sentence frame: \"It's not just X — it's Y\"",
  "Em-dash confetti / stock openers ('In today's fast-paced world')",
  "hero → three feature cards → testimonials → pricing → CTA as the unspecified default layout",
] as const;

/**
 * T1 editorial excellence bar for local-business sites.
 * Every template MUST demonstrate at least 5 of these.
 */
export const AWWWARDS_REQUIREMENTS = [
  "Distinctive typography pairing: serif or editorial display + humanist sans body (justified)",
  "Asymmetric layout: grid-cols-[2fr_3fr] / [3fr_5fr] / 12-col poster grid — break centered-div reflex",
  "OKLCH (or custom hex) trade palette — never default Tailwind indigo/blue-500 identity",
  "Solid section backgrounds with at most ONE subtle radial accent — no multi-stop gradients",
  "Intentional border-radius variation (buttons ≠ cards ≠ panels)",
  "Purposeful motion: CSS scroll-driven reveals OR cubic-bezier(0.22, 1, 0.36, 1) — not fade spam",
  "Editorial typography: tight display tracking, generous body line-height (1.6–1.75)",
  "Real specificity in copy: city names, years in business, license types, review themes",
  "Visual hierarchy through size/weight contrast — not color alone",
  "One signature layout moment per template (numbered services, split proof, masonry reviews, etc.)",
  "Brand-first hero: business name is a hero-level signal, not a nav-only label",
  "Hero budget only: brand + one headline + one sentence + CTA group + atmosphere — proof below fold",
  "prefers-reduced-motion static path shipped; animate transform/opacity/clip-path only",
] as const;

/** Hero composition rules (first viewport) */
export const HERO_BUDGET = [
  "Brand / business name at hero scale (font-display)",
  "One specific headline (outcome + city or trade)",
  "One short supporting sentence",
  "One CTA group (primary + optional secondary)",
  "One dominant atmosphere (full-bleed wash, texture, or photo plane) — not inset cards",
] as const;

export const HERO_FORBIDDEN = [
  "Star ratings / review counts",
  "Trust bar chips",
  "Credential / stat cards",
  "Stats strips",
  "Floating badges or promo stickers",
  "FAQ / schedule / address blocks",
] as const;

/** Shared prompt block prepended to every template generation prompt */
export const DESIGN_QUALITY_PROMPT_BLOCK = `
## MANDATORY: Anti-AI-Slop Design Standards (T1 Editorial / Senior Designer Bar)

You are building a local-business site that must look hand-crafted by a senior agency designer —
NOT the statistical average of AI landing pages. Source: Master Guide anti-AI-slop (2026) +
editorial craft reference (context-engineering-site).

### Execution tier
- Surface: local home-service landing → tier T1 (editorial motion)
- Motion: CSS scroll-driven reveals + one accent moment. No Lenis pins, no WebGL, no custom cursors.
- When in doubt, lower the tier and execute it perfectly.

### NEVER include (instant rejection):
${BANNED_AI_PATTERNS.map((p) => `- ${p}`).join("\n")}

### ALWAYS include:
${AWWWARDS_REQUIREMENTS.map((p) => `- ${p}`).join("\n")}

### Hero (first viewport) — brand-first budget
Allowed:
${HERO_BUDGET.map((p) => `- ${p}`).join("\n")}
Forbidden in first viewport:
${HERO_FORBIDDEN.map((p) => `- ${p}`).join("\n")}
Move proof (rating, years, licenses, trust bar) to a section BELOW the fold.

### Typography
- Display: Instrument Serif (editorial, tight tracking on headlines) — justified for local-service warmth
- Body: DM Sans (humanist, 16–18px, line-height 1.65)
- NO Inter, Geist, Roboto, Outfit, or system-ui for display type

### Layout
- Hero: full-bleed atmosphere, brand name at hero scale, asymmetric composition, min-h-[85svh]
- Services: numbered editorial list OR asymmetric 12-col spans — NEVER grid-cols-3 equal cards
- Section rhythm: alternate density (tight proof bar → spacious about → tight FAQ)
- At least one deliberate symmetry break the model would not invent alone

### Color
- Use the trade OKLCH/hex palette ONLY — never Tailwind blue-500 (#3b82f6) / indigo-500 (#6366f1)
- Backgrounds: solid ink / surface / elevated tokens — single radial accent at 4–8% opacity max
- CTAs: solid fill, subtle hover darken — no colored shadow-lg glow

### Motion (T1)
- Prefer CSS \`animation-timeline: view()\` reveals (class \`.reveal\`) inside prefers-reduced-motion: no-preference
- If JS motion: cubic-bezier(0.22, 1, 0.36, 1); opacity + transform only; max 2 animated elements on load
- Never transition-all / ease-in-out as the house default

### Copy (if generating text)
- Headlines: specific + local ("Austin's 15-Year HVAC Team" not "Your Comfort Experts")
- Subheads: one concrete benefit with a number or timeframe
- Ban buzzwords and "It's not just X — it's Y." Minimize em dashes.
- Trust bar (below fold): license numbers, certifications, response times — not adjectives
`.trim();

/** Master studio brief fragment for WebsiteForge / content_forge */
export const MASTER_STUDIO_BRIEF = `
ROLE
You are a senior creative technologist at an Awwwards-level studio. You build local-business
web experiences at tier T1 (editorial). Zero tolerance for 2026 AI-default output.

HARD EXCLUSIONS
- No blue/indigo/purple-pink signature (#3b82f6, #6366f1, from-purple-500 to-pink-500)
- No Inter/Roboto-only type. Instrument Serif + DM Sans, justified.
- No centered generic SaaS hero. Brand name is hero-scale. Headline names a specific outcome.
- No three-equal-card grids. Asymmetric or numbered editorial services required.
- No decorative fade spam. Motion is scroll-tied or interaction-triggered.
- No buzzwords; no "It's not just X — it's Y."; minimize em dashes.

BEFORE CODE
Output section inventory (hero → proof → services → about → reviews → CTA → FAQ → footer)
with hero budget check. Do not invent credentials, reviews, or license numbers.
`.trim();
