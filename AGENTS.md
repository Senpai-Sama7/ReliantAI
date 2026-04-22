# AGENTS.md — ReliantAI Workspace Guide

Welcome, Agent. You are operating in **ReliantAI**, a high-assurance, multi-project workspace designed for AI automation and document intelligence.

---

## 📜 Core Directives

1. **NO SIMULATION**: Do not use mocks, stubs, or placeholders for external services (Twilio, Groq, etc.) unless specifically configured as a "STUB" mode in the project's `.env`.
2. **PROJECT ISOLATION**: Each top-level directory is a self-contained system. Do not leak dependencies or configuration between them.
3. **VERIFY BEFORE PROCEEDING**: You must run the project's specific test suite or a `curl` health check before marking any task as complete.
4. **HOSTILE AUDIT**: Assume every line of code will be audited for security (SQLi, XSS, Secret leakage) and efficiency.
5. **PROGRESS TRACKING**: Always update `PROGRESS_TRACKER.md` with your status.

## 🧭 Repo-Wide Hostile Audit Protocol

Use this protocol for any whole-workspace review, vulnerability scan, or multi-project remediation pass.

### Specialist Roles

1. **frontend-engineer**: Review browser, React, Next.js, Vite, Electron, and static-HTML surfaces for XSS, unsafe DOM injection, auth-state leakage, build regressions, and broken UI verification paths.
2. **backend-engineer**: Review Python, Rust, and Node service runtimes for auth flaws, unsafe command execution, deserialization risks, weak validation, data-loss hazards, and failing health/test surfaces.
3. **security-engineer**: Review repo-wide controls, secret handling, dependency security, attack paths, rate limiting, session/JWT handling, and auditability gaps.

### Execution Topology

- **Parallel readers, single writer**: Multiple agents may inspect the repo concurrently, but only one active writer may patch shared files at a time.
- **Dependency-order fixes only**: Reproduce failures first, then fix foundational issues before downstream symptoms.
- **Per-phase memory compaction**: After each phase, summarize findings, commands, proof, residual risk, and next gates in `PROGRESS_TRACKER.md`.

### Mandatory Phase Gates

1. **Phase 0 — Inventory & Controls**
   - Enumerate in-scope projects, entrypoints, package managers, lockfiles, and runnable test/build surfaces.
   - Confirm existing AGENTS constraints before any edits.
2. **Phase 1 — Concurrent Discovery**
   - Run specialist review tracks in parallel.
   - Collect reproducible findings with file references and validation commands.
3. **Phase 2 — Reproduce & Prioritize**
   - Reproduce critical and high-severity findings with real commands, health checks, or runtime behavior.
   - Rank by exploitability, blast radius, and dependency order.
4. **Phase 3 — Remediation**
   - Patch one fix batch at a time.
   - Never delete the original failed approach without documenting what replaced it and why.
5. **Phase 4 — Verification & Hostile Retest**
   - Re-run the narrow regression and security checks for each touched component.
   - Attack the changed surfaces with malformed input, missing auth, edge cases, and regression checks.
6. **Phase 5 — Evidence & Residual Risk**
   - Update `PROGRESS_TRACKER.md` with commands, results, proof, residual risks, and any blocked items.
   - If a scanner or service cannot run, record the exact blocker rather than implying success.

### Non-Negotiable Audit Rules

- No phase advances without verifiable proof recorded in `PROGRESS_TRACKER.md`.
- No TODOs, placeholders, fake data paths, or mock-only success claims in production code.
- No destructive commands (`git reset --hard`, `rm -rf`, truncation/wipe endpoints, schema drops) unless the user explicitly requests them.
- No unreviewed secret handling changes; never print or persist live secrets in logs, screenshots, or reports.
- No broad "repo is secure" claim unless the exact projects, commands, and residual gaps are explicitly listed.
- When scanners are available, run them. When they are not, document the missing tool and use the best repo-grounded fallback review.
- For UI proof, prefer live screenshots only after the relevant app is running; otherwise use build/test/Playwright output and document the missing runtime blocker.

### Audit Artifact Contract

- Root `PROGRESS_TRACKER.md` is the canonical hostile-audit ledger. Append new epochs; do not rewrite or collapse prior evidence.
- Proof artifacts must live under `proof/hostile-audit/<timestamp>/phase-<n>/` and include the exact commands, logs, request/response captures, and screenshots used to support claims.
- Every phase summary must include: status, commands run, results, proof paths, blockers, residual risks, and whether the originally proposed reproduction method worked.
- Every touched project `AGENTS.md` must inherit these hostile-audit rules when that project is remediated.
- Scanner installation attempts must be logged with the exact tool name, install command, resulting version, or precise blocker.

