# BackupIQ - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

BackupIQ is an enterprise-grade backup solution with semantic file organization and production reliability. It combines traditional backup capabilities with AI-powered file classification and knowledge graph construction.

**Key Capabilities:**
- Multi-cloud backup (iCloud, Google Drive, AWS S3)
- AI-powered semantic file classification
- Knowledge graph construction from file metadata
- Circuit breakers, exponential backoff, resource monitoring
- Enterprise observability (Prometheus, structured logging)

## Hostile Audit Rules

- BackupIQ auth must fail closed when the shared validator or secrets are unavailable; do not restore anonymous dev bypass behavior.
- Add or update regression tests for security fixes before marking the project complete.
- Append hostile-audit commands, proof, and blockers to the root `PROGRESS_TRACKER.md`.
 
**Target Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  Backup Orchestrator                                    │
│  ├── Resource monitoring (CPU, memory, disk)           │
│  ├── Circuit breakers for cloud APIs                   │
│  └── Exponential backoff retry logic                   │
├─────────────────────────────────────────────────────────┤
│  Semantic Layer                                         │
│  ├── AI classifier (file content analysis)             │
│  ├── Knowledge graph (Neo4j)                           │
│  └── Entity relationships                              │
├─────────────────────────────────────────────────────────┤
│  Storage Adapters                                       │
│  ├── iCloud Drive                                      │
│  ├── Google Drive                                      │
│  └── AWS S3                                            │
└─────────────────────────────────────────────────────────┘
```

---

## Build / Run / Test Commands

### Makefile Workflow
```bash
# Development setup
make install      # Install dependencies
make dev-install  # Install with pre-commit hooks

# Run the application
make run          # Start the backup service

# Testing
make test         # Run all tests
make test-unit    # Unit tests only
make coverage     # Run with coverage report

# Quality checks
make lint         # Run linters
make format       # Format code
make type-check   # Type checking

# Deployment
make docker-build # Build Docker image
make docker-run   # Run in Docker
```

### Direct Commands (if no Makefile)
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run with coverage (95% enforced)
pytest tests/ --cov=src --cov-fail-under=95
```

### Docker
```bash
# Production deployment
docker-compose up -d

# Check health
curl http://localhost:8080/health
curl http://localhost:9090/metrics
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Core** | Python 3.11+ | Main application |
| **Backup Engine** | Custom orchestrator | File backup coordination |
| **AI Classification** | transformers, spacy | Content analysis |
| **Knowledge Graph** | Neo4j | File relationships |
| **Caching** | Redis | Session and metadata |
| **Monitoring** | Prometheus | Metrics collection |
| **Testing** | pytest, pytest-cov | Test suite (95% coverage gate) |
| **Deployment** | Docker, Kubernetes | Container orchestration |

---

## Project Structure

```
BackupIQ/
├── src/
│   ├── core/                    # Core business logic
│   │   ├── orchestrator.py     # Backup coordination
│   │   └── resource_monitor.py # CPU/memory/disk tracking
│   ├── services/                # Business services
│   │   ├── backup_service.py
│   │   ├── classification_service.py
│   │   └── storage_adapters/   # iCloud, Google Drive, S3
│   ├── interfaces/              # External interfaces
│   │   ├── api.py              # REST API
│   │   └── cli.py              # Command line interface
│   └── monitoring/              # Observability
│       ├── metrics.py
│       └── health.py
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── config/
│   ├── environments/           # Environment configs
│   └── services.yml            # Service discovery
├── deployment/                 # Infrastructure as Code
│   ├── docker/
│   └── kubernetes/
└── Makefile                    # Standard commands
```

---

## Critical Code Patterns

### Circuit Breaker Pattern
```python
from src.core.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=CloudAPIError
)

@breaker
async def backup_to_cloud(files: List[Path]):
    # Cloud API call
    pass
```

### Resource Monitoring
```python
from src.core.resource_monitor import ResourceMonitor

monitor = ResourceMonitor(
    max_memory_gb=4.0,
    max_cpu_percent=75
)

if not monitor.check_resources():
    logger.warning("Resources constrained, throttling...")
    await throttle_operations()
```

### Exponential Backoff
```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
async def upload_with_retry(file: Path):
    # Upload logic
    pass
```

---

## Non-Obvious Gotchas

### 1. Coverage Gate at 95%
BackupIQ enforces 95% test coverage - higher than other projects:
```bash
pytest --cov=src --cov-fail-under=95
```

CI will fail if coverage drops below this threshold.

### 2. Semantic Classification Requires Models
The AI classification service requires downloading ML models on first run:
- spaCy model: `en_core_web_sm`
- Transformer model for document classification

These are cached locally after first download.

### 3. Neo4j Connection Pooling
Knowledge graph operations use connection pooling:
```python
# Connections are pooled and reused
# Don't create new driver instances per request
```

### 4. Storage Adapter Registration
New cloud storage adapters must:
1. Implement `StorageAdapter` interface
2. Register in `StorageAdapterFactory`
3. Add configuration schema

### 5. Pre-commit Hooks Required
All commits must pass pre-commit hooks:
```bash
make dev-install  # Installs hooks
# OR manually:
pre-commit install
pre-commit run --all-files
```

### 6. Resource Limits Are Hard Enforced
The orchestrator will pause operations if:
- Memory exceeds `max_memory_gb`
- CPU exceeds `max_cpu_percent`
- Disk space below threshold

This prevents runaway backups from crashing the system.

### 7. Health Check Hierarchy
```
GET /health      # Overall system health
GET /metrics     # Prometheus metrics
GET /status      # Current operation status
GET /version     # Build information
```

---

## Configuration

### Environment-based Config
```yaml
# config/environments/production.yml
backup:
  resources:
    max_memory_gb: 4.0
    max_cpu_percent: 75
    concurrent_uploads: 5

monitoring:
  metrics_port: 9090
  health_port: 8080
  log_level: INFO

storage:
  adapters:
    - s3
    - google_drive
    # - icloud  # Uncomment to enable
```

### Service Discovery
```yaml
# config/services.yml
services:
  backup_orchestrator:
    enabled: true
    instances: 3
  knowledge_graph:
    enabled: true
    database: neo4j://neo4j:7687
```

---

## Testing Strategy

### Test Organization
| Directory | Purpose | Coverage Target |
|-----------|---------|-----------------|
| `tests/unit/` | Isolated component tests | 80% |
| `tests/integration/` | Service integration tests | 15% |
| `tests/e2e/` | Full workflow tests | 5% |

### Key Test Patterns
```python
# Use fixtures for Neo4j test database
@pytest.fixture
def neo4j_test_db():
    # Spin up test container
    yield db
    # Teardown

# Mock cloud APIs in unit tests
@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock:
        yield mock
```

---

## Deployment

### Docker Production
```bash
docker-compose up -d
```

### Kubernetes
```bash
cd deployment/kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Monitoring Endpoints
After deployment, verify:
- Health: `curl http://localhost:8080/health`
- Metrics: `curl http://localhost:9090/metrics`
- Status: `curl http://localhost:8080/status`

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects
