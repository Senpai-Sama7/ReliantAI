# ReliantAI Platform

**Autonomous, Self-Managing, AI-Powered Enterprise Platform**

A federated multi-service platform built around a central integration nervous system. Combines a real-money HVAC dispatch business (Money), enterprise SaaS analytics (B-A-P), compliance and cost management, a multi-tier agent framework (APEX), and a full observability stack — all wired through shared auth, event bus, and saga coordination.

---

## Platform Architecture

```
                        ┌──────────────────────────────────┐
                        │         nginx :80/:443            │
                        │   TLS termination, rate limiting  │
                        └──────┬──────┬──────┬──────┬───────┘
                               │      │      │      │
              ┌────────────────┘      │      │      └──────────────────┐
              ▼                       ▼      ▼                         ▼
  ┌────────────────────┐  ┌─────────────────────┐         ┌────────────────────┐
  │   money :8000      │  │  complianceone :8001 │         │  orchestrator :9000│
  │  HVAC AI Dispatch  │  │  FinOps360 :8002     │         │  AI predictions    │
  │  CrewAI + Gemini   │  │  SOC2/GDPR/AWS costs │         │  auto-scaling      │
  │  Twilio + Stripe   │  │  PostgreSQL          │         │  self-healing      │
  └────────┬───────────┘  └──────────┬──────────┘         │  WebSocket API     │
           │                         │                      └────────┬───────────┘
           │                         │                               │
           └─────────────────────────┼───────────────────────────────┘
                                     │ all services authenticate + publish events through
                                     ▼
              ┌──────────────────────────────────────────────────────┐
              │              integration/ (Central Nervous System)    │
              │  auth :8080      event-bus :8081     saga :8090       │
              │  OAuth2/JWT/RBAC  Redis pub/sub      Kafka + Redis    │
              │  SQLite users     16 event types     distributed tx   │
              │  rate limiting    DLQ (10k cap)      compensation     │
              ├──────────────────────────────────────────────────────┤
              │  metacognitive_layer  ← Layer 5 of APEX agent system  │
              │  nexus-runtime        ← mmap shared memory (C++20)    │
              │  a2a_bridge           ← Google A2A cross-system proto  │
              │  intelligent_routing  ← MAL-predicted task routing    │
              │  hitl_optimizer       ← Human-in-the-loop queue       │
              └──────────────────────────────────────────────────────┘
                                     │
              ┌──────────────────────┴──────────────────────┐
              │           Infrastructure                      │
              │  PostgreSQL :5432   Redis :6379              │
              │  Vault :8200        Kafka :9092 (saga)       │
              └──────────────────────────────────────────────┘
```

### Full Service Map

| Service | Port | Stack | Purpose |
|---------|------|-------|---------|
| Money | 8000 | FastAPI + CrewAI + Gemini + Twilio | HVAC AI dispatch (revenue service) |
| ComplianceOne | 8001 | FastAPI + PostgreSQL | SOC2/GDPR/HIPAA compliance tracking |
| FinOps360 | 8002 | FastAPI + PostgreSQL | Cloud cost management (AWS/Azure/GCP) |
| integration/auth | 8080 | FastAPI + SQLite + Redis | OAuth2/JWT, RBAC (4 roles) |
| integration/event-bus | 8081 | FastAPI + Redis pub/sub | Async event distribution, DLQ |
| integration/saga | 8090 | FastAPI + Kafka + Redis | Distributed transaction coordination |
| orchestrator | 9000 | FastAPI + WebSocket + aiohttp | AI predictions, auto-scaling, self-healing |
| ops-intelligence | 8095 | FastAPI + SQLite | Operations monitoring (8 domain routers) |
| apex/apex-ui | 3000 | Next.js 15 | Agent platform UI |
| Citadel | — | Flask + TimescaleDB:5433 + Redis:6380 | Security & observability (11 services) |
| PostgreSQL | 5432 | postgres:15-alpine | Platform primary DB |
| Redis | 6379 | redis:7-alpine | Cache, sessions, rate limiting |
| Vault | 8200 | HashiCorp Vault | Secrets management (TLS enforced) |
| Prometheus | 9090 | prom/prometheus | Metrics (monitoring compose) |
| Grafana | 3000 | grafana/grafana | Dashboards (monitoring compose) |

