# ReliantAI Platform — Remaining Work Checklist

**Last Updated**: 2026-04-22  
**Platform Status**: 104 bugs fixed, core services production-ready, 20+ services dockerized  
**Outstanding Items**: Categorized by priority

---

## 🔴 CRITICAL — Must Fix Before Production Scale

### 1. Database Migrations
- [x] **Create initial Alembic migrations** for all 3 core databases
  - `migrations/versions/001_create_money_tables.py` — ✅ Created
  - `migrations/versions/002_create_complianceone_tables.py` — ✅ Created
  - `migrations/versions/003_create_finops360_tables.py` — ✅ Created
  - Status: Replaced ad-hoc `init_db()` functions with versioned schema
  - Verification: Run `alembic upgrade head` to apply

### 2. Docker Coverage for Remaining Services
- [x] **Add Dockerfiles for 13 services** (only 5 previously dockerized)
  - [x] Citadel/ — Flask + TimescaleDB service (`Citadel/Dockerfile`)
  - [x] ClearDesk/ — React SPA (`ClearDesk/Dockerfile`, nginx static serve)
  - [x] B-A-P/ — Poetry-based FastAPI (already had Dockerfile, integrated into compose)
  - [x] Gen-H/ — React SPA (`Gen-H/Dockerfile`, nginx static serve)
  - [x] ops-intelligence/ — FastAPI + React (already had Dockerfiles, integrated)
  - [x] apex/apex-agents/ — Python agent framework (already had Dockerfile)
  - [x] apex/apex-ui/ — Next.js 15 (already had Dockerfile)
  - [x] apex/apex-mcp/ — TypeScript MCP server (already had Dockerfile)
  - [x] DocuMancer/ — Electron + Python backend (`DocuMancer/Dockerfile`)
  - [x] Acropolis/ — Rust workspace (already had Dockerfile)
  - [x] BackupIQ/ — Python async (`BackupIQ/Dockerfile`)
  - [x] CyberArchitect/ — Node.js CLI (`CyberArchitect/Dockerfile`)
  - [x] citadel_ultimate_a_plus/ — Python Dash (already had Dockerfile)
  - [x] soviergn_ai/ — Bun + Astro + WASM (`sovieren_ai/Dockerfile`)
  - [x] reGenesis/ — pnpm workspace (`reGenesis/Dockerfile`)

### 3. Docker Compose Integration
- [x] **Add 13 services to docker-compose.yml**
  - Previously only: postgres, money, complianceone, finops360, integration, orchestrator, redis, nginx
  - Now includes: vault, bap, ops-intelligence-backend, ops-intelligence-frontend, apex-agents, apex-ui, apex-mcp, acropolis, citadel-ultimate-a-plus, citadel, cleardesk, gen-h, documancer, backupiq, cyberarchitect, sovieren-ai, regenesis
  - All services declare `networks: - reliantai-network`
  - All services have `stop_grace_period: 30s`
  - All services have `healthcheck` blocks
  - Port conflicts resolved via host remapping (e.g., bap 8108:8000, apex-agents 8109:8001)

### 4. Service Discovery & Health Checks
- [x] **Add `/health` endpoints to non-core services**
  - [x] All 20+ services expose `/health` (or `/api/health` for Citadel)
  - [x] `scripts/health_check.py` updated to check all services
  - [x] Critical vs non-critical classification added
  - [x] `--critical-only` flag added for P1 incident response

---

## 🟠 HIGH — Production Best Practices

### 5. Alerting & Notifications
- [x] **Configure Alertmanager** (`monitoring/alertmanager.yml`)
  - [x] Routing rules: critical → PagerDuty+Slack+Email; warning → Slack+Email; info → Slack
  - [x] Service-specific routing: platform, security, AI teams
  - [x] Inhibition rules: critical suppresses warning/info
  - [x] Environment-variable placeholders for secrets (no hardcoded credentials)

### 6. Security Scanning in CI/CD
- [x] **Add security scanning to `.github/workflows/ci-cd.yml`**
  - [x] OWASP ZAP baseline scan (Job 5)
  - [x] Trivy filesystem + image scanning with SARIF upload
  - [x] gitleaks secrets detection (Job 2, blocking)
  - [x] TruffleHog verified secret scan (Job 2, blocking)
  - [x] bandit `|| true` removed — now blocking on MEDIUM+
  - [x] safety `|| true` removed — now blocking on known vulnerabilities
  - [x] Build matrix expanded to all 20+ services
  - [x] `.gitleaks.toml` created with ReliantAI-specific patterns

### 7. Log Aggregation
- [x] **Deploy Loki + Promtail stack**
  - [x] `docker-compose.monitoring.yml` already includes Loki (port 3100) + Promtail
  - [x] `monitoring/promtail-config.yml` updated with structured JSON log parsing pipeline
  - [x] `monitoring/loki-config.yml` has 7-day retention configured
  - [x] Grafana datasource provisioning includes Loki with correlation_id derived field
  - [x] `shared/logging_config.py` created for Python services (structlog → JSON stdout)
  - [x] Structured logging pattern: `event`, `level`, `service`, `correlation_id`, `timestamp`

### 8. API Versioning
- [x] **Add version prefixes to API routes**
  - [x] Created `shared/api_versioning.py` helper (`include_versioned_router`)
  - [x] ComplianceOne refactored to use `APIRouter` with `/v1` prefix alongside unversioned
  - [x] Pattern documented for remaining services (Money, FinOps360, integration)
  - [x] Version negotiation strategy: backward-compatible dual-mount
  - [x] Deprecation policy documented in `docs/adrs/ADR-004-api-versioning-dual-mount.md` (12-month grace period, `Warning: 299` header)

### 9. Graceful Shutdown
- [x] **Add `stop_grace_period: 30s` to all services in docker-compose.yml**
  - [x] SIGTERM handlers via `shared/graceful_shutdown.py`
    - `GracefulShutdownManager` registers DB pools, Redis clients, async tasks
    - `setup_signal_handlers()` installs SIGTERM/SIGINT handlers
    - `shutdown_all()` executes ordered cleanup: tasks → Redis → DB pools → callbacks → log flush
  - [x] Applied to core Python services:
    - **Money**: lifespan shutdown calls `GracefulShutdownManager.shutdown_all()`; DB pool auto-registered
    - **ComplianceOne**: `@app.on_event("shutdown")` added; DB pool auto-registered
    - **FinOps360**: `@app.on_event("shutdown")` added; DB pool + background budget task auto-registered
    - **Orchestrator**: `stop()` delegates to `GracefulShutdownManager.shutdown_all()`; Redis + 7 background tasks registered
  - [x] Connection draining for in-flight requests (nginx `proxy_next_upstream` handles this)
  - [x] Database connection cleanup on shutdown (psycopg2 `pool.closeall()` via graceful shutdown)

### 10. Load Testing
- [x] **Create load test suite** (locust + asyncio)
  - [x] `tests/load/locustfile.py` — Multi-user HTTP load test
    - MoneyUser (weight 5): dispatch, list, search, metrics
    - ComplianceUser (weight 2): frameworks, controls, violations
    - FinOpsUser (weight 2): dashboard, accounts, budgets, recommendations
    - OrchestratorUser (weight 1): status, dashboard, services, decisions
    - IntegrationUser (weight 1): auth health, event publish
  - [x] `tests/load/sse_load_test.py` — Asyncio SSE stress test (aiohttp)
  - [x] `tests/load/websocket_load_test.py` — Asyncio WebSocket stress test (websockets)
  - [x] Performance baselines documented in `tests/load/README.md`
  - [x] CI/CD integration example provided
  - [x] Auto-scale validation procedure documented

---

## 🟡 MEDIUM — Operational Improvements

### 11. Secrets Management
- [x] **Integrate HashiCorp Vault into docker-compose.yml**
  - [x] Vault container added with health check and persistent volume
  - [x] `VAULT_ADDR` env var added to `.env.example`
  - [x] Vault agent sidecar pattern for runtime secret injection (`shared/vault_client.py` in-process sidecar with background refresh for Docker Compose; Kubernetes Agent Injector migration path documented)
  - [x] Secret rotation procedure documented in `docs/runbooks/vault-secret-management.md`
  - [x] Audit logging for secret access (`shared/vault_client.py` emits structured JSON per access; queryable in Loki)

### 12. API Documentation
- [x] **Auto-generated OpenAPI/Swagger specs**
  - FastAPI services expose `/docs` and `/redoc` automatically
  - [x] Interactive Swagger UI branding (`shared/docs_branding.py` applied to Money, ComplianceOne, FinOps360, Orchestrator, Event Bus)
  - [x] Client SDK generation (`scripts/generate-sdks.sh` with Docker-based OpenAPI Generator; generates Python + TypeScript SDKs; CI job 7 publishes artifacts)

### 13. Database Replication (HA)
- [x] **Configure PostgreSQL primary-replica** (`docker-compose.ha.yml`)
  - [x] Primary-replica with `bitnami/postgresql-repmgr` (synchronous replication `remote_apply`)
  - [x] Hot standby replica for read queries + failover target
  - [x] PgPool-II connection pooler with load balancing and automatic failover (`pgpool:5432` entry point)
  - [x] repmgr automated failover (~30s promotion time)
  - [x] Connection string documented: services use `pgpool:5432` in HA mode (`.env.example` + `docs/runbooks/database-ha.md`)
  - [x] Backup from replica, disaster recovery runbook, monitoring/alerting guidelines documented

### 14. Backup Automation
- [x] **Automate backup verification**
  - [x] `scripts/backup_database.sh` upgraded to multi-DB backup (money, complianceone, finops360, integration, reliantai, bap, apex, citadel)
  - [x] Supports Docker & local PostgreSQL detection
  - [x] Backup integrity checks (gzip + SQL header verification via `--verify`)
  - [x] Single-DB and full-platform restore via `--restore <db> <timestamp>`
  - [x] Retention cleanup (`BACKUP_RETENTION_DAYS`)
  - [x] `scripts/backup-cron` for daily backup (02:00) + verification (03:00) + weekly file archive
  - [x] Restore procedure documented in `docs/runbooks/incident-response.md` in `docs/runbooks/`

### 15. Circuit Breakers at Infrastructure Level
- [x] **Add nginx proxy-level circuit breakers**
  - [x] `nginx/nginx.conf` updated with:
    - `max_fails=3 fail_timeout=30s` on all upstreams (automatic failover)
    - Backup servers (`127.0.0.1:9001-9005`) return structured 503 JSON with `Retry-After: 30`
    - `proxy_next_upstream error timeout invalid_header http_502 http_503 http_504` with 2 retries
    - `proxy_next_upstream_tries 2` for bounded retry
    - `least_conn` load balancing for even distribution
    - `keepalive 32` for persistent upstream connections
  - [x] Application-level: `Money/circuit_breaker.py` already implemented
  - [x] Envoy sidecar documented as future Kubernetes enhancement in `docs/runbooks/service-mesh.md` (Linkerd preferred for auto-mTLS)

---

## 🟢 LOW — Nice to Have

### 16. Blue-Green Deployment
- [x] **Implement zero-downtime deployment** (`scripts/blue-green-deploy.sh`)
  - [x] Traffic switching mechanism (nginx upstream stop/start between blue/green stacks)
  - [x] Database migration compatibility (alembic upgrade head runs on target stack before traffic switch; migrations must be backward-compatible)
  - [x] Rollback capability (`--rollback` flag + automatic rollback on health check or smoke test failure)

### 17. Service Mesh
- [x] **Evaluate Istio/Linkerd** (`docs/runbooks/service-mesh.md`)
  - [x] Documented current Docker Compose capabilities vs Kubernetes needs
  - [x] mTLS migration path (Linkerd auto-mTLS in K8s, Vault+nginx SSL termination in Compose)
  - [x] Traffic management migration (nginx upstream weights → Linkerd TrafficSplit)
  - [x] Retry budgets, circuit breakers, service profiles documented
  - [x] Full Kubernetes migration checklist with phases
  - [x] Docker Compose simulation via `docker-compose.servicemesh.yml` (conceptual/proxy config testing only)

### 18. Advanced Monitoring
- [x] **Add distributed tracing**
  - [x] OpenTelemetry integration (`shared/tracing.py` + `opentelemetry-instrumentation-fastapi` wired into Money, ComplianceOne, FinOps360, Orchestrator, Event Bus)
  - [x] Trace correlation across services (W3C TraceContext propagation via `TraceContextTextMapPropagator`; `inject_trace_context()` for outgoing HTTP headers)
  - [x] Performance bottleneck identification (Jaeger UI on :16686 + Tempo backend on :3200; trace-to-log correlation in Grafana)

### 19. Cost Optimization
- [x] **Add resource quotas/limits**
  - [x] CPU/memory limits added to all services in `docker-compose.yml`
  - [x] Prevents noisy neighbor issues and OOM kills
  - [x] Right-sized based on service profiles (see compose `deploy.resources`)

---

## 🔵 DOCUMENTATION — Keep Updated

### 20. Documentation Maintenance
- [x] **Create incident response runbooks** (`docs/runbooks/incident-response.md`)
  - Severity 1-3 response steps
  - Database recovery procedure
  - Redis recovery procedure
  - Service rollback runbook
  - Security incident response
  - Contact & escalation matrix
- [x] **Update MISSING_ITEMS.md** — File superseded by CHECKLIST.md; CHECKLIST.md is now the authoritative source
- [x] **Add architecture decision records (ADRs)** (`docs/adrs/`)
  - `ADR-001-realdictcursor.md` — Why `RealDictCursor` is mandatory
  - `ADR-002-holts-smoothing.md` — Why Holt's double exponential smoothing for AI predictions
  - `ADR-003-redis-streams-over-kafka.md` — Why Redis Streams for orchestrator internal comms
  - `ADR-004-api-versioning-dual-mount.md` — Why dual-mount (`/` + `/v1/`) for backward-compatible versioning

---

## 📊 Summary Counts

| Priority | Count | Key Items |
|----------|-------|-----------|
| 🔴 CRITICAL | 4 | ✅ Migrations, Docker coverage, Service discovery, Compose integration |
| 🟠 HIGH | 6 | ✅ Alerting, Security scans, Log aggregation, API versioning, Load testing, Graceful shutdown |
| 🟡 MEDIUM | 5 | ✅ Vault in compose, Backup automation, Circuit breakers, Vault sidecar/rotation/audit, API docs branding, DB replication |
| 🟢 LOW | 4 | ✅ Resource limits, Blue-green, Distributed tracing, Client SDK generation, Service mesh (documented) |
| 🔵 DOCS | 1 | ✅ Runbooks created, ADRs documented |
| **TOTAL** | **20** | **✅ 20/20 complete or documented** |

---

## ✅ Verification Commands

```bash
# Check migration status
ls -la migrations/versions/

# Check Docker coverage
docker compose config --services | wc -l  # Should be 26

# Check health endpoints
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8001/health | jq .
curl -s http://localhost:8002/health | jq .
curl -s http://localhost:9000/health | jq .

# Check CI/CD
ls -la .github/workflows/

# Check monitoring stack
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml ps

# Check HA stack
docker compose -f docker-compose.yml -f docker-compose.ha.yml ps
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec postgres-primary repmgr cluster show

# Check all services health
./scripts/health_check.py -v

# Check API versioning
curl -s http://localhost:8001/v1/health | jq .

# Generate SDKs
./scripts/generate-sdks.sh ./sdks
```

---

**Note**: This checklist supersedes `MISSING_ITEMS.md` which is now outdated. Items marked ✅ there (LICENSE, CI/CD, SSL, etc.) are already implemented.
