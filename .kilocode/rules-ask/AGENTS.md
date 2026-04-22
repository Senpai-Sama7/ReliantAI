# AGENTS.md - Ask Mode

## Documentation Hierarchy

1. **Root AGENTS.md** - Multi-project overview (this workspace)
2. **Subproject AGENTS.md** - Authoritative for that project
3. **Subproject README.md** - User-facing docs
4. **ARCHITECTURE.md / HANDOFF.md** - Design decisions

## Documentation by Project

| Project | Primary | Architecture | AI Assistant Rules | Notes |
|---------|---------|--------------|-------------------|-------|
| `Acropolis/` | README.md | ARCHITECTURE.md | CLAUDE.md (generic) | Polyglot runtime requirements |
| `apex/` | README.md | ARCHITECTURE.md | - | APEX_README.md duplicates some info |
| `B-A-P/` | README.md | - | - | Poetry-based setup |
| `BackupIQ/` | README.md | - | - | Makefile-driven |
| `citadel_ultimate_a_plus/` | AGENTS.md | EVALUATION.md | ✓ Comprehensive | Pipeline + state machine docs |
| `ClearDesk/` | README.md | - | - | Component docs inline |
| `Gen-H/` | AGENTS.md | info.md | ✓ 12-section guide | Troubleshooting included |
| `intelligent-storage/` | README.md | - | - | API recipes included |
| `Money/` | AGENTS.md | - | ✓ Extensive | `docs/` folder has patterns |

## Counterintuitive Structures

- **Apex**: 5-layer with uncertainty decomposition (aleatoric vs epistemic)
- **Citadel**: State machine enforced in code, NOT DB constraints
- **Money**: CrewAI lazy-loaded via `_ensure_agents()` despite being core feature
- **Gen-H**: `vercel.json` is safety shim - DO NOT REMOVE
- **Acropolis**: CLAUDE.md is generic (not project-specific), ARCHITECTURE.md has actual design

## Cross-Cutting Tech

| Tech | Used In |
|------|---------|
| Langfuse | Python projects (except Money) |
| LangSmith | Money only |
| SQLite WAL | All local Python projects |
| Vercel | ClearDesk, Gen-H |
| Poetry | B-A-P only (others use pip) |
