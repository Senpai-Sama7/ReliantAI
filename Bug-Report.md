ReliantAI Master Bug Report
SEVERITY 1 — DEPLOYMENT BLOCKERS (System Won't Start)
#	File	Bug
1	docker-compose.yml:88	References ./integration/Dockerfile — file does not exist. docker compose up fails immediately.
2	docker-compose.yml:16	Mounts ./init-scripts:/docker-entrypoint-initdb.d — directory does not exist.
3	reGenesis/	Entire directory is empty. No package.json, no pnpm-workspace.yaml, no source. Design system is gone.
4	apex/apex-agents/api/main.py:73	from agents.layer1.workflow import run_layer1 — agents/layer1/ directory does not exist. Apex API will never start.
5	apex/apex-agents/api/main.py:70	from skill_tools import handle_tool_call, TOOL_LIST — skill_tools module does not exist. Same crash.
6	integration/metacognitive_layer/optimizer.py:121	super().____(OptimizationDomain.CACHE) — four underscores instead of __init__. TypeError on class instantiation. Same bug at line 183.
SEVERITY 2 — CRITICAL SECURITY VULNERABILITIES
#	File	Bug
7	B-A-P/src/api/auth_integration.py:15	sys.path.insert(0, '/home/donovan/Projects/ReliantAI/...') — hardcoded developer home path. Import fails → JWT_AVAILABLE = False → all requests proceed unauthenticated.
8	BackupIQ/auth_integration.py:19,29	Same /home/donovan/ hardcoded path. Same auth bypass.
9	citadel_ultimate_a_plus/auth_integration.py:20,30	Same /home/donovan/ hardcoded path. Same auth bypass. JWT_AVAILABLE = False → return {"username": "anonymous", "roles": ["user"]} for every request.
10	integration/auth/auth_server.py:35 vs integration/shared/jwt_validator.py:23	Auth server reads AUTH_SECRET_KEY; JWT validator reads JWT_SECRET. Different env var names — tokens signed with one key, validated with another. All JWT validation fails.
11	Money/main.py:614	If validate_api_key() raises HTTPException (e.g. billing past_due/cancelled), code catches the exception and falls through to _authorize_request() — cancelled customers bypass billing enforcement.
12	B-A-P/src/api/middleware/auth.py:46	if not auth_integration.validator: return await call_next(request) — fail-open: if JWT module is missing, every request is allowed through without authentication.
13	Money/database.py:25	Default DB URL contains hardcoded password change-in-production in source code.
14	.env.production	API keys are placeholder strings like prod-dispatch-key-change-me-immediately with no enforcement preventing deployment with these values.
15	Money/billing.py:260	Stripe webhook returns HTTP 200 when stripe_webhook_secret is not configured. Attackers can send forged Stripe events and receive a success response.
16	integration/shared/jwt_validator.py:85	Comment explicitly acknowledges TLS verification is not enforced for remote auth service URLs. Insecure by default in production.
SEVERITY 3 — CRITICAL LOGIC/RUNTIME CRASHES
#	File	Bug
17	Money/retry_queue.py:224	next_attempt.replace(second=next_attempt.second + int(delay)) — datetime.replace() requires second to be 0–59. Any retry delay over ~30s will raise ValueError. Fix: use timedelta.
18	Money/retry_queue.py:13	from database import get_pool, logger — logger is not exported from database.py. ImportError on module load.
19	Money/hvac_dispatch_crew.py:173	dispatch_id = f"DSP-{datetime.now(...).strftime('%Y%m%d-%H%M%S')}" — two concurrent requests in the same second generate the same primary key. Second insert fails with duplicate key error.
20	ComplianceOne/main.py:209	dict(row) called on psycopg2 rows which are tuples, not dicts. dict() on a tuple of values (not key-value pairs) crashes with TypeError. RealDictCursor is imported but never used. Same bug in FinOps360/main.py:230.
21	FinOps360/main.py:339	budget = dict(cur.fetchone()) — if no row found, fetchone() returns None. dict(None) raises TypeError.
22	ClearDesk/src/components/dashboard/Dashboard.tsx:159	useState(() => { requestAnimationFrame(() => setVisible(true)); }) — side effects inside useState initializer. Must be useEffect.
23	apex/apex-agents/api/main.py:220	Layer2 API endpoint calls run_layer2(task=..., context=..., agents=...) but the actual run_layer2 function expects agent_name, confidence, aleatoric, epistemic. Completely mismatched signatures — runtime TypeError.
24	apex/apex-agents/agents/layer3/cross_system_dispatch.py	cross_system_dispatch function doesn't exist — only CrossSystemDispatcher class. Import in main.py:63 will crash.
25	integration/saga/saga_orchestrator.py:143	Saga.parse_raw(data) — Pydantic v1 API used in a codebase that also calls .model_dump_json() (v2 API). One will crash depending on which Pydantic version is installed.
26	integration/nexus-runtime/memory_redis.py	_cleanup_expired() is synchronous and accesses mutable dicts that async methods also mutate — race condition during dictionary iteration.
27	Money/circuit_breaker.py:112	isinstance(exception, self.excluded) where self.excluded defaults to (). isinstance(e, ()) raises TypeError in Python.
SEVERITY 4 — HIGH: Race Conditions & Data Corruption
#	File	Bug
28	Money/main.py:878,928	SSE clients added via _sse_clients.add(queue) without lock, but _broadcast_dispatch_event() iterates the set under _sse_lock. Set corrupted under concurrent add/remove.
29	Money/hvac_dispatch_crew.py:278	Global triage_agent, intake_agent etc. reassigned in _ensure_agents() with no locking. Concurrent dispatch requests interfere with each other's agent references.
30	integration/auth/rate_limiter.py:30	defaultdict(asyncio.Lock) — multiple coroutines can create duplicate locks for the same key simultaneously. Race condition in rate limit logic.
31	integration/saga/saga_orchestrator.py:164	Idempotency key is f"{step.step_id}:{uuid.uuid4()}" — new UUID on every call. Idempotency check always fails; same step can execute multiple times.
32	soviergn_ai/wasm-bridge.ts:419	Framebuffer view created before post-read consistency check. Worker can swap buffers between read and check. Torn/corrupt framebuffer displayed.
33	soviergn_ai/wasm-bridge.ts:310	checkGrowth() reads memory length and updates layout — no synchronization. Worker can grow memory between check and layout update.
34	B-A-P/src/tasks/pipeline_tasks.py:15	Celery task (synchronous) calls run_etl_pipeline() (async) via thread spawning. Exceptions in the async code are silently swallowed.
35	integration/saga/saga_orchestrator.py:247	Compensation loop does saga.steps[j] where j ranges from i to 0, but saga.steps may have fewer entries than i. IndexError when compensation triggered before all steps registered.
SEVERITY 5 — HIGH: Auth, Middleware & API Contract Bugs
#	File	Bug
36	B-A-P/src/config/settings.py:49	SECRET_KEY validator rejects "change-me-in-production" but .env.example sets SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32. Validation passes on the example value — wrong default silently accepted.
37	B-A-P/src/config/settings.py:125	If ALLOWED_ORIGINS not set, defaults to [] — zero CORS origins allowed, breaking all frontend access.
38	apex/apex-ui/src/app/api/proxy/[...path]/route.ts:37	Proxy forwards requests to backend but does not forward the Authorization header. All authenticated API calls from the browser will fail.
39	Money/billing.py:147	if not stripe.api_key — but stripe can be None if the package isn't installed. This line raises AttributeError instead of 503.
40	Money/billing.py:297	int(metadata.get("customer_id", 0)) — if value is a non-numeric string, ValueError crashes the Stripe webhook handler.
41	orchestrator/main.py:727	Bare except: in WebSocket broadcast — catches KeyboardInterrupt and suppresses all errors silently.
42	integration/shared/event_types.py:54	payload: Dict[str, Any] = Field(..., max_length=65536) — max_length is silently ignored on Dict fields in Pydantic. No actual payload size limit.
43	Money/main.py:608	Rate limiting runs before authentication. Unauthenticated attacker can rate-limit legitimate users sharing the same IP (NAT/proxy).
SEVERITY 6 — HIGH: Configuration & Infrastructure
#	File	Bug
44	orchestrator/Dockerfile:25	CMD [..., "--reload"] — --reload in production causes continuous restarts on any file modification.
45	Money/Dockerfile:33	Frontend is built with npm ci && npm run build but the FastAPI app never serves the built files.
46	integration/saga/Dockerfile:11	Healthcheck python -c "import requests; requests.get(...)" — no status code check. Always exits 0 (healthy) even when service returns 500.
47	docker-compose.yml:121	Orchestrator depends_on lists [money, complianceone, finops360] — Redis is missing despite orchestrator using REDIS_URL. Starts before Redis is ready.
48	nginx/Dockerfile:10	`COPY ssl/cert.pem ... 2>/dev/null
49	vault/vault-config.hcl:11	Vault configured for tls_cert_file = "/vault/certs/cert.pem" but Vault Dockerfile never copies certificates into the image. Vault won't start in production mode.
50	integration/docker-compose.yml:81	Mounts ./observability/prometheus.yml — integration/observability/ directory doesn't exist. Correct path is ../../monitoring/.
51	monitoring/prometheus.yml:85	cAdvisor scrape target on port 8080 conflicts with the integration/auth service also on port 8080.
52	ops-intelligence/docker-compose.yml:35	Frontend mapped to host port 5174:80 but start.sh runs dev server on 5173. Port mismatch.
53	integration/docker-compose.yml:255	zookeeper-data and zookeeper-logs volumes declared but no Zookeeper service exists in the file.
SEVERITY 7 — MEDIUM: Monitoring Dead Alerts
#	File	Bug
54	monitoring/alert-rules.yml:76	Alert uses metric container_restarts_total — this metric is not exposed by cAdvisor or any configured exporter. Alert will never fire.
55	monitoring/alert-rules.yml:96	Alert uses backup_last_success_timestamp — undefined metric. No exporter emits this. Alert will never fire.
56	monitoring/alert-rules.yml:86	Alert uses ssl_certificate_expiry_seconds — undefined metric. Requires an SSL exporter not in the stack. Alert will never fire.
57	monitoring/grafana/datasources/datasources.yml:23	URL template "$$${__value.raw}" — triple $$$ instead of $. Grafana TraceID derivedFields URL will be interpreted literally instead of interpolated.
58	monitoring/loki-config.yml:24	Schema uses boltdb-shipper — deprecated since Loki 2.8. Should be tsdb. Will cause warnings and may fail on current Loki versions.
SEVERITY 8 — MEDIUM: Logic & Data Errors
#	File	Bug
59	integration/metacognitive_layer/engine.py:199	PostgreSQL URL hardcoded as postgresql://localhost:5435/metacognitive. Same hardcoding in feedback_collector.py:190 and optimizer.py:285. No environment variable support.
60	integration/metacognitive_layer/engine.py:566	str(uuid.uuid4())[:8] — truncated UUID has only ~65,536 possible values. Collision probability is significant in any meaningful dataset.
61	integration/shared/security_middleware.py:114	self._local: Dict[str, List[float]] grows unbounded. _local_max_ips = 10_000 limit exists but cleanup is O(n) per request and lossy. Memory exhaustion attack vector.
62	B-A-P/src/models/data_models.py:23	metadata_ = Column("metadata", JSON, default=dict) — default=dict passes the class itself as default, not a factory. All rows share one mutable dict object. Fix: default_factory=dict.
63	B-A-P/src/api/routes/data.py:33	File written to disk before DB commit. If DB commit fails, file is orphaned — exists on disk with no corresponding database record.
64	FinOps360/main.py:560	Background budget alert task catches all exceptions with print(f"error: {e}") — exception swallowed, no retry, sleeps 1 hour. Alert checks silently stop working on first error.
65	ops-intelligence/backend/routers/performance.py:46	Degradation calculated as abs(current - baseline) / baseline — abs() makes improvements indistinguishable from regressions. A system getting faster looks the same as one getting slower.
66	ops-intelligence/backend/database.py:486	str(uuid.uuid5(...))[:16] — truncating UUID5 to 16 chars greatly increases collision probability. Different companies with same name can collide.
67	migrations/env.py:39	target_metadata = None — Alembic autogenerate is permanently disabled. Only manual migrations possible; model drift will go undetected.
68	ops-intelligence/frontend/src/api/client.ts	No error interceptors, no timeout configured on axios. Network errors silently fail with no retry or feedback.
69	ops-intelligence/frontend/src/components/Layout.tsx:40	health: () => axios.get('/health') — uses bare axios without baseURL, not the configured api instance. Health check hits the wrong URL and fails silently.
70	integration/shared/audit.py	Event channel derived from event_type.split('.')[0] → publishes to events:audit. But subscribers expecting events:audit.log.* from AUDIT_LOG_RECORDED = "audit.log.recorded" never receive audit events.
SEVERITY 9 — MEDIUM: Missing Error Handling
#	File	Bug
71	ClearDesk/src/contexts/DocumentContext.tsx:139	initSyncSession().then(...).then(...) — no .catch(). Unhandled promise rejection on any sync failure.
72	Gen-H/src/services/api.ts:119	getLoginCsrfToken() doesn't check response.ok. On server 500, misleading error "Unable to load login form" instead of actual cause.
73	orchestrator/main.py:881	data = await websocket.receive_json() — no try/except. Invalid JSON closes WebSocket with code 1003 and no feedback to client.
74	integration/event-bus/event_bus.py:221	return json.loads(event_json) — no try/except. Malformed JSON from Redis raises unhandled JSONDecodeError.
75	Money/hvac_dispatch_crew.py:43	Twilio SMS @retry with 3 attempts — if all fail, exception propagates and crashes the entire crew execution. No fallback path.
76	shared/graceful_shutdown.py:54	sys.exit(0) called in signal handler after asyncio.create_task(). Exits before the task runs. Shutdown hooks never execute; resources leak.
77	DocuMancer/backend/server.py:185	Exception handler returns early — remaining files in the batch are silently skipped and never reported to client.
78	integration/auth/auth_server.py:321	await redis_client.setex(...) — redis_client could be None if Redis initialization failed. NoneType error on token revocation.
79	BackupIQ/src/core/config_manager.py:151	If secret not found, returns literal string <SECRET:path> — this placeholder gets used as the actual secret value in subsequent operations.
SEVERITY 10 — MEDIUM: Deprecated & Inconsistent API Usage
#	File	Bug
80	integration/saga/saga_orchestrator.py:212	datetime.utcnow() — deprecated in Python 3.12+, used 6+ times in this file.
81	B-A-P/src/models/analytics_models.py:87	Field(default_factory=datetime.utcnow) — deprecated utcnow(). Use datetime.now(timezone.utc).
82	integration/auth/seed_auth.py:54	datetime.utcnow() while auth_server.py uses datetime.now(UTC). Timezone-naive vs timezone-aware mismatch causes comparison failures.
83	integration/event-bus/event_bus.py:161	.model_dump_json() (Pydantic v2) mixed with Saga.parse_raw() (Pydantic v1) across files. Version mismatch — one will crash.
84	CyberArchitect/ultimate-website-replicator.js:546	new Transform({...}) — Transform is never imported from the stream module. ReferenceError at runtime when SVG optimization runs.
85	DocuMancer/backend/server.py:187	json.loads(item.json()) — item.json() returns a string, then json.loads() parses it back. Should be item.model_dump(). Inefficient and fragile.
SEVERITY 11 — LOW: Config & Best Practice Issues
#	File	Bug
86	docker-compose.yml:9 vs :18	POSTGRES_USER required but healthcheck hardcodes pg_isready -U postgres. If POSTGRES_USER != postgres, healthcheck always fails.
87	integration/auth/Dockerfile:19	Entrypoint embedded as `
88	Acropolis/adaptive_expert_platform/src/middleware.rs:28	NonZeroU32::new(config.rate_limit_per_minute).unwrap() — panics if value is 0. No config validation before use.
89	Acropolis/adaptive_expert_platform/src/mesh.rs:439	.partial_cmp().unwrap() — panics on NaN float comparison in load balancer.
90	Money/main.py	_authorize_request() is sync, called after await validate_api_key() — inconsistent async/sync error handling between auth paths.
91	FinOps360/main.py:419	ORDER BY clause hardcoded in dynamically constructed SQL. Not a direct injection but brittle pattern.
92	apex/infra/docker-compose.yml:19	POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme} — weak default password if env var not set.
93	BackupIQ/deployment/docker/docker-compose.yml:66	Neo4j password hardcoded as backup-enterprise-password in compose file.
94	monitoring/prometheus.yml	Scrape targets reference localhost — won't work when Prometheus runs in a Docker container where services are on different hostnames.
95	scripts/deploy.sh:80	Uses lsof for port checks — not available on Alpine/minimal Linux distros. Port detection silently fails.
96	.env.example	Missing POSTGRES_USER, CORS_ORIGINS, and all VITE_* frontend env vars. New deployments will crash at startup without documentation.
97	integration/metacognitive_layer/api.py:204	generate_latest() returns bytes, passed to JSONResponse which expects str. TypeError on /metrics endpoint.
98	apex/apex-agents/api/auth_integration.py:25	Default AUTH_SERVICE_URL = "http://127.0.0.1:8080" — localhost doesn't resolve inside a Docker container. All auth calls fail in containerized deployments.
99	ops-intelligence/backend/database.py:20	check_same_thread=False with SQLite — while WAL mode helps, concurrent writes can still deadlock under load.
100	tests/test_integration_suite.py:386	await asyncio.sleep(65) inside a test — blocks all other tests for 65 seconds in CI.
101	tests/test_integration_suite.py:280	assert r.status != 500 — allows 404. Test passes even if endpoint doesn't exist.
102	ClearDesk/src/components/ChatPanel.tsx:55	Sort uses order[a.priority] — if priority is not in order, returns undefined, giving NaN comparison and random sort order.
103	ClearDesk/src/components/upload/FileUpload.tsx:98	eslint-disable react-hooks/exhaustive-deps on empty dep array — handleFiles has stale closure over addDocument/updateDocument.
Summary by Severity
Severity	Count
1 — Deployment Blockers	6
2 — Critical Security	9
3 — Critical Runtime Crashes	11
4 — Race Conditions / Data Corruption	8
5 — Auth & API Contract Breaks	8
6 — Infrastructure Config	10
7 — Dead Monitoring Alerts	5
8 — Logic & Data Errors	12
9 — Missing Error Handling	9
10 — Deprecated/Inconsistent APIs	6
11 — Low / Best Practice	18
Total	102
Top 10 Fixes That Unblock the System
Create integration/Dockerfile — nothing deploys without it
Fix /home/donovan/ hardcoded paths in B-A-P, BackupIQ, citadel_ultimate_a_plus — three services currently have auth permanently bypassed in any real environment
Align JWT env var names — AUTH_SECRET_KEY (auth server) vs JWT_SECRET (validator) means no token ever validates
Fix retry_queue.py:224 — datetime.replace(second=...) crashes for any delay > ~30s, breaking the entire retry system
Fix optimizer.py:121,183 — super().____(...) typo (4 underscores) crashes the metacognitive optimizer on startup
Create agents/layer1/ or remove the import — apex-agents can't start
Fix Money auth fallback — cancelled customers bypass billing
Fix RealDictCursor in ComplianceOne and FinOps360 — all list endpoints crash with TypeError
Remove --reload from orchestrator Dockerfile — service is unstable in production
Fix reGenesis/ — the design system is an empty directory
