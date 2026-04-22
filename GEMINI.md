# GEMINI.md — ReliantAI Workspace Scaffold

This file serves as the primary context for Gemini-compatible agents working in the ReliantAI workspace. It provides a high-level overview of the architecture, critical rules, and project-specific guidance. For deeper technical details, always consult the nearest subproject `AGENTS.md` or `README.md`.

## 🏗️ Architecture

ReliantAI is a heterogeneous workspace composed of 15+ independent, top-level systems. **Do not treat it as a single monolithic application.**

### Primary Systems

| Project                    | Stack             | Role                                                       | Authority                  |
| -------------------------- | ----------------- | ---------------------------------------------------------- | -------------------------- |
| `Acropolis/`               | Rust/Julia/Python | Adaptive Expert Platform; hot-reloadable native plugins.   | `ARCHITECTURE.md`          |
| `apex/`                    | Rust/Python/TS    | 5-layer Probabilistic OS with uncertainty & HITL tracking. | `apex/README.md`           |
| `B-A-P/`                   | Python (Poetry)   | Business Analytics Platform; FastAPI + SQLAlchemy 2.0.     | `B-A-P/AGENTS.md`          |
| `BackupIQ/`                | Python            | Enterprise backup with semantic indexing & Neo4j graphs.   | `BackupIQ/README.md`       |
| `Citadel/`                 | Python (FastAPI)  | Modular microservices for Vector, Graph, and Time-Series.  | `Citadel/README.md`        |
| `ClearDesk/`               | React 19 + Vitest | AI-powered Accounts Receivable document processor.         | `ClearDesk/README.md`      |
| `CyberArchitect/`          | Node.js           | Security-focused website replication & archiving suite.    | `CyberArchitect/AGENTS.md` |
| `DocuMancer/`              | Python + Electron | Document conversion and management desktop stack.          | `DocuMancer/README.md`     |
| `Gen-H/`                   | React 19 + Groq   | HVAC growth engine with Composio integration.              | `Gen-H/README.md`          |
| `integration/`             | Python/Docker     | Shared Auth, Event Bus, Saga Gateway, and Proof layer.     | `DEPLOYMENT_STATUS.md`     |
| `intelligent-storage/`     | Python            | RAG + Knowledge Graph file intelligence (ISN).             | `isn-cli.py`               |
| `Money/`                   | Python (CrewAI)   | Houston HVAC AI Dispatch via 5-agent Groq chain.           | `Money/AGENTS.md`          |
| `reGenesis/`               | Node (pnpm)       | Site generation and replication workspace.                 | `reGenesis/README.md`      |
| `soviergn_ai/`             | Rust (WASM)/Bun   | **Nexus**: Browser-native, zero-egress document runtime.   | `soviergn_ai/README.md`    |
| `citadel_ultimate_a_plus/` | Python            | Lead-gen pipeline with explicit state machine logic.       | `lead_queue.py`            |

---

## 🔒 Mandatory Production Rules

- **Rule 1: No Simulation.** No mocks, stubs, or placeholders in production paths. All integrations (Twilio, Groq, etc.) must be real or use established test-mode fallbacks (e.g., `STUB_TWILIO` in `Money`).
- **Rule 2: Project Isolation.** Never modify multiple projects in a single task unless explicitly requested. Each project has its own environment and dependency boundaries.
- **Rule 3: Hostile Audit.** Assume every PR will be reviewed by a skeptical auditor. Capture all rationale, security trade-offs, and performance benchmarks.
- **Rule 4: Verification First.** Use `PROGRESS_TRACKER.md` as the source of truth. You cannot mark a task complete without verifiable proof (logs, health checks, or passed tests).

---

## 🛠️ Preferred Commands

### Navigation & Search

- Quick Inventory: `rg --files <project>`
- Symbol Search: `rg -n "^(class|def|async def|fn|struct|enum|trait) <name>" <project>/`
- Global Search: `rg -n "<pattern>" <project>/`

### Validation Suite

- **B-A-P**: `cd B-A-P && poetry run pytest tests/ -v`
- **Money**: `cd Money && python3 -m pytest tests/ -v`
- **Integration**: `cd integration && pytest tests/ -v`
- **Acropolis**: `cd Acropolis && cargo test`
- **ClearDesk**: `cd ClearDesk && npm test`
- **Sovereign/Nexus**: Check `soviergn_ai/README.md` for `wasm-pack` build and `bun` test commands.

### Dependency Management

- `B-A-P/`: **Poetry ONLY.** Never use pip.
- `Acropolis/`: Cargo Workspace.
- `reGenesis/`: pnpm Workspace.
- `apex/`: Docker Compose + mixed stack.

---

## 🧠 Semantic Context (Serena)

The workspace is instrumented with **Serena** configuration at `/.serena/project.yml`.

- **Primary Support:** TypeScript projects (`ClearDesk/`, `Gen-H/`, `reGenesis/`, `apex/apex-ui/`).
- **Non-TS Support:** For Python/Rust/Julia, use manual symbol search + diagnostics (`cargo test`, `pytest`) as the language server coverage is limited for non-TS.

---

## 📝 Coding Conventions

1. **Database:** SQLite defaults to **WAL mode** for local persistence.
2. **State Machines:** Explicitly defined in code (see `citadel_ultimate_a_plus/lead_queue.py` or `Money/main.py`). Do not infer state from DB constraints alone.
3. **Lazy Loading:** Critical for AI agents (e.g., `Money` project lazy-loads CrewAI via `_ensure_agents()`).
4. **Environment:** Generate secrets with `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`. Use `scripts/bootstrap_env.sh` to scaffold new environment files.

---

## ✅ Testing & Verification Standards

Every completed task **MUST** be accompanied by a Verification Report:

- **Tests**: Command used and output summary (Pass/Fail/Coverage).
- **Security Check**: Verify no secrets leaked, no XSS vectors in templates, and no SQL injection.
- **Proof Artifacts**: Save `curl` responses, test logs, or health check snapshots to the `/integration/proof/` directory when building shared infra.

_Last updated: 2026-03-10_
_Maintainer: Antigravity AI Agent_
