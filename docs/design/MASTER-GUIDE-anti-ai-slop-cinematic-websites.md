# The Master Guide to Building Websites That Don't Look AI-Generated
## The Universal System for God-Tier Web Craft: Any Use Case, Zero AI Fingerprints

> Single-source system for anti-AI-slop research, use-case routing, cinematic motion architecture,
> typography and color craft, interaction grammar, reverse-engineering method, prompting, and production
> hardening. Works for a campaign microsite, a SaaS app, a store, a docs portal, or a nonprofit.
>
> **Evidence policy:** Practices below were verified against **2025–2026 web sources only** (not model
> training memory). Last audited: **2026-07-17**. Immersion/interaction upgrades draw on Codrops (May–Jul
> 2026), Next.js+Lenis guides (Apr 2026), and Adamarant’s immersive stack notes. Primary sources are listed
> in Appendix B. Claims that could not be re-confirmed from a 2025–2026 URL were removed or rewritten.

---

## THE CORE THESIS (read this first)

A coding model outputs the statistical center of its training data. In 2026 that center still reads as
Tailwind blue/indigo, Inter, and three equal cards. "AI slop" is not a bug. It is the model returning
the average. Distinctiveness only exists in decisions the model would never make on its own.

There are only two escapes. Everything in this guide is one of them:

1. **Raise the information in the prompt.** Every taste decision you leave blank gets filled with the
   default. Specify color, type, layout, motion, and exclusions *before* generation.
2. **Raise the craft floor with systems the model never defaults to.** OKLCH ramps, scroll-scrubbed
   timelines, asymmetric grids, real photography, restrained easing.

**Make every taste decision explicit before the model generates, and build systems, not one-off screens.**

One more law makes this universal: **god-tier is use-case-relative.** A cinematic pin sequence on a docs
site is as amateur as a fade-in spam hero on a campaign site. Excellence means the *right* execution tier
for the job, applied with total discipline. Part 0 routes you; everything after executes.

---

## PART 0: THE UNIVERSAL ROUTER (START EVERY PROJECT HERE)

### Step 1 — Classify the job

Answer three questions before any design decision:

1. **Primary user verb:** feel / evaluate / buy / read / do. (A campaign wants *feel*; a dashboard wants *do*.)
2. **Visit frequency:** once (impress) vs daily (respect time and muscle memory).
3. **Content half-life:** permanent brand statement vs constantly changing data.

### Step 2 — Pick the execution tier

| Tier | Name | Motion budget | Where it wins |
|------|------|---------------|---------------|
| **T0** | Static craft | CSS transitions only; zero scroll choreography | Docs, dashboards, checkout, settings, legal |
| **T1** | Editorial motion | CSS scroll-driven reveals, one accent moment, no pins | Blogs, e-commerce browsing, SaaS marketing, local business |
| **T2** | Cinematic scroll | Lenis + GSAP pins/scrub, Motion Script, kinetic type | Campaign sites, brand homes, portfolios, launches |
| **T3** | Immersive world | T2 + justified WebGL/video worlds, persistent canvas | Award pushes, product-as-experience, storytelling flagships |

Routing rules:

- **When in doubt, pick the lower tier and execute it perfectly.** A flawless T1 beats a janky T2 every time.
- Tiers apply **per surface, not per project**: a store can run a T2 lookbook page over a T0 checkout.
- Escalate a tier only when the *content* earns it (story, product drama, brand theater), never because
  "the homepage feels plain."
- De-escalate instantly for: daily-use tools, form-heavy flows, low-end device audiences, tight deadlines.

### Step 3 — Apply the universal invariants (every tier, no exceptions)

These are tier-independent. Slop is banned at T0 exactly as hard as at T3:

1. All Part 1 bans (signature gradients, Inter-only, three equal cards, buzzword copy, fake imagery).
2. OKLCH token system + one justified type pairing (Part 3), even for a plain docs site.
3. At least one deliberate layout decision the template generation would never make (asymmetry, editorial
   type scale, unusual density rhythm) appropriate to the tier.
4. Real content: real screenshots, real data, real photography, named specifics.
5. Interface states designed, not defaulted (Part 3: states and forms).
6. WCAG 2.2 AA, reduced-motion path, keyboard completeness.
7. CWV: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1 on the heaviest page.
8. One interaction grammar sitewide (Part 7), even if the grammar is "hover underline + focus ring only."

### Step 4 — Use-case playbooks (route, then execute the parts)

| Use case | Tier | What god-tier means here | Emphasize parts | Skip |
|----------|------|--------------------------|-----------------|------|
| Campaign / brand launch | T2–T3 | One unforgettable scroll story; restraint elsewhere | 4, 5, 6, 7 | Nothing |
| SaaS marketing site | T1–T2 | Distinct identity + real product proof (live UI, data) | 1, 3, 5, 7 | T3 worlds |
| SaaS app / dashboard | T0 | Speed, state craft, typographic hierarchy, zero jank | 3 (states), 7 (grammar), 9 | Pins, Lenis, cursors |
| E-commerce | T0–T1 (T2 lookbook) | Product photography as hero; frictionless buy path | 3, 6 (media), 9, 12 | Scroll hijack on PDP/checkout |
| Docs / knowledge base | T0 | Reading speed, search, code blocks, anchor integrity | 3, 9, 12 | Lenis entirely |
| Editorial / blog | T1 | Typography as the design; art-directed features | 3, 4 (light), 6 (media) | Heavy pins |
| Portfolio / studio | T2–T3 | Taste demonstration; one signature interaction | 4, 5, 6, 7, 10 | Feature-card thinking |
| Local business / nonprofit | T1 | Warm real imagery, trust signals, NAP/SEO, fast mobile | 3, 6, 12 | 3D, custom cursors |

The playbook decides *where you spend the craft budget*. Every row still inherits all invariants.

---

## PART 1: THE AI-SLOP FINGERPRINT (WHAT TO BAN)

Users decide "this was generated" in the first few seconds, before reading copy. No single tell is fatal.
Stacking three or four is what marks an unedited AI export. 2026 audits of AI-built SaaS landings put
exactly three feature cards above the fold on roughly **71%** of pages, and Inter/system-ui on roughly
**73%** of AI frontends. Ban all of these explicitly in every project.

### The 2026 visual signature (hard bans)

| # | Tell | 2025–2026 evidence |
|---|------|--------------------|
| 1 | Blue / indigo / purple-to-pink gradients (`#3b82f6`, `#6366f1`, `from-purple-500 to-pink-500`) | Called the "AI visual signature" and "Purple Problem"; traces to Tailwind demo defaults and v0/Lovable/Bolt output patterns. |
| 2 | Inter (or Roboto) as the only typeface | Highest-probability safe sans when the prompt leaves type open. |
| 3 | Centered hero + generic "build the future" copy | Fits the *shape* of a hero, not your specific content. |
| 4 | Three equal cards (`grid-cols-3`), identical radius/spacing/shadow, Lucide/Heroicons `Zap`/`Shield`/`Rocket` | Strongest layout fingerprint on AI marketing surfaces. |
| 5 | Uniform fade-in / `transition-all duration-300 ease-in-out` everywhere | Decorative motion with no state or scroll meaning. |
| 6 | Plastic AI illustrations / 3D blobs | Too smooth, too symmetrical, uncanny lighting. |
| 7 | No real proof | Stock/AI people instead of real photos, screenshots, named customers, specific numbers. |
| 8 | Em-dash confetti + stock openers | "In today's fast-paced world," "a rich tapestry of," em dashes in nearly every sentence. |
| 9 | Buzzword soup | `seamless`, `cutting-edge`, `unlock`, `elevate`, `robust`, `best-in-class`, `leverage`, `delve`, `holistic`, `transformative`, `empower`. |
| 10 | Formulaic AI sentence frames | Especially **"It's not just X — it's Y"** and emoji bullet lists with no prioritization. |
| 11 | Boilerplate meta/alt | Duplicate meta, missing OG image, alt text reading "image." |
| 12 | Templated code smell | Dead utility classes, identical card components, missing focus states, accessibility gaps. |

Also ban: purple glow card shadows, rainbow gradient text, pill-shaped everything, white/`slate-50`
backgrounds with no brand decision, `rounded-lg`/`rounded-2xl` stamped on every surface.

### The default layout to refuse

`hero -> three feature cards -> testimonials -> pricing -> CTA` is still the statistically average
"modern startup page." If you do not specify a layout, you get this one. Always specify.

### Copy rules (2025–2026)

- Replace every buzzword with a concrete, falsifiable claim tied to the product or mission.
- No hedging ("may," "can potentially"). No emoji bullet lists.
- Headlines name the specific outcome. They should not fit any other company.
- Minimize em dashes. Prefer periods, commas, colons, or parentheses.
- Ban the frame **"It's not just X — it's Y."** It is a widely recognized AI giveaway in 2025–2026.
- Optional CI: run a slop scanner (`slop-gate`, `slop-radar`) on marketing copy before ship.

---

## PART 2: THE DECISION-FIRST WORKFLOW

Senior designers do not generate a whole site in one shot. Force the agent into the same order.

1. **Route.** Part 0: classify the job, pick the tier per surface, load the playbook row.
2. **Concept.** One sentence for emotional and structural intent.
3. **Design system.** Color, type pairing, grid, states, motion vocabulary. Lock before any component (Part 3).
4. **Narrative Motion Script** (T1+ only; T0 skips straight to build). Scene-by-scene: scroll %, trigger,
   animation, beat, archetype. Approve before code (Part 4).
5. **Build scene by scene** (or screen by screen at T0). Hero first, to 60fps, then the next. Never the
   whole product at once.
6. **Immersion + interaction polish.** Justified media/3D islands, one cursor/hover/transition grammar
   (Parts 6–7), scoped to the tier.
7. **Polish, then dual audit.** Easing/pacing consistency, then Part 13 (anti-slop + tier-aware excellence
   checklist).

"Route first," "Motion Script before code," and "one scene at a time" are the three steps that most prevent
median collapse.

---

## PART 3: THE DESIGN SYSTEM (COLOR, TYPE, GRID, ASSETS, STATES)

### Color: author in OKLCH (2026 standard)

OKLCH is the production default for professional color systems in 2026: perceptual uniformity, native
`oklch()` in evergreen browsers (~96% global support early 2026), and clean `color-mix()` pipelines.

- Never use an unmodified Tailwind/framework color token.
- Author scales in OKLCH so a 10-unit lightness change looks even across hues. Distribute as CSS custom
  properties. Ship hex/sRGB fallbacks via `@supports` or PostCSS for the remaining browsers.
- Keep chroma roughly **0.0–0.4** for UI surfaces; extreme chroma clips on sRGB monitors.
- System anatomy: **Primary**, **Secondary**, **Neutrals** (carries most of the UI), **Semantic**.
- Prefer **neutral-with-accent** over a full-gradient brand.
- **Dark mode is not inversion.** Off-white text on dark gray surfaces; elevate with lightness steps
  (base → card → modal). Desaturate accents ~10–20% on dark.
- **Tokens, not raw hex in components.** Semantic names (`--color-brand-primary`, `--color-text-secondary`,
  `--color-bg-elevated`).
- **Accessibility:** target **WCAG 2.2 AA** (4.5:1 normal text, 3:1 large text / non-text UI). Use APCA
  as a supplementary check. Validate final rendered colors (overlays can fail mid-scroll).

Tailwind CSS v4: define brand colors only in `@theme` / CSS variables. Do not leave default indigo/blue
palette tokens as the site's identity.

```css
@theme {
  --color-brand: oklch(62% 0.16 35);
  --color-surface: oklch(98% 0.01 85);
  --font-display: "Playfair Display", serif;
  --font-body: "Source Sans 3", sans-serif;
}
```

### Typography: one display face, one body face, justified

- One expressive display face + one workhorse body face. Justify the pairing in a one-line comment.
  Inter-for-everything is a slop tell.
- Editorial hierarchy, not SaaS: large tracked-out heroes, tighter section titles, readable body.
- Baseline grid so line-heights lock to shared multiples.
- Prefer container queries over crude `clamp()` for region-local headline scaling.
- Load with `font-display: swap`. Prefer self-hosted, subset WOFF2 when performance matters (2026
  font playbooks emphasize subset + size-adjust to reduce CLS).

### Grid: break the centered-div reflex

Treat the viewport as a coordinate system. Use CSS Grid with named areas so headlines can overlap images.
At least one section must break symmetry on purpose. Prefer asymmetric spans (`3fr 5fr`) or staggered
bento over `grid-cols-3`.

```css
.poster-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: repeat(8, 1fr);
  height: 100vh;
}
.headline   { grid-area: 1 / 1 / 4 / 9; z-index: 2; }
.hero-image { grid-area: 2 / 6 / 9 / 13; }
```

### Assets: the one thing the model cannot fake

- Sketch on paper before Figma. Tool defaults constrain thinking.
- Line art → SVG (animate with `stroke-dashoffset`). Painterly work → WebP/AVIF.
- Layer hand-drawn accents over a precise grid: structure from code, personality from the asset.
- Use textured assets as `clip-path` / `mask-image` sources.
- Compress to WebP/AVIF + responsive `srcset`. Texture-heavy PNGs remain a top performance killer.

### Interface states and forms (where apps quietly turn to slop)

Marketing pages fail on gradients; products fail on states. AI output ships the happy path and defaults
everything else. Design all five states for every data surface **before** building it:

| State | God-tier looks like | Slop looks like |
|-------|---------------------|-----------------|
| Empty | Purposeful onboarding: what this is, one next action, brand-true illustration or specimen data | Gray box, "No data yet" |
| Loading | Skeletons shaped like the real layout; no spinner-only screens; reserved dimensions (CLS 0) | Centered spinner, layout jump on arrival |
| Error | Human sentence, cause if known, retry/recovery action, error preserved input | Red toast: "Something went wrong" |
| Partial | Progressive render; stale-while-revalidate indicators | All-or-nothing blank until fetch resolves |
| Success/done | Confirmation with the *result* (what changed, where it went) | Silent mutation or generic checkmark |

Form craft (universal, tier-independent):

- Labels always visible; placeholders are hints, never labels.
- Validate on blur or submit, never on first keystroke; error text names the fix ("Use at least 8
  characters"), not the violation code.
- Preserve user input through every failure. Losing a form to a validation round-trip is an instant
  credibility kill.
- Buttons state what they do ("Create invoice", not "Submit"); pending state on the button itself.
- 44px minimum touch targets; visible focus rings that match the brand system, not browser default blue.
- Autocomplete attributes, correct input types/modes, no disabled-submit-until-perfect patterns that hide
  what is wrong.

These states are where daily-use products earn "someone senior built this." They cost little; skipping
them is the single most common tell of unedited AI application code.

---

## PART 4: NARRATIVE ARCHITECTURE / MOTION SCRIPT

Award-winning cinematic sites are built like short films. Treat scroll as the primary narrative driver:
pinned story sections, clip-path unmasking, parallax depth, and sequential unfolding paced as one
cinematic sequence, not a pile of isolated effects.

### Motion Script ritual (before any code)

1. Break content into **scenes** (hero, reveal, deep-dive, CTA).
2. For each scene define **entry, hold, exit** plus the **emotional beat** (awe, trust, proof, invite).
3. Assign an **archetype** (below) and a **motion mode**: pinned scrub, infinite loop, simple reveal, or free scroll.
4. Storyboard scroll 0% / 25% / 50% / 100% against those beats.
5. Cap pin distance and count of simultaneous triggers before you write a single tween.

Architecture: `section -> pin -> timeline -> unpin -> next section`.
Not: `scroll -> fade -> scroll -> fade`.

### Scroll-story archetypes (map the brand to a proven shape)

| Archetype | What it feels like | Typical structure | Pin / loop budget | Beat count |
|-----------|--------------------|-------------------|-------------------|------------|
| **Timeline** | Chapters of a story | Sequential pinned scenes, scrubbed progress bar | 1 pin per chapter, ≤1500px each | 3–6 |
| **Orb / journey** | Camera travel through a concept | One long pin; camera or focal object moves through beats | Single pin 1200–2000px | 3–5 |
| **Product reveal** | Film-like product intro | Pinned media + kinetic type + CTA hold | 1 pin ≤1500px | 2–4 |
| **Infinite strip** | Seamless loop you never “finish” | Full-viewport sections + duplicate first section + Lenis `infinite` + snap | Loop, not pin; snap per section | 3+ (Codrops sweet spot) |
| **Phase / nodes** | Enterprise explainer | Hub + branch timelines (`paused: true`) or numbered phases | Light pins or free scroll | 4–8 |

Pick one primary archetype for the homepage. Mixing three archetypes on one page usually reads as chaos.

### Motion Script spreadsheet (shareable team artifact)

Extend the storyboard into a full Motion Script. One row per event. Approve this before generating components.

| Scroll % | Scene | Archetype mode | Trigger | Animation | Emotional beat | Performance note |
|----------|-------|----------------|---------|-----------|----------------|------------------|
| 0 | Hero | Product reveal | load | SplitText + bg scale | Awe | Eager LCP image only |
| 10 | Hero | Product reveal | scrub | Overlay opacity | Hold | Compositor only |
| 24 | About | Timeline | pin start | Portrait clip-path | Trust | Lazy image; reserved aspect |
| 48 | Scholarship | Timeline | scrub | Step index swap | Proof | Cap triggers; no layout props |
| 70 | Drive | Timeline | enter | Counters + collage | Proof | Reduced-motion: static numbers |
| 90 | Footer | Reveal | enter | Type + CTA | Invite | No pin |

A full cinematic page often needs **100–300 rows**. Empty cells are failures: if you cannot name the beat, cut the motion.

**Pin budget (2026 playbooks):** minimum useful pin ≈ half a viewport; rich 3-beat scene ≈ 1000–1500px;
user-tolerance ceiling ≈ **2000px**. Beyond that, users feel trapped even if the animation is good.

### Infinite-scroll storytelling (Codrops “Never Ending Story” pattern)

When the brief wants a continuous strip rather than a finite page:

1. Fullscreen sections (`100svh`, not `100vh`, for mobile Safari toolbar stability).
2. Duplicate the first section at the end; mark the duplicate `aria-hidden="true"`.
3. Lenis `{ infinite: true }` (+ Snap plugin for mandatory section rhythm).
4. Scrubbed parallax on media inside each section (`yPercent -50 → 50`, `ease: 'none'`).
5. On iOS, nest Lenis in a fixed `wrapper`/`content` and use `ScrollTrigger.scrollerProxy` so the loop seam
   does not flash when the toolbar expands.

This is a deliberate archetype, not a default. Skip it for content/docs sites and for any experience that
needs deep reading, forms, or native anchor navigation as primary UX.

---

## PART 5: THE MOTION SYSTEM (2026 STACK)

Premium feel comes from disciplined motion direction, not exotic shaders. Pick the lightest stack that
fits the job.

### Decision tree (2026)

| Site type | Ship |
|-----------|------|
| Docs / content / dashboard | Native scroll. CSS only. Skip Lenis. |
| Marketing page with simple reveals | **CSS scroll-driven animations** (`animation-timeline: view()` / `scroll()`). Zero JS. |
| Landing with pins, scrub, multi-beat storytelling | **Lenis + GSAP ScrollTrigger** (+ SplitText as needed). |
| Also needs React layout/modal transitions | Add **Motion** (formerly Framer Motion) for component enter/exit only. |
| True 3D required by content | Add Three.js / R3F as an island, never decorative. |

### Licensing and packages (important 2025 change)

- **GSAP (including previously Club plugins like SplitText, ScrollSmoother, MorphSVG) has been free for
  commercial use since 2025-04-30** after Webflow's acquisition. You no longer need Club for SplitText.
- Package name for smooth scroll is **`lenis`** (Darkroom Engineering). `@studio-freight/lenis` is retired.
- Lenis v1+ dropped `smoothTouch`; use `syncTouch: true` when you need touch smoothing.
- Do **not** run Lenis and GSAP ScrollSmoother together.
- If driving Lenis from `gsap.ticker`, do **not** also enable Lenis `autoRaf` (two rAF loops).

### Canonical Lenis ↔ GSAP sync

```javascript
// lib/lenis-setup.js
import Lenis from 'lenis'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)
ScrollTrigger.config({ ignoreMobileResize: true }) // prevents mobile URL-bar resize jank

export function initSmoothScroll() {
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
    // syncTouch: true, // only if you intentionally smooth touch
  })

  lenis.on('scroll', ScrollTrigger.update)
  gsap.ticker.add((time) => lenis.raf(time * 1000)) // seconds → ms
  gsap.ticker.lagSmoothing(0) // mandatory with Lenis or scroll anims lag
  return lenis
}
```

Miss any of the three sync steps and scroll decouples from animation. That is the #1 2025–2026 failure mode.

### CSS scroll-driven animations (use for the simple 80%)

Native `animation-timeline: scroll()` / `view()` runs on the compositor with **0 kB JS**. Use for fade-on-
enter, progress bars, light parallax. Keep GSAP for pinning, multi-element choreography, callbacks,
video/WebGL sync, and identical behavior across browsers that still lag on CSS timelines.

```css
@media (prefers-reduced-motion: no-preference) {
  @supports (animation-timeline: view()) {
    .reveal {
      animation: fade-up linear both;
      animation-timeline: view();
      animation-range: entry 0% cover 40%;
    }
  }
}
@keyframes fade-up {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

### Pinned, scrubbed scenes (GSAP)

```javascript
export function pinnedReveal(sectionRef) {
  return gsap.timeline({
    scrollTrigger: {
      trigger: sectionRef,
      start: 'top top',
      end: '+=1500', // stay under ~2000px user-tolerance ceiling
      pin: true,
      scrub: 1,
    },
  })
  .to('.product-image', { scale: 1.4, ease: 'none' })
  .to('.overlay-text', { opacity: 1, y: 0, ease: 'power2.out' }, 0.3)
}
```

Inside a pin, use `scrub` (scroll-linked), not duration-based autoplay.

### Layered parallax

Foreground ~1.0x, mid ~0.5–0.6x, background ~0.2–0.3x. On mobile keep factors ~0.2–0.4x.

### Typography motion

Use SplitText (now free) or a custom splitter for line/char reveals. Prefer `power4.out` / `expo`, never
`ease-in-out` as a house default. Ban decorative uniform fades.

### Accessibility floor (ship first)

Animation that ignores vestibular disorders is an accessibility failure, not a taste trade-off.

- Wrap GSAP setups in `gsap.matchMedia()` with `(prefers-reduced-motion: no-preference)`.
- Disable Lenis (`lenis.stop()` / do not init) when reduced motion is preferred; resume native scroll.
- Put CSS scroll-driven rules inside `@media (prefers-reduced-motion: no-preference)`.
- Ship the static path first; the animated path is enhancement.

### Easing and timeline hygiene

Define a small easing set (`power4`, `expo`, custom cubic-bezier) and reuse it. Build one timeline file per
scene. Use position parameters (`+=`, `-=`) instead of hardcoded delays. Centralize `gsap.registerPlugin`
in one config file.

---

## PART 6: IMMERSIVE MEDIA AND 3D

Award-level work in 2026 often pairs scroll choreography with scoped 3D or deep video, not decorative blobs.
Codrops/Awwwards case studies (scroll-driven Three.js worlds, persistent global canvases, Lenis-synced camera
moves) treat media as narrative infrastructure. Your job is to decide **when** that weight is justified.

### When to reach for what

| Need | Tool | Rule |
|------|------|------|
| Stacked card flips, tilt, z-depth | **CSS 3D** (`perspective`, `rotateX/Y`, `translateZ`) + ScrollTrigger | Prefer first. Zero WebGL cost. |
| Product viewer, architectural scene, scroll-driven camera world | **Three.js / R3F** as a client island | Only if content *is* the 3D. |
| Cinematic product/brand film on scroll | **Pinned HTML5 video** scrubbed by scroll | Often higher impact than light 3D. |
| Fake 3D rotation without a renderer | **Frame sequence** on canvas, scrubbed by progress | Encode once; ship optimized frames. |
| Decorative floating blobs / unrelated mesh | **Do not ship** | This is AI-slop adjacent. Cut it. |

### Island rules (non-negotiable)

- Mount WebGL as an **island**: lazy-loaded, below or at the scene that needs it, destroyed on unmount.
- Prefer a **persistent global canvas** only when navigation must feel like one continuous camera take
  (Awwwards pattern: canvas outside the App Router so routes do not remount the world). Otherwise keep
  scenes local and cheap.
- Drive camera/object transforms from the **same scroll progress** as GSAP/Lenis. One clock. No second
  scroll listener fighting Lenis.
- Compress assets: **KTX2/Basis** textures, **Draco** GLTFs, GPU instancing for repeats, lower-res shaders
  on mobile.
- Cap complexity: if the scene cannot hold 60fps on a mid-tier phone with reduced effects, cut polygons or
  fall back to CSS 3D / video / stills.

### Scroll-controlled video pattern

```javascript
// Pinned section; scroll owns playback. Pause native play.
video.pause()
video.setAttribute('playsinline', '')
video.muted = true // autoplay policies; sound is a separate UX choice

function initScrollVideo() {
  ScrollTrigger.create({
    trigger: '.video-pin',
    start: 'top top',
    end: '+=1500',
    pin: true,
    scrub: 1,
    onUpdate(self) {
      if (!video.duration) return
      video.currentTime = self.progress * video.duration
    },
  })
}

if (video.readyState >= 1) initScrollVideo()
else video.addEventListener('loadedmetadata', initScrollVideo, { once: true })
```

**Reduced-motion / no-WebGL fallbacks:** swap to a still poster, a short autoplay loop without scrub, or a
static frame strip. Never leave a blank canvas.

**Encode:** WebM (VP9/AV1) + MP4 fallback; explicit width/height; preload metadata only until the pin
approaches; reserve aspect-ratio to protect CLS.

### CSS 3D reveal cards (high-end without shaders)

Use a perspective parent and scrub `rotateX` / `z` on stacked cards. Keep transforms compositor-only. This
is the right answer for many “team / chapter stack” moments that would otherwise drag in Three.js for no
content reason.

---

## PART 7: INTERACTION SYSTEM (CURSORS, MICRO-INTERACTIONS, TRANSITIONS)

Scroll narrative is the spine. The skin is a small, consistent interaction grammar. Award sites look
premium because they reuse **one** cursor system, **3–5** hover signatures, and **one** transition dialect
across pages, not because every button invents a new trick.

### Cursor system (one style, multiple states)

Pick a single follower (dot, ring, or soft blob) with lerp toward the pointer. Add context states, not new
cursors per section:

| State | When | Behavior |
|-------|------|----------|
| Default | Rest | Small follower, low opacity |
| Hover interactive | Links, buttons | Scale up / ring expand |
| Hover media | Images, video | “View” / mix-blend or invert |
| Drag / scrub | Sliders, horizontal strips | Change shape to hint drag |
| Reduced motion / touch | `prefers-reduced-motion` or coarse pointer | **Hide custom cursor; restore native** |

Rules: never block text selection or native hit targets; `pointer-events: none` on the follower; disable on
touch devices (`(pointer: fine)` only). Custom cursors are garnish. If they hurt INP or a11y, cut them.

### Canonical hover signatures (allowlist)

Ship at most five. Document where each is legal.

1. **Magnetic** — button/link eases toward pointer within a short radius; elastic return on leave.
2. **Reveal** — image or text unmasks on hover (`clip-path` / overlay wipe). Content pages only where it
   aids scanning.
3. **Lift** — subtle `y` + shadow on cards that are actual interactive units (not decorative cards).
4. **Underline / fill** — typographic hover for text links; prefer this over scale spam in body copy.
5. **Tilt** — light `rotateX/Y` on media tiles; disable on touch and reduced motion.

Ban: hover that moves layout (margin/height), hover that autoplays sound, hover that requires precision
targets smaller than 44px.

### Page transitions

Pick one grammar for the whole product:

| Pattern | Best for | Implementation notes |
|---------|----------|----------------------|
| Crossfade + slight motion | Marketing multi-page | View Transitions API or Motion `AnimatePresence` |
| Shared element (list → detail) | Case studies, products | View Transitions `share-element` / Motion layoutId |
| Wipe / zoom | Portfolio bravado | GSAP timeline on route change; keep under ~600ms |
| Continuous camera (global canvas) | 3D world sites | Do not unmount WebGL; animate camera instead of DOM swap |

**Next.js:** run exit animation → navigate → enter; call `ScrollTrigger.refresh()` and `lenis.scrollTo(0, { immediate: true })` on pathname change. Hydration mismatches will desync pins if you init Lenis twice.

**Anti-slop tie-in:** inconsistent cursors, five different hovers, and a different transition every route are
premium-looking chaos. Audit them as hard as indigo gradients.

---

## PART 8: STACK BLUEPRINTS (NEXT.JS, WEBFLOW, VANILLA)

Same motion laws; different wiring. Use the lightest blueprint that matches the delivery environment.

### Next.js 15/16 App Router blueprint

1. Install: `npm install gsap lenis @gsap/react` (package is `lenis`, import React helpers from `lenis/react`).
2. Create a client `SmoothScroll` provider with `ReactLenis` and **`autoRaf: false`** when syncing to GSAP.
3. Connector effect: `lenis.on('scroll', ScrollTrigger.update)`, `gsap.ticker.add(t => lenis.raf(t * 1000))`,
   `gsap.ticker.lagSmoothing(0)`. Remove both on cleanup.
4. Wrap in `app/layout.tsx` only if the whole marketing surface needs smooth scroll. Skip on docs/dashboard
   routes.
5. Register `ScrollTrigger` once at module scope. Use `useGSAP` for scene timelines so Strict Mode cleanup
   is correct.
6. On `usePathname()` change: `lenis.scrollTo(0, { immediate: true })` + `ScrollTrigger.refresh()`.
7. Keep Server Components as default; mark motion islands `'use client'`. Persistent WebGL canvas, if any,
   mounts outside route segments so navigation does not remount the world.
8. Respect reduced motion before creating Lenis (do not init; use native scroll).

### Webflow + Lenis outline

1. Designer owns structure, type, and CMS. Scripts own scroll math.
2. Init Lenis once on `page` load / Webflow `IX2` ready. Do not also enable Webflow’s native smooth scroll
   on the same page (double scroll handling).
3. Sync Lenis → GSAP with the same three-step ticker pattern. Scope ScrollTriggers to page or symbol roots
   and kill them on Webflow page transitions / IX destroy hooks.
4. Prefer designer interactions for simple hovers; reserve GSAP for pins, scrub, and media sync.
5. Test published domain on real iOS Safari; Webflow preview is not enough for address-bar / `svh` issues.

### Vanilla JS reference (framework-optional)

You can hit award-level motion without React. Codrops-style builds prove it:

- HTML sections + CSS layout tokens.
- One `main.js`: Lenis init, Snap if infinite, ScrollTrigger scenes as plain functions.
- Duplicate section for infinite loops; `aria-hidden` on clones.
- No framework hydration tax; still ship reduced-motion CSS and focus states.

Use vanilla when the site is a campaign microsite or you are reverse-engineering an effect. Use Next.js when
you need routing, CMS, or a persistent 3D world across pages.

### CI/CD gotchas by stack

- **Next.js:** route transitions and streaming hydration can fire before layout; refresh ScrollTrigger after
  fonts (`document.fonts.ready`) and after pathname changes. Avoid initializing Lenis in both layout and page.
- **Webflow:** align custom script order after jQuery/Webflow IX; re-bind after CMS pagination or lightbox
  DOM swaps.
- **All stacks:** Playwright baselines per route; assert reduced-motion static path; Lighthouse budgets for
  LCP/INP/CLS on the heaviest cinematic URL, not only the blog.

---

## PART 9: PERFORMANCE-FIRST RULES (2026 CORE WEB VITALS)

**Current Core Web Vitals (FID is retired).** Google scores field data at the **75th percentile**:

| Metric | Good | Notes |
|--------|------|-------|
| **LCP** | ≤ 2.5s | Preload hero, `fetchpriority="high"`, no lazy on LCP image, WebP/AVIF |
| **INP** | ≤ 200ms | Replaced FID (Mar 2024). Break long tasks >50ms; reduce scroll-bound JS |
| **CLS** | ≤ 0.1 | Explicit width/height or `aspect-ratio` on media; `font-display: swap` |

Lenis itself is tiny (~3 kB gzipped) and usually does not hurt LCP directly. Risk is **INP/CLS** during
scroll: too many triggers, layout thrash, or decode work felt through the hijacked scroll loop. Audit Lenis
sites for INP and CLS, not only LCP.

Hard rules:

- Only animate `transform`, `opacity`, `clip-path`, `mask`, `filter`. Never `top/left/margin/height`.
- Reserve dimensions for every image/video/canvas before load.
- `will-change: transform` only on elements about to animate; remove when idle.
- Wrap GSAP in `gsap.context()` + `ctx.revert()` on unmount. Do not store animation progress in React state.
- `gsap.matchMedia()` for breakpoint-specific configs. Call `ScrollTrigger.refresh()` once after init.
- `ScrollTrigger.config({ ignoreMobileResize: true })` on mobile to stop address-bar resize thrash.
- Lazy-load below-the-fold and 3D islands. Tree-shake GSAP plugins to what you use.
- Prefer CSS scroll-driven for trivial reveals so the main chunk stays small.

### Build-test loop

One scene → real hardware → Performance panel + field CWV → 60fps → next scene. Reduced-motion path is
mandatory, not optional.

---

## PART 10: REVERSE-ENGINEER TO LEVEL UP YOUR TASTE

Treat premium sites as software systems. Reconstruct architecture; do not copy assets.

1. Toolkit: Animations, Layers, Performance, Rendering (Paint Flashing), Spector.js, Wappalyzer, Scroll-Driven Animations Debugger.
2. Detect stack: `window.gsap`, Network for `gsap`, `lenis`, `_next/static`, CSS `animation-timeline`.
3. Record before inspecting. Per frame, premium sites usually change only transform/opacity/mask/filter/video time/shader uniforms.
4. Map a scroll% → trigger → animation spreadsheet.
5. Pretty-print Sources; search `ScrollTrigger`, `scrub`, `pin`, `SplitText`, `lenis`.
6. Paint Flashing: green = bad repaint. Compositor-only motion is the goal.
7. Rebuild one interaction at a time until indistinguishable, then expand.

---

## PART 11: THE PROMPTING SYSTEM

Treat the agent like a studio brief, not a search engine. Never ask for the whole site in one shot.

### Master brief (customize brackets)

```
ROLE
You are a senior creative technologist at an Awwwards-level studio. You build web experiences
with restrained, purposeful craft at every tier, from docs portals to cinematic campaign sites.
Zero tolerance for 2026 AI-default output.

PROJECT
Build a [type of site] for [brand/mission]. Grounded in [real photography / real content].
Reference feel: [cinematic-emotional OR enterprise-precise OR editorial-calm].

EXECUTION TIER (Universal Router)
This surface is tier [T0 static | T1 editorial | T2 cinematic | T3 immersive].
- Apply ALL universal invariants (identity, states, a11y, CWV, copy) regardless of tier.
- Use ONLY the motion techniques allowed at this tier. Techniques above the tier are violations
  of restraint, not bonuses. [List per-surface tiers if the project has multiple, e.g.
  "homepage T2, product pages T1, checkout T0".]

HARD EXCLUSIONS (reject on sight)
- No blue/indigo/purple-pink gradients (#3b82f6, #6366f1, from-purple-500 to-pink-500, etc.)
- No Inter or Roboto as the only typeface. One display + one body; justify the pairing.
- No centered hero with generic SaaS copy. Headline names the specific mission in [X] words.
- No three-equal-card grids / Lucide Zap-Shield-Rocket feature rows. Asymmetric hierarchy required.
- No decorative fade-ins or transition-all duration-300 ease-in-out spam. Motion is scroll-scrubbed
  or interaction-triggered only.
- No plastic 3D blobs or stock AI imagery. Real asset slots only.
- No buzzwords: seamless, cutting-edge, unlock, elevate, robust, best-in-class, leverage, delve,
  holistic, transformative, empower. No "It's not just X — it's Y." Minimize em dashes.
- No emoji bullets. Clean code: real alt, real meta + OG, semantic HTML, visible focus states.

DESIGN DIRECTION
- Color: author in OKLCH [values]; expose CSS tokens; hex fallbacks OK. No default Tailwind palette.
- Typography: [display] + [body].
- Layout: [explicit section order]. At least one deliberate symmetry break.
- Motion: power4/expo/custom bezier. Never ease-in-out as default. Only transform/opacity/
  clip-path/mask/filter.

TECHNICAL STACK (2026)
- [Next.js / Vite] + React
- GSAP (free, including SplitText) + ScrollTrigger for pins/scrub/choreography
- CSS scroll-driven animations for simple reveals (0 JS) where they suffice
- Lenis package `lenis`, synced to gsap.ticker + lagSmoothing(0); ignoreMobileResize: true
- Tailwind v4 with @theme custom tokens only
- Three.js / R3F only if content requires 3D

SCROLL ARCHITECTURE (T2+ surfaces only; omit for T0/T1)
[N] scenes with entry/hold/exit. At least one pinned scrub scene. Pin scroll distance ≤ ~2000px.
Describe each scene before any code.

INTERFACE STATES (all tiers; mandatory for T0 app surfaces)
Design empty/loading/error/partial/success for every data surface before building it.
Skeletons match real layout; errors name the fix; input is never lost.

ACCESSIBILITY + PERFORMANCE
- Ship prefers-reduced-motion static path first (gsap.matchMedia / Lenis off / CSS media query)
- CWV targets: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1
- gsap.context() cleanup; no layout-property animation

BEFORE YOU WRITE CODE
T2+: output scroll% → trigger → animation storyboard for approval first.
T0/T1: output the screen/section inventory with states per surface for approval first.
Do not generate components until I approve it.
```

### Phase prompts

1. **Foundation:** Tailwind v4 `@theme` with ONLY brand OKLCH/hex + fonts. Install `gsap` + `lenis`
   (T2+ only). Wire ticker sync. No default indigo/blue identity tokens.
2. **Hero / first screen only:** Asymmetric layout, specific copy; at T2+ use SplitText/`power4.out`.
   Show alone before continuing.
3. **Scene/screen N only:** Reuse `/lib/animations` (or the state components at T0). Describe the
   connection to N+1 before coding.
4. **Polish:** Fix ease-in-out, non-compositor props, CLS, buzzwords, off-palette gradients, missing
   states.
5. **God-tier gate:** Part 13 prompts (anti-slop + tier-aware excellence).

---

## PART 12: PRODUCTION HARDENING

### Semantic / SEO / answer-engine readiness

- Semantic HTML, one `h1`, skip link, focus states.
- Unique title/description, canonical, real OG image with dimensions.
- JSON-LD from data files; NAP/entity consistency everywhere.
- Speakable summary near top of `<main>`, FAQ via `<details>/<summary>`, optional `llms.txt`.

### CI/CD

PR → Preview; main → Production. Gate on lint, typecheck, unit tests, Playwright visual baselines,
Lighthouse CI (LCP/INP/CLS budgets), then deploy.

### Visual testing

Chromium + Firefox + WebKit at 390 / 768 / 1440 / 1920. Wait for DOM state, not blind timeouts.
Safari remains the highest-risk motion browser; test real devices.

### Monitoring

Sentry + Session Replay for silent ScrollTrigger/WebGL failures. Error boundaries around 3D/heavy GSAP
with static fallbacks. Upload source maps.

### Hygiene

Pin GSAP/Lenis/Three versions. Source assets outside git; commit optimized exports only. One animation
file per scene under `/lib/animations`.

---

## PART 13: THE GOD-TIER GATE (ANTI-SLOP + TIER-AWARE EXCELLENCE)

Anti-slop removes fingerprints; the excellence checklist verifies premium signals are present *for your
tier*. Run both, always. A site passes the gate only when it has zero slop violations **and** scores strong
on every criterion its tier requires.

### Anti-slop audit prompt (universal, every tier)

```
Audit codebase + rendered output against the 2026 AI-slop checklist:
- Zero blue/indigo/purple-pink signature gradients (#3b82f6, #6366f1, purple→pink, etc.)
- Only the two chosen fonts; no silent Inter/system default for display
- No three-equal-card feature grids; no Lucide Zap/Shield/Rocket stamp pattern
- No transition-all duration-300 ease-in-out spam; motion is scrubbed or interaction-triggered
- No copy using: seamless, cutting-edge, unlock, elevate, robust, best-in-class, leverage,
  delve, holistic, transformative, empower, "in today's [x] world", "It's not just X — it's Y"
- Em dashes minimized; real alt text; real meta + custom OG image
- Cursor/hover/transition grammar is ONE system (not a new trick per section)
- Every data surface has designed empty/loading/error/partial/success states (no default spinners,
  no "Something went wrong")
Report every violation and fix it.
```

### Tier-aware excellence checklist

Score each 0–2 (missing / weak / strong). "Required" cells must reach 2 before the build ships; "—" means
the criterion does not apply at that tier and adding it would *hurt* (a pinned scene on a docs site is a
violation, not a bonus).

| Criterion | T0 static | T1 editorial | T2 cinematic | T3 immersive | Strong looks like |
|-----------|-----------|--------------|--------------|--------------|-------------------|
| Distinct identity (color+type+layout decision) | Required | Required | Required | Required | Could not be mistaken for a template |
| Interface states + form craft | Required | Required | Required | Required | All five states designed per Part 3 |
| Accessibility (reduced-motion, keyboard, contrast) | Required | Required | Required | Required | OS-toggle verified; zero traps |
| Performance (LCP/INP/CLS) | Required | Required | Required | Required | Green field data on heaviest page |
| Copy specificity | Required | Required | Required | Required | Headlines fit no other company |
| Editorial reveal moments (CSS scroll-driven) | — | Required | Required | Required | Reveals tied to meaning, not decoration |
| Cinematic scroll sequence (pin + scrub) | — | — | Required | Required | ≥1 pinned scene, entry/hold/exit, ≤2000px |
| Kinetic typography | — | Optional | Required | Required | SplitText/mask reveal on the thesis line |
| Interaction grammar (cursor/hover/transitions) | Focus rings + 1 hover | ≤3 signatures | Full system | Full system | One documented grammar sitewide |
| Immersive media (video scrub / CSS 3D / WebGL) | — | Optional | Optional | Required | Justified by content; static fallback |
| Depth / atmosphere | — | One layer max | Restrained layers | Restrained layers | Grain/parallax serving the story |

### Excellence audit prompt (run with anti-slop)

```
This build targets tier [T0|T1|T2|T3] per the Universal Router. Score it 0-2 on every criterion the
tier requires: identity, states/forms, a11y, performance, copy, [reveals, cinematic scroll, kinetic
type, interaction grammar, immersive media, atmosphere as applicable]. Flag any technique present
ABOVE the declared tier (e.g. pins on a T0 surface) as a violation of restraint. For every score < 2,
propose a concrete fix that does not reintroduce AI-slop fingerprints. Do not add WebGL unless
content requires it.
```

### Functional
- ScrollTriggers correct on first load (not only after resize).
- Cleanup after navigate-away ×10 (no leaks).
- Lenis disabled path works; anchors/keyboard still work.
- CTAs/forms work inside pinned sections.
- Custom cursor never traps focus or breaks touch.

### Performance
- Field or throttled mobile: **LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1**.
- Paint Flashing shows minimal repaint.
- GSAP tree-shaken; CSS used for trivial reveals where possible.
- Video/WebGL islands lazy; static fallbacks present.

### A11y
- OS-level reduced-motion verified.
- Keyboard through every hijacked/pinned section.
- Contrast on final rendered overlays.
- Infinite-loop clones are `aria-hidden`.

### Content
- Real meta/OG. Descriptive alt. Styled 404.

### Reverse-engineering feedback loop

For each award site you study (Part 10: reverse-engineering), mark which checklist rows it hits and *how*
(CSS 3D vs WebGL, infinite strip vs timeline, cursor states). Feed those patterns into your next Motion
Script instead of copying assets.

---

## APPENDIX A: ONE-SCREEN CHEAT SHEET

**Route:** classify verb (feel/evaluate/buy/read/do) → pick tier per surface (T0 static / T1 editorial /
T2 cinematic / T3 immersive) → lower tier executed perfectly beats higher tier executed poorly.

**Ban (every tier):** blue/indigo/purple-pink signature, Inter-only, centered generic hero, three equal
cards, uniform fades / `ease-in-out` spam, decorative 3D blobs, stock AI imagery, buzzwords, "not just
X — it's Y," em-dash confetti, boilerplate meta, random per-page cursors/transitions, default spinners
and "Something went wrong" states.

**Do (every tier):** OKLCH tokens + Tailwind v4 `@theme`, display+body pairing, one deliberate layout
decision, real assets, all five interface states designed, WCAG 2.2 AA + reduced-motion path first.

**Do (T1+):** CSS scroll-driven reveals tied to meaning. **Do (T2+):** Motion Script + archetype first,
Lenis+GSAP pins/scrub, kinetic type, one interaction grammar. **Do (T3):** justified video/CSS 3D/WebGL
islands with static fallbacks.

**Order:** route → concept → design system → Motion Script (T2+) or screen inventory (T0/T1) →
scene-by-scene → immersion/interaction polish → god-tier gate (anti-slop + tier-aware excellence).

**Stack (2026):** lightest tool that fits. CSS timelines when enough. Else `lenis` + free GSAP/ScrollTrigger/
SplitText. Next.js App Router client islands for marketing; Webflow+Lenis when designer-led; vanilla when
campaign-simple. Motion for React UI transitions. R3F only when content needs 3D.

**CWV:** LCP ≤ 2.5s · INP ≤ 200ms · CLS ≤ 0.1 (FID is dead).

**Core principle:** god-tier = the right tier, executed with total discipline: explicit taste decisions,
designed states, coherent interaction grammar, zero AI fingerprints. Never exotic shaders for their own sake.

---

## APPENDIX B: SOURCES (2025–2026 ONLY)

### AI visual / copy fingerprints
- [Why Every AI-Generated Website Looks the Same — Sailop](https://sailop.com/blog/why-every-ai-generated-website-looks-the-same) (Inter ~73%, blue/indigo defaults, grid-cols-3)
- [Tailwind Blue, Purple Gradient, 3 Cards: The Visual Signature of AI in 2026 — Sailop](https://sailop.com/blog/tailwind-blue-purple-gradient-ai-signature-2026) (~71% three-card landings; v0/Lovable/Bolt signature rates)
- [Why AI Design Looks Generic (2026) — Superdesign](https://www.superdesign.dev/blog/why-ai-design-looks-generic)
- [Why Every AI-Built Website Looks the Same (Indigo-500) — Authon](https://blog.authon.dev/why-every-ai-built-website-looks-the-same-blame-tailwinds-indigo-500) (Aug 2025 Wathan context)
- [35 AI design fingerprints — UX Skill](https://uxskill.laithjunaidy.com/blog/ai-design-fingerprints-list.html)
- [10 AI writing patterns — SwissGlobal](https://swissglobal.ch/en/blog/10-ai-writing-patterns-that-make-your-copy-sound-like-everyone-elses/)
- [slop-gate](https://github.com/hwajongpark/slop-gate) / [slop-radar](https://github.com/renefichtmueller/slop-radar) (em dash + buzzword scanners)
- LinkedIn / editorial notes on **"It's not just X — it's Y"** as a 2025 AI sentence tell

### Motion stack 2025–2026
- [Immersive web stack in 2026: Lenis, GSAP, and what to skip — Adamarant](https://adamarant.com/en/blog/immersive-web-stack-in-2026-lenis-gsap-and-what-to-skip) (May/Jun 2026; GSAP free since 2025-04-30; CSS timelines; reduced-motion floor)
- [Lenis official GSAP ScrollTrigger setup — GitHub](https://github.com/darkroomengineering/lenis)
- [Lenis ScrollTrigger ticker fix — JRV Systems](https://jrvsystems.app/blog/lenis-scrolltrigger-gsap-ticker-fix)
- [Scroll experience playbook — ai-web-design-codex](https://github.com/Eneryleen/ai-web-design-codex/blob/main/09-playbooks-and-checklists/playbook-scroll-experience.md) (`ignoreMobileResize`, pin ceilings, `syncTouch`, no dual rAF)
- [Scroll-Stop Animations: The 2026 Playbook — C&E](https://causeandeffectsp.com/blog/scroll-stop-animations-2026-playbook/)
- [CSS scroll-driven vs GSAP — css-scroll-driven.com](https://www.css-scroll-driven.com/core-animation-fundamentals-browser-mechanics/the-rendering-pipeline-for-scroll-animations/css-scroll-driven-animations-vs-gsap-scrolltrigger/)
- [Scroll-Triggered Animation Playbook 2026 — Aidxn](https://aidxn.com/blog/scroll-triggered-animations/)
- [CSS Scroll-Driven Animations patterns 2026 — Solid Web](https://solid-web.com/css-scroll-driven-animations-tutorial/)
- [The Never Ending Story: Infinite scroll with GSAP & Lenis — Codrops (2026-05-28)](https://tympanus.net/codrops/2026/05/28/the-never-ending-story-building-a-seamless-infinite-scroll-experience-with-gsap-lenis/)
- [Architecture behind Trionn: GSAP + Three.js + Lenis + Web Audio — Codrops (2026-07-15)](https://tympanus.net/codrops/2026/07/15/the-architecture-behind-trionn-coordinating-gsap-three-js-lenis-and-web-audio/)
- [Scroll-driven 3D portfolio world — Codrops (2026-04-28)](https://tympanus.net/codrops/2026/04/28/more-than-a-portfolio-building-a-scroll-driven-3d-world-with-something-to-say/)
- [Smooth scrolling in Next.js with Lenis & GSAP (2026) — DevDreaming](https://devdreaming.com/blogs/nextjs-smooth-scrolling-with-lenis-gsap)
- [gsap.matchMedia() docs](https://gsap.com/docs/v3/GSAP/gsap.matchMedia/)
- [prefers-reduced-motion — web.dev](https://web.dev/articles/prefers-reduced-motion)

### Color / Tailwind
- [Build a Color System for Web Design in 2026 — Social Animal](https://socialanimal.dev/blog/build-color-system-web-design-2026/) (OKLCH ~96% support; WCAG 2.2 AA + APCA)
- [Design System with OKLCH — VBCreation](https://vbcreation.io/en/blog/design-system-oklch/)
- [How to Use OKLCH in CSS (2026) — HexPickr](https://hexpickr.com/learn/oklch-css-guide)
- [Tailwind CSS v4.0 announcement](https://tailwindcss.com/blog/tailwindcss-v4)
- [Tailwind v4 theming discussion](https://github.com/tailwindlabs/tailwindcss/discussions/18471)

### Core Web Vitals 2026
- [Web Vitals — web.dev](https://web.dev/articles/vitals) (LCP / **INP** / CLS; FID retired)
- [How to Audit Core Web Vitals in 2026 — SEOJuice](https://seojuice.com/blog/core-web-vitals-2026-audit-changes/)
- [Core Web Vitals 2026 thresholds — Web Help Agency](https://webhelpagency.com/blog/core-web-vitals-2026/)

Re-audit this guide when GSAP licensing, Lenis APIs, CSS scroll-timeline browser support, or CWV
thresholds change. Prefer field CrUX over lab-only scores.
