# ReliantAI Platform - Quick Reference Guide

## One-Command Operations

### Start Everything
```bash
docker compose up -d
```

### Check Health
```bash
./scripts/health_check.py -v
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f money
docker compose logs -f event-bus
docker compose logs -f orchestrator
```

### Stop Everything
```bash
docker compose down
```

---

## Service URLs (Local Development)

| Service | URL | Notes |
|---------|-----|-------|
| **Dashboard** | http://localhost:8880 | Main platform dashboard |
| **Reliant JIT OS** | http://localhost:8085 | AI operations control |
| **ReliantAI API** | http://localhost:8000 | Core platform API |
| **Money Service** | http://localhost:8000 | Revenue/dispatch (via nginx) |
| **GrowthEngine** | http://localhost:8003 | Lead generation |
| **Client Sites** | http://localhost:3000 | Next.js dev server |
| **Event Bus** | http://localhost:8081 | Event messaging |
| **MCP Bridge** | http://localhost:8083 | AI tool registry |
| **Orchestrator** | http://localhost:9000 | Auto-scaling API |
| **PostgreSQL** | localhost:5432 | Primary database |
| **Redis** | localhost:6380 | Cache/messaging |

---

## Common Development Tasks

### ReliantAI API (Core Platform)

```bash
# Navigate to directory
cd /home/donovan/Projects/platforms/ReliantAI/reliantai

# Start API server
uvicorn reliantai.main:app --reload --port 8000

# Start Celery worker (agents queue)
celery -A reliantai.celery_app worker -Q agents --concurrency 2 -l info

# Start Celery beat (scheduled tasks)
celery -A reliantai.celery_app beat -l info

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
PYTHONPATH=. pytest tests/ -x -v
```

### Client Sites (Next.js)

```bash
cd /home/donovan/Projects/platforms/ReliantAI/reliantai-client-sites

# Development server (Turbopack)
npm run dev

# Type check
npx tsc --noEmit

# Build
npm run build

# E2E tests
npm run test:e2e
```

### Money Service

```bash
cd /home/donovan/Projects/platforms/ReliantAI/Money

# Start server
uvicorn main:app --reload --port 8000

# Run tests
pytest tests/ -v
```

### Event Bus

```bash
cd /home/donovan/Projects/platforms/ReliantAI/integration/event-bus

# Start server
python event_bus.py

# Or with uvicorn
uvicorn event_bus:app --reload --port 8081
```

---

## API Testing (cURL)

### Health Checks
```bash
# Core platform
curl http://localhost:8000/health

# Event bus
curl http://localhost:8081/health

# Orchestrator
curl http://localhost:9000/health

# Money
curl http://localhost:8000/health
```

### Create Prospect
```bash
curl -X POST http://localhost:8000/api/v2/prospects \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "ACME HVAC",
    "trade": "hvac",
    "city": "Atlanta",
    "state": "GA",
    "place_id": "ChIJ..."
  }'
```

### Get Generated Site (Public)
```bash
curl http://localhost:8000/api/v2/generated-sites/acme-hvac-atlanta-1234
```

### Publish Event
```bash
curl -X POST http://localhost:8081/publish \
  -H "Authorization: Bearer EVENT_BUS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "lead.created",
    "payload": {"prospect_id": "123", "source": "web"},
    "correlation_id": "corr-123",
    "tenant_id": "default",
    "source_service": "test-script"
  }'
```

### Scan Prospects (GrowthEngine)
```bash
curl -X POST http://localhost:8003/api/prospect/scan \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 33.7490,
    "lng": -84.3880,
    "radius_meters": 5000,
    "keyword": "hvac"
  }'
```

---

## Database Operations

### Connect to PostgreSQL
```bash
# Via docker
docker exec -it reliantai-postgres psql -U postgres -d reliantai

# Local (if postgres client installed)
psql postgresql://postgres:password@localhost:5432/reliantai
```

### Common Queries
```sql
-- List all prospects
SELECT id, business_name, trade, city, status FROM prospects LIMIT 10;

-- Check generated sites
SELECT slug, template_id, status, preview_url FROM generated_sites;

-- View research jobs
SELECT id, prospect_id, status, step FROM research_jobs ORDER BY created_at DESC;

-- Celery task results (if using result backend)
SELECT task_id, status, date_done FROM celery_taskmeta ORDER BY date_done DESC LIMIT 10;
```

### Redis Operations
```bash
# Connect via docker
docker exec -it reliantai-redis redis-cli

# With password
docker exec -it reliantai-redis redis-cli -a YOUR_PASSWORD

# Common commands
KEYS *                    # List all keys
GET event:{id}            # Get event by ID
LRANGE dlq:events 0 10   # Get DLQ entries
PUBLISH events:lead "{}"  # Manual publish
INFO                      # Server info
MONITOR                   # Real-time commands (careful in production!)
```

---

## Environment Variables

### Critical (Required)
```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=reliantai

# Redis
REDIS_URL=redis://localhost:6379/0

# Core API
API_SECRET_KEY=your_secret_key_here

# Event Bus
EVENT_BUS_API_KEY=event_bus_key_here

# Money Service
DISPATCH_API_KEY=dispatch_key_here
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_FROM_PHONE=+1234567890
STRIPE_API_KEY=sk_test_...

# GrowthEngine
GOOGLE_PLACES_API_KEY=your_google_api_key

# MCP Bridge
MCP_API_KEY=mcp_key_here

# Orchestrator
ORCHESTRATOR_API_KEY=orchestrator_key_here
```