---

## Core Services

### Money — HVAC AI Dispatch
The primary revenue service. Houston HVAC customers text or WhatsApp a problem; CrewAI agents backed by Google Gemini perform 4-level urgency triage (`LIFE_SAFETY → 911`, `EMERGENCY`, `URGENT`, `ROUTINE`), assign a technician, and send SMS confirmation via Twilio.

**Three auth methods handled simultaneously:** Bearer JWT (verified against integration/auth:8080), `X-API-Key` header, or session cookie (CSRF-protected login form). Twilio webhook endpoints independently validate `X-Twilio-Signature` HMAC.

**Key capabilities:**
- Stripe billing (free/starter $99/professional $299/enterprise $999) with per-plan dispatch quotas
- SSE live dispatch feed with thread-safe queue fan-out
- Event-sourced state machine with `/api/dispatch/{id}/timeline` endpoint
- Make.com and HubSpot HMAC-signed webhook receivers
- Full Prometheus metrics at `/metrics`
- Jinja2 admin dashboards at `/admin`
- Circuit breaker on auth service calls (3 failures → 30s open)

**Publishes** `EventType.DISPATCH_COMPLETED` to integration/event-bus on every completed dispatch.

### ComplianceOne — Compliance Management
SOC2/GDPR/HIPAA compliance tracking. Manages frameworks, controls, audits, evidence, and violations. Applies the full `shared/security_middleware.py` stack. Refuses to start if `CORS_ORIGINS` is unset or contains `*`.

### FinOps360 — Cloud Cost Management
Multi-cloud cost tracking and optimization. Budgets with threshold alerts checked hourly via `asyncio.create_task`. AI-generated optimization recommendations. Sample AWS/Azure/GCP accounts inserted on first startup. Same security constraints as ComplianceOne.

### Orchestrator — Platform Brain
Single-file `main.py`. Six background async loops: health checks (30s), metrics collection (60s), scaling decisions (2 min — serialized via `asyncio.Queue`), auto-healing (60s), AI predictions via Holt's double exponential smoothing (5 min), optimization reports (hourly).

Scaling bounds: Money 2–10 instances, ComplianceOne/FinOps360 1–5, integration 1–3 (no auto-scale). Scale-up triggers: response_time > 1000ms OR cpu > 75% OR error_rate > 5%. WebSocket endpoint broadcasts real-time events to the dashboard.

---

## Integration Layer

### Auth Contract
```python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "integration", "shared")))
from jwt_validator import get_current_user   # FastAPI Depends() injection
```
Auth service hard-fails at startup if `AUTH_SECRET_KEY` is unset or < 32 chars.

### Event Contract
```python
from integration.shared.event_types import EventType   # 16 canonical event types
from integration.shared.event_bus_client import publish_sync
```

**16 event types:** `lead.created`, `lead.qualified`, `dispatch.requested`, `dispatch.completed`, `document.processed`, `agent.task.created`, `agent.task.completed`, `analytics.recorded`, `saga.started`, `saga.completed`, `saga.failed`, `user.created`, `user.updated`, `user.deleted`, `audit.log.recorded`

All `EventMetadata` fields have `max_length` constraints (hardening against memory exhaustion attacks).

### Advanced Integration Modules
- **`a2a_bridge.py`** — Google's A2A (Agent-to-Agent) protocol for cross-system agent communication between APEX, Money, Citadel, and Acropolis. Task lifecycle: `submitted → working → input_required → completed | canceled | failed`.
- **`intelligent_routing.py`** — Routes tasks using metacognitive layer predictions. Strategies: FASTEST, MOST_CAPABLE, COST_OPTIMIZED, MAL_PREDICTED, FALLBACK_SAFE.
- **`hitl_optimizer.py`** — Human-in-the-loop review queue. Auto-approves patterns with confidence > 0.65 that aren't safety/compliance type. Priority-queued for human review: LOW_CONFIDENCE, HIGH_STAKES, NOVEL_DOMAIN, DISPUTED, SAFETY_CHECK, COMPLIANCE.
- **`metacognitive_layer/`** — Layer 5 of APEX. Learns from observations using Bayesian confidence updates with exponential smoothing (alpha=0.3). Confidence: CRITICAL (0.95), HIGH (0.85), MEDIUM (0.70), LOW (0.50).
- **`nexus-runtime/`** — mmap-based shared memory with atomic synchronization matching C++20 memory order semantics (RELAXED, ACQUIRE, RELEASE, ACQ_REL, SEQ_CST).

---

## Agent Frameworks

### APEX (5-Layer Probabilistic System)
- **L2** — Uncertainty calibration
- **L3** — Specialized agents: analytics, creative, research, sales, cross-system dispatch
- **L4** — Quality assurance: debate, evolution, hostile auditor
- **L5** — Metacognitive engine (in `integration/metacognitive_layer/`): learns patterns, predicts intents, orchestrates autonomous healing

APEX agents publish to Kafka directly (`apex/apex-agents/event_publisher.py`). This is a **separate channel** from the HTTP event-bus service used by Money/ComplianceOne/FinOps360.

### CrewAI (Money Service)
4-agent crew with Google Gemini. Houston HVAC-specific urgency classifier. Tenacity retry on all Twilio sends (3 attempts, 2s wait). LangSmith tracing on all agent calls.

### Acropolis (Rust)
Polyglot agent orchestration with Julia FFI bridge for numerical computing. CLI: `serve | run <batch> | init-admin`. Admin password enforced ≥ 12 chars. OTLP telemetry export. `sled` embedded DB for auth storage.

---

## Frontend & Design

### ClearDesk
Browser-only React SPA. Parses DOCX (mammoth), PDF (pdfjs-dist), images (Tesseract.js OCR), XLSX (xlsx) in-browser. No backend. Deployed to Vercel.

### Gen-H
React SPA with Radix UI + Tailwind. HVAC lead capture flows → feeds into Money dispatch.

### reGenesis (Design System)
pnpm workspace (Node ≥ 20). `@cyberarchitect/design-tokens` is the canonical source of truth. Build order is strictly enforced: tokens first, packages second (sequential, `--parallel=false` is intentional).

### soviergn_ai
Astro static site served via Bun. Rust compiled to WASM for in-browser graph visualization. **Requires** `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp` — only `bun-server.ts` provides these. Without them, `SharedArrayBuffer` (required by WASM threading) throws a `TypeError` in all modern browsers.

---

## Security Architecture

**CORS (fail-closed):** ComplianceOne, FinOps360, and Orchestrator raise `RuntimeError` at startup if `CORS_ORIGINS` is unset or contains `*`. The platform refuses to start in an insecure configuration.

**nginx rate limiting:** `api` zone (10 req/s), `auth` zone (5 req/min).

**Vault:** TLS enforced. No `tls_disable = true`. Default lease 168h, max 720h.

**Hostile Audit Protocol:** Every code change requires `Proof: <command> → <output> @ <timestamp>` stored in `proof/hostile-audit/`. Enforced in CI via `.github/workflows/ci-cd.yml`.

---

## Quick Start

### Prerequisites
Docker, Docker Compose, Bash.

