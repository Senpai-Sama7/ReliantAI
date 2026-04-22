# Citadel A+ Agent Guide

**Last updated:** 2026-02-24

## Project Overview

Citadel is a local-first outbound lead pipeline. It scouts a public business website, qualifies the lead, generates a static site preview, drafts a structured outreach email, and tracks all state transitions in SQLite.

Default operation requires no paid services:
- Deployment backend defaults to `local_fs` (copies into `workspace/deploys/`)
- Email backend defaults to `local_outbox` (writes `.eml` files into `workspace/outbox/`)
- Operator UI/API runs locally via FastAPI

Primary source files:
- `orchestrator.py`: end-to-end pipeline runner and CLI
- `lead_queue.py`: SQLite schema, state machine, metrics, webhook application logic
- `dashboard_app.py`: dashboard UI + read APIs + signed webhook endpoint

## Hostile Audit Persistence

- Append every hostile-audit checkpoint and verification result to the root `PROGRESS_TRACKER.md`.
- Do not mark dashboard API, webhook, or state-machine fixes complete without a real command result, test run, health check, or request/response artifact saved under `proof/hostile-audit/<timestamp>/`.
- Reproduce before patching. If the original exploit path fails, record the failed method and the replacement verification path.
- Keep dashboard and read APIs fail-closed when API keys or webhook secrets are missing.
- If a scanner or service cannot run, record the exact blocker and fallback review path instead of implying success.

## Repository Layout and Module Boundaries

Top-level layout:
- `orchestrator.py`: orchestration flow (`scout -> qualify -> build -> outreach -> optional deploy -> optional email`)
- `lead_queue.py`: persistence and business state transitions
- `dashboard_app.py`: read-only operational dashboard and webhook intake
- `market/`: market weighting logic (`market/census_ranker.py`) and config (`market/target_verticals.json`)
- `schemas/`: JSON schema contracts across pipeline stages
- `scripts/`: operational helpers (currently `send_webhook_event.py`)
- `tests/`: unit/integration/security/schema tests
- `workspace/`: runtime outputs (`state/`, `logs/`, `builds/`, `deploys/`, `outbox/`)

Module ownership:
- Only `lead_queue.py` should own table definitions and pipeline transition rules.
- `orchestrator.py` should produce contract-valid payloads and call DB methods; it should not duplicate DB state logic.
- `dashboard_app.py` should stay focused on read endpoints and webhook verification/dispatch.

Root-level shims (not primary source files):
- `census_ranker.py`: 4-line convenience shim that imports and calls `market.census_ranker.main()`. Not referenced by any other module or the Makefile. The canonical implementation is `market/census_ranker.py`.
- `target_verticals.json`: root duplicate removed in Phase 1. Canonical config is `market/target_verticals.json`.

## Key Configuration and Manifest Files

Present and authoritative:
- `requirements.txt`: Python dependency manifest
- `Makefile`: standard local commands (`install`, `init-db`, `ranker`, `dashboard`, `run`, `test`)
- `.env.template`: environment variable contract
- `.github/workflows/ci.yml`: GitHub Actions CI (runs Actionlint workflow checks + `pytest -q` on push/PR)
- `Dockerfile` and `docker-compose.yml`: containerized dashboard runtime
- `schemas/*.json`: data boundary contracts

Not present in this repository at this revision:
- `pyproject.toml`
- `package.json`
- `Cargo.toml`
- `Pipfile`
- `setup.py`
- `tox.ini`

Special note on target vertical config:
- `market/target_verticals.json` is the only canonical file used by both `Makefile` and `market/census_ranker.py`.

## Technology Stack

- Language: Python
- Web framework: FastAPI
- HTTP client: `httpx`
- HTML parsing: BeautifulSoup + `lxml`
- Validation: `jsonschema` (Draft 7)
- DB: SQLite (`sqlite3` stdlib)
- Config loading: `python-dotenv`
- Testing: `pytest` + FastAPI TestClient
- Optional market data fetcher: `requests` (Census CBP API)
- Optional runtime checkpointing: Bash + `aws` CLI + `sqlite3`

## Build, Run, and Test Commands

Make-based workflow:
- `make venv` — create virtualenv in `.venv/`
- `make install` — install deps into venv
- `make init-db` — initialize SQLite database
- `make ranker` — run Census CBP market ranker
- `make dashboard` — start FastAPI dashboard
- `make run URL=https://example.com` — run pipeline for a URL
- `make test` — run pytest suite
- `make clean` — remove `.pytest_cache`
- `make lint` — run `py_compile` syntax checks on core modules

Direct commands:
- `python lead_queue.py init`
- `python lead_queue.py snapshot`
- `python market/census_ranker.py --config market/target_verticals.json`
- `python orchestrator.py https://example.com --dry-run`
- `python orchestrator.py https://example.com --approve --send-email`
- `python orchestrator.py https://example.com --json`
- `uvicorn dashboard_app:app --host 127.0.0.1 --port 8888`
- `pytest -q`

Dockerized dashboard:
- `docker compose up --build`
- Exposes `127.0.0.1:8888`

## Runtime Architecture and Data Flow

Pipeline in `orchestrator.py`:
1. Load env/config and ensure runtime directories.
2. Scout target website (HTTP fetch + HTML parsing + local-business signals).
3. Qualify and score lead.
4. Validate payloads with JSON schemas.
5. Upsert lead and transition state in SQLite.
6. Build static site artifacts into `workspace/builds/<lead_slug>/<run_id>/`.
7. Draft outreach payload and persist draft.
8. If `--approve`, mark approved and run deployment backend.
9. If `--send-email`, send via configured backend and mark as emailed.

Shared state model:
- `orchestrator.py` and `dashboard_app.py` both use `LeadQueueDB` against the same SQLite file (`CITADEL_DB_PATH`).

## Pipeline State Machine and Eventing

Pipeline statuses (`lead_queue.py`):
- `scouted`
- `qualified`
- `built`
- `approved`
- `deployed`
- `emailed`
- `replied`
- `disqualified`

Valid transitions:
- `scouted -> qualified|disqualified`
- `qualified -> built|disqualified`
- `built -> approved|disqualified`
- `approved -> deployed|disqualified`
- `deployed -> emailed|disqualified`
- `emailed -> replied`
- `replied` terminal
- `disqualified` terminal

Event model:
- Every major action is recorded in `lead_events` with `event_type`, `actor`, optional `run_id`, and JSON payload.
- Webhook events are idempotent through `webhook_receipts` unique key `(source, external_event_id)`.

## Data Contracts (JSON Schemas)

Schemas in `schemas/` are hard validation gates in runtime and tests:
- `qualifier_output.json`: required lead qualification payload
- `builder_input.json`: required static site generation input
- `build_manifest.json`: required build output summary
- `outreach_output.json`: required outreach draft payload

`outreach_output.json` enforces a 7-beat structure:
- `pattern_break`
- `cost_of_inaction`
- `belief_shift`
- `mechanism`
- `proof_unit`
- `offer`
- `action`

## Database Model and Persistence Rules

Tables created by `LeadQueueDB.init_db()`:
- `leads`
- `lead_events`
- `builds`
- `deployments`
- `outreach`
- `replies`
- `webhook_receipts`
- `db_version` (schema migration tracking; seeded with version 1 on fresh DB)

DB connection behavior (`LeadQueueDB.tx()`):
- `PRAGMA journal_mode=WAL`
- `PRAGMA foreign_keys=ON`
- `PRAGMA busy_timeout=5000`
- `PRAGMA synchronous=NORMAL`

Operational characteristics:
- Writes are wrapped in transaction context manager with commit/rollback handling.
- State transitions are enforced in code, not by DB constraints alone.
- Metrics endpoints (`funnel_counts`, `conversion_by_vertical`, `economics_summary`, `beat_compliance_summary`) query directly from SQLite.

## Dashboard Endpoint Inventory

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | DB liveness check (200 ok / 503 degraded) |
| GET | `/` | None | HTML operator dashboard shell (client-side calls hit `/api/*`) |
| GET | `/api/funnel` | API key | Pipeline state counts |
| GET | `/api/verticals` | API key | Conversion stats by vertical |
| GET | `/api/leads` | API key | Lead list (`?limit=` only; clamped to 1..200) |
| GET | `/api/economics` | API key | Revenue/deal economics summary |
| GET | `/api/beat-compliance` | API key | 7-beat outreach compliance stats |
| GET | `/api/lead/{lead_slug}/timeline` | API key | Event timeline for a single lead |
| POST | `/api/webhooks/openclaw` | HMAC signature | Webhook intake (deployment/email/deal callbacks) |

