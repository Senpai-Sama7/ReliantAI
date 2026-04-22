# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Platform Deploy & Control
```bash
./scripts/deploy.sh local          # builds all images, starts services, runs health checks
./scripts/deploy.sh staging
./scripts/deploy.sh production

docker compose up -d               # start all services defined in docker-compose.yml
docker compose down
docker compose logs -f [service]
docker compose restart [service]

# Full monitoring stack (Prometheus, Grafana, Alertmanager, Loki, Promtail)
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Health & Verification
```bash
./scripts/health_check.py -v       # verbose per-service health
./scripts/health_check.py -j       # JSON output
./scripts/verify_integration.py    # end-to-end integration test suite

curl http://localhost:8000/health   # Money
curl http://localhost:8001/health   # ComplianceOne
curl http://localhost:8002/health   # FinOps360
curl http://localhost:8080/health   # Integration/Auth
curl http://localhost:9000/health   # Orchestrator
```

### Orchestrator API (requires API_KEY header)
```bash
curl -H "X-API-Key: $ORCHESTRATOR_API_KEY" http://localhost:9000/status
curl -H "X-API-Key: $ORCHESTRATOR_API_KEY" -X POST \
  "http://localhost:9000/services/money/scale?target_instances=3"
curl -H "X-API-Key: $ORCHESTRATOR_API_KEY" -X POST \
  http://localhost:9000/services/money/restart
# WebSocket dashboard
wscat -c "ws://localhost:9000/ws?token=$ORCHESTRATOR_API_KEY"
```

### Root Database Migrations (targets `reliantai` DB)
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1
# B-A-P has its own separate Alembic config in B-A-P/
```

### B-A-P — Poetry ONLY (never pip; mixing corrupts virtualenv)
```bash
cd B-A-P
poetry install
poetry run uvicorn src.main:app --reload
poetry run pytest
poetry add <package>
poetry run black src/ && poetry run ruff check src/ && poetry run mypy src/
```

### Python Services (Money, ComplianceOne, FinOps360, apex-agents)
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000   # Money
uvicorn main:app --host 0.0.0.0 --port 8001   # ComplianceOne
uvicorn main:app --host 0.0.0.0 --port 8002   # FinOps360
pytest tests/ -v                               # Money tests
```

### Integration Services
```bash
cd integration/auth
uvicorn auth_server:app --port 8080
pytest test_auth_properties.py test_rbac_properties.py test_persistence.py test_rate_limit.py -v

cd integration/event-bus
uvicorn event_bus:app --port 8081
pytest test_event_bus_properties.py -v

cd integration/saga
uvicorn saga_orchestrator:app --port 8090

cd integration/metacognitive_layer
pytest tests/ -v   # has own pytest.ini
```

### Frontend Services
```bash
# ClearDesk (React/Vite)
cd ClearDesk && npm install && npm run dev   # Vite dev server
npm run build && npm run lint

# Gen-H (React/Vite + Radix UI + Tailwind)
cd Gen-H && npm install && npm run dev
npm run build

# apex-ui (Next.js 15)
cd apex/apex-ui && npm install && npm run dev   # port 3000
npm run build && npm run typecheck              # tsc --noEmit

# ops-intelligence frontend (React/Vite, port 5173)
cd ops-intelligence/frontend && npm install && npm run dev
```

### reGenesis Design System (pnpm workspace — Node ≥ 20)
```bash
cd reGenesis
pnpm install
pnpm run build              # build:tokens THEN packages (sequential, intentional)
pnpm run dev                # runs @cyberarchitect/site-example
pnpm run test               # node --test packages/testing/*.mjs
pnpm run test:e2e           # playwright test
pnpm run lint               # eslint
pnpm run generate           # regenerate tokens via tools/generate.mjs
pnpm run verify             # tools/replicator.mjs verify
```

### Acropolis (Rust workspace)
```bash
cd Acropolis
cargo build
cargo test
cargo run -- serve          # start HTTP server
cargo run -- init-admin     # initialize admin (password ≥ 12 chars required)
cargo run -- run <batch>    # batch run mode
cargo deny check            # license/security audit
```

### soviergn_ai (Bun + Astro — requires COOP/COEP headers)
```bash
cd soviergn_ai/Nex-us && npm run build   # build Astro → dist/
cd .. && bun run bun-server.ts           # serve with mandatory SharedArrayBuffer headers
```

### DocuMancer (Electron desktop app)
```bash
cd DocuMancer
npm install
npm run dev                 # electron dev mode
npm run test                # Jest
npm run test:python         # pytest backend/tests/
npm run dist:linux          # electron-builder package
```

### CyberArchitect (Node.js 18+ CLI)
```bash
cd CyberArchitect
node ultimate-website-replicator.js <url> [--incremental] [--brotli] [--avif]
```

### Citadel (own Docker Compose — ports 5433, 6380)
```bash
cd Citadel
docker compose -f compose.yaml up -d   # TimescaleDB:5433, Redis:6380
python backend/app.py
python desktop_gui.py                  # Tkinter control panel
```

### Generate JWT_SECRET / AUTH_SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Architecture

### Service Port Map
| Port | Service | Technology |
|------|---------|-----------|
| 8000 | Money | FastAPI + CrewAI + Gemini + Twilio |
| 8001 | ComplianceOne | FastAPI + PostgreSQL |
| 8002 | FinOps360 | FastAPI + PostgreSQL |
| 8080 | integration/auth | FastAPI + SQLite + Redis |
| 8081 | integration/event-bus | FastAPI + Redis pub/sub |
| 8090 | integration/saga | FastAPI + Kafka + Redis |
| 9000 | orchestrator | FastAPI + WebSocket + aiohttp |
| 8095 | ops-intelligence | FastAPI + SQLite |
| 3000 | apex/apex-ui | Next.js 15 |
| 5173 | ops-intelligence/frontend | React/Vite |
| 5432 | postgres | PostgreSQL 15 (platform) |
| 5433 | Citadel/timescaledb | TimescaleDB (own compose) |
| 6379 | redis | Redis (platform) |
| 6380 | Citadel/redis | Redis (own compose, avoids conflict) |
| 8200 | vault | HashiCorp Vault (TLS) |
| 9090 | prometheus | Metrics (monitoring compose) |
| 9093 | alertmanager | Alerts (monitoring compose) |
| 3000 | grafana | Dashboards (monitoring compose) |

### Dependency Graph
```
nginx:80/443
  ├── money:8000
  │     ├── postgres (money DB)
  │     ├── integration/auth:8080  ← bearer token verification
  │     ├── integration/event-bus:8081  ← publishes DISPATCH_COMPLETED
  │     └── [Twilio, Gemini, Stripe, HubSpot, Make.com, LangSmith]
  ├── complianceone:8001  → postgres (complianceone DB)
  ├── finops360:8002  → postgres (finops360 DB)
  ├── integration:8080
  │     ├── postgres (integration DB) + SQLite (user store)
  │     ├── redis:6379  ← token revocation, rate limiting
  │     ├── [kafka:9092]  ← saga orchestrator
  │     ├── complianceone:8001  ← via ComplianceOneClient
  │     └── finops360:8002  ← via FinOps360Client
  └── orchestrator:9000
        ├── money, complianceone, finops360, integration (health polls q30s)
        └── redis:6379 (via REDIS_URL)

apex/apex-agents → kafka:9092 (Kafka publisher, separate from event-bus)
B-A-P → postgres (asyncpg) + redis + Gemini API
Citadel → timescaledb:5433 + redis:6380 (own Redis, not shared)
citadel_ultimate_a_plus → SQLite (lead queue)
DocuMancer → integration/auth:8080 (JWT validation via shared jwt_validator.py)
BackupIQ → integration/shared (JWT) + [AWS S3, GCS, iCloud]
ops-intelligence → SQLite (own)
Acropolis → sled DB (auth) + OTLP endpoint + optional Julia FFI
```

---

## Per-Service Deep Reference

### `Money/` — HVAC AI Dispatch
**The revenue-generating core of the platform.** Customers text a problem; CrewAI agents triage urgency, assign a technician, send SMS confirmation.

**Entry point:** `main.py` (~1,248 lines)

**Auth (three methods, handled in `_authorize_request()`):**
1. `Authorization: Bearer <jwt>` → verifies against integration/auth:8080
2. `X-API-Key: <key>` → matches `DISPATCH_API_KEY`
3. Session cookie (CSRF-protected login form at `GET /login`)

**Twilio webhooks** (`POST /sms`, `POST /whatsapp`): validate `X-Twilio-Signature` HMAC before processing.

**All API endpoints:**
- `POST /dispatch` — main API dispatch endpoint (billing quota enforced)
- `POST /sms`, `POST /whatsapp` — Twilio webhooks
- `GET /health`, `GET /metrics` (Prometheus)
- `GET /run/{id}` — async job status poll
- `GET /dispatches` — recent history
- `GET /api/dispatch/{id}/timeline` — event-sourced state transitions
- `GET /api/dispatch/funnel` — pipeline funnel metrics
- `GET /api/metrics` — live dashboard metrics
- `GET /api/dispatches/search` — full-text search + filtering
- `PATCH /api/dispatch/{id}/status` — operator status override
- `GET /api/stream/dispatches` — SSE live feed (thread-safe queue fan-out)
- `GET /admin`, `GET /legacy-admin` — Jinja2 admin dashboards
- `GET /login`, `POST /login`, `GET /logout` — session auth
- `GET /integrations/status` — HubSpot/Sheets/Slack connection status
- `POST /webhooks/make/sales-lead` — Make.com HMAC-signed webhook
- `POST /webhooks/hubspot/contact-updated` — HubSpot HMAC-signed webhook
- `/billing/*` — Stripe checkout, plan management, webhook handler

**CrewAI crew (`hvac_dispatch_crew.py`):**
- 4-level urgency: `LIFE_SAFETY` (→ 911), `EMERGENCY`, `URGENT`, `ROUTINE`
- Tools: `triage_urgency` (Houston-specific classifier), `schedule_appointment`, `notify_technician`, `send_customer_update`
- Twilio SMS with tenacity retry (3 attempts, 2s wait)
- LangSmith tracing via `@traceable`

**Billing tiers (`billing.py`):** free (10/mo), starter ($99/100 dispatches), professional ($299/500), enterprise ($999/unlimited). Quota enforced before dispatch.

**Resilience:** Circuit breaker on auth service calls (3 failures → 30s open). In-memory dispatch store (max 1,000 entries) backed by PostgreSQL. Agent warm-up on startup.

**DB tables:** `dispatches`, `messages`, `customers`, `customer_events`

**Publishes:** `EventType.DISPATCH_COMPLETED` to integration/event-bus with `correlation_id=dispatch_id`

**Required env:** `DISPATCH_API_KEY`, `GEMINI_API_KEY`, `TWILIO_SID`, `TWILIO_TOKEN`, `DATABASE_URL`
**Optional:** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `MAKE_WEBHOOK_SECRET`, `HUBSPOT_API_KEY`, `HUBSPOT_WEBHOOK_SECRET`, `EVENT_BUS_URL`, `AUTH_SERVICE_URL`, `LANGSMITH_API_KEY`

---

### `ComplianceOne/` — Compliance Management
**What it does:** SOC2/GDPR/HIPAA compliance tracking — frameworks, controls, audits, evidence, violations.

**Middleware stack (applied in order):** SecurityHeaders → InputValidation → AuditLog → RateLimit (100 rpm). All from `shared/security_middleware.py`.

**CORS:** Requires explicit `CORS_ORIGINS` env var. Raises `RuntimeError` at startup if unset or contains `*`.

**DB tables:** `compliance_frameworks`, `compliance_controls`, `compliance_audits`, `compliance_evidence`, `compliance_violations`

**Endpoints:** `POST/GET /frameworks`, `POST/GET /controls`, `POST/GET /audits`, `POST /audits/{id}/complete`, `POST /evidence`, `POST/GET /violations`, `GET /dashboard`, `GET /health`

**Required env:** `DATABASE_URL`, `COMPLIANCEONE_API_KEY`, `CORS_ORIGINS`

---

### `FinOps360/` — Cloud Cost Management
**What it does:** Cloud cost tracking for AWS/Azure/GCP. Budgets, thresholds, optimization recommendations. Background task checks budgets hourly via `asyncio.create_task`.

**DB tables:** `cloud_accounts`, `cost_data`, `budgets`, `cost_alerts`, `cost_optimization_recommendations`, `resource_utilization`

**Endpoints:** `POST/GET /accounts`, `POST/GET /costs` (group_by=service|daily|raw), `POST/GET /budgets`, `GET /budgets/{id}/status`, `POST /recommendations/generate`, `GET/POST /recommendations/{id}/implement`, `GET /alerts`, `POST /alerts/{id}/acknowledge`, `GET /dashboard`, `GET /health`

**Startup:** Inserts sample AWS/Azure/GCP accounts on first run.

**Same middleware pattern as ComplianceOne.** Required env: `DATABASE_URL`, `FINOPS360_API_KEY`, `CORS_ORIGINS`

---

### `orchestrator/` — Platform Brain
**Single file `main.py`.** No database — in-memory metrics ring buffer + optional Redis.

**Polling schedule (all async background tasks):**
- Health checks: every 30s
- Metrics collection: every 60s
- Scaling decisions: every 2 min (serialized through `asyncio.Queue`)
- Auto-healing: every 60s
- AI predictions: every 5 min (Holt's double exponential smoothing, 2-step-ahead)
- Optimization reports: hourly

**Scaling bounds per service:** `money` (min 2, max 10), `complianceone` (min 1, max 5), `finops360` (min 1, max 5), `integration` (min 1, max 3, scaling disabled).

**Scale-up triggers:** response_time > 1000ms OR cpu > 75% OR error_rate > 5%
**Scale-down triggers:** cpu < 20% AND response_time < 100ms

**WebSocket:** `WS /ws?token=<api_key>` — closes with code 1008 if auth fails. Broadcasts real-time events to all connected clients.

**Required env:** `MONEY_URL`, `COMPLIANCEONE_URL`, `FINOPS360_URL`, `INTEGRATION_URL`, `REDIS_URL`, `API_KEY` (or `ORCHESTRATOR_API_KEY`), `CORS_ORIGINS`

---

### `integration/` — Central Nervous System
Every ReliantAI Python service connects through this layer. Never bypass it.

#### `integration/auth/auth_server.py`
- FastAPI OAuth2/JWT (HS256). **Hard fail at startup if `AUTH_SECRET_KEY` unset or < 32 chars.**
- SQLite user store (`user_store.py`) + Redis for token revocation (`memory_redis.py`).
- Roles: `super_admin`, `admin`, `operator`, `technician`.
- Token lifetimes: access 30 min, refresh 7 days (configurable via env).
- Rate limits: 5 registrations/min, 10 token requests/min (sliding window via `rate_limiter.py`).
- Prometheus metrics: `auth_token_issued_total`, `auth_token_validation_total`, `auth_login_failures_total`, `auth_request_duration_seconds`, `auth_rate_limit_rejections_total`.
- Test files: `test_auth_properties.py`, `test_rbac_properties.py`, `test_persistence.py`, `test_rate_limit.py`, `test_lifespan.py`, `test_verify_endpoint.py`.

#### `integration/event-bus/event_bus.py`
- Redis pub/sub with Pydantic schema validation on every message.
- 24-hour event retention. DLQ capped at 10,000 entries.
- Auth via `EVENT_BUS_API_KEY` Bearer token.
- Prometheus metrics: published, consumed, failed, DLQ size, processing duration, active subscribers.

#### `integration/saga/saga_orchestrator.py`
- Kafka-backed (`aiokafka`) distributed transaction coordinator.
- Redis for idempotency keys. Timeout: 300s. Max retries: 3.
- States: `pending → running → completed | failed → compensating → compensated`.
- Compensating transactions are defined per saga step and run in reverse on failure.

#### `integration/gateway/`
- `kong.yml` — Kong config for JWT-validated API routing. All 15 services wired. Prometheus plugin + correlation-id plugin on every service. Rate limit: 2000 rpm on event-bus.
- `nginx-lb.conf` — nginx upstream load balancer.

#### `integration/metacognitive_layer/`
Layer 5 of the APEX agent system. Self-reflective engine that learns from observations.
- `engine.py` (`MetacognitiveEngine`): asyncpg PostgreSQL backend. Confidence levels: CRITICAL (0.95), HIGH (0.85), MEDIUM (0.70), LOW (0.50). Bayesian confidence update with exponential smoothing (alpha=0.3).
- `intent_predictor.py` — predicts user intent from API call sequences.
- `healing_orchestrator.py` — autonomous healing decisions.
- `optimizer.py` (`AutonomousOptimizer`) — continuous optimization.
- `knowledge_consolidator.py` — knowledge distillation across agents.
- Has own `pytest.ini` and `tests/` directory.

#### `integration/nexus-runtime/`
- `memory.py` — mmap-based shared memory manager with atomic synchronization matching C++20 memory order semantics (RELAXED, ACQUIRE, RELEASE, ACQ_REL, SEQ_CST). Required by metacognitive layer.
- `data_layout.py` — memory region layout definitions.

#### `integration/cross_system_orchestrator.py`
Coordinates tasks across 4 major systems (APEX, Money, Citadel, Acropolis) using the A2A protocol bridge.

#### `integration/a2a_bridge.py`
Implements Google's A2A (Agent-to-Agent) protocol for cross-system agent communication. Task states: `submitted → working → input_required → completed | canceled | failed`. Artifact types: text, file, data, error.

#### `integration/intelligent_routing.py`
`IntelligentRouter` uses metacognitive layer predictions. Strategies: FASTEST, MOST_CAPABLE, COST_OPTIMIZED, MAL_PREDICTED, FALLBACK_SAFE.

#### `integration/hitl_optimizer.py`
Human-in-the-Loop optimizer. Decision types requiring human review: LOW_CONFIDENCE (< 0.65), HIGH_STAKES, NOVEL_DOMAIN, DISPUTED, SAFETY_CHECK, COMPLIANCE. Auto-approves low-risk patterns (confidence > 0.65 and not safety/compliance type).

#### `integration/skill_integration.py`
Exposes 3 core skills (strategic-execution-advisor, autonomous-prospect-engine, proposal-to-contract) via dynamic module loading from `../skills/`. Available as CLI, direct import, or HTTP.

#### `integration/shared/` — Contract files (imported by all Python services)
- `event_types.py` — `EventType` enum (16 events), `EventMetadata` model with `max_length` constraints
- `event_bus_client.py` — `publish_sync()` helper
- `jwt_validator.py` — `get_current_user` FastAPI dependency
- `audit.py` — `emit_audit()`
- `setup.py` — makes this importable as a package

**Standard import pattern used by Money, DocuMancer, BackupIQ, etc.:**
```python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "integration", "shared")))
from jwt_validator import get_current_user
from event_types import EventType
from event_bus_client import publish_sync
```

---

### `B-A-P/` — Business Analytics Platform
**Package manager: Poetry only.** Mixing pip corrupts the virtualenv.

**Stack:** Python 3.11+, FastAPI, SQLAlchemy async (asyncpg), PostgreSQL, Redis (cache), Celery, Google Gemini, Alembic. Own `docker-compose.yml` and Helm chart (`helm/`).

**Source layout (`src/`):**
- `api/routes/analytics.py` — `GET /summary` (persisted dataset stats), `POST /forecast` (AI forecast via Gemini)
- `api/routes/data.py` — dataset upload/management
- `api/routes/pipeline.py` — ETL pipeline control
- `models/analytics_models.py` — `AnalyticsSummary`, `ForecastRequest/Response`
- `models/data_models.py` — `ProcessedDataset` (SQLAlchemy async model)
- `core/database.py` — `db_manager` (asyncpg), `get_db` dependency
- `core/cache.py` — `cache_manager` (Redis)
- `ai/forecast_engine.py` — Gemini-backed forecasting
- `etl/` — ETL pipeline
- `tasks/` — Celery tasks
- `utils/`

**Middleware:** SecurityHeaders → GZip (min 1000 bytes) → Authentication → RateLimit.

**Own Alembic config** in `B-A-P/alembic.ini` + `B-A-P/migrations/` — separate from root `migrations/`.

**Linting:** black (line-length 100), ruff, mypy --strict. All enforced in pyproject.toml.

**Required env:** `DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`

---

### `apex/` — Multi-tier Agent Platform
Three sub-projects, each with own Dockerfile.

**`apex-agents/` (Python):** 4-layer probabilistic workflow:
- L2 `agents/layer2/` — uncertainty calibration (`calibration.py`, `uncertainty.py`, `workflow.py`)
- L3 `agents/layer3/` — specialized agents: `analytics.py`, `creative.py`, `cross_system_dispatch.py`, `dispatcher.py`, `research.py`, `sales.py`
- L4 `agents/layer4/` — quality assurance: `debate_agent.py`, `evolver.py`, `hostile_auditor.py`, `workflow.py`
- `event_publisher.py` — Kafka publisher (`KAFKA_BOOTSTRAP_SERVERS`). Publishes `ApexEvent` with type, data, trace_id, user_id.
- `http_event_bus.py` — HTTP fallback if Kafka unavailable.
- L5 is the metacognitive layer in `integration/metacognitive_layer/`.

**`apex-ui/`:** Next.js 15.1.0 + React 18.3.0. Scripts: `dev`, `build`, `start`, `lint`, `typecheck`.

**`apex-mcp/`:** TypeScript MCP server. Builds to `dist/`.

**Note:** apex-agents uses Kafka directly — separate from the HTTP event-bus service used by Money/ComplianceOne/FinOps360.

---

### `ClearDesk/` — Document Intelligence (React SPA, browser-only)
**No backend.** All document processing runs in-browser. Deployed to Vercel (`vercel.json`).

**Key deps:** `mammoth` (DOCX parsing), `pdfjs-dist` (PDF rendering), `tesseract.js` (OCR), `xlsx`, `recharts` (charts).

**Architecture:** `DocumentContext` (React Context, `src/contexts/DocumentContext.tsx`) → `Dashboard` component (`src/components/dashboard/Dashboard.tsx`). API layer (`src/api/`), services layer (`src/services/`), hooks (`src/hooks/`).

**Scripts:** `vite` dev, `tsc -b && vite build`, `eslint .`

---

### `Gen-H/` — HVAC Lead Generation (React SPA, browser-only)
**Stack:** React + Vite + TypeScript + Radix UI (full component suite) + Tailwind. Package name: `my-app`.

Feeds captured leads into Money/dispatch pipeline. `hvac-lead-generator/` (capture flow) + `hvac-template-library/` (marketing templates).

---

### `reGenesis/` — Design System (pnpm Workspace)
**pnpm 9.7.0, Node ≥ 20.** All packages under `@cyberarchitect/` namespace.

**Packages:**
- `design-tokens` — source of truth for all design tokens (colors, spacing, typography)
- `motion-tokens`, `motion` — animation system
- `ui` — component library
- `types`, `schemas`, `scroll`, `testing` — shared utilities

**Build is strictly ordered:** `design-tokens` and `motion-tokens` must build before `ui` and others. `--parallel=false` is intentional.

**Tools:** `tools/generate.mjs` (token generation), `tools/replicator.mjs` (verify/replicate — used to validate token consistency across packages).

**Testing:** `node --test packages/testing/*.mjs` (unit) + `playwright test` (e2e).

---

### `Acropolis/` — Adaptive Expert Platform (Rust)
**Rust workspace.** Members: `adaptive_expert_platform`, `plugins/*`, `gui`. Resolver: "2".

**`adaptive_expert_platform/src/`:**
- `main.rs` — Clap CLI: `serve` | `run <batch>` | `init-admin`
- `agent.rs` — agent management
- `auth.rs` — `AuthManager`: JWT auth + `sled` embedded DB. Password ≥ 12 chars enforced. JWT secret validated before admin init.
- `batch.rs` — batch run mode
- `server.rs` — HTTP server (Axum/warp)
- `cli.rs` — Clap CLI definitions
- `ffi_julia.rs` — Julia FFI bridge (optional at compile time)
- `lifecycle.rs` — service lifecycle management
- `memory/` — memory management subsystem
- `cache.rs` — caching layer
- `telemetry.rs` — OTLP telemetry export

`plugins/*` — each is a separate Cargo workspace member. `gui/` — desktop GUI crate.

`deny.toml` — cargo-deny for license and security vulnerability checks.

---

### `Citadel/` — Security & Observability Platform
**Own Docker Compose** (`compose.yaml`). Uses TimescaleDB (not standard PostgreSQL) on port **5433** and Redis on port **6380** — intentionally different from platform defaults to avoid conflicts.

**11 specialized services (`services/`):**
- `causal_inference/` — causal analysis engine
- `knowledge_graph/` — entity relationship graph
- `multi_modal/` — multi-modal AI processing
- `nl_agent/` — natural language agent with tool routing
- `orchestrator/` — Citadel-internal orchestrator (not the platform orchestrator)
- `rule_engine/` — rule evaluation
- `time_series/` — TimescaleDB time-series analysis
- `vector_search/` — vector similarity search
- `hierarchical_classification/` — multi-level classification
- `web_service/` — web data collection
- `shell_command/` — shell command execution

**Interfaces:** `backend/app.py` (Flask, `GET /api/health`), `desktop_gui.py` (Tkinter control panel), `local_agent/`.

---

### `citadel_ultimate_a_plus/` — Market Intelligence & Lead Scoring
**Stack:** Python, FastAPI, Dash/Plotly, spaCy NER.

**Key files:**
- `crawler.py` — web scraper for lead discovery
- `census_ranker.py` / `market/census_ranker.py` — US census-based geographic lead ranking
- `inference.py` — spaCy NER for location extraction + vertical classification. Graceful fallback if `en_core_web_sm` model absent.
- `dashboard_app.py` — Dash analytics dashboard. Auth: `CITADEL_DASHBOARD_API_KEY`. Webhook receiver validates HMAC (`OPENCLAW_WEBHOOK_SECRET`). CORS: `CITADEL_CORS_ORIGINS`.
- `lead_queue.py` — SQLite-based lead queue (`DB_PATH_DEFAULT`)
- `market/target_verticals.json` — target vertical definitions

**Required env:** `CITADEL_DASHBOARD_API_KEY`, `OPENCLAW_WEBHOOK_SECRET`, `CITADEL_DB_PATH`, `CITADEL_CORS_ORIGINS`

---

### `BackupIQ/` — Multi-Cloud Backup Orchestration
**Stack:** Python async + vanilla JS frontend (`index.html` + `script.js`). The `package.json` has Electron scripts but the primary interface is web-based.

**`src/` structure:** `core/` (backup orchestration), `monitoring/` (OpenTelemetry + Prometheus + structlog), `storage/` (cloud provider clients).

**Cloud providers:** AWS S3 (boto3), Google Cloud Storage, iCloud (pyicloud). `auth_integration.py` wires to `integration/shared/jwt_validator.py`.

---

### `ops-intelligence/` — Operations Monitoring Platform
**Port:** 8095. Own `docker-compose.yml` + `start.sh`.

**Backend (`backend/main.py`):** FastAPI with 8 domain routers:
- `/api/incidents` — Incident Commander (6-phase protocol)
- `/api/debt` — Technical Debt Quantifier (ROI-based scoring)
- `/api/costs` — FinOps Auditor (separate from FinOps360 service)
- `/api/pipelines` — Data Pipeline Architect (health monitoring)
- `/api/performance` — Performance Surgeon (bottleneck registry)
- `/api/migrations` — Migration Strategist (zero-downtime tracker)
- `/api/api-governance` — API Contract Enforcer
- `/api/revenue` — Revenue tracking
- `/api/health`, `/api/summary` — global summary across all domains

**DB:** SQLite (own, initialized on startup). CORS defaults to `http://localhost:5173`. Frontend: React/Vite (`frontend/src/`).

---

### `DocuMancer/` — Document Management (Electron Desktop)
**Stack:** Electron + Node.js frontend, Python FastAPI backend.

**`backend/server.py`:** FastAPI on `DOCUMANCER_PORT` (default 8000). Endpoints: `POST /convert` (document → structured JSON), `GET /health`. Auth via `backend/auth_integration.py` which uses `integration/shared/jwt_validator.py` (`get_current_user_from_shared_auth`).

**`backend/converter.py`:** Supports `.txt`, `.md`, `.json` natively; other formats via external tools.

**Frontend:** `electron-main.js` (main process), `renderer.js` + `preload.js` (renderer).

**Build:** `electron-builder`. Targets: `dist:win`, `dist:mac`, `dist:linux`. Packaging config in `electron-builder.yml`.

---

### `soviergn_ai/` — Memory Visualization
**Stack:** Bun + Astro + React + Rust → WASM.

**`Nex-us/`** — Astro site source → `dist/`.

**`bun-server.ts`** — Bun HTTP server. Sets `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. These headers are **non-negotiable** — `SharedArrayBuffer` (required by WASM threading) throws `TypeError` in all modern browsers without them. Cannot be served via plain static hosting or standard nginx without these headers at the edge.

**`doc_viz.rs`** — Rust compiled to WASM for in-browser graph visualization algorithms.

**`wasm-bridge.ts`** — TypeScript ↔ WASM bridge. **`NexusMemoryViz.tsx`**, **`ExecutableTopology.jsx`** — React visualization components.

---

### `CyberArchitect/` — Website Replication Toolkit
**Stack:** Node.js 18+, Puppeteer with stealth plugin, cheerio, sharp, svgo.

**Single-file CLI** `ultimate-website-replicator.js`. Notable features:
- True streaming pipeline (assets stream from network to disk, minimal RAM)
- Optional Brotli compression, AVIF/WebP conversion (via sharp)
- Sitemap discovery, robots.txt compliance, `--incremental` mode (ETag/Last-Modified)
- SHA-256 integrity manifest, per-domain circuit breakers, exponential backoff with jitter
- CSS URL rewriting, SVG optimization (svgo)

`auth_middleware.js` — optional JWT middleware for authenticated scraping.

---

### `mcp/schemas/` — Protobuf Service Definitions
gRPC interface definitions (not running services):
- `apex_service.proto` — `ApexOrchestrationService`: `InitiateOperation`, `GetOperationStatus`, `GetBusinessIntelligence` (→ B-A-P), `TriggerWebsiteReplication` (→ CyberArchitect), `TriggerWebsiteSynthesis` (→ reGenesis)
- `isn_service.proto` — Integration Service Namespace
- `common.proto` — shared types (`OperationResponse`, `EntityId`, etc.)

`integration/k8s/hub-deployment.yaml` — Kubernetes Deployment + Service for auth-service (2 replicas, `integration` namespace, `AUTH_SECRET_KEY` from Secret).

---

### `shared/` — Cross-Service Security Middleware (Python)
**Not a package — imported via `sys.path.append`.** Used by ComplianceOne, FinOps360, Orchestrator.

- `security_middleware.py`: `SecurityHeadersMiddleware` (CSP, X-Frame-Options, HSTS for staging/production, Permissions-Policy), `RateLimitMiddleware` (Redis-backed sliding window, falls back to in-memory), `InputValidationMiddleware`, `AuditLogMiddleware`, `verify_api_key` (FastAPI dependency), `create_cors_middleware` (fail-closed — raises `RuntimeError` if `CORS_ORIGINS` unset or contains `*`).
- `graceful_shutdown.py` — SIGTERM/SIGINT handlers for clean service shutdown.

---

### `monitoring/` — Observability Config (not a running service)
Config files for `docker-compose.monitoring.yml`:
- `prometheus.yml` — 15s scrape interval; scrapes money:8000, complianceone:8001, finops360:8002, orchestrator:9000, integration:8080, postgres.
- `alert-rules.yml`, `alertmanager.yml`, `loki-config.yml`, `promtail-config.yml`.
- `grafana/datasources.yml`, `grafana/dashboards/`.

---

### `vault/` — HashiCorp Vault
File storage at `/vault/data`. TLS enforced (`tls_disable = "false"`). API: `https://vault.reliantai.io:8200`. Cluster: `:8201`. Default lease 168h, max 720h. UI enabled.

---

### `nginx/` — Reverse Proxy / TLS Termination
`nginx.conf`: TLS termination, all HTTP → HTTPS redirect. Rate limit zones: `api` (10r/s), `auth` (5r/m). Upstreams: `money_backend`, `complianceone_backend`, `finops360_backend`, `orchestrator_backend`, `integration_backend`. Gzip enabled.

---

### `migrations/` — Root Alembic
Targets `reliantai` PostgreSQL DB (default: `postgresql://postgres:postgres@localhost:5432/reliantai`). Currently only the `versions/` directory + `env.py` — no migration files generated yet. **Separate from `B-A-P/migrations/`.**

---

### `scripts/`
- `deploy.sh` — full platform deploy (builds images, starts infra, starts services, health checks, loads sample data for local/staging)
- `health_check.py` — polls all service health endpoints, retries up to 60s
- `verify_integration.py` — end-to-end integration tests (requires running services)
- `backup_database.sh` — PostgreSQL dump
- `setup_ssl.sh` — TLS certificate setup for nginx

---

### `tests/`
`test_integration_suite.py` — platform-wide integration tests. Requires all services running. Not unit tests — tests actual HTTP endpoints.

---

### `dashboard/`
`index.html` — single-file web UI. Connects to Orchestrator WebSocket on `:9000`. Mounted into nginx container. No build step.

---

## Critical Constraints

| Constraint | Detail |
|------------|--------|
| **B-A-P: Poetry only** | `pip install` corrupts the virtualenv. Always `poetry add` / `poetry install`. |
| **AUTH_SECRET_KEY** | Auth service raises `RuntimeError` at startup if unset or < 32 chars. Hard fail by design. |
| **CORS_ORIGINS** | ComplianceOne, FinOps360, Orchestrator raise `RuntimeError` at startup if unset or contains `*`. |
| **soviergn_ai headers** | `SharedArrayBuffer` requires COOP + COEP headers. Only `bun-server.ts` provides these. Plain nginx/static hosting breaks WASM threading. |
| **Citadel port isolation** | Redis on 6380, TimescaleDB on 5433 — avoids conflict with platform Redis (6379) and PostgreSQL (5432). |
| **Dual event buses** | apex-agents publishes to Kafka directly. Money/ComplianceOne/FinOps360 use the HTTP event-bus service (which uses Redis). These are separate channels. |
| **Acropolis workspace name** | `adaptive_expert_platform` in Cargo.toml — not `orchestrator` or `acropolis`. |
| **reGenesis build order** | Tokens must build before packages. `--parallel=false` is intentional, not an optimization to remove. |
| **Hostile Audit Protocol** | Every completed change requires proof stored in `proof/hostile-audit/`. Format: `Proof: <command> → <output> @ <timestamp>`. Enforced in CI. |
| **sys.path imports** | Python services import shared code via `sys.path.append` (not pip packages). Path is always relative to the calling file's `__file__`. |
| **Acropolis admin password** | Must be ≥ 12 characters. Hard-checked in `auth.rs`. |
| **Orchestrator scaling queue** | All scaling decisions go through a single `asyncio.Queue` consumer — prevents concurrent scale operations on the same service. |