### 1. Configure Environment
```bash
cp .env.example .env
# Required keys — service will hard-fail at startup if any are missing:
# POSTGRES_USER, POSTGRES_PASSWORD
# DISPATCH_API_KEY, GEMINI_API_KEY, TWILIO_SID, TWILIO_TOKEN
# COMPLIANCEONE_API_KEY, FINOPS360_API_KEY
# REDIS_PASSWORD
# CORS_ORIGINS (comma-separated, no wildcards)
# AUTH_SECRET_KEY, JWT_SECRET (generate: python -c "import secrets; print(secrets.token_urlsafe(64))")
```

### 2. Deploy
```bash
./scripts/deploy.sh local
```

### 3. Verify
```bash
./scripts/health_check.py -v
./scripts/verify_integration.py
```

### 4. Access
- **Dashboard:** `http://localhost:9000/dashboard`
- **Money admin:** `http://localhost:8000/admin`
- **With monitoring:** `docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d`
  - Prometheus: `http://localhost:9090`
  - Grafana: `http://localhost:3000`

---

## Development Reference

### Package Managers
| Project | Manager | Constraint |
|---------|---------|-----------|
| B-A-P | **Poetry only** | pip corrupts virtualenv |
| Money, ComplianceOne, FinOps360, orchestrator, apex-agents | pip + requirements.txt | |
| ClearDesk, Gen-H, DocuMancer, apex-ui, apex-mcp | npm | |
| reGenesis | **pnpm 9.7.0** (Node ≥ 20) | workspace protocol |
| soviergn_ai | bun | runtime + Astro |
| Acropolis | cargo | Rust workspace |

### Database Ownership (no cross-service SQL)
| DB | Owner | Engine |
|----|-------|--------|
| `money` | Money | PostgreSQL 15 |
| `complianceone` | ComplianceOne | PostgreSQL 15 |
| `finops360` | FinOps360 | PostgreSQL 15 |
| `integration` | integration/auth | PostgreSQL 15 + SQLite (user store) |
| `reliantai` | root Alembic migrations | PostgreSQL 15 |
| B-A-P DB | B-A-P | PostgreSQL (asyncpg, own connection) |
| Citadel | Citadel | TimescaleDB :5433 |
| ops-intelligence | ops-intelligence | SQLite |
| citadel_ultimate_a_plus | citadel_ultimate_a_plus | SQLite |
| Acropolis | Acropolis | sled (embedded) |

### Testing
```bash
./scripts/verify_integration.py                          # platform-wide (requires running services)
cd Money && pytest tests/test_integration_suite.py -v
cd integration/auth && pytest -v
cd integration/event-bus && pytest test_event_bus_properties.py -v
cd integration/metacognitive_layer && pytest tests/ -v
cd B-A-P && poetry run pytest
cd DocuMancer && npm test && npm run test:python
cd reGenesis && pnpm run test && pnpm run test:e2e
cd Acropolis && cargo test
```

### Adding a New Python Service
1. `sys.path.append("../integration/shared")` → import `get_current_user`, `EventType`, `publish_sync`
2. `sys.path.append("../shared")` → import from `security_middleware`
3. Set `CORS_ORIGINS` env var (required; no wildcards)
4. Add to `docker-compose.yml` with health check
5. Add Prometheus scrape config to `monitoring/prometheus.yml`
6. Add upstream to `nginx/nginx.conf`
7. Capture proof in `proof/hostile-audit/`

---

## Documentation

- [`PLATFORM_GUIDE.md`](./PLATFORM_GUIDE.md) — Full architecture and operations guide
- [`USER_MANUAL.md`](./USER_MANUAL.md) — Service-by-service user manual
- [`AGENTS.md`](./AGENTS.md) — Agent operational guide (deployment, health, service control commands)
- [`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md) — Command cheat sheet
- [`PRODUCTION_CHECKLIST.md`](./PRODUCTION_CHECKLIST.md) — Pre-production checklist
- [`CLAUDE.md`](./CLAUDE.md) — Deep per-service reference for AI-assisted development
- [`integration/saga/SAGA_GUIDE.md`](./integration/saga/SAGA_GUIDE.md) — Distributed transaction guide
