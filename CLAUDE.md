# ReliantAI Platform — CLAUDE.md

## Repos
- reliantai/                → FastAPI + Celery + SQLAlchemy (Python 3.12)
- reliantai-website/        → Vite + React 19 (marketing, reliantai.org)
- reliantai-client-sites/   → Next.js 15 App Router (ISR sites, preview.reliantai.org)

## Hard constraints — never deviate
- NO per-site builds. Sites render via Next.js ISR from DB content.
- Slug: generate_slug(business_name, city) — never from place_id
- Celery Beat: celery_app.py beat_schedule — NOT django_celery_beat
- Tool _run(): SYNCHRONOUS only (sync httpx.Client)
- Preview domain: preview.reliantai.org — NOT reliantai.org/preview/
- CopyAgent LLM: gemini-1.5-pro. All other agents: gemini-1.5-flash.
- All tool _run() are sync. CrewAI threads them internally.

## Commands
api:      uvicorn reliantai.main:app --reload --port 8000
workers:  celery -A reliantai.celery_app worker -Q agents --concurrency 2
beat:     celery -A reliantai.celery_app beat
tests:    pytest tests/ -x -v
migrate:  alembic upgrade head

## Current sprint
Phase: 1 — Infrastructure + Schema
In scope: DB migrations, models, FastAPI skeleton, Celery setup, Docker Compose
