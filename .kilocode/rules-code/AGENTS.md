# AGENTS.md - Code Mode

## Project-Specific Commands (Non-Obvious Only)

```bash
# B-A-P: Poetry-based (NOT pip)
cd B-A-P && poetry install --with dev
poetry run pytest tests/ -v
poetry run black src/ && poetry run ruff check src/

# BackupIQ: Makefile-driven with coverage gate
cd BackupIQ && make dev-install  # Installs pre-commit hooks
make test-unit  # 95% coverage enforced via --cov-fail-under=95

# Citadel: Makefile with specific targets
cd citadel_ultimate_a_plus && make test  # pytest
make lint  # py_compile only, no black/ruff

# Money: Direct pytest (91 tests)
cd Money && python3 -m pytest tests/ -v

# Acropolis: Rust workspace with polyglot requirements
cd Acropolis && cargo build --release
# Requires: Julia runtime, Python+numpy/Pillow, GGUF models

# Apex: Docker Compose only
cd apex/infra && docker compose up --build -d
```

## Critical Code Patterns

### Python Projects
- **Money**: Always `import config` first - validates env vars on import
- **Money**: CrewAI lazy-loaded via `_ensure_agents()` pattern (fast module import)
- **Citadel**: `lead_queue.py` owns all table definitions
- **All SQLite**: Use `PRAGMA journal_mode=WAL` for concurrent writes

### TypeScript Projects
- **Gen-H**: Vercel Blob prod / JSON file dev (silent fallback)
- **Gen-H**: `vercel.json` is safety shim - DO NOT REMOVE
- **All TS**: ESLint uses shared pattern with reactHooks flat config

### Apex A2A Messages
Required fields: `confidence`, `uncertainty` (aleatoric/epistemic), `stakes`, `domain_novelty`
HITL pause triggered at: confidence < 0.65 OR high stakes