### Optional
```bash
# Environment
ENV=development|staging|production

# Client Sites
REVALIDATE_SECRET=revalidate_webhook_secret
API_BASE_URL=http://localhost:8000

# Vault
VAULT_DEV_ROOT_TOKEN_ID=dev-root-token
```

---

## Debugging & Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs --tail=50 {service_name}

# Check dependencies
docker compose ps

# Restart specific service
docker compose restart {service_name}

# Rebuild after code changes
docker compose up -d --build {service_name}
```

### Database Connection Issues
```bash
# Check postgres is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Verify connection from app container
docker exec -it reliantai-money python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:password@postgres:5432/money'); print('OK')"
```

### Celery Tasks Not Running
```bash
# Check worker is running
celery -A reliantai.celery_app inspect active

# Check scheduled tasks
celery -A reliantai.celery_app inspect scheduled

# Purge queue (DANGER: clears pending tasks)
celery -A reliantai.celery_app purge

# View beat schedule
celery -A reliantai.celery_app beat -l debug --max-interval 10
```

### Event Bus Issues
```bash
# Test Redis connection
redis-cli ping

# Check event bus is listening
curl http://localhost:8081/health

# View recent events (if using Redis list)
redis-cli LRANGE events:recent 0 10
```

---

## Code Patterns

### Adding a New Endpoint (FastAPI)
```python
# In api/v2/my_feature.py
from fastapi import APIRouter, Depends
from ..main import verify_api_key

router = APIRouter(prefix="/api/v2/my-feature", tags=["my-feature"])

@router.get("/items")
def list_items(_auth: bool = Depends(verify_api_key)):
    return {"items": []}

@router.post("/items")
def create_item(item: ItemCreate, _auth: bool = Depends(verify_api_key)):
    return {"id": "new-id", **item.dict()}
```

### Adding a Celery Task
```python
# In tasks/my_tasks.py
from ..celery_app import app

@app.task(bind=True, max_retries=3)
def my_background_task(self, prospect_id: str):
    try:
        # Do work
        result = process_something(prospect_id)
        return {"status": "success", "result": result}
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 ** self.request.retries)
```

### Publishing an Event
```python
from integration.shared.event_bus_client import publish_sync
from integration.shared.event_types import EventType, EventPublishRequest

publish_sync(EventPublishRequest(
    event_type=EventType.LEAD_CREATED,
    payload={"prospect_id": prospect.id, "source": "scan"},
    correlation_id=f"corr-{prospect.id}",
    tenant_id="default",
    source_service="my-service"
))
```

### Database Query Pattern
```python
from ..db import get_db_session
from ..db.models import Prospect

def get_prospect(prospect_id: str) -> Prospect:
    with get_db_session() as db:
        prospect = db.query(Prospect).filter_by(id=prospect_id).first()
        if not prospect:
            raise ValueError(f"Prospect not found: {prospect_id}")
        return prospect
```

---

## Pre-Commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Specific hook
pre-commit run black
pre-commit run flake8
```

---

## Testing

### Unit Tests
```bash
# Python
PYTHONPATH=. pytest tests/ -x -v --tb=short

# Specific test
pytest tests/test_prospects.py::test_create_prospect -v
```

### E2E Tests (Client Sites)
```bash
cd reliantai-client-sites

# Install Playwright browsers
npx playwright install

# Run tests
npm run test:e2e

# Run specific test
npx playwright test site-generation.spec.ts

# Debug mode
npx playwright test --debug
```

### Load Testing
```bash
# Using hey (requires installation)
hey -n 1000 -c 50 http://localhost:8000/health

# Using curl + parallel
echo "http://localhost:8000/health" | xargs -P 50 -I {} curl -s {} > /dev/null
```

---

## Docker Compose Shortcuts

```bash
# Scale a service
docker compose up -d --scale money=3

# Exec into running container
docker compose exec money bash

# View resource usage
docker compose stats

# Clean up volumes (DANGER: deletes data)
docker compose down -v

# Build without cache
docker compose build --no-cache

# View config
docker compose config
```

---

## Monitoring Endpoints

All services expose these standard endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness probe (200 = healthy) |
| `GET /metrics` | Prometheus metrics (if enabled) |
| `GET /` | Service info/version |

### Prometheus Metrics (Event Bus Example)
```
GET http://localhost:8081/metrics

# Example output:
events_published_total{channel="events:lead",event_type="lead.created"} 42
events_consumed_total{channel="events:lead",event_type="lead.created"} 42
events_failed_total{channel="events:lead",reason="validation"} 0
dlq_size 0
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit
git add .
git commit -m "feat: add new feature"

# Push
git push origin feature/my-feature

# Create PR via GitHub CLI (optional)
gh pr create --title "feat: my feature" --body "Description"
```

---

## Emergency Procedures

### Platform Down
```bash
# 1. Check status
docker compose ps

# 2. Check logs for errors
docker compose logs --tail=100 | grep -i error

# 3. Restart everything
docker compose down
docker compose up -d

# 4. Verify health
./scripts/health_check.py -v
```

### Database Corruption
```bash
# 1. Stop services
docker compose down

# 2. Backup (if possible)
docker exec reliantai-postgres pg_dumpall -U postgres > backup.sql

# 3. Reset volume (WARNING: DESTROYS DATA)
docker volume rm reliantai_postgres_data

# 4. Restart (will re-initialize)
docker compose up -d postgres
```

### Redis Data Loss
```bash
# 1. Check persistence
docker exec reliantai-redis redis-cli INFO persistence

# 2. Force save
docker exec reliantai-redis redis-cli BGSAVE

# 3. Check RDB file
docker exec reliantai-redis ls -la /data/
```

---

*Quick Reference Version: 1.0*
*Keep this handy during development!*
