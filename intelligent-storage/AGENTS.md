# Intelligent Storage Nexus - Agent Guidelines

AI-powered file intelligence system with semantic search, knowledge graphs, and Tree of Thoughts reasoning.

## Hostile Audit Persistence

- Append every hostile-audit checkpoint and verification result to the root `PROGRESS_TRACKER.md`.
- Do not mark control-plane or cache-path fixes complete without a real command result, test run, health check, websocket proof, or artifact saved under `proof/hostile-audit/<timestamp>/`.
- Reproduce before patching. If the original exploit path fails, record the failed method and the replacement verification path.
- Keep control endpoints fail-closed behind explicit auth and do not restore unsafe serialization paths such as unaudited `pickle` loads.
- If a scanner or service cannot run, record the exact blocker and fallback review path instead of implying success.

---

## Build / Run / Test Commands

### Starting the System
```bash
# Start all services
./start.sh

# Start API server only
python3 api_server.py

# Start web UI only (port 8080)
python3 web_ui.py

# Run indexer pipeline
python3 indexer.py
```

### Testing
```bash
# API health check
curl http://localhost:8000/api/health

# Test semantic search
curl -X POST http://localhost:8000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{"query": "React authentication", "limit": 5}'

# Test knowledge graph
curl -X POST http://localhost:8000/api/graph/query \
  -H "Content-Type: application/json" \
  -d '{"center_file_id": 1000, "depth": 2}'

# Run Python syntax check
python3 -m py_compile api_server.py indexer.py web_ui.py
```

### Database Operations
```bash
# Connect to database
PGPASSWORD=storage_local_2026 psql -h localhost -p 5433 \
  -U storage_admin -d intelligent_storage

# Check file count
PGPASSWORD=storage_local_2026 psql -h localhost -p 5433 \
  -U storage_admin -d intelligent_storage \
  -c "SELECT COUNT(*) FROM files;"

# View logs
tail -f api_server.log
tail -f web_ui.log
```

---

## Code Style Guidelines

### Python Style

**Imports (grouped and sorted):**
```python
# 1. Standard library
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

# 2. Third-party packages
import numpy as np
import psycopg2
import psycopg2.extras
import requests
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel, Field
from psycopg2.extras import execute_values, Json

# 3. Local imports (none in this project)
```

**Naming Conventions:**
- Functions/variables: `snake_case` (e.g., `get_embedding`, `file_id`)
- Classes: `PascalCase` (e.g., `ConnectionManager`, `FileSearchRequest`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DB_DSN`, `EMBED_DIM`, `BATCH_SIZE`)
- Private helpers: `_leading_underscore` (e.g., `_process_embeddings`)

**Type Hints:**
- Use full type annotations for all function signatures
- Use `Optional[X]` for nullable types
- Use `List[X]`, `Dict[K, V]`, `Tuple[X, Y]` from `typing`
- Pydantic models for request/response validation

**Function Structure:**
```python
async def advanced_search(request: FileSearchRequest) -> Dict[str, Any]:
    """
    Advanced hybrid search combining semantic, keyword, and metadata search.
    
    Args:
        request: FileSearchRequest with query and weights
        
    Returns:
        Dict containing results, total count, and metadata
    """
    with get_db() as conn:
        # Implementation
        pass
```

**Error Handling:**
- Use try/except with specific exceptions
- Log errors with context: `logger.error(f"Embedding error: {e}")`
- Raise `HTTPException` for API errors with appropriate status codes
- Rollback database transactions on error

**Database Patterns:**
```python
@contextmanager
def get_db():
    """Database connection context manager."""
    conn = psycopg2.connect(DB_DSN)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with get_db() as conn:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT ...")
```

### Frontend (HTML/CSS/JavaScript)

**Tailwind CSS:** Primary styling via CDN
```html
<script src="https://cdn.tailwindcss.com"></script>
```

**Font Stack:**
- Primary: `Inter` (sans-serif)
- Monospace: `JetBrains Mono` for code

**Custom CSS Classes:**
- `.glass` - Glassmorphism panels
- `.glass-dark` - Dark glass panels
- `.fade-in` - Fade in animation
- `.loading` - Pulse animation
- `.font-mono` - JetBrains Mono font

**JavaScript Patterns:**
```javascript
// Async/await for API calls
async function searchFiles(page = 1) {
    const res = await fetch(`/api/files?page=${page}`);
    const data = await res.json();
    // Handle data
}

// Debounce for search inputs
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => searchFiles(1), 300);
}
```

### SQL/PostgreSQL Style

- Use lowercase for SQL keywords in embedded queries
- Use CTEs for complex queries
- Add comments for major sections
- Index all foreign keys and search columns

---

## Project Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  index.html │────▶│ api_server.py│────▶│  PostgreSQL+    │
│  (Frontend) │◄────│  (FastAPI)   │◄────│  pgvector (5433)│
└─────────────┘     └──────────────┘     └─────────────────┘
                           │                       │
                           ▼                       ▼
                   ┌──────────────┐        ┌──────────────┐
                   │  indexer.py  │        │ Ollama (11434)│
                   │  (Pipeline)  │        │  nomic-embed  │
                   └──────────────┘        └──────────────┘
```

---

## Key Configuration

```python
DB_DSN = "host=localhost port=5433 dbname=intelligent_storage user=storage_admin password=storage_local_2026"
OLLAMA_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768
```

---

## Testing Checklist

Before committing changes:
- [ ] `python3 -m py_compile api_server.py indexer.py web_ui.py` passes
- [ ] API endpoints respond correctly via curl tests
- [ ] Database queries execute without errors
- [ ] Frontend loads without console errors
- [ ] No hardcoded credentials added
- [ ] Logs use appropriate levels (info/error/debug)

---

## ⚠️ Enhancement Tracker Rules (ENHANCEMENT_TRACKER.md)

The file `ENHANCEMENT_TRACKER.md` tracks all planned improvements with a checklist and validation proof. When working on enhancements, agents **must** follow these rules:

1. **Never rewrite, remove, or restructure** any part of the tracker checklist.
2. On task completion, the **only** permitted changes are:
   - Change `[ ]` → `[x]` on the completed task line.
   - Replace `_pending_` on the Proof line with actual validation evidence (commands run, output received, timestamps).
   - Append a new row to the **Completion Log** table at the bottom.
3. **Do not** alter Validation lines, reorder tasks, add/remove sections, or touch any uncompleted task.
4. If a task fails validation, leave it as `[ ]` and append failure notes under its Proof line prefixed with `❌ FAIL:`.
5. **If the planned Implementation method fails**, do NOT delete it. Instead:
   - Keep the original Implementation text intact.
   - Append `❌ FAIL:` with the error/reason it didn't work.
   - Then append `✅ FIX:` with what was done instead and why it worked.
   - The Proof line must show the final passing result with timestamp, commands, and output.
6. These rules are permanent and apply to all agents (human or AI) editing that file.

---

*Last Updated: 2026-02-11*
