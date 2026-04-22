# Code Style & Conventions

## Python
- snake_case functions/vars, PascalCase classes, UPPER_SNAKE constants
- Full type hints on all function signatures
- Pydantic models for request/response
- Imports grouped: stdlib → third-party → local
- Error handling: try/except with specific exceptions, HTTPException for API errors
- DB pattern: `with get_db() as conn: cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)`
- Logging: `logger.error(f"context: {e}")`

## Enhancement Tracker Rules
1. Never rewrite/restructure ENHANCEMENT_TRACKER.md
2. Only: [ ]→[x], replace _pending_ with proof, append to Completion Log
3. If implementation fails: keep original, append ❌ FAIL: reason, then ✅ FIX: what worked
