# ReliantAI Platform — AGENTS.md

## Repos
- `reliantai/` — FastAPI + Celery + SQLAlchemy (Python 3.12) ← main platform
- `reliantai-website/` — Vite + React 19 (marketing, reliantai.org)
- `reliantai-client-sites/` — Next.js 15 App Router (ISR sites, preview.reliantai.org)

## Commands (reliantai/)
```bash
api:      uvicorn reliantai.main:app --reload --port 8000
workers:  celery -A reliantai.celery_app worker -Q agents --concurrency 2
beat:     celery -A reliantai.celery_app beat
tests:    PYTHONPATH=. pytest tests/ -x -v
migrate:  alembic upgrade head

# Docker full stack
./scripts/deploy.sh local
docker compose ps
docker compose logs -f [service]
```

## Hard Constraints (never deviate)
- **No per-site builds** — sites render via Next.js ISR from DB content
- **Slug**: `generate_slug(business_name, city)` — never from place_id
- **Celery Beat**: `celery_app.py beat_schedule` — NOT django_celery_beat
- **Tool _run()**: SYNCHRONOUS only (sync httpx.Client)
- **Preview domain**: `preview.reliantai.org` — NOT reliantai.org/preview/
- **CopyAgent LLM**: gemini-1.5-pro | **All other agents**: gemini-1.5-flash
- All tool `_run()` are sync. CrewAI threads internally.

## Current Sprint
**Phase: 4 — E2E + Deployment**  
In scope: reliantai-client-sites/ E2E Playwright tests, remaining 5 template builds, deployment verification

## Commands (reliantai-client-sites/)
```bash
dev:      npm run dev
build:    npm run build
typecheck: npx tsc --noEmit
test:e2e:  npm run test:e2e
```

## Service Ports (docker-compose.yml)
| Service | Port | Purpose |
|---------|------|---------|
| ReliantAI API | 8000 | FastAPI main |
| Postgres | 5432 | Primary DB |
| Redis | 6379 | Celery broker/cache |
| nginx | 80/443 | Edge routing |

## Key Files
- `reliantai/main.py` — FastAPI entry, API key auth
- `reliantai/celery_app.py` — Celery config, beat_schedule
- `reliantai/db/models.py` — SQLAlchemy models
- `reliantai/db/migrations/` — Alembic migrations
- `reliantai/api/v2/` — API endpoints (v2)
- `reliantai/api/v2/generated_sites.py` — Public site content endpoint (no auth)
- `reliantai/services/site_registration_service.py` — DB write + ISR revalidate
- `docker-compose.yml` — Full platform orchestration
- `reliantai-client-sites/app/[slug]/page.tsx` — ISR dynamic route
- `reliantai-client-sites/app/api/revalidate/route.ts` — Revalidation endpoint
- `reliantai-client-sites/templates/hvac-reliable-blue/` — HVAC template (Phase 3)
- `reliantai-client-sites/tests/e2e/` — Playwright E2E tests
- `reliantai-client-sites/playwright.config.ts` — Playwright config
- `reliantai-client-sites/types/SiteContent.ts` — TypeScript interfaces

## Pre-commit
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
Config: `.pre-commit-config.yaml` (black, isort, flake8, yamllint, gitleaks)

## Required Env Vars
```bash
cp .env.staging.example .env  # fill in API keys
```
Required: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `API_SECRET_KEY`