API key auth is only enforced when `CITADEL_DASHBOARD_API_KEY` is set. When unset, all read endpoints are open.

Rate limiting: configurable per-IP sliding window via `CITADEL_RATE_LIMIT_API_RPM` (default 60) and `CITADEL_RATE_LIMIT_WEBHOOK_RPM` (default 30). Set to 0 to disable.

## Security and Operational Considerations

Implemented controls:
- Optional dashboard read protection via `CITADEL_DASHBOARD_API_KEY` and `X-API-Key` header.
- CORS middleware gated on `CITADEL_CORS_ORIGINS` (comma-separated origins; empty = disabled).
- Per-IP rate limiting on read endpoints and webhook (configurable via env vars).
- Webhook request body size limit: 64KB.
- `lead_slug` path parameter validated with regex `^[a-z0-9-]{5,120}$`.
- Webhook signature verification using:
  - `X-Citadel-Timestamp`
  - `X-Citadel-Signature` (`sha256=<hex>`)
- Timestamp skew enforcement via `OPENCLAW_WEBHOOK_MAX_SKEW_SECONDS`.
- HMAC computation format: `HMAC_SHA256(secret, "{timestamp}.{raw_body}")`.
- JSON-schema validation before accepting stage outputs.
- Webhook idempotency and processing status tracking in `webhook_receipts`.

Supported webhook event types:
- `deployment.succeeded`
- `deployment.failed`
- `outreach.sent`
- `lead.replied`
- `deal.won`
- `deal.lost`

Operational script:
- `sync_state.sh` performs periodic SQLite checkpoint backup and S3 sync for spot/preemptible environments.

## Testing Strategy and Current Baseline

Test files and intent:
- `tests/test_lead_queue.py`: transitions, webhook idempotency, economics/vertical summaries
- `tests/test_orchestrator_local.py`: local full-pipeline integration against in-process HTTP server
- `tests/test_orchestrator_logging.py`: structured JSON logging format/fields (including `run_id`)
- `tests/test_schema_contracts.py`: schema validity and contract constraints
- `tests/test_webhook_signature.py`: webhook signature acceptance/rejection and duplicate event handling
- `tests/test_dashboard_api.py`: read API shape/auth/rate-limit/timeline validations
- `tests/test_health_endpoint.py`: `/health` behavior and auth bypass checks
- `tests/test_census_ranker.py`: target config validation invariants for market ranker

Current baseline from repository exploration:
- `pytest -q` result: `34 passed, 36 warnings`
- Warning profile observed:
  - BeautifulSoup/lxml deprecation warning (`strip_cdata`)
  - `httpx` deprecation warning in tests for raw upload style

## Test Fixtures and Patterns (`tests/conftest.py`)

Shared fixtures:
- `project_root()` — returns `Path` to repo root (for loading schemas, configs)
- `temp_db_path(tmp_path)` — returns an isolated SQLite path under pytest's `tmp_path` (each test gets its own DB)

Shared helper:
- `sign_webhook(secret, payload)` — returns `(raw_bytes, headers_dict)` with valid HMAC signature. Use this for any test that hits the webhook endpoint.

Pattern for new tests:
1. Use `monkeypatch.setenv("CITADEL_DB_PATH", temp_db_path)` to isolate DB access.
2. Import `LeadQueueDB` and call `init_db()` on the temp path.
3. Seed data by calling DB methods directly (not through the pipeline).
4. Use `from fastapi.testclient import TestClient` + `from dashboard_app import app` for endpoint tests.
5. Use `sign_webhook()` from conftest for webhook tests — do not reimplement HMAC logic in individual tests.

## Development Conventions Observed in Code

Conventions currently used:
- `from __future__ import annotations`
- Type hints across public functions and data structures
- `dataclass` for runtime config and payload modeling
- `pathlib.Path` for path handling
- Module loggers (`logging.getLogger("citadel.<module>")`)
- Compact/stable JSON serialization in persistence paths (`separators`, often `sort_keys=True`)
- Explicit schema validation calls before stage handoffs

