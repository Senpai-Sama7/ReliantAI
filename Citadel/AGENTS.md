# Citadel - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

Citadel is a modular collection of Python microservices for building AI-powered applications. Each service is a FastAPI application secured with API key authentication and exposes a `/health` endpoint.

## Hostile Audit Rules

- Any local-agent or shell-execution surface must avoid `shell=True` for user-controlled input and must document the safer replacement path.
- Preserve confirmation gates on destructive local actions and verify regressions with real commands or compile checks.
- Append hostile-audit proof and any residual command-execution risk to the root `PROGRESS_TRACKER.md`.
 
**Services Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  API Gateway                                            │
│  ├── Routes requests to downstream services             │
│  └── Forwards API key to each request                   │
├─────────────────────────────────────────────────────────┤
│  Microservices                                          │
│  ├── Vector Search (Redis + sentence embeddings)       │
│  ├── Knowledge Graph (Neo4j read-only queries)         │
│  ├── Causal Inference (DoWhy treatment effects)        │
│  ├── Time Series (Prophet forecasting)                 │
│  ├── Multi-Modal (text + image embeddings)             │
│  ├── Hierarchical Classification (model training)      │
│  ├── Rule Engine (Experta rule evaluation)             │
│  ├── Orchestrator (Redis stream → services → Neo4j)    │
│  └── NL Agent (Gemini-backed chat + tool routing)      │
└─────────────────────────────────────────────────────────┘
```

---

## Build / Run / Test Commands

### Docker Compose (Recommended)
```bash
# Start all infrastructure (Redis, Neo4j, etc.)
docker compose up -d

# Install Python dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific service tests
pytest tests/test_vector_search.py
pytest tests/test_knowledge_graph.py
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files README.md
```

### Individual Services
```bash
# Vector Search Service
cd services/vector_search
uvicorn app:app --port 8001

# Knowledge Graph Service
cd services/knowledge_graph
uvicorn app:app --port 8002

# (Each service runs independently)
```

### End-to-End Script
```bash
# Run complete pipeline test
./run_end_to_end.sh
```

---

## Technology Stack

| Service | Technology | Purpose |
|---------|------------|---------|
| **Gateway** | FastAPI | Request routing, auth forwarding |
| **Vector Search** | RedisVL, sentence-transformers | Semantic search |
| **Knowledge Graph** | Neo4j, Cypher | Graph queries |
| **Causal Inference** | DoWhy, pandas | Treatment effect estimation |
| **Time Series** | Prophet | Forecasting, anomaly detection |
| **Multi-Modal** | CLIP, PIL | Cross-modal embeddings |
| **Classification** | scikit-learn | Hierarchical classifiers |
| **Rules** | Experta | Rule-based reasoning |
| **Orchestrator** | Redis Streams, async | Event-driven workflows |

---

## Project Structure

```
Citadel/
├── services/
│   ├── api_gateway/            # Request routing
│   ├── vector_search/          # RedisVL embeddings
│   ├── knowledge_graph/        # Neo4j interface
│   ├── causal_inference/       # DoWhy integration
│   ├── time_series/            # Prophet forecasting
│   ├── multi_modal/            # Text + image embeddings
│   ├── hierarchical_classification/  # Model training
│   ├── rule_engine/            # Experta rules
│   └── orchestrator/           # Event coordination
├── backend/
│   ├── app.py                  # Backend entry point
│   └── static/                 # React frontend
├── local_agent/                # Desktop GUI agent
│   ├── agent.py               # Agent logic
│   └── gui.py                 # Tkinter interface
├── notebooks/                  # Jupyter examples
├── scripts/                    # Data ingestion scripts
├── tests/                      # Test suites
├── compose.yaml               # Docker Compose config
├── Makefile                   # Standard commands
└── desktop_gui.py             # Standalone GUI launcher
```

---

## Critical Code Patterns

### API Key Authentication
All services use the same API key pattern:
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.get("/protected", dependencies=[Depends(verify_api_key)])
async def protected_endpoint():
    return {"status": "ok"}
```

### Health Check Standard
Every service MUST implement:
```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "vector_search",
        "version": "1.0.0"
    }
```

### Neo4j Read-Only Queries
Knowledge Graph service enforces read-only:
```python
# Only MATCH queries allowed
if not query.strip().upper().startswith("MATCH"):
    raise HTTPException(400, "Only MATCH queries permitted")
```

### Vector Index Management
```python
# Index creation is idempotent
from redisvl.index import SearchIndex

index = SearchIndex.from_dict(schema, redis_client=redis)
index.create(overwrite=False)  # Won't fail if exists
```

---

## Non-Obvious Gotchas

### 1. Services are Independent FastAPI Apps
Each service in `services/` is a standalone FastAPI application:
- Has its own `requirements.txt`
- Runs on its own port
- Can be deployed independently

The API Gateway routes requests based on URL prefix.

### 2. Pre-commit is Mandatory
All commits must pass pre-commit hooks:
```bash
pre-commit install
```

Hooks include:
- Trailing whitespace removal
- YAML validation
- Python syntax check

### 3. State Machine Enforced in CODE
Unlike other projects with DB constraints, Citadel's orchestrator enforces state transitions in Python code:
```python
# Valid transitions defined in code, not DB
VALID_TRANSITIONS = {
    "pending": ["processing", "cancelled"],
    "processing": ["completed", "failed"],
    # ...
}
```

### 4. Docker Compose Services Name
The compose file is named `compose.yaml` (Docker Compose v2 style), NOT `docker-compose.yml`.

### 5. Redis Streams for Orchestrator
The orchestrator uses Redis Streams (not Pub/Sub):
```python
# Consumer group pattern
redis.xreadgroup(
    groupname="orchestrator",
    consumername=consumer_id,
    streams={"events": ">"}
)
```

### 6. GPU Optional
Most services run on CPU. Only Multi-Modal service benefits significantly from GPU for CLIP embeddings.

### 7. Desktop GUI Launcher
`desktop_gui.py` is a standalone launcher that:
- Starts the local agent
- Provides a Tkinter GUI
- Can be run without Docker

### 8. TimescaleDB for Time Series
While not in the main compose, the orchestrator can persist to TimescaleDB for time-series analytics.

---

## Configuration

### Environment Variables (`.env`)
```bash
# Required for all services
API_KEY=your-secret-api-key

# Service-specific
REDIS_URL=redis://localhost:6379
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# Vector search
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Service Ports (Default)
| Service | Port |
|---------|------|
| API Gateway | 8000 |
| Vector Search | 8001 |
| Knowledge Graph | 8002 |
| Causal Inference | 8003 |
| Time Series | 8004 |
| Multi-Modal | 8005 |
| Hierarchical Classification | 8006 |
| Rule Engine | 8007 |
| Orchestrator | 8008 |

---

## Testing Strategy

### Service Tests
Each service has its own test file:
```bash
pytest tests/test_vector_search.py -v
pytest tests/test_knowledge_graph.py -v
pytest tests/test_causal_inference.py -v
```

### Integration Tests
```bash
# Requires all services running
pytest tests/integration/ -v
```

### End-to-End
```bash
./run_end_to_end.sh
```

---

## Makefile Commands

```bash
make install          # Install dependencies
make test             # Run pytest
make lint             # Run pre-commit
make run-gateway      # Start API gateway
make run-services     # Start all services
make docker-up        # Docker compose up
make docker-down      # Docker compose down
```

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects
