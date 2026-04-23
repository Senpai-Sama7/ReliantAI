# ReliantAI Operator Console — Developer Handoff Spec

**Generated:** 2026-04-23  
**Console entry:** `console/index.html`  
**Design system:** `colors_and_type.css` · `console/tokens.css`  
**Stack target:** React 19 + TypeScript + Next.js 15 App Router + Tailwind 4

---

## Route → Component Map

| Path | Screen | Component | Group | API deps |
|------|---------|-----------|-------|----------|
| `/auth/signin` | Sign In | `AuthSignIn` | Auth | `POST /auth/token` |
| `/auth/mfa` | MFA | `AuthMFA` | Auth | `POST /auth/mfa/verify` |
| `/marketing` | Homepage | `MarketingHome` | Marketing | — |
| `/marketing/pricing` | Pricing | `MarketingPricing` | Marketing | — |
| `/console` | Command Center | `ConsoleHome` | Platform | `GET /services/health` · `GET /integration/events?limit=20` |
| `/cleardesk` | ClearDesk Landing | `ClearDeskLanding` | ClearDesk | — |
| `/cleardesk/queue` | Document Queue | `ClearDeskQueue` | ClearDesk | `GET /api/documents?status=&search=&page=` |
| `/cleardesk/upload` | Upload | `ClearDeskUpload` | ClearDesk | `POST /api/documents/upload` · `POST /api/analyze` |
| `/cleardesk/chat` | AI Chat | `ClearDeskChat` | ClearDesk | `POST /api/chat` (Claude Haiku 4.5 via proxy) |
| `/cleardesk/export` | Export | `ClearDeskExport` | ClearDesk | `GET /api/documents/export?format=&fields=` |
| `/cleardesk/settings` | Settings | `ClearDeskSettings` | ClearDesk | `GET /api/settings` · `PUT /api/settings` |
| `/money/admin` | Dispatch Dashboard | `MoneyAdmin` | Money | `GET /dispatches` · SSE `/dispatches/stream` |
| `/money/billing` | Billing | `MoneyBilling` | Money | `GET /billing/subscription` · Stripe Customer Portal |
| `/apex/overview` | APEX Overview | `ApexOverview` | APEX | `GET /workflow/completed` · `GET /agents` |
| `/apex/hitl` | HITL Review | `ApexHITL` | APEX | `GET /workflow/pending` · SSE `/workflow/stream` · `POST /workflow/hitl/{id}` |
| `/apex/workflows` | Workflow Runner | `ApexWorkflows` | APEX | `POST /workflow/run` · SSE `/workflow/run/{id}/stream` |
| `/apex/langfuse` | Trace Viewer | `ApexLangfuse` | APEX | `GET /traces` · `GET /traces/{id}/spans` |
| `/apex/tools` | Tool Bus | `ApexTools` | APEX | `GET /tools` · `POST /tools/call` |
| `/bap/analytics` | Analytics | `BAPAnalytics` | B-A-P | `GET /datasets` · `GET /etl/jobs` · `GET /insights` |
| `/bap/pipeline` | Pipeline Builder | `BAPPipeline` | B-A-P | `GET /etl/jobs/{id}` · SSE `/etl/jobs/{id}/stream` |
| `/bap/upload` | Dataset Upload | `BAPUpload` | B-A-P | `POST /datasets/upload` · `POST /datasets/{id}/run` |
| `/bap/insights` | AI Insights | `BAPInsights` | B-A-P | `GET /insights?type=&conf_min=` |
| `/integration/overview` | Service Registry | `IntegrationOverview` | Integration | `GET /gateway/services` · `GET /integrations` |
| `/integration/bus` | Event Bus | `IntegrationBus` | Integration | SSE `/events/stream` · `GET /events?source=&limit=` |
| `/integration/sagas` | Saga Transactions | `IntegrationSagas` | Integration | `GET /sagas` · `GET /sagas/{id}` · `POST /sagas/{id}/compensate` |
| `/integration/auth` | Auth Sessions | `IntegrationAuth` | Integration | `GET /auth/sessions` · `DELETE /auth/sessions/{id}` |
| `/settings` | Org Settings | `AdminSettings` | Admin | `GET /org` · `PUT /org` · `GET /api-keys` · `POST /api-keys` |
| `/admin/billing` | Platform Billing | `AdminBilling` | Admin | `GET /billing` · Stripe Customer Portal |
| `/admin/audit` | Audit Log | `AuditLog` | Admin | `GET /audit?service=&user=&limit=` |

---

## Component Inventory

### Shared primitives (`console/UI.jsx`)

| Component | Props | Notes |
|-----------|-------|-------|
| `CountUp` | `to, duration?, prefix?, suffix?, decimals?` | Animates on mount; rAF + setTimeout fallback |
| `Badge` | `label, tone?, pulse?, size?` | tones: neutral/cyan/green/gold/red/purple/teal/orange/life |
| `Btn` | `variant?, size?, tone?, onClick?, disabled?, icon?` | variants: primary/secondary/ghost/danger/success |
| `Panel` | `style?, elevated?` | Dark surface container — always 0 border-radius |
| `PanelHeader` | `title, sub?, right?` | Sticky-safe panel header with optional right slot |
| `MetricTile` | `label, value, unit?, delta?, color?, icon?` | Flex tile for stat strips |
| `ConfBar` | `val, width?, showLabel?` | 0–1 animated fill bar, color-coded at 0.9/0.7 thresholds |
| `Sparkline` | `data, width?, height?, color?, fill?` | SVG polyline with gradient fill |
| `Kbd` | `children` | Keyboard shortcut pill |
| `EmptyState` | `icon?, title, body?, cta?` | Centered empty state with lucide icon |
| `Skel` | `w?, h?, style?` | Shimmer skeleton block |
| `Tabs` | `tabs, active, onChange, tone?` | Horizontal tab bar — bottom border active indicator |
| `Input` | `icon?, type?, error?, size?` | Wrapped input with optional leading icon and inline error |
| `Divider` | `label?, style?` | Horizontal rule with optional label |
| `Logo` | `size?, showWord?, wordSize?` | SVG chevron-diamond mark + wordmark |

### Shell components (`console/Shell.jsx`)

| Component | Role |
|-----------|------|
| `Sidebar` | Left rail — collapsible, grouped nav, service accent colors, user footer |
| `TopBar` | 44px breadcrumb bar — Cmd+K trigger, system health indicator |
| `EventFeed` | Right rail — live SSE event stream, collapsible to icon mode |
| `CommandPalette` | Full-screen overlay — keyboard nav (↑↓↵ esc), route search |
| `Router` | Reads `window.ROUTES`, renders `window[component]`, handles stubs |

---

## Token Usage Per Surface

### Color application rules

```
Background hierarchy (never invert):
  page root       → --re-bg (#020510)
  card / panel    → --re-surface (#060c1a)
  hover row / modal → --re-surface-hi (#091424)
  tooltip / cmd   → --re-surface-pop (#0d1e35)

Text grades:
  headings / values  → --re-text-bright (#ffffff)
  body copy          → --re-text (#a8c4de)
  labels / secondary → --re-text-dim (#4a6880)
  placeholders       → --re-text-muted (#1e3348)

Accent usage — strictly semantic, never decorative:
  ClearDesk surfaces → --re-teal (#00d4aa) / #00FF94
  Money surfaces     → --re-gold (#ffc400)
  APEX surfaces      → --re-purple (#7c5cfc)
  B-A-P surfaces     → --re-cyan (#00e5ff) / --re-teal
  Integration        → --re-green (#00ff7a)
  Success / healthy  → --re-green
  Critical / safety  → --re-red (#ff3b5c)
  Primary CTA        → --re-cyan

Data values:  always IBM Plex Mono, never sans-serif
IDs / codes:  always IBM Plex Mono, color --re-text-muted or accent
Headings:     Neue Haas Grotesk (or Inter Tight fallback) — NOT Fraunces
Body / UI:    IBM Plex Sans
```

### Border rules

```
Default panel:   1px solid #0c1a2c
Hover / active:  1px solid #152637
Accent active:   1px solid <accent-color>
Focus ring:      box-shadow: 0 0 0 2px <accent>25
Error state:     1px solid #ff3b5c
No border-radius on panels or cards — 2px max on buttons/badges/inputs
```

---

## State Machines

### ClearDesk document flow

```
UPLOADED → [OCR + Claude extract] → PARSED
PARSED   → [confidence >= 0.70 AND amount < threshold] → READY (auto-export eligible)
PARSED   → [confidence < 0.70 OR amount >= threshold]  → ESCALATED (human queue)
ESCALATED → [human: approve] → READY
ESCALATED → [human: reject]  → REJECTED
READY    → [export triggered] → EXPORTED
```

**Security invariant:** document preview must pass through DOMPurify before any DOM insertion. No `innerHTML` with raw document bytes.

### Money dispatch flow

```
INBOUND SMS/CALL → triage_agent
triage_agent: detect keywords
  → gas/CO/smoke/fire/explosion → LIFE_SAFETY: 911 directive, NO dispatch, owner notified
  → other → intake_agent

intake_agent → scheduler_agent → dispatch_agent → followup_agent

Status progression:
PENDING → SCHEDULED → EN_ROUTE → ON_SITE → COMPLETED
                                           ↘ CANCELLED
```

**Security invariant:** `LIFE_SAFETY` keyword detection MUST block auto-dispatch. This is enforced in `triage_agent` tool call, not UI. UI shows the banner and disables dispatch actions.

### APEX execution tier assignment

```
confidence = f(L1_analyze, L2_calibration)
domain_novelty = f(L1_analyze)

T1 Reflexive:    confidence >= 0.92 AND domain_novelty < 0.50 → auto-approve, log only
T2 Deliberative: confidence >= 0.65 AND domain_novelty < 0.85 → approve with reasoning
T3 Contested:    confidence < 0.65 OR stakes == HIGH          → HITL required
T4 Unknown:      domain_novelty >= 0.85                       → HITL + escalate to owner
```

### Saga compensation

```
PENDING → RUNNING → COMPLETED
                  ↘ FAILED → COMPENSATING → COMPENSATED
                                          ↘ COMPENSATION_FAILED (manual intervention)
```

Redis TTL: 24h. State stored as JSON at `saga:{saga_id}`.

---

## API Endpoint Reference

### Auth service (port 8001, via Kong `/auth`)
```
POST /auth/token          — OAuth2 password flow → {access_token, refresh_token, expires_in}
POST /auth/refresh        — Rotate tokens
POST /auth/mfa/verify     — TOTP verify → {access_token}
GET  /auth/sessions       — Active JWT session list (admin only)
DELETE /auth/sessions/{id} — Revoke session
GET  /health              — No auth required
```

### ClearDesk API (port 8002, via Kong `/cleardesk`)
```
GET  /api/documents            — ?status= &search= &page= &limit=
POST /api/documents/upload     — multipart/form-data → document_id
POST /api/analyze              — {document_id} → {confidence, extracted_data, summary_en, summary_es}
GET  /api/documents/{id}       — Full document record
PATCH /api/documents/{id}      — {status, assignee, notes}
GET  /api/documents/export     — ?format=csv|json &fields= → stream
GET  /api/settings             — Org-level thresholds and config
PUT  /api/settings             — Update thresholds
POST /api/chat                 — {messages, context_doc_ids} → SSE stream
```

### Money API (FastAPI, port 8003, via Kong `/money`)
```
GET  /dispatches               — ?status= &urgency= &limit=
POST /dispatch                 — {lead_info, issue, source} → dispatch_id (triggers CrewAI)
GET  /dispatches/{id}          — Full dispatch + message thread
PATCH /dispatches/{id}         — {status, notes}
POST /dispatches/{id}/sms      — Resend SMS
GET  /agents/status            — CrewAI agent pipeline status
GET  /billing/subscription     — Stripe subscription details
SSE  /dispatches/stream        — Live dispatch events
```

### APEX (Next.js API routes, port 8000, via Kong `/apex`)
```
POST /workflow/run             — {input, context?} → {workflow_id}
GET  /workflow/pending         — HITL decision queue
GET  /workflow/completed       — Completed workflow list
POST /workflow/hitl/{id}       — {action: approve|reject, reasoning} → decision recorded
GET  /workflow/run/{id}/stream — SSE execution trace
GET  /traces                   — Langfuse trace list
GET  /traces/{id}/spans        — Span breakdown
GET  /agents                   — Registered specialist agents
GET  /tools                    — MCP tool registry
POST /tools/call               — {tool_name, input} → result
POST /memory/search            — {query, k?} → [{content, similarity}]
POST /memory/save              — {content, metadata}
```

### B-A-P (FastAPI, port 8004, via Kong `/bap`)
```
GET  /datasets                 — Dataset inventory
POST /datasets/upload          — multipart → {dataset_id}
POST /datasets/{id}/run        — Trigger ETL pipeline
GET  /etl/jobs                 — Active + recent jobs
GET  /etl/jobs/{id}            — Job status + log
SSE  /etl/jobs/{id}/stream     — Live stage updates
GET  /insights                 — ?type=anomaly|forecast|summary &conf_min=
GET  /insights/{id}            — Full insight record
```

### Integration layer
```
GET  /gateway/services         — Kong registered services
GET  /integrations             — Connected external integrations + circuit breaker status
POST /publish                  — Publish event to bus
SSE  /events/stream            — Live event feed
GET  /events                   — ?source= &kind= &limit=
GET  /dlq                      — Dead letter queue
GET  /sagas                    — Active saga list
GET  /sagas/{id}               — Saga detail + step trace
POST /sagas/{id}/compensate    — Trigger compensation
GET  /audit                    — ?service= &user= &action= &limit=
```

---

## Security Invariants (UI-level enforcement)

These MUST be enforced in every implementation. They correspond to the security tab in `/settings`.

1. **No auth tokens in browser storage** — `localStorage`, `sessionStorage`, `IndexedDB` must never contain JWTs, API keys, or capability secrets. Session state lives server-side.

2. **Document preview is text-safe** — All document content rendered in the UI must pass through `DOMPurify.sanitize()` before any DOM insertion. Never use `innerHTML` with raw document bytes.

3. **Life-safety auto-dispatch is blocked** — If `urgency === 'LIFE_SAFETY'`, the UI must show the red pulsing banner, disable dispatch actions, and display "911 directive — no technician dispatched". This is enforced in `triage_agent` but the UI must also enforce it.

4. **No default credentials** — All service connections require explicit env vars. The settings UI must not accept empty API keys.

5. **No raw UUID KV access** — ClearDesk cross-device sync uses signed session codes (displayed in Settings → Sync), never raw document UUIDs exposed to the browser.

6. **Fail-closed auth** — The auth service health indicator in the top bar must reflect real service state. If `/auth/health` fails, the UI must block access and show an error, not fall through to an unauthenticated state.

7. **No direct service-to-service calls** — All cross-service data (e.g., Money dispatch triggering ClearDesk update) must flow through the integration event bus. No direct API calls between service UIs.

---

## Design Handoff Checklist

- [ ] Tokens imported from `colors_and_type.css` — no hardcoded hex values in components
- [ ] All data values use `IBM Plex Mono` — no sans-serif for numeric/ID fields
- [ ] Border-radius max 2px — verify no `rounded-lg`, `rounded-xl` in Tailwind classes
- [ ] No box-shadows on cards/panels — elevation via background-color stepping only
- [ ] Hover states: background steps up one level (`--re-surface` → `--re-surface-hi`)
- [ ] Loading states: shimmer skeleton (`Skel` component) matching screen layout
- [ ] Empty states: centered, with lucide icon + action CTA (`EmptyState` component)
- [ ] LIFE_SAFETY banner: `animation: pulse 1.4s ease infinite` — red, full-width, sticky
- [ ] Confidence scores: `ConfBar` component — thresholds at 0.90 (green), 0.70 (gold), below (red)
- [ ] All event types in `snake.dot.notation` — never camelCase in UI labels
- [ ] Status enums in `SCREAMING_SNAKE_CASE` — never lowercase in badges

---

## File Structure (implementation target)

```
src/
├── app/                          # Next.js 15 App Router
│   ├── (auth)/
│   │   ├── signin/page.tsx       # AuthSignIn
│   │   └── mfa/page.tsx          # AuthMFA
│   ├── (marketing)/
│   │   ├── page.tsx              # MarketingHome
│   │   └── pricing/page.tsx      # MarketingPricing
│   ├── console/
│   │   ├── layout.tsx            # Shell (Sidebar + TopBar + EventFeed)
│   │   ├── page.tsx              # ConsoleHome
│   │   ├── cleardesk/
│   │   │   ├── page.tsx          # ClearDeskQueue
│   │   │   ├── upload/page.tsx   # ClearDeskUpload
│   │   │   ├── chat/page.tsx     # ClearDeskChat
│   │   │   ├── export/page.tsx   # ClearDeskExport
│   │   │   └── settings/page.tsx # ClearDeskSettings
│   │   ├── money/
│   │   │   ├── page.tsx          # MoneyAdmin
│   │   │   └── billing/page.tsx  # MoneyBilling
│   │   ├── apex/
│   │   │   ├── page.tsx          # ApexOverview
│   │   │   ├── hitl/page.tsx     # ApexHITL
│   │   │   ├── workflows/page.tsx# ApexWorkflows
│   │   │   ├── langfuse/page.tsx # ApexLangfuse
│   │   │   └── tools/page.tsx    # ApexTools
│   │   ├── bap/
│   │   │   ├── page.tsx          # BAPAnalytics
│   │   │   ├── pipeline/page.tsx # BAPPipeline
│   │   │   ├── upload/page.tsx   # BAPUpload
│   │   │   └── insights/page.tsx # BAPInsights
│   │   ├── integration/
│   │   │   ├── page.tsx          # IntegrationOverview
│   │   │   ├── bus/page.tsx      # IntegrationBus
│   │   │   ├── sagas/page.tsx    # IntegrationSagas
│   │   │   └── auth/page.tsx     # IntegrationAuth
│   │   └── admin/
│   │       ├── page.tsx          # AdminSettings
│   │       ├── billing/page.tsx  # AdminBilling
│   │       └── audit/page.tsx    # AuditLog
├── components/
│   ├── ui/                       # Badge, Btn, Panel, Tabs, Input, etc.
│   ├── shell/                    # Sidebar, TopBar, EventFeed, CommandPalette
│   ├── cleardesk/                # DocumentCard, ConfBar, DocumentDetail, ChatPanel
│   ├── money/                    # DispatchRow, DispatchModal, AgentTrace
│   ├── apex/                     # UncertaintyGauge, TierBadge, HITLCard, SpanDetail
│   ├── bap/                      # InsightCard, ETLJobRow, PipelineGraph
│   └── integration/              # SagaStepTrace, EventRow, SessionRow
├── lib/
│   ├── api/                      # Type-safe fetch wrappers per service
│   ├── auth/                     # JWT validation, session management
│   ├── sse/                      # SSE client hook (useEventStream)
│   └── tokens.ts                 # Design token constants (re-exports from CSS vars)
└── styles/
    └── tokens.css                # Revenue Engine v6 tokens (copy of colors_and_type.css)
```

---

*Handoff generated from design prototype at `console/index.html`. All component names, API routes, and state machine descriptions are implementation-ready.*
