import { DESIGN_QUALITY_PROMPT_BLOCK } from "./design-quality-standards";

export interface TemplateMeta {
  id: string;
  label: string;
  trade: string;
  tradeLabel: string;
  accent: string;
  accentBg: string;
  theme: "dark" | "light";
  heroLayout: "single" | "dual-card" | "dual-decor";
  primaryColor: string;
  colorName: string;
  description: string;
  personality: string;
  bestFor: string;
  uniqueFeatures: string[];
  prompt: string;
}

export const TEMPLATE_DEFINITIONS: TemplateMeta[] = [
  {
    id: "hvac-reliable-blue",
    label: "Reliable Blue",
    trade: "hvac",
    tradeLabel: "HVAC",
    accent: "blue-400",
    accentBg: "bg-blue-500",
    theme: "dark",
    heroLayout: "single",
    primaryColor: "#2563eb",
    colorName: "Blue",
    description: "Editorial, trust-forward HVAC template. Asymmetric hero, masonry reviews, sentence-split About — senior-agency craft.",
    personality: "Dependable & Authoritative",
    bestFor: "HVAC, general contracting, any trade where trust and professionalism are paramount",
    uniqueFeatures: [
      "Asymmetric 2-column hero (grid-cols-[2fr_3fr]) with editorial Instrument Serif headline",
      "Editorial narrative About section (sentence-split storytelling)",
      "Masonry review layout with serif quote watermarks",
      "Varied service card hierarchy — featured spans wider, not three identical cards",
      "Single radial accent on solid slate-950 — no multi-stop gradients",
    ],
    prompt: `Create a trade service landing page for an HVAC company called "{business_name}" in {city}, {state}. Use the "hvac-reliable-blue" template design system:

## Color System
- Primary: blue-700 (CTAs), blue-500 (icons, accents) — NOT default blue-500/indigo
- Backgrounds: solid slate-950 (Hero, About, FAQ, Footer), slate-900 (Services, Reviews)
- Cards: slate-800/60 with slate-700/60 borders
- Text: white (primary), slate-400 (secondary), slate-500 (muted)
- Accent: ONE radial ellipse at 6% opacity max — no multi-stop gradients

## Layout
1. ContactBar (fixed top, h-10, solid bg-slate-950 border-b border-slate-800/60 — NO backdrop-blur)
2. TrustBanner (trade badges)
3. Hero (min-h-[85vh], asymmetric lg:grid-cols-[2fr_3fr], left-aligned copy, right column = credential stack)
4. StatsBar (accent="blue-400")
5. SectionDivider (variant="dots")
6. Services (asymmetric grid — one featured card span-2, varied card heights — NOT 3 equal columns)
7. CTASection (color="blue", variant="urgency")
8. About section (max-w-3xl editorial story with sentence-split narrative, trust box with blue left accent bar)
9. SectionDivider (variant="line")
10. Reviews (masonry columns-1 md:columns-2 lg:columns-3, serif quote marks)
11. CTASection (color="blue", variant="estimate")
12. SectionDivider (variant="wave")
13. FAQ (max-w-3xl, accordion)
14. Footer (4-col grid)

## Hero Details
- Background: solid bg-slate-950 + single radial accent at 60% 40%
- NO word-reveal animation — single fade-up block for headline
- Primary CTA: bg-blue-700 rounded-md (6px) — NO shadow-lg glow
- Secondary CTA: border border-blue-500/30 rounded-md
- Trust bar: license-specific items with Shield icons
- Right column: offset credential card (years + rating) — NOT decorative circles

## Service Cards
- bg-slate-800/60 border-slate-700/60 rounded-lg
- Hover: border-color only — NO -translate-y lift on every card
- Icon container: w-11 h-11 bg-blue-500/10 rounded-md
- Featured card: spans 2 cols on lg, taller padding

## Typography
- Display: Instrument Serif, font-bold, tracking-tight
- Body: DM Sans, text-base leading-relaxed (1.65)
- Hero: text-4xl sm:text-5xl lg:text-6xl
- Section headings: text-3xl sm:text-4xl`,
  },
  {
    id: "plumbing-trustworthy-navy",
    label: "Trustworthy Navy",
    trade: "plumbing",
    tradeLabel: "Plumbing",
    accent: "blue-400",
    accentBg: "bg-blue-700",
    theme: "dark",
    heroLayout: "single",
    primaryColor: "#1d4ed8",
    colorName: "Navy",
    description: "Emergency-focused with a static red alert badge. Featured service card hierarchy and featured-review split layout — urgency without AI-slop motion.",
    personality: "Urgent & Trustworthy",
    bestFor: "Plumbing, emergency services, 24/7 availability trades",
    uniqueFeatures: [
      "Static red emergency pill badge — solid indicator, no animate-ping",
      "Featured service card (index 0) with editorial hierarchy — solid navy accent, not gradient",
      "Featured review split layout (first review full-width, rest in 2-col grid)",
      "Dynamic cert-icon mapping (CERT_ICONS lookup by keyword)",
      "Asymmetric hero lg:grid-cols-[2fr_3fr] with left-aligned copy",
    ],
    prompt: `Create a trade service landing page for a plumbing company called "{business_name}" in {city}, {state}. Use the "plumbing-trustworthy-navy" template design system:

## Color System
- Primary: blue-700 (CTAs), blue-500 (icons, accents) — NOT default blue-500 as CTA fill
- Emergency accent: red-500/10 bg, red-500/20 border, red-300 text (static badge only)
- Backgrounds: solid slate-950 (Hero, About, FAQ, Footer), slate-900 (Services, Reviews)
- Cards: slate-800/60 with slate-700/60 borders; featured: solid bg-blue-950/40 border-blue-500/30
- Text: white (primary), slate-400 (secondary), slate-500 (muted)
- Accent: ONE radial ellipse at 6% opacity max — no multi-stop gradients, no blur-3xl

## Layout
1. ContactBar (fixed top, h-10, solid bg-slate-950 border-b border-slate-800/60 — NO backdrop-blur; "24/7 Emergency Plumbing")
2. TrustBanner (trade badges — license/response-time specifics)
3. Hero (min-h-[85vh], asymmetric lg:grid-cols-[2fr_3fr], left-aligned copy, right column = emergency credential stack)
4. StatsBar (accent="blue-400")
5. SectionDivider (variant="dots")
6. Services (asymmetric grid — index 0 featured with "Most Requested" badge, varied card heights — NOT 3 equal columns)
7. CTASection (color="blue", variant="urgency")
8. About section (max-w-2xl editorial story, trust box with blue left accent bar border-l-2 border-blue-500/40)
9. Reviews (featured first review full-width with serif quote watermark, remaining in grid-cols-1 md:grid-cols-2)
10. FAQ (HelpCircle icon above heading, max-w-3xl accordion)
11. Footer (4-col grid, website URL link)

## Hero Details
- Background: solid bg-slate-950 + single radial accent at 60% 40%
- Static emergency pill above stars: bg-red-500/10 border-red-500/20 rounded-full, AlertTriangle + "24/7 EMERGENCY", solid red-400 status dot (NO animate-ping)
- NO word-reveal animation — single fade-up block for headline
- Primary CTA: bg-blue-700 rounded-md (6px) — NO shadow-lg glow
- Secondary CTA: border border-blue-500/30 rounded-md
- Right column: offset credential card (response time + rating) — NOT decorative circles

## Service Cards
- bg-slate-800/60 border-slate-700/60 rounded-lg
- Featured (index 0): solid bg-blue-950/40 border-blue-500/30, larger icon w-14 h-14, "Most Requested" badge text-[0.65rem] tracking-widest uppercase
- Hover: border-color only — NO -translate-y lift on every card
- Icon container (regular): w-11 h-11 bg-blue-500/10 rounded-md

## Dynamic Cert Icons
- CERT_ICONS map: { licensed: ShieldCheck, master: Award, certified: BadgeCheck, insured: Shield, bonded: Shield, background: UserCheck, epa: Leaf, nec: Zap }

## Typography
- Display: Instrument Serif, font-bold, tracking-tight
- Body: DM Sans, text-base leading-relaxed (1.65)
- Hero: text-4xl sm:text-5xl lg:text-6xl
- Section headings: text-3xl sm:text-4xl

## Local Copy Guidance
- Headlines: city + emergency specificity ("{city}'s 24/7 Drain & Leak Team")
- Trust bar: license numbers, bonded/insured status, typical arrival window — not adjectives`,
  },
  {
    id: "electrical-sharp-gold",
    label: "Sharp Gold",
    trade: "electrical",
    tradeLabel: "Electrical",
    accent: "amber-400",
    accentBg: "bg-amber-500",
    theme: "dark",
    heroLayout: "dual-card",
    primaryColor: "#d97706",
    colorName: "Amber/Gold",
    description: "Two-column asymmetric hero with a solid SAFETY FIRST credential card. Uniform slate-950 sections. Bold, safety-first energy — no glassmorphism.",
    personality: "Bold & Safety-First",
    bestFor: "Electrical, solar, trades where safety credentials are the differentiator",
    uniqueFeatures: [
      "Asymmetric hero lg:grid-cols-[2fr_3fr] with SAFETY FIRST credential card (solid bg — no backdrop-blur)",
      "Uniform slate-950 background across ALL sections",
      "Featured service card at index 2 — varied hierarchy",
      "Intentional radius: rounded-md CTAs, rounded-lg cards",
      "Single radial amber accent — no blur-3xl glow blobs",
    ],
    prompt: `Create a trade service landing page for an electrical company called "{business_name}" in {city}, {state}. Use the "electrical-sharp-gold" template design system:

## Color System
- Primary: amber-700 (CTAs), amber-400 (icons, accents), amber-500 (borders)
- Backgrounds: UNIFORM solid slate-950 across ALL sections (no alternating, no multi-stop gradients)
- Cards: slate-900/50 borders; featured: solid bg-amber-950/30 border-2 border-amber-500/40
- Text: white (primary), slate-400 (secondary), slate-500 (muted)
- Stars: fill-amber-400 text-amber-400
- Accent: ONE radial ellipse at 6% opacity max — no blur-3xl

## Layout
1. ContactBar (fixed top, h-10, solid bg-slate-950 border-b border-slate-800/60 — NO backdrop-blur; "24/7 Emergency Electrical")
2. TrustBanner (trade="electrical" — license/NEC/safety specifics)
3. Hero (min-h-[85vh], asymmetric lg:grid-cols-[2fr_3fr]: left=copy, right=SAFETY FIRST credential card)
4. StatsBar (accent="amber-400")
5. SectionDivider (variant="dots")
6. Services (featured card at INDEX 2 with "Most Popular" badge, varied heights — NOT 3 equal columns)
7. CTASection (color="amber", variant="urgency")
8. About (left-aligned story, trust box with border-l-2 border-amber-500/30 pl-8 sm:pl-12)
9. Reviews (masonry columns-1 md:columns-2 lg:columns-3, amber-500/10 serif quote watermarks)
10. CTASection (color="amber", variant="estimate")
11. FAQ (amber-500/30 open border, max-w-3xl)
12. Footer (4-col grid with SECTION_ANCHORS, Globe icon link)

## Hero Details
- Background: solid bg-slate-950 + single radial accent at 60% 40%
- NO word-reveal animation — single fade-up block for headline
- Primary CTA: bg-amber-700 rounded-md (6px) — NO shadow-lg glow
- Secondary CTA: border border-amber-500/30 rounded-md
- Right column SAFETY FIRST card (semantic content, NOT decorative circles):
  - solid border border-amber-500/20 bg-amber-950/40 rounded-lg p-8 sm:p-10 — NO backdrop-blur
  - Shield icon h-10 w-10 text-amber-400
  - "SAFETY FIRST" text-sm font-bold tracking-[0.3em] uppercase
  - License/insured specifics as subtitle (city + years), not vague adjectives
  - Single fade-up (opacity + y) — property-specific transition, NOT transition-all

## Service Cards
- Featured at INDEX 2 (Math.min(2, services.length - 1))
- Featured: solid bg-amber-950/30 border-2 border-amber-500/40, icon w-14 h-14
- Regular: bg-slate-900/50 border-slate-700/60 rounded-lg, icon w-12 h-12
- Hover: border-color only — NO -translate-y on every card
- "Most Popular" badge: text-xs font-semibold uppercase tracking-wider

## Typography
- Display: Instrument Serif, font-bold, tracking-tight
- Body: DM Sans, text-base leading-relaxed (1.65)
- Hero: text-4xl sm:text-5xl lg:text-6xl, lg:text-left
- Section headings: text-3xl sm:text-4xl font-bold font-display
- About label: text-sm font-semibold uppercase tracking-[0.2em] text-amber-400

## Local Copy Guidance
- Headlines: city + safety/license specificity ("{city}'s Licensed Residential Electricians")
- Trust bar: license numbers, NEC compliance, response times — not "Expert Team"`,
  },
  {
    id: "roofing-bold-copper",
    label: "Bold Copper",
    trade: "roofing",
    tradeLabel: "Roofing",
    accent: "orange-400",
    accentBg: "bg-orange-500",
    theme: "dark",
    heroLayout: "dual-card",
    primaryColor: "#ea580c",
    colorName: "Orange/Copper",
    description: "Two-column hero with rating/years/inspection credential stack. Static free-inspection badge — bold, action-oriented, no ping animation.",
    personality: "Bold & Action-Oriented",
    bestFor: "Roofing, storm damage, trades offering free inspections or strong guarantees",
    uniqueFeatures: [
      "Asymmetric hero with credential stack (rating, years, inspection CTA)",
      "Static free-inspection status indicator — solid dot, no animate-ping",
      "Trust points as horizontal card grid with varied sizing",
      "Custom inline SVG checkmarks",
      "Review stagger offset pattern for editorial rhythm",
    ],
    prompt: `Create a trade service landing page for a roofing company called "{business_name}" in {city}, {state}. Use the "roofing-bold-copper" template design system:

## Color System
- Primary: orange-700 (CTAs), orange-400 (accents, years display, icons), orange-500 (badges)
- Backgrounds: solid slate-950 (Hero, About, FAQ, Footer), slate-900 (Services, Reviews)
- Cards: slate-900/40 border border-slate-800/60; featured: solid bg-orange-950/30 border-2 border-orange-500/40
- Text: white (primary), slate-400 (secondary), slate-300
- Stars: fill-yellow-400 text-yellow-400
- Accent: ONE radial ellipse at 6% opacity max — no blur-3xl, no multi-stop gradients

## Layout
1. ContactBar (fixed top, h-10, solid bg-slate-950 border-b border-slate-800/60 — NO backdrop-blur; orange-400 phone icon)
2. TrustBanner (trade="roofing" — warranty/inspection specifics)
3. Hero (min-h-[85vh], asymmetric lg:grid-cols-[2fr_3fr]: left=copy, right=credential card stack)
4. StatsBar (accent="orange-400")
5. SectionDivider (variant="dots")
6. Services (featured card at index 0 with border-2 and "MOST POPULAR" badge — NOT 3 equal columns)
7. CTASection (color="orange", variant="urgency")
8. About (centered header, trust points as HORIZONTAL CARD GRID — not a flat list)
9. SectionDivider (variant="line")
10. Reviews (grid with stagger offset pattern [0, 12, 0, 12, 0, 12] marginTop)
11. CTASection (color="orange", variant="estimate")
12. SectionDivider (variant="wave")
13. FAQ (border-orange-500/30 when open, max-w-3xl)
14. Footer (4-col grid, SECTION_ANCHORS array)

## Hero Details
- Background: solid bg-slate-950 + single radial accent at 60% 40%
- NO word-reveal animation — single fade-up block for headline
- Primary CTA: bg-orange-700 rounded-md (6px) — NO shadow-lg glow
- Secondary CTA: border-2 border-orange-500/40 rounded-md (thicker secondary border is this template's signature)
- Business name pre-title: text-sm font-semibold uppercase tracking-widest text-orange-400
- Right column 3-card stack (semantic content — NOT decorative circles):
  1. Rating card: text-5xl font-bold tabular-nums, 5 stars, review count
  2. Years card: text-4xl font-bold text-orange-400 + "serving {city}" text
  3. FREE INSPECTION banner: bg-orange-700 text-white text-base font-bold px-8 py-4 rounded-lg, ArrowRight icon
     - Above banner: static badge with solid orange-500 status dot + "FREE INSPECTIONS" text-xs font-bold uppercase tracking-widest — NO animate-ping

## Service Cards
- Featured (index 0): solid bg-orange-950/30 border-2 border-orange-500/40, "MOST POPULAR" badge text-[10px] font-bold uppercase tracking-widest
- Regular: bg-slate-900/40 border-slate-800/60 rounded-lg
- Hover: border-color only — NO -translate-y lift / whileHover y on every card
- Icon container: w-11 h-11 bg-orange-500/10 rounded-md

## Unique Patterns
- Trust points as card grid: grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5; each point bg-slate-900/50 border-slate-800/70 rounded-lg px-5 py-4 with custom SVG checkmark (bg-orange-500/15 rounded-full)
- Review stagger: alternating marginTop [0, 12, 0, 12, 0, 12] for editorial rhythm
- Two line dividers: between About→Reviews and after Services CTA

## Typography
- Display: Instrument Serif, font-bold, tracking-tight
- Body: DM Sans, text-base leading-relaxed (1.65)
- Hero: text-4xl sm:text-5xl lg:text-6xl xl:text-7xl tracking-tight leading-[1.05]
- Section headings: text-3xl sm:text-4xl

## Local Copy Guidance
- Headlines: city + storm/warranty specificity ("{city} Storm-Damage Roofing Specialists")
- Trust bar: free inspection window, warranty years, license — not "Quality Service"`,
  },
  {
    id: "painting-clean-minimal",
    label: "Clean Minimal",
    trade: "painting",
    tradeLabel: "Painting",
    accent: "amber-700",
    accentBg: "bg-amber-700",
    theme: "light",
    heroLayout: "dual-decor",
    primaryColor: "#b45309",
    colorName: "Amber/Ink",
    description: "The ONLY light-theme template. Editorial stone/amber/ink palette — asymmetric hero with offset credential block. No violet, no decorative circles.",
    personality: "Clean & Design-Forward",
    bestFor: "Painting, interior design, landscaping, any trade where visual taste is the differentiator",
    uniqueFeatures: [
      "ONLY light-theme template — bg-white and bg-stone-50 sections",
      "Amber/ink editorial palette (terracotta #b45309) — never violet/purple",
      "Asymmetric hero with offset stat/credential block — NOT concentric circles",
      "White card FAQ on stone-50 background",
      "Dark footer (bg-stone-900) contrasting with light content",
    ],
    prompt: `Create a trade service landing page for a painting company called "{business_name}" in {city}, {state}. Use the "painting-clean-minimal" template design system:

## CRITICAL: This is the ONLY LIGHT THEME template
- ALL shared components (TrustBanner, StatsBar, SectionDivider, CTASection) receive light={true}
- Section backgrounds alternate: solid bg-white and bg-stone-50 — NO multi-stop gradients
- Footer is DARK (bg-stone-900 border-stone-800) — contrast with light content
- ContactBar is WHITE (bg-white border-b border-stone-200) — solid, NO backdrop-blur
- Text colors: text-stone-600 (secondary), text-stone-700 (body), text-stone-900 (primary) — NOT slate-300/400/500
- Border colors: border-stone-200 (default), border-amber-200 (active)
- Palette is stone / amber / ink ONLY — NEVER violet, purple, or indigo

## Color System
- Primary: amber-700 (CTAs, icons) — #b45309 terracotta/ink; amber-800 (hover)
- Backgrounds: solid bg-white (Hero, Services, Reviews), bg-stone-50 (About, FAQ)
- Cards: bg-white border-stone-200 (regular); featured: solid bg-amber-50 border-2 border-amber-200
- ContactBar: bg-white border-b border-stone-200
- Accent: ONE subtle radial at 4–6% opacity max on Hero — no blur-3xl glow blobs
- Inactive stars: text-stone-300
- Certification badges: bg-amber-50 border-amber-200 text-amber-800 rounded-full

## Layout
1. ContactBar (bg-white border-stone-200, "Free Color Consultation", text-stone-800)
2. TrustBanner (light={true})
3. Hero (min-h-[85vh], asymmetric lg:grid-cols-[2fr_3fr]: left=copy, right=offset credential/stat block)
4. StatsBar (accent="amber-700", light={true})
5. SectionDivider (variant="dots", light={true})
6. Services (featured card at index 0: bg-amber-50 border-2 border-amber-200 — NOT 3 equal columns)
7. CTASection (color="amber", variant="urgency", light={true})
8. About (editorial header + vertical accent bar bg-amber-200 + 2-col trust cards bg-white border-stone-200)
9. SectionDivider (variant="line", light={true})
10. Reviews (masonry columns, serif quotation marks, avatar bg-amber-100 text-amber-800)
11. CTASection (color="amber", variant="estimate", light={true})
12. SectionDivider (variant="wave", light={true})
13. FAQ (white cards bg-white border-stone-200, border-amber-200 when open)
14. Footer (DARK: bg-stone-900 border-stone-800)

## Hero Details
- Background: solid bg-white + single subtle radial (amber at ~5% opacity) — no via-gradient washes
- NO word-reveal animation — single fade-up block for headline
- Primary CTA: bg-amber-700 text-white rounded-md (6px) — NO shadow-lg glow
- Secondary CTA: border border-amber-200 text-amber-800 rounded-md hover:bg-amber-50
- Right column: offset credential/stat block (years + rating + local project count) — semantic content, NOT concentric circles or blur orbs

## Service Cards
- bg-white border-stone-200 rounded-lg
- Featured (index 0): bg-amber-50 border-2 border-amber-200, taller padding / span emphasis
- Hover: border-color only — NO -translate-y on every card
- Icon container: w-11 h-11 bg-amber-100 text-amber-700 rounded-md

## Typography
- Display: Instrument Serif, font-bold, tracking-tight, text-stone-900
- Body: DM Sans, text-base leading-relaxed (1.65), text-stone-700
- Hero: text-4xl sm:text-5xl lg:text-6xl
- Section headings: text-3xl sm:text-4xl font-bold text-stone-900 font-display tracking-tight
- About label: text-sm font-semibold uppercase tracking-wider text-amber-700

## Local Copy Guidance
- Headlines: city + finish/craft specificity ("{city} Interior Painters — Crisp Trim, Honest Estimates")
- Trust bar: years, insurance, color-consultation window — not "Expert Team" or exclamation-heavy copy`,
  },
  {
    id: "landscaping-earthy-green",
    label: "Earthy Green",
    trade: "landscaping",
    tradeLabel: "Landscaping",
    accent: "emerald-400",
    accentBg: "bg-emerald-500",
    theme: "dark",
    heroLayout: "dual-decor",
    primaryColor: "#10b981",
    colorName: "Emerald",
    description: "Organic, nature-inspired asymmetric hero with offset credential block. Centered About with vertical accent bar — solid emerald on slate, no orbs.",
    personality: "Organic & Sustainable",
    bestFor: "Landscaping, lawn care, eco-friendly trades, outdoor services",
    uniqueFeatures: [
      "Asymmetric hero with credential/stat block — NOT concentric circles",
      "Solid emerald accent on slate-950 — single radial at low opacity only",
      "Centered About section with vertical accent bar",
      "2-col trust point card grid with size variation",
      "Masonry reviews with serif quotation marks",
    ],
    prompt: `Create a trade service landing page for a landscaping company called "{business_name}" in {city}, {state}. Use the "landscaping-earthy-green" template design system:

## Color System
- Primary: emerald-700 (CTAs), emerald-400 (icons, accents), emerald-500 (borders)
- Backgrounds: solid slate-950 (Hero, About, FAQ, Footer), slate-900 (Services, Reviews)
- Cards: slate-800/50 border-slate-700/80; featured: solid bg-emerald-950/40 border-2 border-emerald-500/40
- Text: white (primary), slate-400 (secondary), slate-500 (muted), emerald-200/80 (hero subtitle)
- Stars: fill-yellow-400 text-yellow-400
- Accent: ONE radial ellipse at 6% opacity max — no blur-3xl, no multi-stop gradients

## Layout
1. ContactBar (fixed top, h-10, solid bg-slate-950 border-b border-slate-800/50 — NO backdrop-blur; "Free Landscape Estimate")
2. TrustBanner (trade="landscaping" — season/service-area specifics)
3. Hero (min-h-[85vh], asymmetric lg:grid-cols-[2fr_3fr]: left=copy, right=offset credential/stat block)
4. StatsBar (accent="emerald-400")
5. SectionDivider (variant="dots")
6. Services (featured card at index 0 — varied hierarchy, NOT 3 equal columns)
7. CTASection (color="emerald", variant="urgency")
8. About (centered header, vertical accent bar bg-emerald-500/20, trust cards grid sm:grid-cols-2 with size variation)
9. SectionDivider (variant="line")
10. Reviews (masonry columns-1 md:columns-2 lg:columns-3, serif quotation marks, avatar bg-emerald-900 text-emerald-300)
11. CTASection (color="emerald", variant="estimate")
12. SectionDivider (variant="wave")
13. FAQ (border-emerald-500/30 when open, max-w-3xl)
14. Footer (4-col grid, "Visit Us" with Globe icon)

## Hero Details
- Background: solid bg-slate-950 + single radial accent at 60% 40%
- NO word-reveal animation — single fade-up block for headline
- Primary CTA: bg-emerald-700 rounded-md (6px) — NO shadow-lg glow
- Secondary CTA: border border-emerald-400/40 text-emerald-200 rounded-md
- Right column: offset credential/stat block (years serving + seasonal packages + local project count) — semantic content, NOT concentric circles, blur orbs, or scale-pulse decoration

## Service Cards
- Featured (index 0): solid bg-emerald-950/40 border-2 border-emerald-500/40, icon bg-emerald-400/20 text-emerald-300 w-14 h-14, "MOST POPULAR" badge
- Regular: bg-slate-800/50 border-slate-700/80 rounded-lg, icon bg-emerald-500/10 text-emerald-400 w-11 h-11 rounded-md
- Hover: border-color only — NO -translate-y on every card

## About Section
- Centered header with emerald label
- Left-side vertical accent bar: bg-emerald-500/20 rounded-full (inside max-w-4xl)
- Trust point cards: bg-slate-900/50 border-slate-800 rounded-lg in sm:grid-cols-2 — vary padding/height on one card
- Divider line: solid border-t border-emerald-500/20 (not multi-stop gradient line)

## Typography
- Display: Instrument Serif, font-bold, tracking-tight
- Body: DM Sans, text-base leading-relaxed (1.65)
- Hero: text-4xl sm:text-5xl lg:text-6xl
- Section headings: text-3xl sm:text-4xl
- About label: text-sm font-semibold uppercase tracking-wider text-emerald-400

## Local Copy Guidance
- Headlines: city + outdoor seasonality ("{city} Landscape Design — Built for Local Soil & Seasons")
- Trust bar: service radius, seasonal maintenance windows, insurance — not vague eco adjectives`,
  },
];

/** Templates with mandatory anti-AI-slop quality standards prepended to every prompt */
export const TEMPLATES: TemplateMeta[] = TEMPLATE_DEFINITIONS.map((t) => ({
  ...t,
  prompt: `${DESIGN_QUALITY_PROMPT_BLOCK}\n\n${t.prompt}`,
}));