---

## 🏗️ Workspace Overview

ReliantAI is a multi-system workspace containing 14+ autonomous business execution systems. The **Integration Layer** (ports 8080/8081) provides shared authentication and event bus infrastructure.

### System Catalog

| System | Language | Status | Purpose |
|:-------|:---------|:-------|:--------|
| **ClearDesk** | TypeScript/React 19 | Active Development | AR Document Processing (has prospective customer) |
| **Integration** | Python/FastAPI | ✅ Operational | Auth (8080) + Event Bus (8081) |
| **Money** | Python/CrewAI | Experiment | HVAC AI Dispatch (5-agent Groq chain) |
| **B-A-P** | Python/Poetry | Experiment | Business Analytics Platform |
| **Citadel** | Python/FastAPI | Experiment | Vector/Graph Microservices |
| **BackupIQ** | Python | Experiment | Semantic Backup with Knowledge Graphs |
| **intelligent-storage** | Python | Experiment | File Intelligence with Semantic Search |
| **Acropolis** | Rust/Julia | Experiment | Expert Plugin Platform |
| **apex** | Rust/TS/Python | Experiment | Probabilistic Multi-Agent OS |
| **Gen-H** | TypeScript/React | Experiment | HVAC Growth Engine |
| **DocuMancer** | Electron/Python | Experiment | Document Converter Desktop App |
| **reGenesis** | Node.js/pnpm | Experiment | Site Generator with Puppeteer |
| **CyberArchitect** | Node.js | Experiment | Site Archiver |
| **citadel_ultimate_a_plus** | Python | Experiment | Extended Citadel Features |
| **soviergn_ai** | Rust/WASM | Experiment | Browser-Native Compute Runtime |

---

## 🚀 Quick Start — Integration Services

The integration layer is **operational** and provides authentication and event bus services to all projects.

```bash
# 1. Bootstrap all environment variables across projects
./scripts/bootstrap_env.sh

# 2. Start Redis (required for integration)
docker start redis-test 2>/dev/null || docker run -d --name redis-test -p 6379:6379 redis:7-alpine

# 3. Start integration services
cd integration/auth && python auth_server.py &      # Port 8080
cd integration/event-bus && python event_bus.py &   # Port 8081

# 4. Verify health
curl http://localhost:8080/health  # Auth service
curl http://localhost:8081/health  # Event bus
```

### Integration Test Suite

```bash
cd integration
source ../.venv/bin/activate
python -m pytest auth/ event-bus/ tests/ -v

# Expected results:
# ✅ Auth Service:    4/5 tests passing
# ✅ Event Bus:      10/10 tests passing
# ✅ NEXUS Runtime:  19/19 tests passing
# ✅ Data Layout:    17/17 tests passing
# ──────────────────────────────────────
#    TOTAL:          50/51 tests passing
```

---

## 🛠️ Technology Stack by Project

### Python Projects

| Project | Package Manager | Framework | Key Dependencies |
|:--------|:----------------|:----------|:-----------------|
| **B-A-P** | Poetry | FastAPI + SQLAlchemy 2.0 | pandas, polars, OpenAI, Celery, alembic |
| **integration** | pip | FastAPI + Redis | python-jose, bcrypt, pydantic, structlog |
| **Money** | pip | FastAPI + CrewAI | Groq, Twilio, Composio, SQLite (WAL) |
| **Citadel** | pip | FastAPI microservices | RedisVL, Neo4j, Prophet, DoWhy, Experta |
| **BackupIQ** | pip | Custom orchestrator | transformers, Neo4j, spaCy, boto3 |
| **intelligent-storage** | pip | FastAPI + psycopg2 | Ollama embeddings, PostgreSQL/pgvector |

**Python Standards:**
- Python 3.11+ required
- Use `python3` to invoke commands (not `py` or `python`)
- **B-A-P uses Poetry exclusively** — never use pip in B-A-P
- All tests use pytest with asyncio support

### TypeScript/React Projects

| Project | Package Manager | Framework | Key Dependencies |
|:--------|:----------------|:----------|:-----------------|
| **ClearDesk** | npm | React 19 + Vite 7 | Tailwind 4, pdfjs-dist, mammoth, tesseract.js |
| **Gen-H** | npm | React 19 + Vite 7 | Radix UI, shadcn, gsap, recharts, Tailwind 3 |
| **reGenesis** | pnpm 9.7 | Node.js toolchain | Puppeteer, cheerio, sharp, ajv, Playwright |
| **apex/apex-ui** | npm | Next.js 15 | LangGraph integration, SSE streaming |
| **apex/apex-mcp** | npm | MCP SDK | Circuit breakers, 15+ tool integrations |

**TypeScript Standards:**
- Node.js 20+ required for most projects
- reGenesis requires pnpm (specified in packageManager field)
- TypeScript 5.x with strict mode

### Rust Projects

| Project | Build Tool | Key Components |
|:--------|:-----------|:---------------|
| **Acropolis** | Cargo workspace | Tokio, jlrs (Julia FFI), libloading, Tauri GUI |
| **apex/apex-core** | Cargo | Axum 0.8, A2A message bus, circuit breakers |
| **soviergn_ai** | Cargo | WASM, SharedArrayBuffer, Bun integration |

**Rust Standards:**
- Use `cargo test` for testing
- Acropolis uses workspace members: `adaptive_expert_platform/`, `plugins/`, `gui/`

---

## 🔧 Build and Test Commands

### Per-Language Quick Reference

```bash
# Python Projects
poetry install --with dev    # B-A-P only
poetry run pytest tests/ -v  # B-A-P tests
pip install -r requirements.txt  # Other Python projects
python -m pytest tests/ -v       # Standard test command

# TypeScript/React Projects
npm install                  # Standard install
npm run dev                  # Start dev server
npm run build                # Production build
npm run lint                 # ESLint check

# For reGenesis specifically:
pnpm install                 # pnpm required
pnpm run build
pnpm run test

# Rust Projects
cargo build                  # Debug build
cargo build --release        # Optimized build
cargo test                   # Run tests
cargo check                  # Fast syntax/type check
```

### Integration Layer Commands

```bash
# Full stack with Docker
cd integration
docker-compose up -d

# Individual services
cd auth && python auth_server.py          # Port 8080
cd event-bus && python event_bus.py       # Port 8081

# Test suite
cd integration
pytest auth/ event-bus/ tests/ -v
```

---

## 🏛️ Project Structure Conventions

Each project follows these organizational patterns:

```
project-name/
├── src/ or app/              # Source code
│   ├── components/           # UI components (React)
│   ├── api/ or routes/       # API endpoints
│   └── utils/ or core/       # Utilities
├── tests/                    # Test files
│   ├── test_*.py            # Python tests
│   └── *.test.ts            # TypeScript tests
├── requirements.txt          # Python deps (or pyproject.toml)
├── package.json              # Node.js deps
├── Cargo.toml                # Rust deps
├── Dockerfile                # Container build
├── .env.example              # Environment template
├── AGENTS.md                 # Project-specific guide
└── README.md                 # Human documentation
```

### Configuration Files

| File | Purpose |
|:-----|:--------|
| `pyproject.toml` | Python Poetry config, tool settings (black, ruff, mypy) |
| `package.json` | Node.js dependencies and scripts |
| `Cargo.toml` | Rust workspace/package manifest |
| `docker-compose.yml` | Multi-service local deployment |
| `.env` | Local environment variables (never commit) |
| `.env.example` | Template for required variables |

---

## 🧪 Testing Strategy

### Python Testing

- **Framework**: pytest with pytest-asyncio
- **Coverage**: B-A-P enforces 90%, BackupIQ enforces 95%
- **Property Testing**: hypothesis library used in integration
- **Async**: `asyncio_mode = auto` in pytest.ini

```bash
# Standard Python test command
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-fail-under=90

# Specific test file
python -m pytest tests/test_api.py -v
```

### TypeScript Testing

- **Framework**: Vitest (ClearDesk, Gen-H), Jest (DocuMancer), Playwright (E2E)
- **Command**: `npm test` or `pnpm test`

### Rust Testing

```bash
cargo test           # All tests
cargo test --release # Optimized tests
cargo test <filter>  # Specific tests
```

---

## 🔒 Security & Data Conventions

### Authentication Patterns

**JWT (Integration Layer):**
```bash
# Login to get token
curl -X POST "http://localhost:8080/token" \
  -d "username=test&password=testpass123"

# Use token in requests
curl http://localhost:8080/protected/read \
  -H "Authorization: Bearer <access_token>"
```

