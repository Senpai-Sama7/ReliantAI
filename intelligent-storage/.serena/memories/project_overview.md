# Intelligent Storage Nexus - Project Overview

## Purpose
AI-powered file intelligence system with semantic search, knowledge graphs, and Tree of Thoughts reasoning. Indexes 250K+ files with 768-dim embeddings via Ollama/nomic-embed-text, stores in PostgreSQL 17 + pgvector + Apache AGE.

## Tech Stack
- Python 3, FastAPI, psycopg2 (sync), asyncpg (installed, migration pending)
- PostgreSQL 17 on port 5433, pgvector, Apache AGE v1.5.0
- Ollama (localhost:11434) for embeddings (nomic-embed-text) and LLM (qwen3-8b)
- Frontend: HTML/Tailwind CSS/D3.js (index.html)

## Key Files
- `api_server.py` — Main FastAPI server (2182 lines, 67 functions, 21 sync DB blocks)
- `indexer.py` — Batch file scanner/embedder (435 lines)
- `web_ui.py` — Standalone FastAPI UI (322 lines)
- `config.py` — Centralized env config (17 ISN_ prefixed constants)
- `schema.sql` — Full DB schema
- `start.sh` — Startup script

## Database
- Host: localhost, Port: 5433, User: storage_admin, Pass: storage_local_2026, DB: intelligent_storage
- CRITICAL: `PGHOST` env var points to Neon cloud — always use explicit `-h localhost`
- Table ownership: `postgres` owns tables, `storage_admin` cannot create/drop indexes
- 352,660 embeddings in file_embeddings table

## Enhancement Tracking
- `ENHANCEMENT_TRACKER.md` — THE checklist. NEVER rewrite/restructure. Only mark [x], replace _pending_, append to log.
- `AGENTS.md` — Agent guidelines and tracker rules
