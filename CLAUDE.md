# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Platform Deploy & Control
```bash
./scripts/deploy.sh local          # full one-click deploy (builds images, starts all services, health checks)
./scripts/deploy.sh staging
./scripts/deploy.sh production

docker compose up -d               # start all services
docker compose down                # stop all services
docker compose logs -f [service]   # tail logs for a service
docker compose restart [service]   # restart single service

# Enable monitoring stack (Prometheus, Grafana, Alertmanager, Loki)
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Health & Verification
```bash
./scripts/health_check.py -v       # verbose per-service health
./scripts/health_check.py -j       # JSON output
./scripts/verify_integration.py    # full integration test suite

curl http://localhost:8000/health   # Money
curl http://localhost:8001/health   # ComplianceOne
curl http://localhost:8002/health   # FinOps360
curl http://localhost:8080/health   # Integration/Auth
curl http://localhost:9000/health   # Orchestrator
```

### Orchestrator API
```bash
curl http://localhost:9000/status
curl -X POST "http://localhost:9000/services/[name]/scale?target_instances=3"
curl -X POST http://localhost:9000/services/[name]/restart
curl http://localhost:9000/dashboard      # dashboard data (JSON)
```

### Database Migrations (root-level, targets main reliantai DB)
```bash
alembic upgrade head               # apply all migrations
alembic revision --autogenerate -m "description"
alembic downgrade -1
```

### B-A-P (Poetry ONLY — never pip, mixing corrupts virtualenv)
```bash
cd B-A-P
poetry install
poetry run pytest
poetry run uvicorn src.main:app --reload
poetry add <package>
poetry run black src/ && poetry run ruff check src/ && poetry run mypy src/
```

### ClearDesk (React/Vite frontend)
```bash
cd ClearDesk
npm install
npm run dev        # Vite dev server
npm run build      # tsc + Vite build → dist/
npm run lint
```

### Gen-H (React/Vite + Radix UI)
```bash
cd Gen-H
npm install
npm run dev
npm run build
```

### apex-ui (Next.js)
```bash
cd apex/apex-ui
npm install
npm run dev        # Next.js on port 3000
npm run build
npm run typecheck  # tsc --noEmit
```

### apex-agents (Python, pip-based)
```bash
cd apex/apex-agents
pip install -r requirements.txt
pytest
```

### reGenesis (pnpm workspace — design system)
```bash
cd reGenesis
pnpm install
pnpm run build             # builds tokens then packages
pnpm run dev               # runs @cyberarchitect/site-example
pnpm run test              # node --test packages/testing/*.mjs
pnpm run test:e2e          # playwright test
pnpm run lint
pnpm run generate          # regenerate tokens via tools/generate.mjs
```

### Acropolis (Rust workspace)
```bash
cd Acropolis
cargo build
cargo test
cargo run                  # adaptive_expert_platform binary
```

### DocuMancer (Electron desktop app)
```bash
cd DocuMancer
npm install
npm run dev                # electron in dev mode
npm run dist               # package for current platform
npm run test               # jest
npm run test:python        # pytest backend tests
```

### soviergn_ai (Bun + Astro)
```bash
cd soviergn_ai
bun install
bun run bun-server.ts      # serve Astro dist with COOP/COEP headers
```

### CyberArchitect (Node.js scraper)
```bash
cd CyberArchitect
node ultimate-website-replicator.js [url] [options]
```

### Integration Layer (individual services)
```bash
# Auth Service
cd integration/auth && pip install -r requirements.txt
uvicorn auth_server:app --port 8080
pytest test_auth_properties.py test_rbac_properties.py test_persistence.py -v

# Event Bus
cd integration/event-bus && pip install -r requirements.txt
uvicorn event_bus:app --port 8081
pytest test_event_bus_properties.py -v