**API Key (Project-specific):**
```python
# Standard pattern across projects
X-API-Key: your-secret-key
```

### Security Requirements

1. **SQLite WAL Mode**: Local databases MUST use Write-Ahead Logging for concurrency
2. **JWT Secrets**: Auth secrets must be 32+ characters, loaded from environment
3. **Input Sanitization**: All SMS/Email outputs must be sanitized to prevent XSS
4. **Rate Limiting**: Global 60 req/min per API key/IP standard
5. **State Machines**: Prefer explicit transition logic over nullable database flags

### Environment Variable Standards

```bash
# Required across projects
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=minimum-32-characters-for-jwt
API_KEY=project-specific-api-key

# Integration specific
AUTH_SECRET_KEY=minimum-32-characters
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 📊 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Integration Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  Auth Service   │◄───────►│      Redis      │           │
│  │    Port 8080    │         │    Port 6379    │           │
│  │                 │         │                 │           │
│  │  • OAuth2/JWT   │         │  • Sessions     │           │
│  │  • RBAC (4)     │         │  • Pub/Sub      │           │
│  │  • bcrypt       │         │  • Token store  │           │
│  └────────┬────────┘         └────────┬────────┘           │
│           │                           │                    │
│           │    ┌─────────────────┐    │                    │
│           └───►│   Event Bus     │◄───┘                    │
│                │   Port 8081     │                         │
│                │                 │                         │
│                │  • Pub/Sub      │                         │
│                │  • Schema val   │                         │
│                │  • DLQ          │                         │
│                └─────────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Service Communication Rules

1. **Direct service-to-service calls are FORBIDDEN**
2. Use Event Bus for async communication
3. Use Gateway (or direct auth service) for sync API calls
4. Every request must include `X-Correlation-ID` header for tracing
5. All events must conform to schema with `event_id`, `event_type`, `source`, `timestamp`, `payload`, `correlation_id`

---

## 📝 Code Style Guidelines

### Python

```python
# Import order (strict)
# 1. Standard library
import os
import json
from datetime import datetime

# 2. Third-party
from fastapi import FastAPI
from sqlalchemy import select
from pydantic import BaseModel

# 3. Local (absolute imports)
from src.config import settings
from src.core.database import get_db

# Type hints encouraged
def process_data(item_id: str) -> dict[str, Any]:
    """Docstrings for all public functions."""
    pass
```

### TypeScript

```typescript
// Strict TypeScript config
// Prefer interfaces over types for objects
// Use explicit return types on exported functions

export interface ApiResponse<T> {
  data: T;
  status: number;
  timestamp: string;
}

export async function fetchData(): Promise<ApiResponse<Data>> {
  // Implementation
}
```

---

## 🚀 Deployment Patterns

### Docker Compose (Development)

```bash
# Most projects have docker-compose.yml
docker-compose up -d           # Start services
docker-compose logs -f         # View logs
docker-compose down            # Stop services
```

### Health Check Verification

Before marking any task complete, verify:

```bash
# Auth Service
curl http://localhost:8080/health
# Expected: {"status":"healthy","redis":"connected"}

# Event Bus
curl http://localhost:8081/health
# Expected: {"status":"healthy","redis":"connected","service":"event-bus"}

# Project-specific endpoints
curl http://localhost:8000/health  # Most Python services
curl http://localhost:3000/api/health  # Next.js apps
```

---

## 📚 Key Documentation Files

| File | Purpose |
|:-----|:--------|
| `README.md` | Project overview for humans |
| `AGENTS.md` | AI agent guidance (this pattern) |
| `QUICK_START.md` | Integration operational guide |
| `DEPLOYMENT_STATUS.md` | Live deployment details |
| `PROGRESS_TRACKER.md` | Phase tracking and task status |
| `SCAFFOLD_PLAN.md` | Scaffold generation planning |
| `CLAUDE.md` | Claude-specific context |
| `GEMINI.md` | Gemini-specific context |

---

## ✅ Final Verification Checklist

Before completing any task:

- [ ] Passed all unit tests (`pytest`, `cargo test`, `npm test`)
- [ ] No secrets in plaintext or captured in logs
- [ ] All new dependencies added to correct lockfile (Poetry, Cargo, pnpm, npm)
- [ ] `PROGRESS_TRACKER.md` updated with status
- [ ] Health check endpoints respond correctly
- [ ] Created a verification report in final message

---

*Last Updated: 2026-03-10*  
*Primary Contact: Antigravity AI*  
*Integration Status: OPERATIONAL*
