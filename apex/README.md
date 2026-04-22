# APEX
**Autonomous Probabilistic Execution System**

[![CI](https://github.com/Senpai-Sama7/apex/actions/workflows/ci.yml/badge.svg)](https://github.com/Senpai-Sama7/apex/actions/workflows/ci.yml)
![Rust](https://img.shields.io/badge/Rust-1.83-orange?logo=rust)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue?logo=typescript)
![License](https://img.shields.io/badge/license-private-red)

APEX is a five-layer multi-agent operating system built for autonomous business execution. It replaces the coordination-without-intelligence failure mode of conventional multi-agent systems by treating agents as a cognitive stack — where each layer's output constrains and informs the layer below it.

Every decision carries full uncertainty decomposition. Every action is auditable. Every contested decision stops for human review before execution.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1 — Orchestration (Cognitive Command)            │
│  Theory of Mind → Data Model Plan → Metacognition       │
│  → APEX Commander                                       │
├─────────────────────────────────────────────────────────┤
│  Layer 2 — UPS Probabilistic Intelligence               │
│  Calibration Auditor · Uncertainty Decomposition        │
│  · Decision Gate (aleatoric / epistemic)                │
├─────────────────────────────────────────────────────────┤
│  Layer 3 — Specialist Execution                         │
│  Research · Creative · Analytics · Sales                │
├─────────────────────────────────────────────────────────┤
│  Layer 4 — Adversarial Quality                          │
│  Hostile Auditor · Debate Agent · Evolver               │
├─────────────────────────────────────────────────────────┤
│  Layer 5 — Integration                                  │
│  Context7 · Zapier · MCP Tool Bus (15+ servers)         │
└─────────────────────────────────────────────────────────┘

  [TypeScript UI]  ←── SSE stream ──  [Rust apex-core bus]
                                            ↑         ↓
                                   POST /message    tier routing
                                            ↓
                                   [Python apex-agents]
                                            ↓
                                   [TypeScript apex-mcp]
                                            ↓
                         Context7 / Zapier / HubSpot / Notion / Stripe
```

### Execution Tiers

Every A2A message is routed to one of four tiers before any agent logic runs:

| Tier | Condition | Path |
|------|-----------|------|
| **T1 Reflexive** | Confidence > 0.92, stakes = low | Direct to Layer 3 |
| **T2 Deliberative** | Confidence 0.65–0.92 | Full L1–L3 pipeline |
| **T3 Contested** | Confidence < 0.65 or high stakes | All 5 layers + HITL |
| **T4 Unknown** | Domain novelty > 0.85 | Immediate human escalation |

---

## Stack

| Service | Language | Framework | Role |
|---------|----------|-----------|------|
| `apex-core` | Rust | Axum 0.8 + Tokio | A2A message bus, confidence router, circuit breakers |
| `apex-agents` | Python | FastAPI + LangGraph | All agent logic (Layers 1–4) |
| `apex-ui` | TypeScript | Next.js 15 | HITL dashboard, uncertainty visualization |
| `apex-mcp` | TypeScript | MCP SDK | Dynamic tool bus (15+ integrations) |

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | Latest | [docker.com](https://www.docker.com/products/docker-desktop) |
| Rust | 1.83+ | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/Senpai-Sama7/apex.git
cd apex

# 2. Configure environment
cp infra/.env.example .env
# Edit .env — set POSTGRES_PASSWORD, ANTHROPIC_API_KEY (or OPENAI_API_KEY),
# GEMINI_API_KEY for memory embeddings,
# and LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY

# 3. Start all services
cd infra && docker compose up --build -d

# 4. Verify everything is running
docker compose ps
# All services should show: Up (healthy)
```

---

## API Reference

All endpoints are prefixed by their service URL. Default local ports:
- `apex-core` → `http://localhost:8000`
- `apex-agents` → `http://localhost:8001`

### apex-core

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/message` | Submit an A2A message — returns routing tier and trace ID |
| `GET` | `/metrics` | Circuit breaker status for all integrations |

### apex-agents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/workflow/run` | Run full Layer 1 pipeline (ToM → Data Plan → Routing → HITL if needed) |
| `POST` | `/workflow/{thread_id}/resume` | Resume a workflow paused at HITL |
| `GET` | `/workflow/{thread_id}/status` | Check if workflow is waiting for human review |
| `GET` | `/workflow/hitl/pending` | List all workflows awaiting human review |
| `GET` | `/workflow/hitl/stream` | SSE stream — real-time HITL notifications |
| `POST` | `/agents/layer1/theory-of-mind` | Run Theory of Mind in isolation |

### A2A Message Schema

```json
{
  "message_id": "uuid",
  "trace_id":   "uuid",
  "sender":     "agent_name",
  "recipient":  {"type": "Layer", "value": 2},
  "payload":    {},
  "context": {
    "confidence":     0.87,
    "uncertainty":    {"aleatoric": 0.08, "epistemic": 0.13},
    "stakes":         "medium",
    "domain_novelty": 0.1
  },
  "timestamp": "2026-03-03T00:00:00Z"
}
```

---

## Environment Variables

Copy `infra/.env.example` to `.env`. Required before first run:

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_USER` | ✅ | Database username |
| `POSTGRES_PASSWORD` | ✅ | Database password — use something strong |
| `POSTGRES_DB` | ✅ | Database name |
| `ANTHROPIC_API_KEY` | ✅ (or OpenAI) | Claude API key for agent inference |
| `OPENAI_API_KEY` | Optional | Legacy OpenAI inference key during provider cutover |
| `GEMINI_API_KEY` | ✅ | Gemini API key for memory embeddings |
| `LLM_PROVIDER` | ✅ | `anthropic` or `openai` |
| `LANGFUSE_PUBLIC_KEY` | Recommended | Observability tracing |
| `LANGFUSE_SECRET_KEY` | Recommended | Observability tracing |
| `HITL_AUTO_APPROVE_SECONDS` | Optional | Seconds before auto-approval (default: 300) |
| `HITL_AUTO_APPROVE_CONFIDENCE` | Optional | Min confidence for auto-approval (default: 0.75) |

---

## Project Structure

```
apex/
├── apex-core/          # Rust — A2A bus, confidence router, circuit breakers
├── apex-agents/        # Python — All LLM agent logic (Layers 1–4)
│   ├── agents/
│   │   ├── layer1/     # Theory of Mind, Data Model Plan, workflow graph
│   │   ├── layer2/     # Calibration, uncertainty decomposition
│   │   ├── layer3/     # Research, Creative, Analytics, Sales
│   │   └── layer4/     # Hostile Auditor, Debate, Evolver
│   ├── hitl/           # HITL interrupt, auto-approver, feedback loop
│   ├── memory/         # Episodic, semantic, procedural memory
│   ├── core/           # Model router, A2A client, checkpointer
│   └── observability/  # Langfuse tracing
├── apex-ui/            # TypeScript — HITL dashboard (Increment 5)
├── apex-mcp/           # TypeScript — MCP tool bus (Increment 5)
├── infra/              # Docker Compose, init.sql, .env.example
└── docs/               # Architecture, A2A schema, runbook
```

---

## Observability

Every LLM call, agent invocation, and routing decision is traced automatically via [Langfuse](https://langfuse.com). Create a free account, add your keys to `.env`, and every workflow run appears in your Langfuse dashboard with:

- Full prompt and output for every agent
- Latency and token cost per node
- Confidence and uncertainty values per message
- Human correction events linked to their originating trace

---

## Human-in-the-Loop

Workflows routed to T3 or T4 pause execution and publish a notification to Redis. The HITL dashboard (Increment 5) reads this via SSE and presents the approval UI.

**Auto-approval** fires automatically when:
1. Confidence ≥ `HITL_AUTO_APPROVE_CONFIDENCE`
2. Stakes are not `high` or `irreversible`
3. `HITL_AUTO_APPROVE_SECONDS` have elapsed with no human response

Human corrections are stored to episodic memory and surfaced to the Layer 4 Evolver agent as training signal.

---

## Roadmap

- [x] Increment 1 — Infrastructure (PostgreSQL + pgvector + Redis)
- [x] Increment 2 — apex-core Rust A2A bus + confidence router
- [x] Increment 3 — Python agent service + Theory of Mind
- [x] Increment 4 — Data Model Plan + HITL + auto-approval + feedback loop
- [ ] Increment 5 — TypeScript HITL dashboard + uncertainty visualization
- [ ] Increment 6 — Layer 2 calibration + Layer 3 specialist agents
- [ ] Increment 7 — Layer 4 adversarial quality (Hostile Auditor + Evolver)
- [ ] Increment 8 — MCP tool bus + Zapier outbound

---

## Security

- No secrets are ever hardcoded. All credentials are loaded from `.env` at runtime.
- The CI pipeline scans every push for hardcoded API key patterns.
- `.env` is listed in `.gitignore` and CI verifies it is never committed.
- The audit log is append-only at the database rule level — no update or delete is possible.
- Circuit breakers protect every external integration from cascade failures.

---

*Built by [Douglas Mitchell](https://github.com/Senpai-Sama7) — Houston, TX*
