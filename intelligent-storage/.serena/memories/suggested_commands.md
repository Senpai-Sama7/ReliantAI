# Suggested Commands

## Run
```bash
python3 api_server.py          # Main API server (port 8000)
python3 web_ui.py              # Web UI (port 8080)
python3 indexer.py             # Batch indexer
./start.sh                     # Start all
```

## Test
```bash
python3 -m py_compile api_server.py indexer.py web_ui.py config.py  # Syntax check
curl http://localhost:8000/api/health                                # Health check
curl -X POST http://localhost:8000/api/search/advanced -H "Content-Type: application/json" -d '{"query": "test", "limit": 5}'
```

## Database
```bash
PGPASSWORD=storage_local_2026 psql -h localhost -p 5433 -U storage_admin -d intelligent_storage
# CRITICAL: Always use -h localhost (PGHOST env var points to Neon cloud)
```

## System
```bash
git status / git diff / git log
ls, cd, grep, find — standard Linux
```
