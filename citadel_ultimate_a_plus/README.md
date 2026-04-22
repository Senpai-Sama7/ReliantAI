<div align="center">

# 🏰 Citadel

### Turn any business website into a qualified lead, a personalized outreach draft, and a tracked pipeline — in one command.

[![Tests](https://img.shields.io/badge/tests-34%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-proprietary-lightgrey)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue)]()

</div>

---

## What Citadel Does

Citadel is a self-hosted outbound lead generation engine for local service businesses. Give it a URL, and it will:

1. **Scout** the website — pull business signals, services offered, location, and contact info
2. **Qualify** the lead — score it against your target criteria with schema-validated gates
3. **Build** a static site preview — generate a personalized artifact for outreach context
4. **Draft** outreach copy — create a structured 7-beat email ready to send
5. **Track** everything — persist every state transition, from first touch to closed deal

```
You                          Citadel                         Output
 │                              │                               │
 │  python orchestrator.py      │                               │
 │  https://acme-plumbing.com   │                               │
 │  --approve --send-email      │                               │
 │─────────────────────────────▶│                               │
 │                              │  Scout website ──────────────▶│ Lead record
 │                              │  Qualify lead ───────────────▶│ Score + signals
 │                              │  Build preview ──────────────▶│ Static site
 │                              │  Draft outreach ─────────────▶│ 7-beat email
 │                              │  Deploy + send ──────────────▶│ .eml in outbox
 │                              │                               │
 │◀─────────────────────────────│  Done. Check your dashboard.  │
```

**No paid services required.** Everything runs locally out of the box — SQLite for state, local filesystem for deploys, `.eml` files for email. Plug in SMTP, S3, or any external service when you're ready.

---

## Who This Is For

| You are... | Citadel gives you... |
|------------|---------------------|
| **A service business owner** tired of paying $80+/lead on shared platforms | Exclusive leads, personalized outreach, and a dashboard showing exactly what's converting |
| **A technical founder** building an outbound product or agency | A working pipeline with schema contracts, webhook integrations, and 34 passing tests to build on |
| **An agency** running outbound for multiple clients | A self-hosted engine you can white-label — no per-seat pricing, full data ownership |

---

## Quick Start

### Option A: Local (recommended for first run)

```bash
# 1. Clone and set up
git clone <repo-url> && cd citadel
cp .env.template .env          # edit with your brand/config
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium      # required for multi-page crawling
python -m spacy download en_core_web_trf  # optional: ML-based lead scoring

# 2. Initialize
python lead_queue.py init
python market/census_ranker.py --config market/target_verticals.json  # optional: rank your market

# 3. Run your first lead
python orchestrator.py https://example-plumbing.com --dry-run          # preview without writing
python orchestrator.py https://example-plumbing.com --approve --send-email  # full pipeline

# 4. See your dashboard
uvicorn dashboard_app:app --host 127.0.0.1 --port 8888
# Open http://127.0.0.1:8888
```

### Option B: Docker

```bash
cp .env.template .env
docker compose up --build
# Dashboard at http://127.0.0.1:8888
```

### Option C: Make (all commands at a glance)

```bash
make install      # create venv + install deps
make init-db      # initialize SQLite database
make ranker       # run Census market ranker
make run URL=https://example.com   # full pipeline
make dashboard    # start operator console
make test         # run test suite
make lint         # syntax checks
make clean        # remove cache files
```

---

## The Pipeline

Every lead moves through a strict state machine. No lead skips a step, no data is lost.

```
  ┌──────────┐    ┌────────────┐    ┌─────────┐    ┌──────────┐
  │ Scouted  │───▶│ Qualified  │───▶│  Built  │───▶│ Approved │
  └──────────┘    └────────────┘    └─────────┘    └──────────┘
                                                        │
                  ┌────────────┐    ┌─────────┐         │
                  │  Replied   │◀───│ Emailed │◀────────┘
                  └────────────┘    └─────────┘

  Any state ──▶ Disqualified (terminal)
  Replied ──▶ terminal
```

Every transition is recorded as an event with actor, timestamp, run ID, and payload. Nothing is overwritten — you get a full audit trail.

---

## The Dashboard

A real-time operator console with everything you need to see at a glance:

| Endpoint | What it shows |
|----------|--------------|
| `/` | Live dashboard — pipeline counts, conversion rates, lead status |
| `/api/funnel` | Pipeline state counts (scouted → qualified → built → ... → replied) |
| `/api/verticals` | Conversion breakdown by vertical (plumbing, HVAC, etc.) |
| `/api/leads` | Lead list with status, scores, and timestamps |
| `/api/economics` | Revenue summary — deal values, average ticket, pipeline value |
| `/api/beat-compliance` | How well your outreach follows the 7-beat structure |
| `/api/lead/{slug}/timeline` | Full event history for any single lead |
| `/health` | System health check (200 OK or 503 degraded) |

All `/api/*` endpoints are protected by API key when `CITADEL_DASHBOARD_API_KEY` is set. Rate-limited per IP.

---

## The 7-Beat Outreach Model

Every outreach draft follows a proven 7-beat structure, enforced by JSON schema:

| Beat | Purpose | Example |
|------|---------|---------|
| 1. Pattern Break | Stop the scroll — say something unexpected | "Your emergency page doesn't have a click-to-call button" |
| 2. Cost of Inaction | Quantify what doing nothing costs them | "$3K–$6K/month in lost calls" |
| 3. Belief Shift | Challenge their current assumption | "Shared leads aren't cheaper — they just feel cheaper" |
| 4. Mechanism | How it works (simple, not technical) | "We find businesses that need you and reach out on your behalf" |
| 5. Proof Unit | Evidence it works | "14 replies from 147 contacts in Week 2" |
| 6. Offer | What they get, what it costs | "$1,500/mo, no contract, cancel anytime" |
| 7. Action | Specific next step with a deadline | "Reply for a 2-min video of your market" |

The schema at `schemas/outreach_output.json` enforces this structure at runtime. If a draft doesn't hit all 7 beats, it fails validation.

---

## Market Intelligence

Citadel includes a built-in market ranker powered by U.S. Census Bureau data:

```bash
python market/census_ranker.py --config market/target_verticals.json
```

This pulls real establishment counts by NAICS code for your target geography and writes `market/market_weights.json` — so you know exactly how many plumbing, HVAC, electrical, roofing, landscaping, and painting businesses operate in your area before you send a single email.

**Configured verticals** (in `market/target_verticals.json`):
Plumbing · HVAC · Electrical · Roofing · Landscaping · Painting

---

## Webhooks

Citadel accepts inbound webhook events for deployment callbacks, email tracking, and deal outcomes:

```
POST /api/webhooks/openclaw
```

**Supported events:**

| Event | What it does |
|-------|-------------|
| `deployment.succeeded` | Marks lead as deployed |
| `deployment.failed` | Records failure, keeps lead in current state |
| `outreach.sent` | Confirms email delivery |
| `lead.replied` | Advances lead to replied status |
| `deal.won` | Records closed revenue |
| `deal.lost` | Records loss reason |

**Security:** Every webhook is verified with HMAC-SHA256 signature + timestamp skew enforcement. Duplicate events are rejected via idempotency keys. Request body capped at 64KB.

```
Headers:
  X-Citadel-Timestamp: 1708800000
  X-Citadel-Signature: sha256=<HMAC of "{timestamp}.{body}" using OPENCLAW_WEBHOOK_SECRET>
```

---

## Configuration

Copy `.env.template` to `.env` and customize. Key settings:

| Variable | Default | What it controls |
|----------|---------|-----------------|
| **Core** | | |
| `CITADEL_DB_PATH` | `workspace/state/lead_queue.db` | SQLite database location |
| `CITADEL_DASHBOARD_HOST` | `127.0.0.1` | Dashboard bind address |
| `CITADEL_DASHBOARD_PORT` | `8888` | Dashboard port |
| `CITADEL_DEFAULT_CITY` | `Houston` | Fallback city for leads without geo signals |
| `CITADEL_DEFAULT_STATE` | `TX` | Fallback state |
| **Security** | | |
| `CITADEL_DASHBOARD_API_KEY` | _(empty)_ | API key for `/api/*` endpoints (empty = open) |
| `OPENCLAW_WEBHOOK_SECRET` | `change-me` | HMAC signing key for webhooks |
| `CITADEL_CORS_ORIGINS` | _(empty)_ | Allowed CORS origins (empty = disabled) |
| `CITADEL_RATE_LIMIT_API_RPM` | `60` | API rate limit per IP per minute |
| `CITADEL_RATE_LIMIT_WEBHOOK_RPM` | `30` | Webhook rate limit per IP per minute |
| **Email** | | |
| `EMAIL_BACKEND` | `local_outbox` | `local_outbox` (writes .eml files) or `smtp` (sends live) |
| `SMTP_HOST` / `SMTP_PORT` | _(empty)_ / `587` | SMTP server for live sending |
| `SMTP_USE_TLS` | `true` | TLS for SMTP connections |
| **Deploy** | | |
| `DEPLOY_BACKEND` | `local_fs` | `local_fs` copies to `workspace/deploys/` |
| `DEPLOY_ENABLED` | `true` | Enable/disable deployment step |
| **Branding** | | |
| `BRAND_NAME` | `ReliantAI` | Your company name in outreach |
| `BRAND_FROM_EMAIL` | | Sender email address |
| `BRAND_OPTOUT_EMAIL` | | CAN-SPAM opt-out address |
| **Logging** | | |
| `CITADEL_LOG_FORMAT` | `text` | `text` or `json` structured logging |
| `CITADEL_LOG_PATH` | `workspace/logs/orchestrator.log` | Log file location |

See `.env.template` for the complete list with inline comments.

---

## Project Structure

```
citadel/
├── orchestrator.py          # Pipeline engine — scout, qualify, build, draft, deploy, send
├── lead_queue.py            # SQLite state machine — leads, events, builds, deployments
├── dashboard_app.py         # FastAPI dashboard — read APIs, webhook intake, health check
│
├── market/
│   ├── census_ranker.py     # Census CBP market intelligence
│   └── target_verticals.json # Vertical + geography configuration
│
├── schemas/                 # JSON schema contracts (validation gates)
│   ├── qualifier_output.json
│   ├── builder_input.json
│   ├── build_manifest.json
│   └── outreach_output.json
│
├── tests/                   # 34 tests — pipeline, API, webhooks, schemas, logging
│   ├── conftest.py          # Shared fixtures (temp DB, webhook signer)
│   ├── test_lead_queue.py
│   ├── test_orchestrator_local.py
│   ├── test_orchestrator_logging.py
│   ├── test_schema_contracts.py
│   ├── test_webhook_signature.py
│   ├── test_dashboard_api.py
│   ├── test_health_endpoint.py
│   └── test_census_ranker.py
│
├── sales/                   # GTM assets, playbooks, and business plan
│
├── workspace/               # Runtime outputs (not source code)
│   ├── state/               # SQLite database
│   ├── logs/                # Structured logs
│   ├── builds/              # Generated static sites
│   ├── deploys/             # Deployed artifacts
│   └── outbox/              # .eml email files
│
├── .env.template            # Environment variable contract (30 vars)
├── Dockerfile               # Container image with health check
├── docker-compose.yml       # One-command deployment
├── Makefile                 # Developer workflow commands
├── sync_state.sh            # S3 checkpoint daemon for spot instances
└── requirements.txt         # Python dependencies
```

---

## Security

Citadel is built with defense-in-depth for a self-hosted system:

- **API authentication** — optional API key on all read endpoints
- **Webhook verification** — HMAC-SHA256 with timestamp skew enforcement
- **Idempotent webhooks** — duplicate events rejected via receipt tracking
- **Rate limiting** — configurable per-IP sliding window on APIs and webhooks
- **Request size limits** — 64KB max webhook body
- **Input validation** — JSON schema gates at every pipeline stage
- **Path validation** — lead slugs validated with regex `^[a-z0-9-]{5,120}$`
- **CORS control** — disabled by default, explicit opt-in via env var
- **WAL mode SQLite** — safe concurrent reads with busy timeout

---

## Testing

```bash
pytest -q
# 34 passed, 36 warnings
```

| Test file | What it covers |
|-----------|---------------|
| `test_lead_queue.py` | State transitions, webhook idempotency, economics summaries |
| `test_orchestrator_local.py` | Full pipeline integration against in-process HTTP server |
| `test_orchestrator_logging.py` | Structured JSON logging format and run ID propagation |
| `test_schema_contracts.py` | Schema validity and contract constraint enforcement |
| `test_webhook_signature.py` | HMAC acceptance/rejection and duplicate event handling |
| `test_dashboard_api.py` | API shape, auth, rate limiting, timeline validation |
| `test_health_endpoint.py` | Health check behavior and auth bypass |
| `test_census_ranker.py` | Target config validation invariants |

---

## Deployment Options

| Mode | How | Best for |
|------|-----|----------|
| **Local** | `python orchestrator.py` + `uvicorn` | Development, first pilots |
| **Docker** | `docker compose up --build` | Consistent environments, demos |
| **Spot/Preemptible** | Docker + `sync_state.sh` | Cost-optimized production (auto-checkpoints to S3) |

The `sync_state.sh` daemon handles SQLite WAL checkpointing and S3 sync with IMDSv2 token refresh — designed for AWS spot instances that can be interrupted.

---

## Roadmap

Citadel is production-ready for single-operator use today. The [v2 roadmap](PROGRESS_TRACKER_v2.md) covers 14 phases of expansion:

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Deep crawling (multi-page site analysis) | Planned |
| 2 | ML inference (lead scoring models) | Planned |
| 3 | Additional deploy backends (S3, Netlify, Vercel) | Planned |
| 4 | Queue system (async job orchestration) | Planned |
| 5 | PostgreSQL support (multi-user scale) | Planned |
| 6 | Documentation + integration guides | Planned |
| 7 | Email deliverability tooling (warmup, SPF/DKIM) | Planned |
| 8 | Team collaboration (multi-user, roles) | Planned |
| 9 | Native integrations (CRM, Slack, Zapier) | Planned |
| 10 | AI content generation (LLM-powered outreach) | Planned |
| 11 | Prometheus metrics + alerting | Planned |
| 12 | Email reply parsing (auto-classification) | Planned |
| 13 | A/B testing (subject lines, send times) | Planned |
| 14 | Professional support infrastructure | Planned |

---

## Sales & GTM Assets

The `sales/` directory contains a complete go-to-market kit:

- **Business plans** — operating doc + bank-ready version with financial projections
- **One-pagers** — buyer-focused collateral for 7 verticals + agency ICP
- **Outbound copy packs** — 3-email sequences with personalization hooks per vertical
- **Playbooks** — prospect sourcing, call scripts, qualification rubric, observation examples
- **Templates** — reusable vertical parameter map for spinning up new markets

See [`sales/README.md`](sales/README.md) for the full inventory.

---

<div align="center">

**Built for operators who want more booked jobs, not more software to manage.**

[Quick Start ↑](#quick-start) · [Dashboard ↑](#the-dashboard) · [Configuration ↑](#configuration) · [Roadmap ↑](#roadmap)

</div>
