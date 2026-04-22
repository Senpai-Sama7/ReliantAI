ReliantAI Master Bug Report — CHECKLIST
SEVERITY 1 — DEPLOYMENT BLOCKERS (System Won't Start)
- [x] 1. `docker-compose.yml:88` — References ./integration/Dockerfile — file does not exist. **FIXED: Created integration/Dockerfile**
- [x] 2. `docker-compose.yml:16` — Mounts ./init-scripts:/docker-entrypoint-initdb.d — directory does not exist. **FIXED: Created init-scripts/ directory**
- [x] 3. `reGenesis/` — Entire directory is empty. No package.json, no pnpm-workspace.yaml, no source. Design system is gone. **FIXED: Directory contains complete design system monorepo with package.json, packages/, apps/, and all config files**
- [x] 4. `apex/apex-agents/api/main.py:73` — from agents.layer1.workflow import run_layer1 — agents/layer1/ directory does not exist. **FIXED: Created agents/layer1/workflow.py**
- [x] 5. `apex/apex-agents/api/main.py:70` — from skill_tools import handle_tool_call, TOOL_LIST — skill_tools module does not exist. **FIXED: apex-tools/skill_tools.py exists, path fixed**
- [x] 6. `integration/metacognitive_layer/optimizer.py:121` — super().____(OptimizationDomain.CACHE) — four underscores instead of __init__. TypeError on class instantiation. Same bug at line 183. **FIXED: Changed to super().__init__()**
SEVERITY 2 — CRITICAL SECURITY VULNERABILITIES
- [x] 7. `B-A-P/src/api/auth_integration.py:15` — hardcoded /home/donovan/ path. **FIXED: Changed to relative path resolution**
- [x] 8. `BackupIQ/auth_integration.py:19,29` — Same /home/donovan/ hardcoded path. **FIXED: Changed to relative path resolution**
- [x] 9. `citadel_ultimate_a_plus/auth_integration.py:20,30` — Same /home/donovan/ hardcoded path. **FIXED: Changed to relative path resolution**
- [x] 10. `integration/auth/auth_server.py:35 vs jwt_validator.py:23` — AUTH_SECRET_KEY vs JWT_SECRET mismatch. **FIXED: jwt_validator.py now reads AUTH_SECRET_KEY**
- [x] 11. `Money/main.py:614` — cancelled customers bypass billing enforcement. **FIXED: Re-raise HTTPException for 401/403/429 errors**
- [x] 12. `B-A-P/src/api/middleware/auth.py:46` — fail-open auth when JWT unavailable. **FIXED: Changed to fail-closed (returns 503)**
- [x] 13. `Money/database.py:25` — Default DB URL contains hardcoded password change-in-production. **FIXED: Removed default, require DATABASE_URL env var**
- [x] 14. `.env.production` — API keys are placeholder strings with no enforcement. **FIXED: Added validate_production_config() function in shared/security_middleware.py and called in Money/main.py startup**
- [x] 15. `Money/billing.py:260` — Stripe webhook returns HTTP 200 when stripe_webhook_secret not configured. **FIXED: Return 500 when secret not configured**
- [x] 16. `integration/shared/jwt_validator.py:85` — TLS verification not enforced for remote auth service URLs. **FIXED: Enable TLS verification by default with SKIP_TLS_VERIFY env var for localhost**
SEVERITY 3 — CRITICAL LOGIC/RUNTIME CRASHES
- [x] 17. `Money/retry_queue.py:224` — datetime.replace() crashes for delays >30s. **FIXED: Use datetime + timedelta()**
- [x] 18. `Money/retry_queue.py:13` — logger not exported from database.py. **FIXED: Added local logger import**
- [x] 19. `Money/hvac_dispatch_crew.py:173` — dispatch_id collision on concurrent requests. **FIXED: Added UUID suffix**
- [x] 20. `ComplianceOne/main.py:209` — dict(row) crashes on psycopg2 tuples. **FIXED: Added cursor_factory=RealDictCursor**
- [x] 21. `FinOps360/main.py:339` — dict(cur.fetchone()) crashes on None. **FIXED: Added cursor_factory=RealDictCursor**
- [x] 22. `ClearDesk/src/components/dashboard/Dashboard.tsx:159` — side effects inside useState. **FIXED: Moved to useEffect**
- [x] 23. `apex/apex-agents/api/main.py:220` — run_layer2 signature mismatch. **FIXED: Created wrapper in layer2/__init__.py**
- [x] 24. `apex/apex-agents/agents/layer3/cross_system_dispatch.py` — cross_system_dispatch function missing. **FIXED: Created wrapper function in layer3/__init__.py**
- [ ] 25. `integration/saga/saga_orchestrator.py:143` — Pydantic v1 vs v2 API mismatch. **PENDING: Upgrade to Pydantic v2 consistently**
- [ ] 26. `integration/nexus-runtime/memory_redis.py` — _cleanup_expired() sync/async race. **PENDING: Add async lock**
- [x] 27. `Money/circuit_breaker.py:112` — isinstance(exception, self.excluded) with empty tuple. **FIXED: Added check for empty excluded**
SEVERITY 4 — HIGH: Race Conditions & Data Corruption
- [x] 28. `Money/main.py:878,928` — SSE clients added without lock. **FIXED: Code already has proper locks around all SSE client operations**
- [x] 29. `Money/hvac_dispatch_crew.py:278` — Global agents reassigned without locking. **FIXED: Added _agent_init_lock with double-check**
- [ ] 30. `integration/auth/rate_limiter.py:30` — defaultdict(asyncio.Lock) race. **PENDING: Use proper lock factory**
- [ ] 31. `integration/saga/saga_orchestrator.py:164` — Idempotency key uses new UUID each call. **PENDING: Use deterministic key**
- [ ] 32. `soviergn_ai/wasm-bridge.ts:419` — Framebuffer race condition. **PENDING: Add synchronization**
- [ ] 33. `soviergn_ai/wasm-bridge.ts:310` — checkGrowth() race condition. **PENDING: Add synchronization**
- [ ] 34. `B-A-P/src/tasks/pipeline_tasks.py:15` — Celery async exceptions swallowed. **PENDING: Add proper exception handling**
- [ ] 35. `integration/saga/saga_orchestrator.py:247` — Compensation loop IndexError. **PENDING: Add bounds check**
SEVERITY 5 — HIGH: Auth, Middleware & API Contract Bugs
- [ ] 36. `B-A-P/src/config/settings.py:49` — SECRET_KEY validator accepts wrong default. **PENDING: Fix validation regex**
- [ ] 37. `B-A-P/src/config/settings.py:125` — ALLOWED_ORIGINS defaults to [] breaking frontend. **PENDING: Add sensible default**
- [x] 38. `apex/apex-ui/src/app/api/proxy/[...path]/route.ts:37` — Proxy doesn't forward Authorization header. **FIXED: Added header forwarding**
- [x] 39. `Money/billing.py:147` — stripe.api_key AttributeError if stripe None. **FIXED: Added null check for stripe module**
- [x] 40. `Money/billing.py:297` — int(metadata.get()) crashes on non-numeric. **FIXED: Added try/except ValueError and TypeError**
- [x] 41. `orchestrator/main.py:727` — Bare except: catches KeyboardInterrupt. **FIXED: Replaced with (ConnectionError, RuntimeError, Exception)**
- [ ] 42. `integration/shared/event_types.py:54` — max_length ignored on Dict fields. **PENDING: Implement custom validation**
- [x] 43. `Money/main.py:608` — Rate limiting runs before auth. **FIXED: Moved rate limiting after authentication**
SEVERITY 6 — HIGH: Configuration & Infrastructure
- [x] 44. `orchestrator/Dockerfile:25` — --reload in production. **FIXED: Removed --reload flag**
- [x] 45. `Money/Dockerfile:33` — Frontend built but not served. **FIXED: Added static file mounting from frontend/dist to /app/static**
- [x] 46. `integration/saga/Dockerfile:11` — Healthcheck no status code check. **FIXED: Added status code check (exit 0 if 200 else 1)**
- [x] 47. `docker-compose.yml:121` — Orchestrator missing Redis in depends_on. **FIXED: Added redis to depends_on list**
- [x] 48. `nginx/Dockerfile:10` — Incomplete COPY command. **FIXED: Removed shell operators (||, 2>/dev/null) from COPY commands**
- [x] 49. `vault/vault-config.hcl:11` — Vault TLS certs not copied. **FIXED: Added COPY commands to vault/Dockerfile for SSL certs**
- [x] 50. `integration/docker-compose.yml:81` — Wrong observability path. **FIXED: Changed path from ./observability to ../../monitoring**
- [x] 51. `monitoring/prometheus.yml:85` — Port 8080 conflict. **FIXED: Changed cAdvisor port from 8080 to 8081**
- [x] 52. `ops-intelligence/docker-compose.yml:35` — Port 5174 vs 5173 mismatch. **FIXED: Changed CORS_ORIGINS from 5173 to 5174**
- [x] 53. `integration/docker-compose.yml:255` — Zookeeper volumes without service. **FIXED: Removed zookeeper-data and zookeeper-logs volumes**
SEVERITY 7 — MEDIUM: Monitoring Dead Alerts
- [ ] 54. `monitoring/alert-rules.yml:76` — container_restarts_total metric not exposed. **PENDING: Add cAdvisor or remove alert**
- [ ] 55. `monitoring/alert-rules.yml:96` — backup_last_success_timestamp undefined. **PENDING: Add exporter or remove alert**
- [ ] 56. `monitoring/alert-rules.yml:86` — ssl_certificate_expiry_seconds undefined. **PENDING: Add SSL exporter or remove alert**
- [x] 57. `monitoring/grafana/datasources/datasources.yml:23` — Triple $$$ in URL template. **FIXED: Changed $$$ to $ in URL template**
- [x] 58. `monitoring/loki-config.yml:24` — boltdb-shipper deprecated. **FIXED: Changed store from boltdb-shipper to tsdb**
SEVERITY 8 — MEDIUM: Logic & Data Errors
- [x] 59. `integration/metacognitive_layer/engine.py:199` — Hardcoded PostgreSQL URL. **FIXED: Added os.getenv() for METACOGNITIVE_DB_URL with fallback**
- [x] 60. `integration/metacognitive_layer/engine.py:566` — Truncated UUID collision risk. **FIXED: Removed [:8] truncation, using full UUID**
- [x] 61. `shared/security_middleware.py:114` — Unbounded dict growth. **FIXED: Added LRU-style eviction to prevent unbounded growth**
- [x] 62. `B-A-P/src/models/data_models.py:23` — Mutable default dict. **FIXED: Changed to lambda: {}**
- [x] 63. `B-A-P/src/api/routes/data.py:33` — File written before DB commit. **FIXED: Reversed order - commit to DB first, then write file**
- [x] 64. `FinOps360/main.py:560` — Background task exceptions swallowed. **FIXED: Added proper logging with exc_info and retry delay**
- [x] 65. `ops-intelligence/backend/routers/performance.py:46` — abs() hides improvements. **FIXED: Removed abs() to distinguish improvements from degradations**
- [x] 66. `ops-intelligence/backend/routers/revenue.py:123` — Truncated UUID5 collision. **FIXED: Removed [:16] truncation, using full UUID5**
- [x] 67. `migrations/env.py:39` — Alembic autogenerate disabled. **FIXED: Set target_metadata = Base.metadata**
- [ ] 68. `ops-intelligence/frontend/src/api/client.ts` — No axios error interceptors. **PENDING: Add interceptors**
- [ ] 69. `ops-intelligence/frontend/src/components/Layout.tsx:40` — Bare axios without baseURL. **PENDING: Use configured api instance**
- [x] 70. `integration/shared/event_types.py:27` — Wrong event channel for audit. **FIXED: Changed event type from audit.log.recorded to audit.log**
SEVERITY 9 — MEDIUM: Missing Error Handling
- [x] 71. `ClearDesk/src/contexts/DocumentContext.tsx:139` — No .catch() on promise chain. **FIXED: Added .catch() with error logging**
- [x] 72. `Gen-H/src/services/api.ts:119` — Doesn't check response.ok. **FIXED: Added response.ok check with error throw**
- [x] 73. `orchestrator/main.py:997` — websocket.receive_json() no try/except. **FIXED: Added try/except for JSON parsing errors**
- [x] 74. `integration/event-bus/event_bus.py:221` — json.loads() no try/except. **FIXED: Added try/except for JSONDecodeError with specific error message**
- [x] 75. `Money/hvac_dispatch_crew.py:46` — Twilio retry exception crashes crew. **FIXED: Added exception handling with fallback SID**
- [ ] 76. `shared/graceful_shutdown.py:54` — sys.exit() before task runs. **PENDING: Await shutdown task**
- [ ] 77. `DocuMancer/backend/server.py:185` — Exception handler returns early. **PENDING: Continue processing remaining files**
- [ ] 78. `integration/auth/auth_server.py:321` — redis_client could be None. **PENDING: Add null check**
- [ ] 79. `BackupIQ/src/core/config_manager.py:151` — Returns literal placeholder string. **PENDING: Raise error instead**
SEVERITY 10 — MEDIUM: Deprecated & Inconsistent API Usage
- [ ] 80. `integration/saga/saga_orchestrator.py:212` — datetime.utcnow() deprecated. **PENDING: Use datetime.now(timezone.utc)**
- [ ] 81. `B-A-P/src/models/analytics_models.py:87` — datetime.utcnow() deprecated. **PENDING: Use datetime.now(timezone.utc)**
- [ ] 82. `integration/auth/seed_auth.py:54` — Timezone-naive vs aware mismatch. **PENDING: Use datetime.now(UTC) consistently**
- [ ] 83. `integration/event-bus/event_bus.py:161` — Pydantic v1/v2 API mix. **PENDING: Standardize on Pydantic v2**
- [ ] 84. `CyberArchitect/ultimate-website-replicator.js:546` — Transform not imported. **PENDING: Add import from stream**
- [ ] 85. `DocuMancer/backend/server.py:187` — Inefficient json.loads(item.json()). **PENDING: Use item.model_dump()**
SEVERITY 11 — LOW: Config & Best Practice Issues
- [ ] 86. `docker-compose.yml:9 vs :18` — POSTGRES_USER vs hardcoded postgres healthcheck. **PENDING: Use env var in healthcheck**
- [ ] 87. `integration/auth/Dockerfile:19` — Entrypoint embedded with backtick issues. **PENDING: Fix syntax**
- [ ] 88. `Acropolis/adaptive_expert_platform/src/middleware.rs:28` — NonZeroU32::new().unwrap() panics. **PENDING: Add validation**
- [ ] 89. `Acropolis/adaptive_expert_platform/src/mesh.rs:439` — .partial_cmp().unwrap() panics on NaN. **PENDING: Handle NaN**
- [ ] 90. `Money/main.py` — Inconsistent async/sync auth handling. **PENDING: Make _authorize_request async**
- [ ] 91. `FinOps360/main.py:419` — Hardcoded ORDER BY in dynamic SQL. **PENDING: Parameterize safely**
- [ ] 92. `apex/infra/docker-compose.yml:19` — Weak default password changeme. **PENDING: Remove default**
- [ ] 93. `BackupIQ/deployment/docker/docker-compose.yml:66` — Neo4j password hardcoded. **PENDING: Use env var**
- [ ] 94. `monitoring/prometheus.yml` — localhost scrape targets. **PENDING: Use service names**
- [ ] 95. `scripts/deploy.sh:80` — Uses lsof not available on Alpine. **PENDING: Use netstat or ss**
- [ ] 96. `.env.example` — Missing POSTGRES_USER, CORS_ORIGINS, VITE_* vars. **PENDING: Add all required vars**
- [ ] 97. `integration/metacognitive_layer/api.py:204` — generate_latest() returns bytes. **PENDING: Decode to str**
- [ ] 98. `apex/apex-agents/api/auth_integration.py:25` — localhost doesn't work in Docker. **PENDING: Use service name**
- [ ] 99. `ops-intelligence/backend/database.py:20` — SQLite check_same_thread=False. **PENDING: Use PostgreSQL**
- [ ] 100. `tests/test_integration_suite.py:386` — asyncio.sleep(65) blocks tests. **PENDING: Use pytest-asyncio**
- [ ] 101. `tests/test_integration_suite.py:280` — assert r.status != 500 allows 404. **PENDING: Check for 200 OK**
- [ ] 102. `ClearDesk/src/components/ChatPanel.tsx:55` — Sort with undefined comparison. **PENDING: Add fallback value**
- [ ] 103. `ClearDesk/src/components/upload/FileUpload.tsx:98` — eslint-disable causes stale closure. **PENDING: Fix deps or memoize**
Summary by Severity
| Severity | Total | Fixed | Pending |
|----------|-------|-------|---------|
| 1 — Deployment Blockers | 6 | 6 | 0 |
| 2 — Critical Security | 9 | 9 | 0 |
| 3 — Critical Runtime Crashes | 11 | 9 | 2 |
| 4 — Race Conditions / Data Corruption | 8 | 2 | 6 |
| 5 — Auth & API Contract Breaks | 8 | 5 | 3 |
| 6 — Infrastructure Config | 10 | 10 | 0 |
| 7 — Dead Monitoring Alerts | 5 | 2 | 3 |
| 8 — Logic & Data Errors | 12 | 10 | 2 |
| 9 — Missing Error Handling | 9 | 5 | 4 |
| 10 — Deprecated/Inconsistent APIs | 6 | 0 | 6 |
| 11 — Low / Best Practice | 18 | 0 | 18 |
| **TOTAL** | **102** | **58** | **44** |

## Fixed (58 bugs)
**Severity 1:** #1, #2, #3, #4, #5, #6  
**Severity 2:** #7, #8, #9, #10, #11, #12, #13, #14, #15, #16  
**Severity 3:** #17, #18, #19, #20, #21, #22, #23, #24, #27  
**Severity 4:** #28, #29  
**Severity 5:** #38, #39, #40, #41, #43  
**Severity 6:** #44, #45, #46, #47, #48, #49, #50, #51, #52, #53  
**Severity 7:** #57, #58  
**Severity 8:** #59, #60, #61, #62, #63, #64, #65, #66, #67, #70  
**Severity 9:** #71, #72, #73, #74, #75  

## Pending (44 bugs)
All remaining bugs above marked with `[ ]`
## Top 10 Critical Fixes Completed ✓
All deployment blockers and critical security vulnerabilities have been fixed:

1. ✅ Create integration/Dockerfile — **FIXED**
2. ✅ Fix /home/donovan/ hardcoded paths in auth files — **FIXED**
3. ✅ Align JWT env var names — **FIXED**
4. ✅ Fix retry_queue.py datetime.replace() crash — **FIXED**
5. ✅ Fix optimizer.py super().__init__ typo — **FIXED**
6. ✅ Create agents/layer1/ workflow — **FIXED**
7. ✅ Fix Money auth fallback for cancelled customers — **FIXED**
8. ✅ Fix RealDictCursor in ComplianceOne and FinOps360 — **FIXED**
9. ✅ Remove --reload from orchestrator Dockerfile — **FIXED**
10. ✅ Fix B-A-P fail-open auth middleware — **FIXED**

---

## Next Priority Fixes (Pending)

### Critical Remaining:
- **reGenesis/** empty directory (#3) — Design system needs package.json and source files
- SSE race condition (#28) — Add lock around _sse_clients.add()
- ClearDesk useState side effects (#22) — Move to useEffect

### High Priority:
- Stripe webhook security (#15) — Return 500 when secret not configured
- Hardcoded DB password (#13) — Move to env var only
- Pydantic v1/v2 mismatch (#25) — Standardize on v2
