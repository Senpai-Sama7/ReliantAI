# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

ReliantAI is a federated enterprise microservices platform with 20+ services orchestrated via Docker Compose. The **integration layer** (`integration/`) functions as the central nervous system — providing auth, eventing, saga coordination, and service discovery. The **Money service** is the primary revenue engine (HVAC dispatch using CrewAI + Gemini).

## Quick Start

```bash
cp .env.example .env          # Fill in required API keys
./scripts/deploy.sh local      # Build and start all services
./scripts/health_check.py -v   # Verify all services are healthy
```

## Architecture Rules (Never Break)

- **Every service** MUST declare `networks: - reliantai-network` in `docker-compose.yml`
- **Every container** MUST have `curl` installed for Docker health checks
- **Database connections** MUST use `cursor_factory=RealDictCursor` (psycopg2) to avoid tuple/dict crashes
- **Event bus payloads** MUST stay under 64KB (enforced by `@field_validator` in `integration/shared/event_types.py`)
- **Rate limiting** MUST run AFTER authentication (ref: `Money/main.py` pattern)
- **Never bare except** — use minimum `(ConnectionError, RuntimeError, Exception)`
- **Auth failures** return 503 if config is missing (fail-closed)
- All unhandled event bus exceptions MUST push to `dlq:events` or `dlq:handler_errors`

## Architecture

### Services & Ports

| Service | Port | Purpose |
|---------|------|---------|
| Money | 8000 | HVAC dispatch, SMS (Twilio), billing (Stripe), CrewAI + Gemini |
| ComplianceOne | 8001 | SOC2/HIPAA/GDPR compliance tracking |
| FinOps360 | 8002 | Cloud cost optimization |
| GrowthEngine | 8003 | Google Places lead generation |
| Integration Auth | 8080 | OAuth2/JWT, RBAC (4 roles) |
| Event Bus | 8081 | Redis pub/sub + Kafka, 16 event types, DLQ |
| Orchestrator | 9000 | 6 async loops: health, metrics, scaling, healing, AI, reports |
| Reliant JIT OS | 8085 | Zero-config AI operations UI |
| MCP Bridge | 8083 | Tool bridge for AI agents |
| Nginx | 8880 | Edge routing with JWT validation |
| Saga | 8090 | Distributed transaction coordinator |

### Shared Code (mounted as read-only volume into containers)

- `shared/security_middleware.py` — `SecurityHeadersMiddleware`, `RateLimitMiddleware`
- `shared/jwt_validator.py` — RS256 JWT validation
- `shared/event_types.py` — `EventType` enum (16 variants), `EventPublishRequest` with 64KB validator
- `shared/event_bus_client.py` — `publish_sync` helper
- `shared/graceful_shutdown.py` — `GracefulShutdownManager`

### Data Flows

1. **Dispatch**: Customer SMS → Twilio → `Money/main.py POST /sms` → CrewAI triage → Stripe check → DB save → Event bus publish → SSE broadcast
2. **Auth**: Request → `RateLimitMiddleware` → `_authorize_request` (JWT/API key/session triple check) → proceed
3. **Scaling**: Orchestrator health loop → metrics → Holt-Winters forecast → Docker API scale → WebSocket broadcast
4. **Events**: Service publishes → `/publish` → Redis SETEX + PUBLISH → `process_subscriptions` listener → handler → DLQ on failure

## Development Commands

### Python Services

```bash
# Install deps (per service)
pip install -r Money/requirements.txt

# Run a single service test
pytest integration/auth/test_auth_properties.py -v
pytest integration/event-bus/test_event_bus_properties.py -v
pytest integration/shared/test_jwt_validator.py -v
pytest citadel_ultimate_a_plus/tests/ -v
pytest integration/metacognitive_layer/tests/ -v

# Run integration test suite
python -m pytest tests/test_integration_suite.py -v

# Run load tests
python tests/load/sse_load_test.py
python tests/load/websocket_load_test.py

# Type check
mypy Money/main.py --strict

# Lint
ruff check Money/
```

### Docker

```bash
docker compose up -d                    # Start all services
docker compose up -d money              # Start single service
docker compose build money              # Rebuild single service
docker compose restart money            # Restart after code changes
docker compose logs -f money            # Follow service logs
docker compose down                     # Stop (preserves volumes)
docker compose down -v                  # Stop and wipe volumes
docker compose ps                       # Show health status
```

### Deployment & Verification

```bash
./scripts/deploy.sh local               # Build & start full stack
./scripts/deploy.sh staging             # Staging deployment
./scripts/health_check.py -v            # Verify 6+ services healthy
./scripts/verify_integration.py         # Cross-service contract tests
./scripts/deploy.sh production          # Production deployment
```

### Migrations

```bash
# Per-service Alembic migrations
cd Money && alembic upgrade head
cd ComplianceOne && alembic upgrade head
```

## Key Patterns

- **Import order**: stdlib → third-party → workspace shared (`integration.shared.*`, `shared.*`) → local
- **Logging**: `structlog.get_logger()` with structured fields (`correlation_id=`)
- **Naming**: services = lowercase (`money`), env vars = `UPPER_SNAKE_CASE`, endpoints = kebab-case, Python = snake_case
- **Circuit breaker** (`Money/circuit_breaker.py`): 3 failures → 30s open state
- **Event types**: 16 canonical types in `EventType` enum — do not add without cross-team alignment

## Hostile Audit Protocol

Every code change must be verified through live execution before being marked complete. Proof must follow the format:
`Proof: <command> → <output> @ <timestamp>`

## Project Directory Structure

```
ReliantAI/
├── Money/              # Revenue engine (FastAPI, CrewAI, Gemini, Twilio, Stripe)
├── integration/        # Central nervous system
│   ├── auth/           # JWT/OAuth2 auth service
│   ├── event-bus/      # Redis pub/sub + DLQ
│   ├── saga/           # Distributed transaction coordinator
│   ├── shared/         # Shared schemas, validators, clients
│   ├── mcp-bridge/     # AI tool bridge
│   ├── gateway/        # API gateway
│   └── metacognitive_layer/  # Meta-cognitive engine
├── orchestrator/       # Platform brain (Holt-Winters, auto-scaling)
├── ComplianceOne/      # Compliance tracking
├── FinOps360/          # Cloud cost optimization
├── GrowthEngine/       # Lead generation
├── reliant-os/         # JIT OS (zero-config AI operations)
├── dashboard/          # Web dashboard
├── shared/             # Shared middleware (mounted into containers)
├── scripts/            # Deploy, health check, verification
├── tests/              # Integration and load tests
└── docker-compose.yml  # Full platform orchestration
```

## B-A-P Warning

The B-A-P sub-project uses **Poetry only**. Never use `pip` with it — mixing corrupts the virtualenv.