# Saga Orchestrator
cd integration/saga && pip install -r requirements.txt
uvicorn saga_orchestrator:app --port 8090
```

### Money (HVAC Dispatch)
```bash
cd Money
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
pytest tests/test_integration_suite.py -v
```

---

## Architecture

### Service Port Map
| Port | Container | Role |
|------|-----------|------|
| 8000 | money | HVAC AI Dispatch (CrewAI + Gemini + Twilio) |
| 8001 | complianceone | SOC2/GDPR/HIPAA compliance tracking |
| 8002 | finops360 | Cloud cost management & budgeting |
| 8080 | integration/auth | OAuth2/JWT auth, RBAC (4 roles) |
| 8081 | integration/event-bus | Redis pub/sub + DLQ |
| 8090 | integration/saga | Distributed transaction coordinator (Kafka) |
| 9000 | orchestrator | AI predictions, auto-scaling, WebSocket dashboard |
| 5432 | postgres | Primary PostgreSQL |
| 6379 | redis | Cache, sessions, rate limiting |
| 8200 | vault | HashiCorp Vault (TLS, secrets) |
| 9090 | prometheus | Metrics (monitoring compose) |
| 9093 | alertmanager | Alerts (monitoring compose) |
| 3000 | grafana | Dashboards (monitoring compose) |

---

## Per-Folder Reference

### `integration/` — Central Nervous System
Every ReliantAI sub-project wires into this layer. Never bypass it.

- **`auth/`** — `auth_server.py`: FastAPI OAuth2/JWT service. SQLite user store (`user_store.py`), Redis for token revocation. Roles: `super_admin`, `admin`, `operator`, `technician`. Uses sliding-window rate limiter (`rate_limiter.py`). Fails hard on missing `AUTH_SECRET_KEY`.
- **`event-bus/`** — `event_bus.py`: Redis pub/sub with JSON schema validation, 24-hour retention, DLQ capped at 10 000 entries. Auth via `EVENT_BUS_API_KEY`.
- **`saga/`** — `saga_orchestrator.py`: Kafka-backed distributed transaction coordinator. Redis for idempotency keys. Configurable timeout (default 300 s) and max retries (default 3). Compensating transactions built in.
- **`gateway/`** — Kong config (`kong.yml`) for JWT-validated API routing + nginx load-balancer config.
- **`service-mesh/`** — Linkerd install manifest + circuit breaker (`circuit_breaker.py`).
- **`observability/`** — Grafana datasources + dashboards config.
- **`metacognitive_layer/`** — Self-reflective engine: `engine.py` (reasoning loop), `intent_predictor.py`, `healing_orchestrator.py`, `optimizer.py`, `knowledge_consolidator.py`. Has its own `pytest.ini`.
- **`nexus-runtime/`** — `memory.py`, `data_layout.py` — in-process memory/data abstraction used by metacognitive layer.
- **`shared/`** — **The integration contract files all services import:**
  - `jwt_validator.py` — `get_current_user` FastAPI dependency
  - `event_types.py` — `EventType` enum (16 types), `EventMetadata` Pydantic model with `max_length` constraints
  - `event_bus_client.py` — `publish_sync()` helper
  - `audit.py` — `emit_audit()`

### `Money/` — HVAC AI Dispatch
**Stack:** Python, FastAPI, CrewAI + Gemini, Twilio, Composio, LangSmith, PostgreSQL.

- `main.py` — HTTP server. Endpoints: `POST /dispatch`, `POST /sms` (Twilio webhook), `POST /whatsapp`, `GET /health`, `GET /run/{id}`, `GET /dispatches`. Bearer token or `x-api-key` auth. Validates Twilio signatures on webhook endpoints.
- `hvac_dispatch_crew.py` — CrewAI agents. 4-level urgency classifier: `LIFE_SAFETY` → 911, `EMERGENCY`, `URGENT`, `ROUTINE`. LangSmith tracing via `@traceable`. Twilio SMS with tenacity retry (3 attempts, 2 s wait).
- `billing.py`, `circuit_breaker.py`, `rate_limiter.py`, `retry_queue.py` — production resilience utilities.
- `database.py` — PostgreSQL via psycopg2. Functions: `save_dispatch`, `update_dispatch_status`, `get_dispatch`, `get_recent_dispatches`, `log_message`, `log_customer_event`.
- `frontend/` — Jinja2 templates served by main.py.
- **Required env:** `DISPATCH_API_KEY`, `GEMINI_API_KEY`, `TWILIO_SID`, `TWILIO_TOKEN`, `DATABASE_URL`.
- **Tests:** `tests/test_integration_suite.py` (pytest).

### `B-A-P/` — Business Analytics Platform
**Stack:** Python 3.11+, FastAPI, SQLAlchemy async, PostgreSQL (asyncpg), Redis, Celery, Google Gemini, Alembic.  
**Package manager: Poetry only.**

- `src/` — main package: `ai/`, `api/`, `config/`, `core/`, `etl/`, `models/`, `tasks/`, `utils/`
- `migrations/` — Alembic migrations (separate from root `migrations/`).
- `helm/` — Kubernetes Helm chart for production deploy.
- `scripts/` — data loading and maintenance scripts.
- **Linting:** black (line-length 100), ruff (line-length 100), mypy --strict.
- **Testing extras:** pytest-benchmark, locust (load testing), faker.

### `ClearDesk/` — Document Intelligence (React SPA)
**Stack:** React + Vite + TypeScript, deployed to Vercel (`vercel.json`).

- `src/contexts/DocumentContext.tsx` — global document state (React Context).
- `src/components/dashboard/Dashboard.tsx` — main shell component.
- Key deps: `mammoth` (DOCX), `pdfjs-dist` (PDF), `tesseract.js` (OCR), `xlsx`, `recharts`.
- `src/api/` — API client layer; `src/services/` — business logic; `src/hooks/` — custom hooks.
- No backend here — document processing runs in-browser.

### `Gen-H/` — HVAC Lead Generation (React SPA)
**Stack:** React + Vite + TypeScript + Radix UI + Tailwind.

- `hvac-lead-generator/` — lead capture flow.
- `hvac-template-library/` — reusable HVAC marketing templates.
- `src/api/` — API calls; `src/services/` — lead pipeline logic; `src/sections/` — page sections.
- Feeds leads into Money's dispatch system.

### `apex/` — Multi-tier Agent Platform
Three sub-projects, each with own Dockerfile:

- **`apex-agents/`** — Python FastAPI agent backend. `agents/`, `api/`, `core/`, `memory/`, `observability/`. Publishes events via `event_publisher.py` to the integration event bus. Uses `google-genai` for LLM calls.
- **`apex-ui/`** — Next.js 14 frontend (port 3000). `npm run dev` / `npm run typecheck`.
- **`apex-mcp/`** — MCP server (TypeScript). Built to `dist/`.
- **`infra/`** — infrastructure-as-code for apex services.

### `reGenesis/` — Design System (pnpm Workspace)
**Stack:** pnpm monorepo, TypeScript, Playwright for e2e.

- `packages/design-tokens/` — source of truth for all design tokens.
- `packages/motion/`, `packages/motion-tokens/` — animation system.
- `packages/ui/` — component library.
- `packages/types/`, `packages/schemas/`, `packages/scroll/`, `packages/testing/` — shared utilities.
- `apps/site-example/` — reference implementation / docs site.
- `tools/generate.mjs` — token generation script; `tools/replicator.mjs` — verify/replicate tooling.
- Build order matters: tokens → packages (sequential, not parallel).

### `Acropolis/` — Adaptive Expert Platform (Rust)
**Stack:** Rust workspace (Cargo), with GUI crate.

- `adaptive_expert_platform/src/` — main binary: `main.rs`, `agent.rs`, `auth.rs`, `batch.rs`, `cache.rs`, `cli.rs`, `ffi_julia.rs` (Julia FFI bridge), `lifecycle.rs`, `memory/`.
- `plugins/*` — plugin crates, each a workspace member.
- `gui/` — desktop GUI crate.
- `deny.toml` — cargo-deny config (license/security checks).

### `Citadel/` — Security & Observability Platform
**Stack:** Python backend + TimescaleDB + Redis (port 6380 to avoid conflict) + own Docker Compose.

- `backend/app.py` — Flask backend.
- `services/` — 11 specialized services: `causal_inference/`, `knowledge_graph/`, `multi_modal/`, `nl_agent/`, `orchestrator/`, `rule_engine/`, `time_series/`, `vector_search/`, `hierarchical_classification/`, `web_service/`, `shell_command/`.
- `desktop_gui.py` — Tkinter desktop control panel.
- `local_agent/` — local agent runner.
- Uses TimescaleDB (not standard PostgreSQL) — runs on port 5433 by default.

### `citadel_ultimate_a_plus/` — Market Intelligence & Lead Scoring
**Stack:** Python, Dash/Plotly dashboard, spaCy NER.

- `crawler.py` — web crawler for lead discovery.
- `census_ranker.py` — US census-based geographic lead ranking.
- `inference.py` — spaCy NER for location extraction + vertical classification. Falls back gracefully if models absent.
- `market/` — `census_ranker.py`, `target_verticals.json`.
- `sales/`, `marketing/` — pipeline and outreach modules.
- `dashboard_app.py` — Dash analytics dashboard.
- `schemas/` — Pydantic models; `tests/` — pytest suite.

### `BackupIQ/` — Backup Orchestration
**Stack:** Python async backend + vanilla JS frontend (not Electron, despite `package.json` having Electron scripts — the main interface is `index.html` + `script.js`).

- `src/` — `core/`, `monitoring/`, `storage/`.
- Cloud providers: AWS S3 (boto3), Google Cloud Storage, iCloud (pyicloud).
- `auth_integration.py` — wires into integration/shared JWT validator.
- Observability: OpenTelemetry + Prometheus + structlog.

### `DocuMancer/` — Document Management (Electron Desktop)
**Stack:** Electron + Node.js frontend, Python FastAPI backend.

- `backend/server.py` — FastAPI document server; `backend/converter.py` — format conversion; `backend/auth_integration.py`.
- `frontend/electron-main.js`, `renderer.js`, `preload.js` — Electron shell.
- `npm run test` — Jest; `npm run test:python` — pytest backend.
- `npm run dist` / `dist:linux` / `dist:win` / `dist:mac` — electron-builder packaging.

### `ops-intelligence/` — Operations Monitoring
**Stack:** Python FastAPI backend + React/Vite + TypeScript frontend.

- `backend/main.py`, `backend/models.py`, `backend/database.py`, `backend/routers/`.
- `frontend/src/` — React Vite app.
- Has its own `docker-compose.yml` + `start.sh`.

### `soviergn_ai/` — Memory Visualization & Documentation
**Stack:** Bun + Astro static site + React components + Rust (WASM bridge).

- `Nex-us/` — Astro site source (builds to `dist/`).
- `bun-server.ts` — Bun HTTP server that sets COOP/COEP headers (required for SharedArrayBuffer / WASM threading).
- `wasm-bridge.ts` — TypeScript ↔ WASM bridge.
- `doc_viz.rs` — Rust source compiled to WASM for in-browser graph visualization.
- `NexusMemoryViz.tsx`, `ExecutableTopology.jsx` — React visualization components.

### `CyberArchitect/` — Website Replication Toolkit (Node.js)
**Stack:** Node.js 18+, Puppeteer.

- `ultimate-website-replicator.js` — single-file CLI tool.
- Features: streaming pipeline, Brotli compression, AVIF/WebP conversion, sitemap discovery, robots.txt compliance, SHA-256 integrity manifest, incremental replication (`--incremental`), per-domain circuit breakers.
- `auth_middleware.js` — optional auth integration.

### `orchestrator/` — Platform Brain
**Stack:** Python FastAPI, single file `main.py`.

- Polls all services every 30 s; predicts resource needs 30 min ahead (requires `numpy`).
- Auto-scales 2–10 instances; auto-heals via `docker compose restart`.
- WebSocket endpoint for real-time dashboard updates.
- Imports `shared/security_middleware.py` for CORS, rate limiting, input validation, audit logging.

### `shared/` — Cross-Service Security Middleware (Python)
Imported via `sys.path.append` by ComplianceOne, FinOps360, orchestrator, and others.

- `security_middleware.py` — `SecurityHeadersMiddleware` (CSP, X-Frame-Options, HSTS), `RateLimitMiddleware`, `InputValidationMiddleware`, `AuditLogMiddleware`, `verify_api_key`, `create_cors_middleware`.
- `graceful_shutdown.py` — signal handlers for clean service shutdown.
- **CORS rule:** `CORS_ORIGINS` env var is required and must not contain `*`.

### `monitoring/` — Observability Config
Not a service itself — config files consumed by `docker-compose.monitoring.yml`.

- `prometheus.yml` — scrape configs for all services (15 s interval).
- `alert-rules.yml` — alerting rules.
- `alertmanager.yml` — alert routing.
- `loki-config.yml` + `promtail-config.yml` — log aggregation.
- `grafana/datasources.yml`, `grafana/dashboards/` — Grafana provisioning.

### `vault/` — HashiCorp Vault
- `vault-config.hcl` — file storage backend, TLS enforced, UI enabled.
- API: `https://vault.reliantai.io:8200`. Cluster: `:8201`.

### `nginx/` — Reverse Proxy
- `nginx.conf` — TLS termination and upstream routing.
- `ssl/` — TLS certificates.

### `migrations/` — Root Alembic Migrations
Targets the main `reliantai` PostgreSQL DB. Separate from B-A-P's own migrations.
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/reliantai
```

### `mcp/schemas/` — Protobuf Schemas
- `apex_service.proto`, `isn_service.proto`, `common.proto` — gRPC service definitions.
- `integration/k8s/hub-deployment.yaml` — Kubernetes deployment for hub service.

### `dashboard/` — Web Dashboard
Single-file `index.html` connecting to the Orchestrator WebSocket on `:9000`. No build step.

### `scripts/`
- `deploy.sh` — full platform deploy.
- `health_check.py` — service health poller.
- `verify_integration.py` — end-to-end integration tests.
- `backup_database.sh` — PostgreSQL dump.
- `setup_ssl.sh` — TLS certificate setup.

### `tests/`
- `test_integration_suite.py` — platform-wide integration tests (requires running services).

---

## Integration Contracts (Must Know)

### Auth Contract
All Python services that need auth:
```python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "integration", "shared")))
from jwt_validator import get_current_user
# Then in FastAPI:
# async def endpoint(user = Depends(get_current_user)): ...
```
Requires `AUTH_SERVICE_URL` (default `http://localhost:8080`) and `JWT_SECRET` env vars.

### Event Contract
All services that publish events:
```python
from integration.shared.event_types import EventType, EventPublishRequest
from integration.shared.event_bus_client import publish_sync
```
All 16 event types live in `EventType` enum in `integration/shared/event_types.py`.

### Security Middleware Contract
Python services that use the shared middleware:
```python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared")))
from security_middleware import SecurityHeadersMiddleware, RateLimitMiddleware, verify_api_key, create_cors_middleware
```
`CORS_ORIGINS` must be set (comma-separated, no wildcards).

### Hostile Audit Protocol
Before marking any task complete, capture proof:
```
Proof: <command> → <output> @ <timestamp>
```
Store in `proof/hostile-audit/`. CI enforced via `.github/workflows/ci-cd.yml`.

---

## Common Gotchas

| Gotcha | Reality |
|--------|---------|
| `pip install` in B-A-P | Use `poetry add` / `poetry install` only |
| Raw SQL outside B-A-P migrations | Each service owns its own DB schema; Money uses psycopg2 directly |
| Port 6379 conflict with Citadel | Citadel Redis runs on **6380**, not 6379 |
| `AUTH_SECRET_KEY` unset | Auth service raises `RuntimeError` at startup — hard fail by design |
| `CORS_ORIGINS` unset or `*` | ComplianceOne, FinOps360, and orchestrator all raise `RuntimeError` at startup |
| soviergn_ai without COOP/COEP | `SharedArrayBuffer` throws in all modern browsers — serve only via `bun-server.ts` |
| Acropolis workspace member name | It's `adaptive_expert_platform` in Cargo.toml, not `orchestrator` |
| reGenesis build order | Tokens must build before packages; `--parallel=false` is intentional |
| TimescaleDB in Citadel | Not standard PostgreSQL — use `timescale/timescaledb` image |
