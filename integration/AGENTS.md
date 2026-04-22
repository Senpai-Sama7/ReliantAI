# ReliantAI Integration Layer - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

The Integration Layer provides shared infrastructure for the ReliantAI platform: authentication, API gateway, event bus, saga orchestration, and observability. It enables communication between the 14 autonomous business execution systems.

**Key Capabilities:**
- OAuth2/JWT authentication service
- API gateway with routing and rate limiting
- Event bus for async communication (Redis/Kafka)
- Saga pattern for distributed transactions
- Observability stack (metrics, logging, tracing)

**Architecture Pattern:**
```
┌─────────────────────────────────────────────────────────┐
│  API Gateway (Kong/nginx)                               │
│  ├── Route to services                                  │
│  ├── Rate limiting                                      │
│  └── Auth token validation                              │
├─────────────────────────────────────────────────────────┤
│  Auth Service                                           │
│  ├── OAuth2 flows                                       │
│  ├── JWT issuance/validation                            │
│  └── User/session management                            │
├─────────────────────────────────────────────────────────┤
│  Event Bus                                              │
│  ├── Redis Streams (simple)                            │
│  └── Kafka (high throughput)                           │
├─────────────────────────────────────────────────────────┤
│  Saga Orchestrator                                      │
│  ├── Distributed transaction coordination              │
│  ├── Compensation logic                                │
│  └── State persistence                                 │
├─────────────────────────────────────────────────────────┤
│  Observability                                          │
│  ├── Prometheus metrics                                │
│  ├── Structured logging                                │
│  └── Distributed tracing                               │
└─────────────────────────────────────────────────────────┘
```

---

## Build / Run / Test Commands

### Docker Compose (Full Stack)
```bash
# Start all infrastructure services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all
docker-compose down

# Restart specific service
docker-compose restart gateway
```

### Individual Services

**Auth Service:**
```bash
cd auth
pip install -r requirements.txt
python auth_server.py
# Runs on port 8001 by default
```

**Event Bus:**
```bash
# Start Redis (required)
redis-server

# Test event bus
cd events
pip install redis pydantic
python -c "from event_bus import EventBus; print('Event bus ready')"
```

**Gateway:**
```bash
cd gateway
# Kong configuration
kong start -c kong.conf
```

### Testing
```bash
# Run all integration tests
pytest tests/ -v

# Test specific component
pytest tests/test_auth.py -v
pytest tests/test_event_bus.py -v
pytest tests/test_saga.py -v
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Gateway** | Kong / nginx | API routing, rate limiting |
| **Auth** | Python/FastAPI + python-jose | OAuth2/JWT |
| **Event Bus** | Redis Streams / Kafka | Async messaging |
| **Saga** | Python + Redis | Distributed transactions |
| **Observability** | Prometheus + Grafana | Metrics |
| **Logging** | structlog / ELK | Centralized logs |
| **Tracing** | Jaeger / OpenTelemetry | Request tracing |

---

## Project Structure

```
integration/
├── auth/                         # OAuth2/JWT service
│   ├── auth_server.py           # FastAPI entry
│   ├── requirements.txt
│   └── tests/
├── gateway/                      # API gateway configs
│   ├── kong.conf
│   ├── nginx.conf
│   └── routes/
├── events/                       # Event bus implementation
│   ├── event_bus.py             # Redis-based bus
│   ├── kafka_bus.py             # Kafka-based bus
│   └── requirements.txt
├── saga/                         # Saga orchestrator
│   ├── orchestrator.py
│   ├── compensation.py
│   └── state_store.py
├── observability/                # Monitoring stack
│   ├── prometheus.yml
│   ├── grafana-dashboards/
│   └── tracing/
├── bridges/                      # Service connectors
│   ├── to_apex.py
│   ├── to_citadel.py
│   └── ...
├── service-mesh/                 # Service discovery
├── shared/                       # Shared utilities
├── tests/                        # Integration tests
├── docker-compose.yml           # Full stack
└── README.md
```

---

## Critical Code Patterns

### JWT Token Validation
```python
# auth/middleware.py
from jose import jwt, JWTError

async def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

