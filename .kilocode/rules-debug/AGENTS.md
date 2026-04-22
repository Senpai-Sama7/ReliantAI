# AGENTS.md - Debug Mode

## Silent Failure Patterns

1. **Citadel webhooks** fail silently on HMAC invalid - check `webhook_receipts` table, not logs
2. **Money CrewAI** auto-fallback to local triage on Groq failure - look for "fallback" in logs
3. **Gen-H Vercel Blob** silent fallback to JSON in dev; hard fails in prod if misconfigured
4. **Apex circuit breakers** - check `/metrics` endpoint, not service logs
5. **Acropolis plugins** fail silently if .so/.dll not in plugins/ directory

## Log & Data Locations

| Project | Logs | Database | Debug Command |
|---------|------|----------|---------------|
| citadel_ultimate_a_plus | `workspace/logs/` | `workspace/state/citadel.db` | `sqlite3 citadel.db "SELECT * FROM lead_events ORDER BY created_at DESC LIMIT 5;"` |
| Money | `hvac_dispatch.log` | `dispatch.db` | `python3 hvac_dispatch_crew.py --message "test" --temp 85` |
| B-A-P | stdout (structlog) | PostgreSQL | `poetry run pytest tests/ -v --tb=short` |
| BackupIQ | `logs/` | Configurable | `make test-unit` (95% cov gate) |
| Apex | `docker compose logs -f <service>` | PostgreSQL | `docker compose ps` for health |
| intelligent-storage | WebSocket streams | PostgreSQL | Check WebSocket connection first |

## Apex Service Debugging

```bash
cd apex/infra
docker compose logs -f apex-agents    # Python agent logs
docker compose logs -f apex-ui        # Next.js UI logs
docker compose logs -f apex-mcp       # MCP server logs
docker compose logs -f postgres       # Database logs
```

Health endpoints:
- apex-core: `localhost:8000/health`
- apex-agents: `localhost:8001/health`
- Langfuse: `localhost:3000`

## Quick Environment Validation

```bash
# Python projects
python3 -c "from config import *; print('Config OK')"  # Money/Citadel pattern

# TypeScript
npx tsc --noEmit  # Type check without emit
```
