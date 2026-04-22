# B-A-P Business Analytics Platform - Agent Guide

**Last updated:** 2026-03-10

## Project Overview

B-A-P (Business Analytics Platform) is an enterprise-ready, AI-powered analytics SaaS that transforms business data into actionable insights and forecasts. Built for high-throughput ETL, real-time AI, and seamless cloud-native deployment.

**Core Value:** "Your business data but made smart and easy to read"

## Hostile Audit Persistence

- Append every hostile-audit checkpoint and verification result to the root `PROGRESS_TRACKER.md`.
- Do not mark auth, control-plane, or data-path fixes complete without a real command result, test run, health check, or screenshot saved under `proof/hostile-audit/<timestamp>/`.
- Reproduce before patching. If the original reproduction path fails, record the failed method and the replacement method that actually proved the issue.
- Fail closed when shared auth dependencies or secrets are unavailable; do not restore `DEV_MODE` bypasses for convenience.
- If a scanner or service cannot run, record the exact blocker and the fallback review path instead of implying success.

**Key Capabilities:**
- FastAPI-powered async API with auto-generated OpenAPI docs
- Real-time ETL pipelines with pandas/polars
- Gemini integration for business intelligence
- Production-grade security (JWT, rate limiting, headers)
- Prometheus metrics and structured logging

---

## Build / Run / Test Commands

### ⚠️ CRITICAL: Use Poetry, NOT pip
This project uses Poetry for dependency management. Never use pip.

```bash
# Install dependencies (production + dev)
poetry install --with dev

# Run the application
poetry run uvicorn src.main:app --reload --port 8000

# Run tests
poetry run pytest tests/ -v

# Run tests with coverage
poetry run pytest tests/ --cov=src --cov-fail-under=90

# Format code
poetry run black src/

# Lint code
poetry run ruff check src/

# Type check
poetry run mypy src/

# Run all pre-commit hooks
poetry run pre-commit run --all-files
```

### Docker Deployment
```bash
# Start with Docker Compose (includes PostgreSQL + Redis)
docker-compose up --build

# Access API docs
open http://localhost:8000/docs
open http://localhost:8000/redoc
```

### Database Operations
```bash
# Start only databases
docker-compose up -d postgres redis

# Connect to PostgreSQL
psql -h localhost -U postgres -d analytics_db
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Web Framework** | FastAPI 0.111 | Async API with auto docs |
| **ORM** | SQLAlchemy 2.0 + asyncpg | Database abstraction |
| **Caching** | Redis 5.x + hiredis | High-performance caching |
| **Data Processing** | pandas 2.x + polars 0.20 | ETL pipelines |
| **AI/ML** | Google Gemini 2.5 Flash | Insights generation |
| **Auth** | python-jose + passlib | JWT tokens, bcrypt hashing |
| **Tasks** | Celery 5.x + Redis | Background job processing |
| **Logging** | structlog | Structured JSON logging |
| **Metrics** | prometheus-client | Application metrics |
| **Testing** | pytest + pytest-asyncio + httpx | Test suite |

---

## Project Structure

```
B-A-P/
├── src/
│   ├── main.py                   # FastAPI entry point
│   ├── config/settings.py        # Pydantic settings (env var validation)
│   ├── api/
│   │   ├── routes/              # API endpoints
│   │   │   ├── analytics.py     # Analytics queries
│   │   │   ├── data.py          # Data ingestion
│   │   │   └── pipeline.py      # ETL pipeline management
│   │   └── middleware/          # Auth, rate limiting, security
│   ├── ai/
│   │   ├── llm_client.py        # Gemini integration
│   │   ├── gpt_client.py        # Compatibility wrapper
│   │   ├── insights_generator.py # Business insights
│   │   └── forecast_engine.py   # Predictive analytics
│   ├── etl/pipeline.py          # Data transformation logic
│   ├── models/                  # SQLAlchemy models
│   └── core/                    # Database, cache, security
├── tests/                       # Test suites
│   ├── test_api.py             # Endpoint tests
│   ├── test_etl.py             # Pipeline tests
│   ├── test_core.py            # Unit tests
│   └── test_concurrency.py     # Load tests
├── helm/                        # Kubernetes deployment
├── pyproject.toml              # Poetry configuration
└── docker-compose.yml          # Local infrastructure
```

---

## Critical Code Patterns

### Import Order (Strict)
```python
# 1. Standard library
import os
import json
from datetime import datetime

# 2. Third-party
from fastapi import FastAPI, Depends
from sqlalchemy import select
from pydantic import BaseModel

# 3. Local (absolute imports)
from src.config import settings
from src.core.database import get_db
```

### Settings Loading (config.py)
```python
from src.config import settings  # ALWAYS import this first

# Settings validates env vars on import
# Raises PydanticValidationError if required vars missing
```

### Async Database Pattern
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_analytics(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Metric))
    return result.scalars().all()
```

### Celery Task Definition
```python
from celery import Celery
from src.config import settings

app = Celery('bap', broker=settings.redis_url)

@app.task(bind=True, max_retries=3)
def process_etl_pipeline(self, pipeline_id: str):
    try:
        # ETL logic
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## Non-Obvious Gotchas

### 1. ⚠️ NEVER Use pip in B-A-P
This project uses Poetry exclusively:
- ❌ `pip install -r requirements.txt` - WRONG
- ✅ `poetry install --with dev` - CORRECT

Mixing pip and Poetry will corrupt the virtualenv.

### 2. Settings Validation on Import
The `config.py` module validates all environment variables when imported:
```python
from src.config import settings  # This validates immediately
```

If required env vars are missing, the app crashes on startup with a clear error.

### 3. Async SQLAlchemy 2.0 Syntax
Always use the 2.0 style:
```python
# CORRECT (2.0 style)
result = await db.execute(select(Model).where(Model.id == id))

# WRONG (1.x style)
result = await db.query(Model).filter(Model.id == id).first()
```

### 4. Poetry Scripts vs Package Scripts
Commands in `pyproject.toml`:
```toml
[tool.poetry.scripts]
# These are CLI commands, not npm-style scripts
bap = "src.main:main"
```

To run development tasks:
```bash
# Use poetry run, not poetry script
poetry run pytest
poetry run black src/
```

### 5. PostgreSQL + Redis Required
The app will not start without:
- PostgreSQL 14+ (connection string in `DATABASE_URL`)
- Redis 6+ (connection string in `REDIS_URL`)

Use `docker-compose up -d postgres redis` for local development.

### 6. Coverage Gate at 90%
CI enforces 90% minimum coverage:
```bash
pytest --cov=src --cov-fail-under=90
```

### 7. Environment File Loading Order
1. `.env` file (if exists)
2. Environment variables (override .env)
3. Default values in `Settings` class

---

## Testing Strategy

### Test Categories
| Type | Location | Command |
|------|----------|---------|
| Unit | `tests/test_core.py` | `poetry run pytest tests/test_core.py` |
| API | `tests/test_api.py` | `poetry run pytest tests/test_api.py` |
| ETL | `tests/test_etl.py` | `poetry run pytest tests/test_etl.py` |
| Concurrency | `tests/test_concurrency.py` | `poetry run pytest tests/test_concurrency.py` |
| Performance | `tests/test_performance.py` | `poetry run pytest tests/test_performance.py --benchmark-only` |

### Fixtures (conftest.py)
```python
# Async database session fixture
@pytest.fixture
async def db():
    async with async_session() as session:
        yield session
        await session.rollback()
```

---

## Deployment

### Docker Production
```bash
docker build -t bap:latest .
docker run -p 8000:8000 --env-file .env bap:latest
```

### Kubernetes (Helm)
```bash
cd helm
helm install bap . -f values.yaml
```

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
```

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects
