# APEX Autonomous Probabilistic Execution System - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

APEX is a five-layer multi-agent operating system built for autonomous business execution. It replaces coordination-without-intelligence by treating agents as a cognitive stack where each layer's output constrains the layer below.

**Every decision carries:**
- Full uncertainty decomposition (aleatoric/epistemic)
- Confidence scoring
- Audit trail
- Human-in-the-loop (HITL) pause for contested decisions

## Hostile Audit Persistence

- Append every hostile-audit checkpoint and verification result to the root `PROGRESS_TRACKER.md`.
- Do not mark `apex-agents`, `apex-mcp`, or proxy/auth changes complete without a real command result, test run, health check, or screenshot saved under `proof/hostile-audit/<timestamp>/`.
- Reproduce before patching. If the original exploit path fails, record both the failed method and the replacement proof path.
- Default all shared-auth integrations to fail closed when validators, secrets, or upstream auth services are unavailable.
- If a scanner or service cannot run, record the exact blocker and fallback review path instead of implying success.

**Execution Tiers:**
| Tier | Condition | Path |
|------|-----------|------|
| T1 Reflexive | Confidence > 0.92, low stakes | Direct to Layer 3 |
| T2 Deliberative | Confidence 0.65–0.92 | Full L1–L3 pipeline |
| T3 Contested | Confidence < 0.65 or high stakes | All 5 layers + HITL |
| T4 Unknown | Domain novelty > 0.85 | Immediate human escalation |

---

## Build / Run / Test Commands

### Complete Stack (Docker Compose)
```bash
# Start all services (postgres, langfuse, apex-agents, apex-mcp, apex-ui, langfuse)
cd infra && docker compose up --build -d

# View logs
docker compose logs -f apex-agents
docker compose logs -f apex-mcp

# Stop everything
docker compose down

# Rebuild specific service
docker compose up apex-agents --build -d
```

### Individual Components

**apex-agents (Python/FastAPI):**
```bash
cd apex-agents
pip install -r requirements.txt
python -m pytest tests/ -v
```

**apex-mcp (TypeScript/MCP SDK):**
```bash
cd apex-mcp
npm install
npm run build
npm test
```

**apex-ui (Next.js 15):**
```bash
cd apex-ui
npm install
npm run dev      # Development server
npm run build    # Production build
```

---

## Technology Stack

| Service | Language | Framework | Port | Role |
|---------|----------|-----------|------|------|
| `apex-core` | Rust | Axum 0.8 + Tokio | - | A2A message bus, circuit breakers |
| `apex-agents` | Python | FastAPI + LangGraph | 8001 | Agent logic (Layers 1–4) |
| `apex-ui` | TypeScript | Next.js 15 | 3000 | HITL dashboard, uncertainty viz |
| `apex-mcp` | TypeScript | MCP SDK | 4000 | Dynamic tool bus (15+ integrations) |
| Postgres | SQL | pgvector/pg16 | 5432 | Primary database |
| Langfuse | - | - | 3001 | Agent observability |

---

## Project Structure

```
apex/
├── apex-agents/                  # Python agent logic
│   ├── agents/
│   │   ├── layer1/              # Orchestration agents
│   │   ├── layer2/              # UPS probabilistic intelligence
│   │   ├── layer3/              # Specialist execution
│   │   └── layer4/              # Adversarial quality
│   ├── api/main.py              # FastAPI entry point
│   └── test_event_publisher.py  # Event testing
├── apex-mcp/                     # TypeScript MCP tool bus
│   ├── src/tools/               # 15+ integrations (HubSpot, Notion, Stripe...)
│   └── src/circuit-breaker.ts   # Resilience patterns
├── apex-ui/                      # Next.js HITL dashboard
│   ├── src/components/          # UncertaintyGauge, HitlList, etc.
│   └── src/app/api/             # Proxy routes
├── infra/                        # Docker Compose, migrations
│   ├── docker-compose.yml       # Complete stack definition
│   └── migrations/              # SQL schema files
└── docs/ARCHITECTURE.md         # Detailed architecture docs
```

---

## Critical Code Patterns

### A2A Message Required Fields
Every agent-to-agent message MUST include:
```python
{
    "confidence": float,           # 0.0 - 1.0
    "uncertainty": {
        "aleatoric": float,        # Irreducible uncertainty
        "epistemic": float         # Knowledge uncertainty
    },
    "stakes": "low|medium|high",
    "domain_novelty": float        # 0.0 - 1.0
}
```

### HITL Pause Trigger
Human review is triggered when:
- `confidence < 0.65`
- `stakes == "high"`
- `domain_novelty > 0.85`

### Circuit Breaker Pattern
```typescript
// apex-mcp uses circuit breakers for external APIs
const breaker = new CircuitBreaker({
    failureThreshold: 5,
    resetTimeout: 30000,
    halfOpenMaxCalls: 3
});
```

---

## Non-Obvious Gotchas

### 1. Langfuse Requires Separate Postgres
APEX uses TWO postgres instances:
- `postgres` (pgvector:pg16) - Main app database
- `postgres-langfuse` (postgres:16-alpine) - Langfuse analytics

This avoids multi-DB initialization complexity. Don't try to share them.

### 2. APEX_README.md vs README.md
- `README.md` - Standard project overview
- `APEX_README.md` - Detailed APEX-specific documentation

### 3. Environment Variables
Critical env vars (see `.env.example`):
- `POSTGRES_PASSWORD` - Main DB password
- `LANGFUSE_DB_PASSWORD` - Analytics DB password
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - agent inference access
- `GEMINI_API_KEY` - memory embeddings access
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` - Observability

### 4. Layer 3 Agent Registration
Specialist agents (Research, Creative, Analytics, Sales) are registered dynamically. New agents must:
1. Implement the layer3 agent interface
2. Register in `layer3/__init__.py`
3. Expose capabilities manifest

### 5. MCP Tool Bus Discovery
Tools are discovered at runtime via MCP protocol. Tool registration:
- Static: Defined in `src/tools/index.ts`
- Dynamic: Fetched from tool servers at startup

### 6. SSE Stream for HITL
The UI connects via Server-Sent Events (SSE) for real-time HITL:
- Endpoint: `GET /api/proxy/hitl-stream`
- Reconnects automatically on disconnect
- Heartbeat every 30 seconds

---

## Testing Strategy

### Unit Tests
```bash
# Python agents
cd apex-agents && pytest tests/ -v

# TypeScript MCP
cd apex-mcp && npm test
```

### Integration Tests
```bash
# Start full stack
cd infra && docker compose up -d

# Wait for health checks
curl http://localhost:8001/health  # apex-agents
curl http://localhost:4000/health  # apex-mcp
```

### End-to-End Tests
```bash
# Trigger a workflow and verify HITL behavior
curl -X POST http://localhost:8001/message \
  -H "Content-Type: application/json" \
  -d '{"agent": "layer1/commander", "input": "..."}'
```

---

## Deployment Notes

### Production Requirements
- Docker Swarm or Kubernetes recommended
- Minimum 4GB RAM per apex-agents instance
- Postgres connection pooling (default: 20)
- Redis for distributed locking (if multi-instance)

### Monitoring
- Langfuse dashboard: `http://localhost:3001`
- Prometheus metrics: `GET /metrics` on each service
- Health checks: `GET /health` on each service

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects
