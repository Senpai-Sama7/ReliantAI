# ReliantAI Design System

**Revenue Engine v6 · Dark-First · Sharp Corners · Monospace Data**

ReliantAI is a unified platform of 15+ integrated business applications sharing common infrastructure for authentication, event coordination, and secure communication. From AI-powered document processing to HVAC dispatch automation, every system shares the same foundation for seamless data flow.

**Owner:** Douglas Mitchell, Houston TX  
**Tagline:** "Leads contacted in seconds. Not hours."  
**Business Hook:** HBR research — leads contacted within 60 minutes are 7× more likely to qualify. ReliantAI responds in seconds vs. industry average 24–48 hours.

---

## Sources

- **Codebase:** `integration/` — Integration Layer (Auth, Event Bus, API Gateway, Saga Orchestrator, Observability). Mounted via File System Access API. Contains Kong gateway routes to all 15 services, JWT auth with RBAC, Redis Streams event bus, Saga orchestration, and Metacognitive Autonomy Layer architecture.
- **Design Tokens:** `uploads/design-tokens.css` — Revenue Engine v6 token spec. The single source of truth for all visual decisions. Full product brief embedded.
- **No Figma link was provided.**

---

## Products

| Service | Accent | Status | Description |
|---------|--------|--------|-------------|
| **ClearDesk** | `#00d4aa` teal | 🟢 Active customer | AI-powered AR document processing, confidence scoring, escalation system |
| **Money** | `#ffc400` gold | 🟡 Tested & verified | HVAC AI dispatch automation, CrewAI multi-agent, 7× lead stat |
| **B-A-P** | `#00e5ff` cyan | 🟡 Tested & verified | Business analytics platform, ETL pipeline, AI insights, forecasting |
| **APEX** | `#7c5cfc` purple | 🟡 Tested & verified | 5-layer probabilistic autonomous agent OS with HITL and uncertainty viz |
| **Integration Layer** | `#00ff7a` green | ✅ Fully operational | Auth, API gateway, event bus, saga orchestration, observability |

**Stack context:**
- ClearDesk: React 19 + TypeScript + Vite + Tailwind 4 + Recharts
- Money: FastAPI + CrewAI + PostgreSQL + Twilio
- B-A-P: FastAPI + SQLAlchemy + Celery + Redis + Recharts
- APEX: Next.js 15 App Router + TypeScript
- Integration: Python/FastAPI + Kong + Redis Streams + Kafka + Prometheus/Grafana

---

## CONTENT FUNDAMENTALS

### Voice & Tone

ReliantAI copy is **professional, technical, and implementation-aware**. It reads like something a senior infrastructure engineer wrote for a technical founder — not a startup marketer.

- **Dense and specific.** Avoids vague summaries. Uses real field names (`dispatch_id`, `confidence_score`, `correlation_id`), real entity schemas, real API routes.
- **Deterministic.** Emphasizes certainty, safety, production-readiness. "Seconds, not hours." Not "faster responses."
- **No fluff.** Every sentence earns its place. Bullet points preferred over paragraphs in UI.
- **First-person avoidance in UI.** Labels like "Documents", "Dispatches", not "Your Documents", "Your Dispatches."
- **Title case for navigation.** Sentence case for descriptions and body copy.
- **Numbers are significant.** "7×", "0.93 confidence", "< 200ms", "$52,400" — monospace everywhere data appears.
- **Status language is precise.** `LIFE_SAFETY`, `EMERGENCY`, `URGENT`, `ROUTINE`. `PENDING`, `PROCESSING`, `ESCALATED`, `COMPLETED`. Never softened.
- **No emoji in product UI.** Status uses color-coded badges. Emoji only in outreach emails (sparingly).
- **Dual-language capability.** ClearDesk outputs both English and Spanish summaries. Treat bilingual as first-class.

### Examples

> "Leads contacted in seconds. Not hours."  
> "7× more likely to qualify. Seconds, not hours."  
> "INV-2025-0441 · Martinez HVAC Supply Co. · $52,400 · DUE 2025-05-01"  
> "Confidence: 0.94 · Epistemic: 0.12 · Aleatoric: 0.22"  
> "LIFE_SAFETY — 911 escalated. Owner notified."  
> "dispatch.completed · source: money · corr: a3f9-…"

### Casing

- Navigation items: Title Case
- Headings: Title Case or ALL CAPS for critical alerts
- Body, descriptions, labels: Sentence case
- Event types: `snake.dot.notation` (e.g., `dispatch.completed`)
- Status enums: `SCREAMING_SNAKE_CASE`
- IDs and codes: monospace, never truncated

---

## VISUAL FOUNDATIONS

### Color System

**Backgrounds** — layered dark navy-black surfaces:
- `--re-bg: #020510` — page background, deepest layer
- `--re-surface: #060c1a` — primary card/panel surface
- `--re-surface-hi: #091424` — elevated surface (modals, popovers)
- `--re-surface-pop: #0d1e35` — highest elevation (tooltips, dropdowns)

**Text** — carefully graded contrast:
- `--re-text-bright: #ffffff` — headings, critical values
- `--re-text: #a8c4de` — primary body text
- `--re-text-dim: #4a6880` — labels, secondary info
- `--re-text-muted: #1e3348` — placeholders, disabled

**Borders:**
- `--re-border: #0c1a2c` — default panel borders
- `--re-border-brt: #152637` — hover/active borders

**Accents** (disciplined use — never scattered):
- `--re-cyan: #00e5ff` — primary interactive, CTAs, active nav, B-A-P
- `--re-green: #00ff7a` — success, completed, healthy, Integration Layer
- `--re-gold: #ffc400` — Money service, revenue metrics, premium
- `--re-red: #ff3b5c` — critical, escalated, LIFE_SAFETY
- `--re-purple: #7c5cfc` — APEX, AI/ML surfaces
- `--re-teal: #00d4aa` — ClearDesk, document processing, confidence

### Typography

- **Display:** `Fraunces` — headings only (loaded from Google Fonts)
- **Sans:** `IBM Plex Sans` — all body, UI, labels, navigation
- **Mono:** `IBM Plex Mono` — all data values, IDs, codes, metrics, confidence scores

Type scale is disciplined: large display for hero moments, body at 13–14px for dense data tables, monospace at 12–13px for values.

### Spacing

Common spacing scale: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 48px, 64px.

### Corner Radii

**Sharp.** `border-radius: 0` for panels, cards, containers. `border-radius: 2px` for interactive elements (buttons, badges, inputs). Never rounded cards.

### Borders & Surfaces

- 1px solid borders using `--re-border` or `--re-border-brt`
- No drop shadows — elevation is communicated purely through background color stepping
- Inner glow on active accented elements: thin `box-shadow: inset 0 0 0 1px <accent>` or `0 0 8px <accent>30`
- No outer box-shadows on cards

### Backgrounds & Textures

- **No gradients** except subtle linear overlays at opacity 0–15% for hero sections
- **No background images** in the product UI (only the Money marketing site uses Ken Burns photo hero)
- **No patterns, textures, or illustrations** in the product UI
- Data-dense tables fill the viewport — surfaces are workspaces, not canvases

### Animation

- `150ms ease` — micro-interactions, hover color transitions
- `200ms ease` — panel reveals, badge state changes
- `300ms ease` — sidebar open/close, modal entrance
- **No bounces.** Strictly ease curves — feels precise, not playful
- Shimmer skeleton loaders for loading states (horizontal sweep animation)
- LIFE_SAFETY alerts pulse with CSS animation at 1s period

### Hover & Press States

- **Hover:** background lightens by one surface step (e.g., `--re-surface` → `--re-surface-hi`); border brightens to `--re-border-brt`; text-dim brightens to `--re-text`
- **Active/press:** background steps up again; subtle accent glow
- **Focus:** 1px outline in `--re-cyan` at 60% opacity, no offset
- **Disabled:** opacity 0.4, cursor not-allowed

### Iconography

Uses **Lucide** icon system (stroke-based, 1.5px weight, square aesthetic). See ICONOGRAPHY section below.

### Cards

Cards are rectangles. `border-radius: 0`. 1px border `--re-border`. Background `--re-surface`. Padding 16px or 24px. No shadows. Hover lifts to `--re-surface-hi` background. Active selected state adds 1px left border in accent color.

### Imagery

- The Money marketing site uses editorial dark photography (Ken Burns zoom)
- Product UI has no imagery — it's all data
- Color vibe: cool, blue-toned, dark. No warm photography.

### Use of Transparency & Blur

- Sidebar overlay on mobile uses `backdrop-filter: blur(8px)` with `rgba(2,5,16,0.85)`
- No frosted glass in the product UI desktop
- Alert banners use solid surface colors, not transparent

---

## ICONOGRAPHY

**System:** Lucide Icons (CDN: `https://unpkg.com/lucide@latest`)  
**Style:** Stroke-based, 1.5px stroke weight, square/geometric aesthetic, no fill  
**Size:** 16px in table rows/labels, 20px in navigation, 24px in headers  
**Color:** Inherits `currentColor` from text — uses `--re-text-dim` for inactive, `--re-text` for active, accent color for status indicators

**No custom icon font was found** in the integration codebase. Lucide is the closest CDN match to the stroke-weight and geometric precision expected by the design system.

**Common icons in use:**
- Navigation: `layout-dashboard`, `file-text`, `zap`, `cpu`, `layers`, `settings`, `credit-card`, `users`
- Status: `check-circle-2`, `alert-triangle`, `x-circle`, `clock`, `loader-2`
- Actions: `upload`, `download`, `search`, `filter`, `more-horizontal`, `chevron-right`
- Data: `bar-chart-2`, `trending-up`, `activity`, `database`

**No emoji in product UI.** No PNG icons. No colored icon circles. No icon-in-badge patterns.

---

## File Index

```
README.md                          ← This file
SKILL.md                           ← Agent skill definition

colors_and_type.css                ← CSS custom properties (tokens + semantic)

assets/                            ← Brand assets (no binary assets found in codebase)
  reliantai-logo.svg               ← Inline SVG wordmark
  cleardesk-mark.svg
  money-mark.svg
  apex-mark.svg
  bap-mark.svg

preview/                           ← Design System tab cards
  colors-backgrounds.html
  colors-text.html
  colors-accents.html
  colors-borders.html
  type-display.html
  type-body.html
  type-mono.html
  type-scale.html
  spacing-tokens.html
  spacing-in-use.html
  radius-borders.html
  shadows-elevation.html
  components-buttons.html
  components-badges.html
  components-inputs.html
  components-cards.html
  components-tables.html
  components-alerts.html
  brand-logos.html
  brand-service-marks.html

ui_kits/
  platform/                        ← ReliantAI Command Center + shared shell
    index.html
    Sidebar.jsx
    TopBar.jsx
    Dashboard.jsx
    EventStream.jsx
  cleardesk/                       ← ClearDesk document processing
    index.html
    StatsOverview.jsx
    DocumentCard.jsx
    DocumentDetail.jsx
    FilterPanel.jsx
  money/                           ← Money HVAC dispatch
    index.html
    AdminDashboard.jsx
    DispatchTable.jsx
    DispatchDetailModal.jsx
    AgentMonitor.jsx
  apex/                            ← APEX autonomous agent OS
    index.html
    HITLDashboard.jsx
    WorkflowRunner.jsx
    UncertaintyGauge.jsx
```
