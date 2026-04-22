# AGENTS.md - Architect Mode

This file provides guidance to agents when architecting solutions in this repository.

## Multi-Project Architecture Constraints

### Critical Rule: Project Isolation

- Each project is **completely independent** - no shared dependencies at root
- Cross-project imports are prohibited
- Each project maintains its own:
  - Dependency management (requirements.txt, package.json, Cargo.toml)
  - Build and test configurations
  - Deployment pipelines
  - Database schemas

### Integration Points

The only approved integration mechanism is **MCP (Model Context Protocol)**:

- apex-mcp/ provides tool bus for cross-project operations
- Individual projects expose APIs for external consumption
- Webhooks used for async callbacks (Citadel, Money)

## Project Architecture Patterns

### Acropolis - Polyglot Adaptive Expert Platform
```
Rust Orchestrator → Agent Trait Impl → External Runtimes
       ↓                    ↓                   ↓
   Core Hub        Julia/Python/LLM      Julia Runtime
                    Plugin Agents         Python Scripts
                                          GGUF Models
```
- **Key**: Hub knows only Agent trait, not internal logic
- **Runtimes**: Julia (CausalInference.jl), Python (numpy/Pillow), LLM (llama_cpp)
- **Plugins**: Native .so/.dll via libloading (DQN example)

### Apex - 5-Layer Probabilistic OS
```
Layer 1: Orchestration → L2: UPS Intelligence → L3: Specialist Execution
                              ↓                        ↓
              Uncertainty Decomposition      Research/Creative/Analytics/Sales
              [aleatoric | epistemic]        ↓
L4: Adversarial Quality ← L5: Integration ← Results
    [Hostile Auditor,                     [Context7, Zapier, MCP]
     Debate, Evolver]
```
- **4-Tier Routing**: T1-T4 based on confidence/stakes BEFORE agent logic
- **HITL Trigger**: confidence < 0.65 OR high stakes
- **A2A Bus**: Rust apex-core with required fields (confidence, uncertainty, stakes, domain_novelty)

### Citadel - Pipeline State Machine
```
Scout → Qualify → Build → Approve → Deploy → Email → Replied
                ↓
         Disqualified (terminal)
```
- State transitions in CODE, not DB constraints
- JSON Schema validation at each stage (`schemas/*.json`)
- Webhook idempotency via `webhook_receipts` table
- SQLite WAL for single-node

### Money - CrewAI 5-Agent Chain
```
SMS/WhatsApp → Safety Gate → CrewAI Chain → SQLite → SMS Response
                      ↓ (fallback)
         Local Triage Engine (keyword + temp=0.0)
```
- **Lazy Loading**: `_ensure_agents()` pattern for fast import
- **Zero-AI Fallback**: Keyword + temperature for reliability
- **LangSmith**: Only project using it (not Langfuse)

### ClearDesk - Document Intelligence
```
Upload → Multi-format Parser → Claude Analysis → Structured Output
   ↓                                                      ↓
7 Formats (PDF, Image, Word, Excel, CSV, Email, Text)  EN+ES Summaries
```
- **Judgment Layer**: Claude (not RPA)
- **Dual-language**: EN+ES simultaneously
- **Vercel Edge**: KV required for persistence (limits)

### Intelligent Storage - RAG + Knowledge Graph
```
Files → Indexer → Embeddings + Graph → Hybrid Search API
   ↓                                   ↓
PostgreSQL + pgvector              RRF Ranking
Apache AGE (optional)              Fallback: NetworkX
```
- **Local-first**: Ollama for embeddings
- **Hybrid**: semantic + keyword + metadata
- **Graph**: PageRank/communities (optional AGE backend)

## Technology Matrix

| Project | Web | AI | DB | Obs | Notes |
|---------|-----|----|----|-----|-------|
| Acropolis | - | Polyglot | - | - | Rust + Julia + Python + Zig |
| apex | FastAPI | LangGraph | PostgreSQL | Langfuse | 5-layer probabilistic OS |
| B-A-P | FastAPI | GPT-4o | PostgreSQL | Prometheus | Poetry, Redis cache |
| BackupIQ | - | - | Configurable | Prometheus | Makefile-driven |
| citadel | FastAPI | - | SQLite | - | State machine, JSON Schema |
| ClearDesk | Vercel Edge | Claude | Cloudflare KV | - | Dual-language output |
| Gen-H | Next.js | CrewAI | - | - | vercel.json safety shim |
| ISN | FastAPI | Ollama | PostgreSQL | - | Graph: AGE or NetworkX |
| Money | FastAPI | CrewAI | SQLite | LangSmith | Lazy CrewAI loading |

## Critical Constraints

1. **Acropolis**: Runtime dependencies (Julia, Python, GGUF) must exist in env
2. **Apex**: Agents MUST be stateless - caching layer assumes this
3. **Citadel**: Forward-only migrations (no rollback)
4. **Money**: CrewAI lazy-loaded to avoid slow startup
5. **ClearDesk**: Vercel Edge limits require KV
6. **Gen-H**: vercel.json safety shim - DO NOT REMOVE
7. **ISN**: Graph backend optional, fallback to NetworkX

## New Project Checklist

1. Own dependency management (requirements.txt/package.json/Cargo.toml)
2. Local AGENTS.md with build/test commands
3. `.env.example` file
4. Add to root AGENTS.md project table
5. Document non-obvious patterns
