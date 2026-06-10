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
**Phase: 5 — Deployment Verification**  
In scope: Deploy to Vercel, configure `API_BASE_URL`, verify ISR slugs render, monitor Celery beat tasks

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

## Cursor Cloud specific instructions

### Sprint stack (Phase 5 — recommended for client-sites + API work)

The sprint product loop is `reliantai/` (API) + `reliantai-client-sites/` (Next.js ISR). Start infrastructure, then run services locally.

**Infrastructure (Postgres + Redis)** — `reliantai/docker-compose.yml` does not publish DB ports and `docker compose build` currently fails on a `crewai`/`sqlalchemy==1.4.52` pip conflict. Use standalone containers with published ports:

```bash
sudo docker run -d --name reliantai-postgres \
  -e POSTGRES_DB=reliantai -e POSTGRES_USER=reliantai -e POSTGRES_PASSWORD=reliantai_dev \
  -p 5432:5432 postgres:16-alpine

sudo docker run -d --name reliantai-redis \
  -p 6379:6379 redis:7-alpine \
  redis-server --requirepass reliantai_dev --maxmemory 256mb --maxmemory-policy allkeys-lru
```

Do **not** mount `reliantai/db/migrations/001_platform.sql` into Postgres init — it references `clients` before that table exists. Use Alembic instead:

```bash
export PYTHONPATH=/workspace
export DATABASE_URL=postgresql://reliantai:reliantai_dev@localhost:5432/reliantai
export REDIS_URL=redis://:reliantai_dev@localhost:6379/0
export API_SECRET_KEY=dev_secret_key_change_in_production
cd reliantai && alembic upgrade head
```

**API (local, without crewai)** — full `pip install -r requirements.txt` fails due to embedchain/SQLAlchemy 2.x vs pinned 1.4.52. Install core API deps (see update script) and run:

```bash
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH=/workspace
cd reliantai
python3 -m uvicorn reliantai.main:app --host 0.0.0.0 --port 8000 --reload
```

**Next.js client sites** — create `reliantai-client-sites/.env.local`:

```
API_BASE_URL=http://localhost:8000
REVALIDATE_SECRET=dev_revalidate_secret
NEXT_PUBLIC_PREVIEW_DOMAIN=preview.reliantai.org
```

Then `npm run dev` (port 3000). `/showcase` works with mock data alone; `/[slug]` needs API + a seeded `generated_sites` row.

**Verification quick checks**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v2/generated-sites/<slug>
curl http://localhost:3000/showcase
curl http://localhost:3000/api/health
```

**Tests** — `reliantai` model tests use SQLite in-memory (no Postgres): `PYTHONPATH=/workspace pytest reliantai/tests/ -x -v`. Client-sites: `npx tsc --noEmit` passes; `npm run lint` has pre-existing warnings.

**Celery workers** — require full `requirements.txt` (crewai) which does not pip-resolve today; skip unless Docker image build is fixed upstream.

**Full monorepo stack** — root `./scripts/deploy.sh local` starts 15+ microservices on different ports; it does **not** start `reliantai/` or `reliantai-client-sites/`.