### Event Bus Publish/Subscribe
```python
# events/event_bus.py
import redis
from pydantic import BaseModel

class EventBus:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def publish(self, channel: str, event: BaseModel):
        self.redis.xadd(channel, event.dict())
    
    async def subscribe(self, channel: str, group: str):
        return self.redis.xreadgroup(
            groupname=group,
            consumername="consumer-1",
            streams={channel: ">"}
        )
```

### Saga Pattern
```python
# saga/orchestrator.py
class SagaOrchestrator:
    async def execute(self, saga_id: str, steps: list):
        executed = []
        try:
            for step in steps:
                result = await step.execute()
                executed.append(step)
                await self.save_state(saga_id, step, result)
        except Exception as e:
            # Compensate completed steps
            for step in reversed(executed):
                await step.compensate()
            raise SagaFailedException(saga_id, e)
```

### API Gateway Route
```yaml
# gateway/routes/services.yml
services:
  - name: apex-agents
    url: http://apex-agents:8001
    routes:
      - name: apex-route
        paths:
          - /apex
    plugins:
      - name: rate-limiting
        config:
          minute: 100
      - name: jwt
        config:
          uri_param_names: []
```

---

## Non-Obvious Gotchas

### 1. Services Must Use Integration Layer
All 14 ReliantAI projects communicate through this layer:
- Direct service-to-service calls are forbidden
- Use event bus for async communication
- Use gateway for sync API calls

### 2. Auth Service is Central
Every request (except health checks) must include valid JWT:
```
Authorization: Bearer <token>
```

The auth service issues tokens with claims:
```json
{
  "sub": "user-id",
  "service": "apex",
  "roles": ["admin", "operator"],
  "iat": 1709673600,
  "exp": 1709677200
}
```

### 3. Event Schema Enforcement
All events must conform to schema:
```python
class Event(BaseModel):
    event_id: str          # UUID v4
    event_type: str        # dot-notation category
    source: str            # Service name
    timestamp: datetime    # ISO 8601
    payload: dict          # Event data
    correlation_id: str    # For tracing
```

### 4. Saga State Persistence
Saga state is stored in Redis with TTL:
```python
# Auto-expire after 24 hours
redis.setex(f"saga:{saga_id}", 86400, state_json)
```

### 5. Gateway Rate Limiting
Per-service limits enforced at gateway:
- Apex: 100 req/min
- Citadel: 200 req/min
- Money: 50 req/min

Exceeding returns `429 Too Many Requests`.

### 6. Health Check Bypass
Gateway allows `/health` endpoints without auth:
```yaml
plugins:
  - name: jwt
    config:
      anonymous: health-check-consumer  # Bypass for health
```

### 7. Event Bus Backpressure
Redis Streams consumer groups handle backpressure:
- Pending messages tracked per consumer
- Automatic re-delivery on failure
- Dead letter queue for max retries

### 8. Cross-Project Correlation
All requests must include `X-Correlation-ID`:
```python
headers = {
    "Authorization": f"Bearer {token}",
    "X-Correlation-ID": str(uuid.uuid4())
}
```

This enables distributed tracing across all 14 projects.

---

## Configuration

### Environment Variables
```bash
# Auth
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (Event Bus)
REDIS_URL=redis://localhost:6379/0

# Kafka (optional, for high throughput)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Gateway
KONG_DATABASE=off
KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml

# Observability
PROMETHEUS_PORT=9090
JAEGER_ENDPOINT=http://localhost:14268/api/traces
```

### Service Registration
Services register on startup:
```python
# Each service calls on boot
await gateway.register_service(
    name="apex-agents",
    host="apex-agents",
    port=8001,
    health_url="/health"
)
```

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
# Requires full stack running
docker-compose up -d

pytest tests/integration/ -v
```

### End-to-End Flow
```bash
# Test complete auth → gateway → service flow
python tests/e2e/test_full_flow.py
```

### Load Testing
```bash
# Test rate limiting
locust -f tests/load/locustfile.py
```

---

## Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/auth-deployment.yaml
kubectl apply -f k8s/gateway-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
```

### Health Checks
After deployment, verify:
```bash
# Auth service
curl http://localhost:8001/health

# Gateway
curl http://localhost:8000/status

# Event bus
redis-cli ping
```

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects

See also:
- `/home/donovan/Projects/ReliantAI/PROGRESS_TRACKER.md` - Detailed integration status
- `/home/donovan/Projects/ReliantAI/integration_plan/V.md` - Integration planning
