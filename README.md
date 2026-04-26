<div align="center">
  <h1>🚀 ReliantAI Platform</h1>
  <p><b>Autonomous AI Lead Generation & Site Generation for Home Services</b></p>
  <p><i>Zero-Configuration • CrewAI-Powered • Next.js ISR • Production-Ready</i></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()
  [![Performance](https://img.shields.io/badge/Performance-Grade%20A%2B-brightgreen.svg)]()
  [![Security](https://img.shields.io/badge/Security-Grade%20A-success.svg)]()
  [![Architecture](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20CrewAI%20%2B%20Next.js-orange.svg)]()
</div>

---

## 🎯 What is ReliantAI?

ReliantAI is an autonomous lead generation and website creation platform for home service businesses (HVAC, plumbing, electrical, roofing, painting, landscaping). It combines:

- **AI-Powered Lead Discovery**: Google Places API → CrewAI filtering → Quality scoring
- **Automated Site Generation**: CopyAgent writes content → SiteRegistrationService → Next.js ISR
- **Multi-Channel Outreach**: Twilio SMS + Resend email with personalized pitches
- **Zero Per-Site Builds**: Single Next.js 15 App Router with ISR handles all sites

### Key Differentiators

| Feature | Traditional Approach | ReliantAI |
|---------|---------------------|-----------|
| **Site Deployment** | Per-site builds (30-90s each) | ISR from DB (instant) |
| **Content Generation** | Manual copywriting | CrewAI CopyAgent |
| **Lead Discovery** | Manual Google searching | Automated Places API + filtering |
| **Configuration** | Complex `.env` files | Zero-config JIT OS wizard |
| **Architecture** | Static exports | Dynamic ISR with revalidation |

---

## 🏗️ Architecture Overview

### System Topology

```
reliantai.org (Vite SPA — marketing website)
    │
    │ POST /api/v2/prospects          (inbound — website form)
    │ POST /api/v2/prospects/scan     (outbound — autonomous scan)
    │
    ▼
api.reliantai.org (FastAPI + Uvicorn)
    │
    ├── POST /api/v2/prospects        → saves to DB, queues Celery task
    ├── GET  /api/v2/generated-sites/{slug}  → returns site_content JSON
    ├── POST /api/v2/webhooks/stripe  → triggers provisioning
    └── POST /api/v2/webhooks/twilio  → routes inbound SMS
    │
    ▼
Redis (broker + result backend)
    │
    ├── Queue: agents          (2 workers, Gemini API tasks)
    ├── Queue: outreach        (4 workers — Twilio/Resend)
    └── Queue: provisioning    (1 worker — Stripe/idempotent)
    │
    ▼
Celery Workers
    │
    ├── run_prospect_pipeline(prospect_id)
    │     BusinessResearcher → CompetitorAnalyst → CopyAgent → SiteRegistration → OutreachAgent
    │
    └── process_scheduled_followups()  ← every 5 min via Beat
    │
    ▼
Postgres (single DB, all platform data)

preview.reliantai.org (Next.js 15 App Router, Vercel)
    ├── /[slug]         → ISR page: fetches site_content from API, renders template
    └── /api/revalidate → POST to revalidate ISR cache
```

### Critical Architecture Decisions

**ADR-001: No Per-Site Builds**
- Sites rendered via ISR on one shared Next.js app
- Deploy = one `INSERT INTO generated_sites`
- Vercel ISR handles rendering, zero `npm build` per prospect

**ADR-002: Single Postgres DB**
- One Postgres instance, all tables in one schema
- Simplified operations for solo developer/small team
- Can partition later if needed

**ADR-003: Synchronous Tools**
- All CrewAI tool `_run()` methods are synchronous
- CrewAI runs tools in thread pool internally
- Avoids async/sync boundary complexity

**ADR-004: preview.reliantai.org Subdomain**
- Client sites at `preview.reliantai.org/{slug}`
- `reliantai.org` is Vite SPA — cannot do ISR/SSR
- Separate deployment keeps marketing site independent

---

## 📁 Project Structure

```
ReliantAI/
├── reliantai/                    # FastAPI + Celery platform core
│   ├── agents/                    # CrewAI agents and tools
│   │   ├── tools/
│   │   │   ├── google_places.py     # Places API text search + details
│   │   │   ├── gbp_scraper.py       # GBP completeness scoring
│   │   │   ├── pagespeed.py         # PageSpeed Insights
│   │   │   ├── schema_builder.py    # Schema.org LocalBusiness JSON-LD
│   │   │   ├── schema_validator.py  # Rich Results Test API
│   │   │   ├── twilio_sms.py        # SMS sending
│   │   │   └── resend_email.py      # Email sending
│   │   ├── home_services_crew.py    # 5-agent Crew definition
│   │   └── llm.py                   # Gemini Pro/Flash factory
│   ├── api/v2/
│   │   ├── prospects.py             # Inbound + outbound prospect APIs
│   │   ├── generated_sites.py       # Public site content endpoint
│   │   └── webhooks.py              # Stripe + Twilio webhooks
│   ├── db/
│   │   ├── migrations/001_platform.sql  # Initial schema
│   │   ├── models.py                # SQLAlchemy ORM
│   │   └── __init__.py              # get_db_session() + engine
│   ├── services/
│   │   └── site_registration_service.py  # Replaces VercelDeployTool
│   ├── tasks/
│   │   └── prospect_tasks.py        # Celery task definitions
│   ├── celery_app.py                # Celery config (no Django)
│   └── main.py                      # FastAPI app factory
│
├── reliantai-client-sites/        # Next.js 15 ISR app
│   ├── app/
│   │   ├── [slug]/page.tsx          # Dynamic ISR route
│   │   └── api/revalidate/route.ts  # Cache revalidation endpoint
│   ├── templates/
│   │   ├── hvac-reliable-blue/      # HVAC template
│   │   ├── plumbing-trustworthy-navy/
│   │   ├── electrical-sharp-gold/
│   │   ├── roofing-bold-copper/
│   │   ├── painting-clean-minimal/
│   │   └── landscaping-earthy-green/
│   ├── components/PreviewBanner.tsx # Buy CTA overlay
│   ├── lib/api.ts                   # getSiteContent() fetcher
│   ├── types/SiteContent.ts         # TypeScript interfaces
│   └── next.config.ts
│
├── docker-compose.yml               # Full platform orchestration
├── .env.example                     # Environment variable template
└── README.md                        # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.20+
- API keys: Google Places, Gemini, Twilio, Stripe, Resend

### Option 1: Zero-Configuration (JIT OS)

```bash
# Clone and start
git clone https://github.com/your-org/ReliantAI.git
cd ReliantAI
docker compose up -d

# Open setup wizard
open http://localhost:8085  # macOS
xdg-open http://localhost:8085  # Linux
```

Enter API keys through the secure wizard — no `.env` editing required.

### Option 2: Traditional Setup

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your API keys
nano .env

# 3. Deploy
./scripts/deploy.sh local

# 4. Verify
./scripts/health_check.py -v
```

### Environment Variables

```bash
# Core
DATABASE_URL=postgresql://reliantai:password@postgres:5432/reliantai
REDIS_URL=redis://:password@redis:6379/0
SECRET_KEY=<64-byte-hex>
API_SECRET_KEY=<32-byte-hex>

# Google APIs
GOOGLE_PLACES_API_KEY=<key>
GOOGLE_PAGESPEED_API_KEY=<key>
GOOGLE_AI_API_KEY=<key>              # Gemini

# Communications
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
RESEND_API_KEY=<key>
FROM_EMAIL=you@domain.com

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Deployment
PLATFORM_API_URL=https://api.reliantai.org
PLATFORM_API_KEY=<same-as-API_SECRET_KEY>
REVALIDATE_SECRET=<32-byte-hex>
```

---

## 🧪 Development Workflow

### Start Services

```bash
# Full platform
docker compose up -d

# Specific services
docker compose up -d api postgres redis celery-agents

# View logs
docker compose logs -f api
```

### Run Pipeline Manually

```bash
# 1. Create a prospect
curl -X POST http://localhost:8000/api/v2/prospects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_SECRET_KEY" \
  -d '{
    "trade": "hvac",
    "city": "Houston",
    "state": "TX",
    "business_name": "Apex HVAC",
    "phone": "+17135551234",
    "email": "owner@apexhvac.com"
  }'

# 2. Pipeline runs automatically via Celery
# 3. Check status
curl http://localhost:8000/api/v2/prospects/{prospect_id}/status

# 4. View generated site
open http://localhost:3000/{slug}  # Client sites
```

### Run Tests

```bash
# Unit tests
pytest tests/ -x -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (Client sites)
cd reliantai-client-sites
npm run test:e2e
```

---

## 📊 Service Overview

| Service | Port | Purpose | Key Tech |
|---------|------|---------|----------|
| **ReliantAI API** | 8000 | FastAPI core, agents, webhooks | FastAPI, Celery, SQLAlchemy |
| **Client Sites** | 3000 | Next.js ISR renderer | Next.js 15, Tailwind, Framer Motion |
| **Postgres** | 5432 | Platform database | PostgreSQL 16 |
| **Redis** | 6379 | Celery broker, caching | Redis 7 |
| **Celery Workers** | — | Background task processing | 2 agents + 4 outreach workers |
| **JIT OS** | 8085 | Zero-config operations UI | React + FastAPI |

---

## 🔧 Hard Constraints (Never Deviate)

- **NO per-site builds**: Sites render via Next.js ISR from DB content
- **Slug generation**: `generate_slug(business_name, city)` — never from place_id
- **Celery Beat**: `celery_app.py beat_schedule` — NOT django_celery_beat
- **Tool `_run()`**: SYNCHRONOUS only (sync httpx.Client)
- **Preview domain**: `preview.reliantai.org` — NOT reliantai.org/preview/
- **CopyAgent LLM**: gemini-1.5-pro | **All other agents**: gemini-1.5-flash

---

## 🛡️ Security

- **Fail-closed**: Missing config causes startup failure, not degraded security
- **API Key Auth**: Service-to-service via `X-API-Key` header with constant-time comparison
- **JWT Auth**: User sessions via Bearer tokens with RS256
- **Webhook Verification**: Stripe + Twilio signatures validated
- **Rate Limiting**: 100 req/min per IP, 1000 req/min per API key
- **TCPA Compliance**: STOP word detection, opt-out handling

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | This file — quickstart & overview |
| `USER_MANUAL.md` | Complete operations guide |
| `AGENTS.md` | AI agent development guidelines |
| `CLAUDE.md` | Developer reference for Claude Code |

---

## 📜 License

MIT License — see LICENSE file for details.

---

**ReliantAI Platform v2.0** — Autonomous Lead Generation for Home Services