Practical coding expectations:
- Keep schema files and runtime payload builders in sync.
- Preserve transition rules in `lead_queue.py` when adding states/events.
- Add/adjust tests when modifying CLI flags, webhook behavior, schema fields, or DB workflow.

## Deployment and Environment Modes

Local mode (default):
- DB at `workspace/state/lead_queue.db`
- Deploy backend `local_fs`
- Email backend `local_outbox`
- Dashboard via `uvicorn` or Docker

Container mode:
- Docker image runs `uvicorn dashboard_app:app`
- Compose mounts `./workspace` and `./market` into container

Email backend modes:
- `local_outbox`: writes `.eml` files
- `smtp`: sends through configured SMTP server

Deploy backend modes:
- Implemented: `local_fs`
- Any other value currently raises runtime error in `orchestrator.py`

## Environment Variable Reference

The authoritative source is `.env.template` (30 variables at current revision). Key groups:

- **Core paths/runtime:** `CITADEL_DB_PATH`, `CITADEL_LOG_PATH`, `CITADEL_DASHBOARD_HOST`, `CITADEL_DASHBOARD_PORT`, `CITADEL_WORKDIR`
- **Geography defaults:** `CITADEL_DEFAULT_CITY`, `CITADEL_DEFAULT_STATE`
- **Dashboard/API auth:** `CITADEL_DASHBOARD_API_KEY`
- **Webhook security:** `OPENCLAW_WEBHOOK_SECRET`, `OPENCLAW_WEBHOOK_MAX_SKEW_SECONDS`
- **Branding/compliance:** `BRAND_NAME`, `BRAND_FROM_NAME`, `BRAND_FROM_EMAIL`, `BRAND_POSTAL_ADDRESS`, `BRAND_OPTOUT_EMAIL`
- **Deployment/email backends:** `DEPLOY_BACKEND`, `DEPLOY_ENABLED`, `EMAIL_BACKEND`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM_EMAIL`
- **Rate limit/CORS/logging:** `CITADEL_CORS_ORIGINS`, `CITADEL_LOG_FORMAT`, `CITADEL_RATE_LIMIT_API_RPM`, `CITADEL_RATE_LIMIT_WEBHOOK_RPM`
- **Market + ops integration:** `CENSUS_API_KEY`, `STATE_BUCKET`

When adding new env vars, always update `.env.template` and code defaults together (see AI Agent Working Rules).

## Known Constraints and Non-goals

Current constraints in code:
- Lead scouting is single-page HTML fetch; no crawler depth management.
- Vertical/city/state inference is heuristic and keyword-based.
- Deployment backend support is intentionally narrow (`local_fs` only in current code).
- No migration framework; schema initialization is in `init_db()`.
- Dashboard provides read APIs and webhook intake, not full CRUD operations.

Non-goals implied by implementation:
- No built-in task queue or distributed job orchestration.
- No multi-database abstraction layer.
- No front-end build toolchain (static artifacts are generated directly by Python).

## AI Agent Working Rules for This Repo

When making changes:
1. Start by identifying whether the change belongs in `orchestrator.py`, `lead_queue.py`, `dashboard_app.py`, `schemas/`, or `tests/`.
2. Treat `schemas/*.json` as interface contracts; update schema + producer + tests together.
3. For workflow/state changes, update:
   - `PIPELINE_STATES`
   - `VALID_TRANSITIONS`
   - any webhook mapping in `apply_webhook_event`
   - corresponding tests
4. For new env vars, update `.env.template` and code defaults together.
5. For operational command changes, keep `Makefile`, `README.md`, and this file aligned.
6. Do not treat `workspace/` runtime artifacts as source code.
7. Use `pytest -q` as baseline validation before and after substantial changes.

Fast orientation path for new agents:
1. Read `README.md`
2. Read `orchestrator.py` main flow (`run_pipeline` and `_cli`)
3. Read `lead_queue.py` schema/state/event logic
4. Read `dashboard_app.py` endpoints and webhook verification
5. Check `schemas/` and then `tests/`
