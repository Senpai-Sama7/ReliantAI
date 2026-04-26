# 📖 ReliantAI Platform — User Manual

Welcome to the **ReliantAI Platform**. This manual is designed to provide you with an intuitive, comprehensive understanding of the platform's features, architecture, and operational procedures. Whether you are an engineer, an operator, or a product manager, this guide will help you navigate and utilize the system effectively.

---

## 📑 Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Getting Started](#2-getting-started)
3. [Reliant JIT OS](#3-reliant-jit-os)
4. [Core Concepts & Architecture](#4-core-concepts--architecture)
5. [Service Deep Dives](#5-service-deep-dives)
   - [💰 ReliantAI API (FastAPI + Celery)](#-reliantai-api-fastapi--celery)
   - [🌐 ReliantAI Client Sites (Next.js ISR)](#-reliantai-client-sites-nextjs-isr)
   - [💰 Money (Revenue & Dispatch)](#-money-revenue--dispatch)
   - [🚀 GrowthEngine (Lead Generation)](#-growthengine-lead-generation)
   - [🛡️ ComplianceOne (Governance)](#-complianceone-governance)
   - [💸 FinOps360 (Cost Optimization)](#-finops360-cost-optimization)
   - [🧠 Orchestrator (Platform Brain)](#-orchestrator-platform-brain)
   - [🤖 Apex Framework (AI Agents)](#-apex-framework-ai-agents)
   - [🏢 Gen-H (Lead Gen)](#-gen-h-lead-gen)
   - [📊 Ops-Intelligence & Citadel](#-ops-intelligence--citadel)
   - [🔌 Integration & Auth (Event Bus)](#-integration--auth-event-bus)
6. [Deployment & Operations](#6-deployment--operations)
7. [API & Authentication](#7-api--authentication)
8. [Troubleshooting Guide](#8-troubleshooting-guide)

---

## 1. Platform Overview

ReliantAI is an enterprise-grade, event-driven microservices ecosystem. It is designed to autonomously run a business (like an HVAC service company) while simultaneously providing enterprise SaaS capabilities (Compliance, Cloud Cost Optimization, AI orchestration).

**Key Capabilities:**
- **Autonomous Dispatching:** SMS messages from customers are triaged by AI (CrewAI + Gemini) and automatically routed to technicians.
- **Self-Healing Infrastructure:** The platform monitors its own CPU/Memory metrics and uses predictive algorithms (Holt-Winters) to scale services up or down dynamically.
- **Strict Data Isolation:** Every service has its own dedicated PostgreSQL database. Services communicate *only* via HTTP REST or the Redis Event Bus.
- **Zero-Configuration Setup:** The new Reliant JIT OS eliminates `.env` files entirely — just enter API keys in the browser wizard.

---

## 2. Getting Started

### Prerequisites
- Docker (24.0+)
- Docker Compose (2.20+)
- Modern web browser

### Quick Start (Zero-Configuration)

The easiest way to get started is using the Reliant JIT OS:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/ReliantAI.git
cd ReliantAI

# 2. Start the entire platform
docker compose up -d

# 3. Open the JIT OS interface
# http://localhost:8085
```

### First-Time Setup

When you open http://localhost:8085 for the first time:

1. You'll see the **Initialization Wizard**
2. Enter your API keys (Gemini, Stripe, Twilio, Google Places)
3. Click **"Initialize Platform"**
4. The system automatically configures everything

**No `.env` files. No manual editing. No documentation to read first.**

### Manual Setup (Advanced)

If you prefer traditional configuration:

```bash
# 1. Copy and edit environment variables
cp .env.example .env
# Edit .env with your API keys

# 2. Run the deployment script
./scripts/deploy.sh local

# 3. Verify all services are healthy
./scripts/health_check.py -v
```

---

## 3. Reliant JIT OS

The **Reliant JIT OS** is your AI-powered operations center. It's a chat-based interface that lets you control the entire platform using natural language.

### Access
- **URL:** http://localhost:8085
- **No login required** (local development)

### AI Modes

| Mode | Icon | Purpose | Best For |
|------|------|---------|----------|
| **Auto** | ⚡ | Mixed tasks | General questions, combined operations |
| **Support** | 💬 | Help & guidance | Learning the platform, how-to questions |
| **Engineer** | 💻 | Code generation | Adding features, fixing bugs, refactoring |
| **Sales** | 💰 | Lead generation | Finding prospects, sending outreach |

### Common Tasks

**Check System Status:**
```
"What's the system status?"
"Show me all running services"
"Are there any errors?"
```

**Find Leads:**
```
"Find HVAC companies in Atlanta with 4+ stars"
"Search for dentists in Chicago without websites"
"Generate a list of 50 plumbers in Houston"
```

**Modify Code:**
```
"Add a refund endpoint to Money service"
"Fix the healthcheck in dashboard"
"Update pricing for enterprise customers"
```

**Generate Reports:**
```
"Generate a compliance report for SOC2"
"Show me cloud cost analysis for last month"
"Create a system health report"
```

### Security

The JIT OS has built-in safety guardrails:

- ✅ **Can modify** application code
- ✅ **Can read** logs and metrics
- ✅ **Can generate** reports and analyses
- ❌ **Cannot delete** system files
- ❌ **Cannot format** disks
- ❌ **Cannot shutdown** the server

All AI-generated code is validated before execution. Dangerous commands are automatically blocked.

### Execution History

Every AI operation is logged:
- **Timestamp** — when it happened
- **Prompt** — what you asked
- **Code Hash** — security fingerprint
- **Status** — success / error / blocked
- **Duration** — how long it took

Access this via the **"Execution History"** button in the left sidebar.

### Troubleshooting JIT OS

| Problem | Solution |
|---------|----------|
| "Connection failed" | Wait 10s, refresh, check `docker compose ps` |
| "Gemini API Key not set" | Complete setup wizard at http://localhost:8085 |
| Code blocked | Rephrase request, use specific paths |
| High memory usage | Restart containers: `docker compose restart` |

For complete JIT OS documentation, see:
- `reliant-os/USER_MANUAL.md` — Detailed user guide
- `reliant-os/README.md` — Technical API documentation

---

## 4. Core Concepts & Architecture

To use or develop on ReliantAI, you must understand three core patterns:

### Event-Driven CQRS
We strictly separate reads and writes. When a service (e.g., `Money`) updates a record, it publishes an event (`dispatch_completed`) to the **Event Bus**. Other services subscribe to these events to update their own read models.

### Distributed Sagas
For transactions spanning multiple services (e.g., *Register User -> Bill Credit Card -> Provision Cloud Account*), we use the **Saga Pattern**. If a step fails, the Saga Orchestrator triggers compensating (rollback) events in reverse order.

### Circuit Breakers
External integrations (Twilio, Stripe, Cloud APIs) are wrapped in Circuit Breakers. If an API fails 3 times, the breaker "opens" for 30 seconds, immediately returning 503s to prevent system lockup and queue exhaustion.

---

## 5. Service Deep Dives

### 🏠 ReliantAI API (FastAPI + Celery)
**Purpose:** Central API for managing prospects, generating site content, and orchestrating background tasks.
**Port:** 8000 (via nginx) or 8000 directly
**Key Features:**
- **CrewAI Agent Pipeline:** Autonomous agents for GBP scraping, PageSpeed auditing, schema building, SMS/email notifications.
- **Site Registration:** Registers business landing pages with Google, triggers ISR revalidation on content changes.
- **Prospects API:** Enriched prospect data with years_in_business, service_area, owner info, business intelligence.
- **Celery Beat:** Scheduled task pipeline (prospect discovery → site generation → schema submission → review monitoring).
- **AI-Controllable:** Yes — JIT OS can register sites, trigger revalidation, query prospects.

### 🌐 ReliantAI Client Sites (Next.js ISR)
**Purpose:** Dynamically generates branded landing pages for home service businesses at runtime via ISR.
**Port:** 3000
**Key Features:**
- **ISR at /[slug]:** Pages regenerate every 3600s or on-demand via `POST /api/revalidate`.
- **6 Trade Templates:** HVAC (blue), Plumbing (blue), Electrical (amber), Roofing (orange), Painting — light theme (violet), Landscaping (emerald).
- **No Per-Site Builds:** One Next.js app, content driven from API — all pages served from shared ISR cache.
- **Preview Mode:** Live preview links with branded banner, checkout CTA, and lighthouse scores.
- **Revalidation Auth:** On-demand revalidation requires `Authorization: Bearer <token>` matching `REVALIDATE_SECRET`.
- **Interactive Showcase (`/showcase`):** Four-view template studio:
  - *Preview:* Template rendering in device frames (Desktop with macOS chrome, Tablet, Mobile with notch)
  - *Grid:* All 6 templates simultaneously with hover actions
  - *Prompt:* Syntax-highlighted generation prompts with metadata cards and copy-to-clipboard
  - *Compare:* Side-by-side with independent selectors
  - Keyboard shortcuts: `↑↓` cycle templates, `\` toggle sidebar
  - Live data editing: override business name, phone, city, headline with real-time preview updates
- **Template Preview (`/preview`):** Simplified browser with JSON data viewer and grid layout
- **AI-Controllable:** Yes — JIT OS can trigger revalidation, preview sites, check template health.

**Customer Journey Example:**
1. **Prospect Discovery:** GrowthEngine finds "Reliable Cooling & Heating" in Austin with 4.8★ rating.
2. **API Registration:** Prospect saved with `trade=hvac`, `business_name=Reliable Cooling & Heating`, `city=Austin`.
3. **Slug Generation:** `reliable-cooling-heating-austin` created via `generate_slug`.
4. **Content Generation:** Celery worker fetches business details, generates SiteContent with HVAC-specific headers.
5. **ISR Caching:** First visitor to `/reliable-cooling-heating-austin` triggers DB fetch, caches page for 3600s.
6. **Live Preview:** Sales team clicks "Preview" in dashboard → sees branded site with CTA to schedule consultation.
7. **Content Update:** Business owner changes phone number → API update triggers Celery revalidation task.
8. **Cache Update:** Next visitor gets fresh content — outdated ISR cache purged on revalidation.

See `reliantai-client-sites/README.md` for full development documentation.

### 💰 Money (Revenue & Dispatch)
**Purpose:** Handles incoming customer requests, job dispatching, and billing.
**Port:** 8000
**Key Features:**
- **Twilio SMS Webhook:** Receives SMS messages from customers.
- **AI Triage:** Uses CrewAI agents and Gemini to assess emergency levels (e.g., "My AC is leaking!" -> Emergency).
- **Stripe Integration:** Handles customer invoicing and subscriptions.
- **AI-Controllable:** Yes — JIT OS can modify billing code, generate invoices, handle refunds.

### 🚀 GrowthEngine (Lead Generation)
**Purpose:** Autonomous lead generation using Google Places API.
**Port:** 8003
**Key Features:**
- **Smart Filtering:** Finds businesses by rating, review count, and website presence.
- **Outreach Automation:** Generates personalized SMS pitches via Twilio.
- **CRM Integration:** Automatically adds leads to the Money service database.
- **AI-Controllable:** Yes — JIT OS can scan for leads, filter prospects, send messages.

### 🛡️ ComplianceOne (Governance)
**Purpose:** Continuously tracks organizational compliance against frameworks like SOC2, HIPAA, and GDPR.
**Port:** 8001
**Key Features:**
- **Automated Evidence Collection:** Ingests events from other services to prove compliance (e.g., user access logs).
- **Gap Analysis:** Identifies missing controls and generates remediation reports.
- **AI-Controllable:** Yes — JIT OS can generate compliance reports, check control status.

### 💸 FinOps360 (Cost Optimization)
**Purpose:** Analyzes cloud provider infrastructure costs.
**Port:** 8002
**Key Features:**
- **Right-Sizing:** Recommends downgrading underutilized instances.
- **Automated Tagging:** Integrates with AWS/Azure/GCP to apply compliance tags to cloud resources.
- **Anomaly Detection:** Alerts on sudden spikes in cloud spending.
- **AI-Controllable:** Yes — JIT OS can analyze costs, generate savings reports.

### 🧠 Orchestrator (Platform Brain)
**Purpose:** The autonomic nervous system of the platform.
**Port:** 9000
**Key Features:**
- **Six Async Loops:** Continuously runs loops for Health, Metrics, Scaling, Healing, AI Predictions, and Reporting.
- **Docker API Integration:** Automatically scales up containers (`docker scale`) when load increases.
- **WebSocket Feeds:** Pushes live system metrics to the dashboard.
- **AI-Controllable:** Yes — JIT OS can scale services, check health, view metrics.

### 🤖 Apex Framework (AI Agents)
**Purpose:** A comprehensive suite for deploying, managing, and interacting with AI agents.
**Components:**
- `apex-ui`: The Next.js frontend for agent interaction.
- `apex-agents`: The backend routing engine.
- `apex-mcp`: Integrates the Model Context Protocol (MCP) to allow agents to utilize external tools seamlessly.

### 🏢 Gen-H (Lead Gen)
**Purpose:** High-conversion templating library and lead generation for home service professionals.
**Port:** 8040
**Key Features:**
- Pre-built, customizable UI templates.
- Lead capture forms routed directly into the `Money` service CRM.

### 📊 Ops-Intelligence & Citadel
**Purpose:** Analytics, telemetry, and market intelligence.
**Key Features:**
- `Ops-Intelligence`: Aggregates logs, metrics, and traces for operator dashboards.
- `Citadel Ultimate A+`: Ingests census data and market metrics to rank territories and prioritize ad spend.

### 🔌 Integration & Auth (Event Bus)
**Purpose:** The central nervous system.
**Port:** 8080 (Auth), 8081 (Event Bus)
**Key Features:**
- **Event Bus (`:8081`):** Redis-backed pub/sub system with strict 64KB payload validation.
- **Auth Server (`:8080`):** Issues and validates JWTs using RS256 asymmetric keys.
- **Saga Orchestrator:** Manages distributed rollbacks.

---

## 6. Deployment & Operations

### Local Development
To spin up the entire platform locally:

```bash
# 1. Setup environment variables (or use JIT OS wizard)
cp .env.example .env

# 2. Run the deployment script
./scripts/deploy.sh local

# 3. Verify Health
./scripts/health_check.py -v

# 4. Open JIT OS
# http://localhost:8085
```

### Production Deployment
Production deployments use `docker-compose.yml` merged with `docker-compose.prod.yml` (if applicable), enforcing strict security, HSTS, and TLS.

```bash
./scripts/deploy.sh production
```

### Managing Services
- **View Logs:** `docker compose logs -f <service_name>`
- **Restart a Service:** `docker compose restart <service_name>`
- **Manually Scale:** `docker compose up -d --scale money=3`
- **JIT OS Control:** Just type "Scale up Money service" in the chat interface

---

## 7. API & Authentication

### Authentication Flow
All public endpoints are protected by `SecurityHeadersMiddleware` and `RateLimitMiddleware`.

1. Obtain a token via `POST /api/auth/login`.
2. Pass the token in the `Authorization: Bearer <token>` header.
3. Services validate the JWT locally using the public key provided by the Auth Service.

### Cross-Origin Resource Sharing (CORS)
CORS is strictly enforced. In `.env`, ensure `CORS_ORIGINS` accurately reflects your frontend domains (e.g., `https://app.reliantai.com`). Wildcards (`*`) are prohibited in production.

### JIT OS API
The JIT OS provides its own API for programmatic access:

- `GET /api/os/status` — Check configuration status
- `POST /api/os/setup` — Initialize with API keys
- `POST /api/os/chat` — Send message to AI
- `GET /api/os/execution-history` — View audit log

See `reliant-os/README.md` for complete API documentation.

---

## 8. Troubleshooting Guide

**1. JIT OS shows "Connection to Core AI failed"**
- **Cause:** Backend container not running or nginx proxy misconfigured.
- **Fix:** `docker compose ps | grep reliant-os`. Check logs: `docker compose logs -f reliant-os-backend`.

**2. Service X shows as `(unhealthy)` in Docker**
- **Cause:** The Docker healthcheck failed.
- **Fix:** Check the logs: `docker compose logs <service>`. Ensure the service is actually listening on the port. Verify that the `.env` variables are correctly populated.

**3. Authentication returns 503 Unavailable**
- **Cause:** The service cannot reach the `integration` Auth Server, or the JWT public key is missing.
- **Fix:** Ensure the `integration` container is healthy. Check the `AUTH_SERVICE_URL` variable.

**4. "invalid command line string" for Redis**
- **Cause:** Historically an issue with empty passwords in compose files.
- **Fix:** Ensure your repository is up to date (this was resolved in v3.0). Ensure `.env` is loaded correctly.

**5. Event Bus Payload Errors**
- **Cause:** You attempted to publish a message larger than 64KB.
- **Fix:** Truncate large strings or offload large payloads to a blob store (S3/GCS) and pass the URI in the event instead.

**6. JIT OS Code Execution Blocked**
- **Cause:** AI generated potentially dangerous code.
- **Fix:** Read the block reason in execution output. Rephrase request to avoid dangerous operations. Use specific paths.

**7. Lost Secret Vault After Restart**
- **Cause:** Docker volume not mounted or deleted.
- **Fix:** Re-enter keys in setup wizard. To prevent: backup volume regularly with `docker cp`.

**8. Client Site Not Updating After Content Change**
- **Cause:** ISR cache hasn't revalidated yet (default: 3600s).
- **Fix:** Trigger on-demand revalidation: `curl -X POST https://api.reliantai.com/api/revalidate -H "Authorization: Bearer <token>" -d '{"slug":"business-name-city"}'` or wait for next Celery beat cycle.

**9. Client Site Template 404**
- **Cause:** `template_id` in DB doesn't match any known template (hvac, plumbing, electrical, roofing, painting, landscaping).
- **Fix:** Update the prospect's `template_id` in the database to a valid value, or add a new template mapping in `reliantai-client-sites/lib/api.ts`.

---

*For further assistance, please consult the `Bug-Report.md` registry, the JIT OS chat interface, or reach out to the platform engineering team.*
