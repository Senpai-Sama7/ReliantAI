# CLAUDE.md — ReliantAI Claude Context Scaffold

This file provides root context for Claude agents in the ReliantAI workspace. Use it to understand the broad system goals and then dive into project-specific `AGENTS.md` or `README.md` files.

## 🏗️ Workspace Shape

ReliantAI is a heterogeneous workspace with 15+ independent projects. treat each top-level directory as its own product.

| System             | Role                        | Authority File                          |
| :----------------- | :-------------------------- | :-------------------------------------- |
| **Acropolis**      | Adaptive Expert Module      | `Acropolis/ARCHITECTURE.md`             |
| **apex**           | Probabilistic OS            | `apex/README.md`                        |
| **B-A-P**          | Business Analytics Platform | `B-A-P/AGENTS.md`                       |
| **BackupIQ**       | Semantic Backup Engine      | `BackupIQ/README.md`                    |
| **Citadel**        | Vector/Graph Microservices  | `Citadel/README.md`                     |
| **ClearDesk**      | AR Document Processing      | `ClearDesk/README.md`                   |
| **CyberArchitect** | Security-Driven Archiver    | `CyberArchitect/README.md`              |
| **DocuMancer**     | Desktop Document Stack      | `DocuMancer/README.md`                  |
| **Gen-H**          | HVAC Growth Tools           | `Gen-H/README.md`                       |
| **integration**    | Shared Auth & Event Bus     | `DEPLOYMENT_STATUS.md`                  |
| **ISN**            | Intelligent Storage         | `intelligent-storage/README.md`         |
| **Money**          | AI HVAC Dispatcher          | `Money/AGENTS.md`                       |
| **reGenesis**      | Site Replication/Generation | `reGenesis/README.md`                   |
| **Nexus**          | Zero-Egress browser WASM    | `soviergn_ai/README.md`                 |
| **Gold Lead**      | Lead-Gen Pipeline           | `citadel_ultimate_a_plus/lead_queue.py` |

---

## 🔒 Non-Negotiable Rules

1. **Rule 1: No Simulation.** Mocks are forbidden in production logic. Use real integrations or established test-mode fallbacks.
2. **Rule 2: Project Isolation.** Do not modify multiple projects in a single task unless explicitly ordered.
3. **Rule 3: Hostile Audit.** Assume your code will be audited for security (SQLi, XSS, tokens) and edge-case handling.
4. **Rule 4: Verification First.** Use `PROGRESS_TRACKER.md` to verify current state and mark completions.

---

## 🛠️ Preferred Commands

- **Inventory**: `rg --files <project>`
- **Validation**:
  - B-A-P: `cd B-A-P && poetry run pytest`
  - Money: `cd Money && python3 -m pytest`
  - Integration: `cd integration && pytest`
  - Acropolis: `cd Acropolis && cargo test`
  - reGenesis: `cd reGenesis && pnpm test`
- **Operation**:
  - `curl http://localhost:8080/health` (Auth)
  - `curl http://localhost:8081/health` (Event Bus)

---

## 🧠 Semantic Analysis (Serena)

- **TS Coverage**: High (ClearDesk, Gen-H, reGenesis, apex-ui).
- **Non-TS**: Use `rg` for symbol definitions: `rg -n "^(class|def|async def|fn|struct|enum|trait) <name>" <project>/`.

---

## 📝 General Conventions

- **Database**: SQLite WAL mode is mandatory for local persistence.
- **Environment**: Scaffold with `scripts/bootstrap_env.sh`.
- **JWT**: Secrets must be 32+ characters and non-default.
- **Sanitization**: All AI-generated outputs must be sanitized before being sent to SMS/Email.

_Last Updated: 2026-03-10_
_Maintainer: Antigravity AI Agent_
