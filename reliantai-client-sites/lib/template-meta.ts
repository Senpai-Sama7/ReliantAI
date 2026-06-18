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
    description: "Emergency-focused with red alert badge. Featured service card and featured review split layout. The urgency template for emergency trades.",
    personality: "Urgent & Trustworthy",
    bestFor: "Plumbing, emergency services, 24/7 availability trades",
    uniqueFeatures: [
      "Red emergency pill badge — static indicator, NO animate-ping",
      "Featured service card (index 0) with editorial hierarchy",
      "Featured review split layout (first review full-width, rest in grid)",
      "Dynamic cert-icon mapping (CERT_ICONS lookup by keyword)",
      "Asymmetric hero with left-aligned copy",
    ],
    prompt: `Create a trade service landing page for a plumbing company called "{business_name}" in {city}, {state}. Use the "plumbing-trustworthy-navy" template design system:

## Color System
- Primary: blue-600 (CTAs), blue-400 (icons), blue-300 (hover)
- Emergency accent: red-500/10 bg, red-500/20 border, red-300 text (for emergency badge)
- Backgrounds: slate-950 (Hero, About, FAQ), slate-900 (Services), slate-900/95 (Reviews)
- Cards: slate-800/40, featured: bg-gradient-to-br from-blue-950/50 to-slate-900/60 border-blue-500/30
- Text: white, slate-400, slate-300, slate-500
- Accent glow: bg-blue-600/3 blur-3xl

## Layout
1. ContactBar (fixed top, h-12, bg-slate-900, "24/7 Emergency Plumbing")
2. TrustBanner
3. Hero (min-h-[90vh], single-column with RED emergency pill badge above stars)
4. StatsBar (accent="blue-400")
5. Services (grid with featured card at index 0 — "Most Requested" badge, gradient bg, larger icon)
6. CTASection (urgency)
7. About (left-aligned max-w-2xl story, trust box with border-l-2 border-blue-500/40)
8. Reviews (featured first review as full-width, rest in grid-cols-1 md:grid-cols-2)
9. FAQ (with HelpCircle icon above heading)
10. Footer (includes "Built by ReliantAI" credit, website URL link)

## Emergency Badge
- Red pill badge above hero stars: bg-red-500/10 border-red-500/20 rounded-full
- AlertTriangle icon + "24/7 EMERGENCY" text
- animate-ping dot indicator (w-2 h-2 bg-red-400)
- text-xs font-semibold tracking-widest uppercase

## Featured Service Card
- Index 0 gets: bg-gradient-to-br from-blue-950/50 to-slate-900/60
- border border-blue-500/30 shadow-lg
- "Most Requested" badge: text-[0.65rem] tracking-widest uppercase
- Larger icon container: w-14 h-14
- Arrow slides group-hover:ml-2 on CTA

## Featured Review
- First review rendered as standalone card with gradient background
- Large serif quotation mark decoration
- Remaining reviews in 2-col grid

## Dynamic Cert Icons
- CERT_ICONS map: { licensed: ShieldCheck, master: Award, certified: BadgeCheck, insured: Shield, bonded: Shield, background: UserCheck, epa: Leaf, nec: Zap }

## Hero
- min-h-[90vh] (slightly shorter than full screen)
- fadeUp animation with per-word custom delay (i * 0.06)
- Primary CTA: bg-blue-600 rounded-xl shadow-lg shadow-blue-600/25 hover:bg-blue-500`,
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
    description: "Two-column hero with decorative SAFETY FIRST card. All sections on uniform slate-950 background. Bold, safety-first energy.",
    personality: "Bold & Safety-First",
    bestFor: "Electrical, solar, trades where safety credentials are the differentiator",
    uniqueFeatures: [
      "Two-column asymmetric hero with credential card (not decorative placeholder)",
      "SAFETY FIRST card: Shield icon, solid bg — NO backdrop-blur",
      "Uniform slate-950 background across ALL sections",
      "Featured service card at index 2 — varied hierarchy",
      "rounded-md CTAs with intentional radius variation",
    ],
    prompt: `Create a trade service landing page for an electrical company called "{business_name}" in {city}, {state}. Use the "electrical-sharp-gold" template design system:

## Color System
- Primary: amber-600 (CTAs), amber-400 (icons, accents), amber-500 (glows, borders)
- Backgrounds: UNIFORM slate-950 across ALL sections (no alternating)
- Cards: slate-900/50 borders, featured: bg-amber-950/30 border-2 border-amber-500/40
- Text: white, slate-400, slate-300, slate-500
- Stars: fill-amber-400 text-amber-400
- Accent glow: bg-amber-500/[0.07] blur-3xl

## Layout
1. ContactBar (fixed top, h-12, bg-slate-900, "24/7 Emergency Electrical")
2. TrustBanner (trade="electrical")
3. Hero (min-h-screen, TWO-COLUMN: left=text content, right=SAFETY FIRST decorative card)
4. StatsBar (accent="amber-400")
5. Services (featured card at INDEX 2 with "Most Popular" badge, py-28 depth)
6. CTASection (color="amber", variant="urgency")
7. About (left-aligned story, trust box with border-l-2 border-amber-500/30 pl-8 sm:pl-12)
8. Reviews (masonry columns, amber-500/10 quote watermarks)
9. CTASection (color="amber", variant="estimate")
10. FAQ (amber-500/30 open border)
11. Footer (4-col grid with SECTION_ANCHORS array, Globe icon link)

## CRITICAL: Hero SAFETY FIRST Card
Right column contains a decorative card:
- border border-amber-500/20 bg-amber-500/[0.04] backdrop-blur-sm rounded-2xl p-8 sm:p-10
- Shield icon at h-10 w-10 text-amber-400
- "SAFETY FIRST" in text-sm font-bold tracking-[0.3em] uppercase
- "Licensed & Insured" subtitle in text-slate-500
- Animation: y:20→0, delay:0.5, duration:0.8

## CRITICAL: Border Radius
- ALL CTAs use rounded-lg (NOT rounded-xl) — this is the ONLY template with rounded-lg

## Service Cards
- Featured at INDEX 2 (Math.min(2, services.length - 1))
- Featured: bg-amber-950/30 border-2 border-amber-500/40 shadow-amber-500/10
- "Most Popular" badge: text-xs font-semibold uppercase tracking-wider
- Regular card icon: w-12 h-12, Featured: w-14 h-14 with bolder amber styling

## Typography
- Hero headline: centered lg:text-left, single block (NO word-reveal animation)
- Section headings: text-3xl sm:text-4xl font-bold font-display
- About label: text-sm font-semibold uppercase tracking-[0.2em] text-amber-400`,
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
    description: "Two-column hero with rating/years/CTA card stack. Animated ping dot for free inspection badge. Bold, action-oriented.",
    personality: "Bold & Action-Oriented",
    bestFor: "Roofing, storm damage, trades offering free inspections or strong guarantees",
    uniqueFeatures: [
      "Two-column hero with credential stack (rating, years, inspection CTA)",
      "Static status indicator — NO animate-ping",
      "Trust points as horizontal card grid with varied sizing",
      "Custom inline SVG checkmarks",
      "Review stagger offset pattern for editorial rhythm",
    ],
    prompt: `Create a trade service landing page for a roofing company called "{business_name}" in {city}, {state}. Use the "roofing-bold-copper" template design system:

## Color System
- Primary: orange-600 (CTAs), orange-400 (accents, years display, icons), orange-500 (glows, badges)
- Backgrounds: slate-950 (Hero, About, FAQ, Footer), slate-900 (Reviews)
- Cards: slate-900/40 border-2 border-slate-800/60, featured: bg-orange-500/10 border-2 border-orange-500/40
- Text: white, slate-400, slate-300
- Star: fill-yellow-400 text-yellow-400
- Ping badge: bg-orange-500/15 with animate-ping dot

## Layout
1. ContactBar (fixed top, h-12, bg-slate-950/95 backdrop-blur-sm, text-orange-400 phone icon)
2. TrustBanner (trade="roofing")
3. Hero (min-h-[90vh], TWO-COLUMN: left=text, right=credential card stack)
4. StatsBar (accent="orange-400")
5. Services (featured card at index 0 with border-2 and "MOST POPULAR" badge)
6. CTASection (color="orange", variant="urgency")
7. About (centered header, trust points as HORIZONTAL CARD GRID — not list)
8. SectionDivider (variant="line") — FIRST line divider
9. Reviews (grid with STAGGER offset pattern [0, 12, 0, 12, 0, 12] marginTop)
10. CTASection (color="orange", variant="estimate")
11. SectionDivider (variant="wave")
12. FAQ (border-orange-500/30 when open)
13. Footer (4-col grid, SECTION_ANCHORS array)

## CRITICAL: Hero Right Column (3-card stack)
1. **Rating card**: text-5xl font-bold tabular-nums for rating number, 5 stars, review count
2. **Years card**: text-4xl font-bold text-orange-400 years display + "serving" text
3. **FREE INSPECTION TODAY banner**: bg-orange-600 text-white text-base font-bold px-8 py-4 rounded-2xl shadow-xl, ArrowRight icon
   - Above the banner: ping animation badge with "FREE INSPECTIONS" text-xs font-bold uppercase tracking-widest

## CRITICAL: CSS Ping Animation
Two nested spans: outer span with "relative flex h-2.5 w-2.5", inner animate-ping span with "absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75", plus a relative span with "inline-flex rounded-full h-2.5 w-2.5 bg-orange-500"

## Unique Patterns
- **Trust points as card grid**: grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5, each point is bg-slate-900/50 border-slate-800/70 rounded-xl px-5 py-4 with custom SVG checkmark (bg-orange-500/15 rounded-full)
- **Secondary CTA uses border-2** (thicker border than other templates' single border)
- **Review stagger**: Alternating marginTop values [0, 12, 0, 12, 0, 12] for masonry-like effect
- **whileHover**: framer-motion whileHover={{ y: -6 }} on service cards, whileHover={{ y: -4 }} on review cards
- **Two line dividers**: One between About and Reviews, plus the standard one after Services CTA

## Typography
- Hero headline: text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold font-display tracking-tight leading-[1.05]
- Business name as pre-title: text-sm font-semibold uppercase tracking-widest text-orange-400
- "MOST POPULAR" badge: text-[10px] font-bold uppercase tracking-widest (smallest badge size)`,
  },
  {
    id: "painting-clean-minimal",
    label: "Clean Minimal",
    trade: "painting",
    tradeLabel: "Painting",
    accent: "violet-600",
    accentBg: "bg-violet-500",
    theme: "light",
    heroLayout: "dual-decor",
    primaryColor: "#7c3aed",
    colorName: "Violet",
    description: "The ONLY light-theme template. Editorial, airy, design-forward — asymmetric hero with offset stat block. NO decorative circles.",
    personality: "Clean & Design-Forward",
    bestFor: "Painting, interior design, landscaping, any trade where visual taste is the differentiator",
    uniqueFeatures: [
      "ONLY light-theme template — bg-white and bg-stone-50 sections",
      "Asymmetric hero with offset stat/credential block — NOT concentric circles",
      "White card FAQ on stone-50 background",
      "Serif quotation marks in reviews",
      "Dark footer (bg-stone-900) contrasting with light content",
    ],
    prompt: `Create a trade service landing page for a painting company called "{business_name}" in {city}, {state}. Use the "painting-clean-minimal" template design system:

## CRITICAL: This is the ONLY LIGHT THEME template
- ALL shared components (TrustBanner, StatsBar, SectionDivider, CTASection) receive light={true}
- Section backgrounds alternate: bg-white and bg-stone-50
- Footer is DARK (bg-stone-900 border-stone-800) — contrast with light content
- ContactBar is WHITE (bg-white border-b border-stone-200)
- Text colors: text-slate-600 (secondary), text-slate-700 (body), text-slate-900 (primary) — NOT slate-300/400/500
- Border colors: border-stone-200 (default), border-violet-200 (active)

## Color System
- Primary: violet-600 (CTAs, icons), violet-500 (hover), violet-200 (borders, light accents)
- Backgrounds: bg-white (Services, Reviews), bg-stone-50 (About, FAQ), bg-gradient-to-b from-white via-violet-50/30 to-white (Hero)
- Cards: bg-white border-stone-200 (regular), featured: bg-violet-50 border-2 border-violet-200 shadow-lg
- ContactBar: bg-white border-b border-stone-200
- Accent glow: bg-violet-200/20 blur-3xl (Hero)
- Inactive stars: text-stone-300 (not slate-600)

## Layout
1. ContactBar (bg-white border-stone-200, "Free Color Consultation" text, text-slate-800)
2. TrustBanner (light={true})
3. Hero (min-h-screen, TWO-COLUMN: left=text, right=concentric violet circles)
4. StatsBar (accent="violet-600", light={true})
5. SectionDivider (variant="dots", light={true})
6. Services (featured card at index 0: bg-violet-50 border-2 border-violet-200)
7. CTASection (color="violet", variant="urgency", light={true})
8. About (centered header + vertical accent bar bg-violet-200 rounded-full + 2-col trust cards bg-white border-stone-200)
9. SectionDivider (variant="line", light={true})
10. Reviews (masonry columns, SERIF quotation mark " character, avatar bg-violet-100 text-violet-600)
11. CTASection (color="violet", variant="estimate", light={true})
12. SectionDivider (variant="wave", light={true})
13. FAQ (white cards bg-white border-stone-200, border-violet-200 when open, shadow-sm)
14. Footer (DARK: bg-stone-900 border-stone-800)

## CRITICAL: Hero Right Column (Concentric Circles)
Decorative only, no content:
- Outer: w-80 h-80 bg-violet-200/20 rounded-full blur-2xl
- Middle: w-56 h-56 bg-violet-300/15 rounded-full border border-violet-300/20 blur-xl
- Inner: w-32 h-32 bg-violet-400/10 rounded-full

## CTA Button Styles
- Primary: bg-violet-600 text-white rounded-xl shadow-lg shadow-violet-600/25 hover:bg-violet-500
- Secondary: border border-violet-200 text-violet-700 rounded-xl hover:bg-violet-50 hover:border-violet-300 (LIGHT OUTLINE STYLE)

## Certification Badges
- bg-violet-50 border-violet-200 text-violet-700 rounded-full (light badge style, NOT dark slate)

## Typography
- All headings on light backgrounds use text-slate-900 (NOT text-white)
- Section headings: text-3xl sm:text-4xl font-bold text-slate-900 font-display tracking-tight
- About label: text-sm font-semibold uppercase tracking-wider text-violet-600
- Trust points text: text-sm font-medium text-slate-700`,
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
    description: "Organic, nature-inspired with asymmetric hero and offset credential block. Centered About with vertical accent bar.",
    personality: "Organic & Sustainable",
    bestFor: "Landscaping, lawn care, eco-friendly trades, outdoor services",
    uniqueFeatures: [
      "Asymmetric hero with credential stat block — NOT concentric circles",
      "Solid emerald accent on slate-950 — single radial glow only",
      "Centered About section with vertical accent bar",
      "2-col trust point card grid with size variation",
      "Masonry reviews with serif quotation marks",
    ],
    prompt: `Create a trade service landing page for a landscaping company called "{business_name}" in {city}, {state}. Use the "landscaping-earthy-green" template design system:

## Color System
- Primary: emerald-600 (CTAs), emerald-400 (icons, accents, hover), emerald-500 (borders, glows)
- Backgrounds: slate-950 (Hero, About, FAQ, Footer), slate-900 (Services, Reviews)
- Cards: slate-800/50 border-slate-700/80, featured: bg-emerald-900/30 border-2 border-emerald-500/40
- Text: white, slate-400, slate-300, slate-500, emerald-200/80 (hero subtitle)
- Accent glow: bg-emerald-500/5 blur-3xl (Hero), bg-emerald-600/3 blur-3xl (Services)
- Stars: fill-yellow-400 text-yellow-400

## Layout
1. ContactBar (fixed top, bg-slate-950 border-b border-slate-800/50, "Free Landscape Estimate")
2. TrustBanner (trade="landscaping")
3. Hero (min-h-screen, TWO-COLUMN: left=text, right=concentric emerald circles)
4. StatsBar (accent="emerald-400")
5. SectionDivider (variant="dots")
6. Services (featured card at index 0: bg-emerald-900/30 border-2 border-emerald-500/40 shadow-lg shadow-emerald-500/10)
7. CTASection (color="emerald", variant="urgency")
8. About (centered text-center header, vertical accent bar bg-emerald-500/20, trust cards grid sm:grid-cols-2)
9. SectionDivider (default)
10. Reviews (masonry columns, serif quotation mark character, avatar bg-emerald-900 text-emerald-300)
11. CTASection (color="emerald", variant="estimate")
12. SectionDivider (variant="wave")
13. FAQ (border-emerald-500/30 when open, hover:text-emerald-300)
14. Footer (4-col grid, "Visit Us" section with Globe icon, "Built by ReliantAI" credit)

## CRITICAL: Hero Right Column (Concentric Circles — ANIMATED)
Scale animation (0.92→1, duration 0.8, delay 0.2):
- Outer: w-72 h-72 bg-emerald-500/10 rounded-full blur-2xl
- Middle: w-52 h-52 bg-emerald-600/15 rounded-full border border-emerald-500/10
- Inner: w-32 h-32 bg-emerald-400/10 rounded-full

## CRITICAL: Hero Scale Animation
motion.div initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }}
transition={{ duration: 0.8, delay: 0.2 }}
This is the ONLY template with scale animation on Hero right column.

## Service Card Featured (index 0)
- bg-emerald-900/30 border-2 border-emerald-500/40 shadow-lg shadow-emerald-500/10
- Icon: bg-emerald-400/20 text-emerald-300 (featured) vs bg-emerald-500/10 text-emerald-400 (regular)
- "MOST POPULAR" badge

## About Section
- Centered: text-center header with emerald label
- Left-side vertical accent bar: bg-emerald-500/20 rounded-full (inside max-w-4xl)
- Trust point cards: bg-slate-900/50 border-slate-800 rounded-xl in sm:grid-cols-2
- Gradient line: bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent

## Reviews
- Masonry layout (columns-1 md:columns-2 lg:columns-3)
- Serif quotation mark: text-emerald-500/30 text-5xl font-serif
- Avatar: bg-emerald-900 text-emerald-300

## CTA Button Styles
- Primary: bg-emerald-600 text-white rounded-xl shadow-lg shadow-emerald-600/25 hover:bg-emerald-500 hover:shadow-emerald-500/30
- Secondary: border border-emerald-400/40 text-emerald-200 rounded-md hover:border-emerald-300 hover:text-white`,
  },
];

/** Templates with mandatory anti-AI-slop quality standards prepended to every prompt */
export const TEMPLATES: TemplateMeta[] = TEMPLATE_DEFINITIONS.map((t) => ({
  ...t,
  prompt: `${DESIGN_QUALITY_PROMPT_BLOCK}\n\n${t.prompt}`,
}));