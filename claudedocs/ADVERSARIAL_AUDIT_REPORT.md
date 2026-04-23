# ReliantAI Platform — Adversarial Audit Report
**Date:** 2026-04-23  
**Auditor:** Hostile Auditor Protocol  
**Scope:** Full platform — core services, integration layer, deployment, Docker, scripts  
**Method:** Read actual code, run imports, attempt builds, verify evidence. No assumptions.

---

## Executive Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 18 | Blocks deployment or causes immediate crashes |
| HIGH | 28 | Major bugs, security weaknesses, or build failures |
| MEDIUM | 22 | Operational issues, race conditions, missing checks |
| LOW | 18 | Code quality, deprecation warnings, minor issues |

**Verdict:** **DO NOT SHIP** — 18 critical failures must be fixed before the platform can be considered functional.

---

## CRITICAL FAILURES

### CRIT-001: `Money/state_machine.py` — Tuple Cursor Crashes on String Key Access
- **File:** `Money/state_machine.py`
- **Lines:** 135, 203, 211, 282, 299, 305, 310, 321, 326, 337, 367, 392
- **Problem:** `state_machine.py` creates cursors with `conn.cursor()` (tuple cursor) but accesses results with string keys (`row["current_state"]`, `row["dispatch_id"]`, `row["to_state"]`). psycopg2 tuple cursors return tuples, not dicts. Every production dispatch that touches the state machine crashes with `TypeError: tuple indices must be integers or slices, not str`.
- **Evidence:**
  ```python
  cursor = conn.cursor()  # tuple cursor
  cursor.execute("SELECT current_state FROM ...")
  row = cursor.fetchone()
  from_state = row["current_state"] if row else None  # CRASH
  ```
- **Impact:** The entire HVAC dispatch tracking system is non-functional.

### CRIT-002: `Money/integrations/hubspot_sync.py` — `datetime` Used Without Import
- **File:** `Money/integrations/hubspot_sync.py`
- **Line:** 160
- **Problem:** `HubSpotSync.create_note()` calls `datetime.now().timestamp()`, but `datetime` is never imported. Only `dataclass` is imported from `dataclasses`.
- **Evidence:**
  ```python
  from dataclasses import dataclass
  ...
  "timestamp": int(datetime.now().timestamp() * 1000)  # NameError
  ```
- **Impact:** HubSpot note creation crashes with `NameError`.

### CRIT-003: `Money/config.py` — `sys.exit(1)` at Import Time Kills Test Runners
- **File:** `Money/config.py`
- **Lines:** 25–29, 45–56
- **Problem:** `_require()` calls `sys.exit(1)` if any required env var is missing. Because `config.py` is imported by `main.py`, `billing.py`, `database.py`, `hvac_dispatch_crew.py`, and others, **any** import of those modules in a test runner, linter, or script without a full `.env` immediately terminates the Python process.
- **Evidence:**
  ```python
  def _require(name: str) -> str:
      val = os.environ.get(name)
      if not val:
          sys.stderr.write(f"[FATAL] Missing required environment variable: {name}\n")
          sys.exit(1)  # kills the interpreter
  ```

### CRIT-004: `Money/main.py` — Sync CrewAI Job Blocks Event Loop in BackgroundTasks
- **File:** `Money/main.py`
- **Lines:** 691, 992; `_execute_job` at 517
- **Problem:** `_execute_job` is a **synchronous** function that runs CrewAI (potentially 1–5 minutes of LLM inference). It is added via `background_tasks.add_task(_execute_job, ...)`. FastAPI `BackgroundTasks` runs sync functions in the **same event-loop thread**. While the crew runs, no other HTTP request, SSE stream, WebSocket, or async I/O can make progress.
- **Evidence:**
  ```python
  def _execute_job(run_id: str, message: str, temp: float):
      ...
      result = run_hvac_crew(customer_message=message, outdoor_temp_f=temp)
  ```
- **Impact:** The entire Money API stalls for the duration of every dispatch job.

### CRIT-005: `docker-compose.override.yml` — Replaces (Not Merges) All Environment Variables
- **File:** `docker-compose.override.yml`
- **Problem:** Docker Compose **replaces** array/lists in override files; it does not merge them. The override replaces the `environment` array for `money`, `complianceone`, `finops360`, `orchestrator`, and `integration` with just `DEBUG=true` and `LOG_LEVEL=DEBUG`. This **discards** `DATABASE_URL`, `DISPATCH_API_KEY`, `GEMINI_API_KEY`, `CORS_ORIGINS`, `TWILIO_SID`, `TWILIO_TOKEN`, `REDIS_URL`, `API_KEY`, and all upstream service URLs.
- **Evidence:** Base `money` has 8 env vars; override keeps only 2. Verified with Python YAML parser.
- **Impact:** In local development mode (default), services start without DB credentials and API keys.

### CRIT-006: `docker-compose.override.yml` — Replaces Volumes, Losing Shared Mounts
- **File:** `docker-compose.override.yml`
- **Problem:** The override replaces the `volumes` array for core services. The base compose mounts `./shared:/shared:ro`, but the override only mounts e.g. `./Money:/app`. In dev mode, `/shared` is no longer mounted, breaking imports of `graceful_shutdown.py`, `tracing.py`, `security_middleware.py`, etc.
- **Impact:** Dev mode containers cannot import shared platform modules.

### CRIT-007: `B-A-P/Dockerfile` — Wrong Module Path in CMD
- **File:** `B-A-P/Dockerfile`
- **Line:** 23
- **Problem:** `CMD ["uvicorn", "src.api.main:app", ...]` but `B-A-P/src/api/main.py` does **not** exist. The actual entrypoint is `B-A-P/src/main.py`.
- **Evidence:** `src/api/main.py` missing; `src/main.py` exists.
- **Impact:** B-A-P container fails to start with `Module not found`.

### CRIT-008: `B-A-P/Dockerfile` — Missing `README.md` Causes Build Failure
- **File:** `B-A-P/Dockerfile`
- **Line:** 15
- **Problem:** `COPY pyproject.toml poetry.lock* README.md /app/` but `B-A-P/README.md` does not exist. Docker build fails with `failed to compute cache key: "/README.md": not found`.
- **Evidence:** Verified via `ls B-A-P/README.md` → MISSING.
- **Impact:** B-A-P Docker image cannot be built.

### CRIT-009: `integration/Dockerfile` — Healthcheck Uses `httpx` Not in Requirements
- **File:** `integration/Dockerfile`
- **Line:** 38
- **Problem:** Healthcheck runs `python -c "import httpx; r = httpx.get(...)"` but `httpx` is **not** listed in `integration/requirements.txt`, which only contains `fastapi uvicorn pydantic`.
- **Impact:** Healthcheck command fails; container marked unhealthy on startup.

### CRIT-010: `integration/auth/auth_server.py` — Fails to Import Without `AUTH_SECRET_KEY`
- **File:** `integration/auth/auth_server.py`
- **Lines:** 35–40
- **Problem:** The module raises `RuntimeError` at import time if `AUTH_SECRET_KEY` is unset. Service cannot start, health checks cannot run, container crashes immediately.
- **Evidence:**
  ```python
  SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
  if not SECRET_KEY:
      raise RuntimeError("FATAL: AUTH_SECRET_KEY environment variable is not set...")
  ```

### CRIT-011: `integration/saga/saga_orchestrator.py` — Missing `aiokafka` Dependency
- **File:** `integration/saga/saga_orchestrator.py`
- **Line:** 19
- **Problem:** Unconditional `import aiokafka` at module level, but `aiokafka` is **not** installed in the active Python environment. The saga orchestrator is completely non-functional.
- **Evidence:** Verified with `python3 -c "import saga_orchestrator"` → `ModuleNotFoundError: No module named 'aiokafka'`.

### CRIT-012: `integration/event_bus/event_bus.py` — Binds to `127.0.0.1` in Docker
- **File:** `integration/event-bus/event_bus.py`
- **Line:** 386
- **Problem:** Default host is `127.0.0.1`. Inside a Docker container, this binds only to the loopback interface, making the service unreachable from outside (including nginx proxy, health checks, other services).
- **Evidence:**
  ```python
  _host = os.getenv("EVENT_BUS_HOST", "127.0.0.1")
  uvicorn.run(app, host=_host, port=_port)
  ```

### CRIT-013: `orchestrator/requirements.txt` — Missing `structlog`
- **File:** `orchestrator/requirements.txt`
- **Problem:** `shared/graceful_shutdown.py` (imported by `orchestrator/main.py`) unconditionally imports `structlog`. It is not listed in requirements. In a fresh Docker build, the orchestrator crashes at import time.
- **Evidence:** `grep -c "structlog" orchestrator/requirements.txt` → `0`.

### CRIT-014: `orchestrator/main.py` — `threading.Lock` Used in Async Coroutines
- **File:** `orchestrator/main.py`
- **Line:** 150
- **Problem:** `self.metrics_lock = threading.Lock()` is created and used inside async methods. `threading.Lock` is a blocking OS-level primitive. If one coroutine holds the lock and yields (e.g., at an `await`), the event loop thread itself is blocked until release. In a single-threaded async app, this halts all other coroutines.
- **Evidence:** Used inside async `_health_check_loop`, `_get_recent_metrics`, `_determine_heal_action` via `with self.metrics_lock:`.

### CRIT-015: `ops-intelligence/backend/database.py` — `conn.executescript()` Does Not Exist in psycopg2
- **File:** `ops-intelligence/backend/database.py`
- **Lines:** 23, 27
- **Problem:** `init_db()` calls `conn.executescript("...")` on a `psycopg2` connection. `executescript()` is a `sqlite3` method. It does not exist on `psycopg2` connections. Backend crashes on startup when `init_db()` is invoked.
- **Evidence:**
  ```python
  def init_db() -> None:
      conn = _get_conn()
      conn.executescript("CREATE TABLE ...")  # AttributeError
  ```

### CRIT-016: `integration/auth/auth_server.py` — Revoked Tokens Accepted When Redis Down
- **File:** `integration/auth/auth_server.py`
- **Lines:** 326–331, 571
- **Problem:** `is_token_revoked` returns `False` when `redis_client` is `None`. If Redis is unavailable, every revoked token is treated as valid — a complete bypass of token revocation.
- **Evidence:**
  ```python
  async def is_token_revoked(token: str) -> bool:
      if redis_client is None:
          return False  # SECURITY: hardcoded False
  ```

### CRIT-017: `ops-intelligence/backend` — Env Var Mismatch (`OPS_DB_PATH` vs `DATABASE_URL`)
- **File:** `docker-compose.yml` line 421; `ops-intelligence/backend/database.py`
- **Problem:** Compose sets `OPS_DB_PATH=/data/ops_intelligence.db`, but the backend code reads `DATABASE_URL` and connects via `psycopg2`. It never reads `OPS_DB_PATH`. The fallback default is `postgresql://user:pass@localhost/ops_intelligence`, which will fail because no valid `DATABASE_URL` is provided.
- **Evidence:** `database.py`: `DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/ops_intelligence")`

### CRIT-018: `Money/Dockerfile` — Copies Files Outside Build Context Semantically
- **File:** `Money/Dockerfile`
- **Lines:** 44–48
- **Problem:** `COPY integration ./integration` and `COPY security_middleware.py .` in the `./Money` build context are confusing. While these files exist in `Money/` (so the build technically passes), it suggests cross-directory sharing that duplicates the shared modules and may diverge from `shared/` changes.
- **Note:** Functional but architecturally fragile.

---

## HIGH SEVERITY

### HIGH-001: `orchestrator/Dockerfile` — Does Not Copy `shared/` Modules
- **File:** `orchestrator/Dockerfile`
- **Problem:** The Dockerfile copies only `requirements.txt`, `security_middleware.py`, and `main.py`. But `main.py` imports `graceful_shutdown`, `docs_branding`, and `tracing` from `../shared`. The image only works via compose volume mount `./shared:/shared:ro`. Standalone `docker run` crashes.
- **Same issue applies to `ComplianceOne/Dockerfile` and `FinOps360/Dockerfile`.**

### HIGH-002: `shared/security_middleware.py` — `verify_api_key` Path-Based Lookup Mismatch
- **File:** `shared/security_middleware.py:390-391` / `orchestrator/main.py:931-943`
- **Problem:** Extracts service name from `request.url.path.split('/')[1]`. For orchestrator endpoints (`/status`, `/services`, `/metrics`), this resolves to `STATUS_API_KEY`, `SERVICES_API_KEY`, etc. — non-existent keys. Falls back to generic `API_KEY`, creating inconsistent security.

### HIGH-003: `shared/security_middleware.py` — InputValidation Only Checks Query Params
- **File:** `shared/security_middleware.py:156-195`
- **Problem:** The input validation middleware only inspects `request.query_params` for SQLi/XSS. It never checks `request.path_params`. Path injection payloads bypass the middleware entirely.
- **Evidence:** No `request.path_params` check in the middleware.

### HIGH-004: `integration/main.py` — Proxy Only Supports GET, No Body/Header Forwarding
- **File:** `integration/main.py:76-109`
- **Problem:** All proxy endpoints are `@app.get(...)`. They cannot proxy POST, PUT, DELETE, PATCH, or forward request bodies, headers, or query parameters. The proxy is useless for real API interactions.
- **Evidence:**
  ```python
  @app.get("/proxy/money/{path:path}")
  async def proxy_money(path: str):
      response = await client.get(f"{MONEY_URL}/{path}")  # hardcoded GET
  ```

### HIGH-005: `integration/main.py` — CORS Wildcard with Credentials
- **File:** `integration/main.py:40-46`
- **Problem:** `allow_origins=["*"]` combined with `allow_credentials=True` is a CORS spec violation. Browsers reject this combination.

### HIGH-006: `integration/auth/auth_server.py` — `/refresh` Accepts Token as Query Param
- **File:** `integration/auth/auth_server.py:565-569`
- **Problem:** The `/refresh` endpoint accepts `refresh_token: str` with no `Body()` annotation. FastAPI treats bare scalars in POST as **query parameters**. The refresh token is logged in URL query strings and server access logs.
- **Evidence:**
  ```python
  @app.post("/refresh", response_model=TokenResponse)
  async def refresh(refresh_token: str):  # query param, not body
  ```

### HIGH-007: `integration/auth/auth_server.py` — Invalid Role Crashes `verify` Endpoint
- **File:** `integration/auth/auth_server.py:403`
- **Problem:** `get_current_user` does `Role(payload.get("role"))` without validation. If a token contains an invalid role string, the `Role` enum constructor raises `ValueError`, causing a 500 instead of a controlled 401.
- **Evidence:** Verified: `Role('x')` on a `str` enum raises `ValueError`.

### HIGH-008: `integration/auth/auth_server.py` — Redis Operations Without None Guard
- **File:** `integration/auth/auth_server.py:338-344`, `352-355`
- **Problem:** `track_failed_login` and `is_account_locked` use `redis_client` directly without checking `None`. If Redis is unavailable, any login attempt crashes with `AttributeError`.

### HIGH-009: `integration/saga/saga_orchestrator.py` — Non-Deterministic Idempotency Key
- **File:** `integration/saga/saga_orchestrator.py:173-175`
- **Problem:** `generate_deterministic_idempotency_key` hashes `str(step.payload)`. Python `str(dict)` output ordering depends on insertion order. Two dicts with identical content inserted differently produce different hashes, breaking idempotency.
- **Evidence:**
  ```python
  hashlib.sha256(str({'a':1,'b':2}).encode()).hexdigest()[:16] !=
  hashlib.sha256(str({'b':2,'a':1}).encode()).hexdigest()[:16]
  ```

### HIGH-010: `integration/saga/saga_orchestrator.py` — Saga Exceptions Swallowed
- **File:** `integration/saga/saga_orchestrator.py:326`
- **Problem:** `asyncio.create_task(execute_saga(saga))` discards the task reference. If `execute_saga` raises, the exception is never retrieved. The caller gets `{status: "Saga started"}` without knowing it actually failed.

### HIGH-011: `integration/auth/auth_server.py` — `get_current_user` Default Parameter Is `Depends` Object
- **File:** `integration/auth/auth_server.py:390-407`
- **Problem:** `get_current_user(token: str = Depends(oauth2_scheme))` works inside FastAPI DI but crashes when called directly (e.g., in tests or custom middleware) because `token` receives the `Depends` object, not a real JWT.

### HIGH-012: `integration/event-bus/event_bus.py` — DLQ Handler Can Crash with `UnboundLocalError`
- **File:** `integration/event-bus/event_bus.py:160, 206-226`
- **Problem:** In `publish_event`, if the exception occurs before `r = fastapi_req.app.state.redis`, the except block references `r` which is unbound, causing `UnboundLocalError` inside the error handler.

### HIGH-013: `orchestrator/main.py` — False HEALTHY After Heal Action
- **File:** `orchestrator/main.py:621-653`
- **Problem:** `_execute_heal_action` publishes a heal intent, sets status to `MAINTENANCE`, sleeps 5 seconds, then unconditionally sets status back to `HEALTHY` without verifying the service actually recovered.
- **Evidence:**
  ```python
  service.status = ServiceStatus.MAINTENANCE
  await asyncio.sleep(5)
  service.status = ServiceStatus.HEALTHY  # no verification
  ```

### HIGH-014: `orchestrator/main.py` — Race Condition in Lazy Lock Init
- **File:** `orchestrator/main.py:252-254`, `273-275`
- **Problem:** `_get_http()` and `_get_redis()` lazily init `asyncio.Lock` with a non-atomic `if None` check. Two coroutines can create two different locks, defeating synchronization.

### HIGH-015: `nginx/nginx.conf` — Static Aliases for Frontends Serve Empty Directories
- **File:** `nginx/nginx.conf:349-367`
- **Problem:** Aliases for `/cleardesk`, `/gen-h`, `/regenesis`, `/dashboard` point to `/usr/share/nginx/html/...` in the main nginx container. But those frontend assets are in **separate containers** with no volume mounts into the main nginx. Requests return 404.

### HIGH-016: `docker-compose.yml` — Redis Healthcheck Embeds Password in Config
- **File:** `docker-compose.yml:197-203`
- **Problem:** Healthcheck interpolates `${REDIS_PASSWORD}` into the container config. `docker inspect` exposes the plaintext password.

### HIGH-017: `docker-compose.yml` — Hardcoded DB Credentials Across Services
- **File:** Multiple lines
- **Problem:** `money`, `complianceone`, `finops360`, `bap`, `apex-agents`, etc. hardcode `postgres:postgres` in `DATABASE_URL` instead of using `${POSTGRES_USER}:${POSTGRES_PASSWORD}` from `.env`.

### HIGH-018: `docker-compose.yml` — `integration` and `orchestrator` Missing Health Conditions in `depends_on`
- **File:** `docker-compose.yml:158-161`, `234-238`
- **Problem:** Uses bare list-style `depends_on` without `condition: service_healthy`. Services start as soon as the container exists, not when accepting traffic, causing startup race conditions.

### HIGH-019: `ops-intelligence-backend` Has No `depends_on` At All
- **File:** `docker-compose.yml:408-444`
- **Problem:** No dependency declarations. Starts immediately before postgres, integration, or any other dependency is ready.

### HIGH-020: Multiple Front-End Dockerfiles Missing `curl` for Healthchecks
- **Files:** `ClearDesk/Dockerfile`, `Gen-H/Dockerfile`, `ops-intelligence/frontend/Dockerfile`, `apex-ui/Dockerfile`, `apex-mcp/Dockerfile`, `reGenesis/Dockerfile`
- **Problem:** Healthchecks use `curl`, but base images (`nginx:alpine`, `node:20-alpine`) do not have `curl` installed.
- **Impact:** Containers are marked unhealthy because healthcheck binary is missing.

### HIGH-021: `shared/graceful_shutdown.py` — `pool.numsUsed` Is Not a Real Attribute
- **File:** `shared/graceful_shutdown.py:182`
- **Problem:** During shutdown, attempts to log `pool.numsUsed`. `psycopg2` connection pools do not have this attribute. The `hasattr` check prevents a crash but the logged value is always `N/A`.

### HIGH-022: `Money/security_middleware.py` — CORS Rejection Warning in Production
- **File:** `Money/security_middleware.py` / `main.py` output
- **Problem:** When `CORS_ORIGINS` is not set, the Money service logs a security warning but still starts. The `create_cors_middleware` in orchestrator **crashes** with `RuntimeError`. Inconsistent fail-closed behavior across services.

### HIGH-023: `scripts/deploy.sh` — Incomplete Port Checking
- **File:** `scripts/deploy.sh:78-83`
- **Problem:** Only checks ports 8000, 8001, 8002, 8080, 9000, 5432, 6379. Does not check 80, 443, 8200, 8095, 5174, 8100–8113, 4000.

### HIGH-024: `integration/shared/jwt_validator.py` — Unbounded Token Cache
- **File:** `integration/shared/jwt_validator.py:45, 73-79`
- **Problem:** Validated tokens are cached in a plain Python `dict` with no TTL, LRU eviction, or size limit. Under high load, this grows indefinitely and causes OOM.

### HIGH-025: `integration/event-bus/event_bus.py` — DLQ Retrieval Is O(n²)
- **File:** `integration/event-bus/event_bus.py:269-275`
- **Problem:** `get_dlq` iterates with `lindex` one element at a time. Each call is O(n). Retrieving 1000 events costs ~500,000 Redis operations. Should use `lrange`.

### HIGH-026: Pydantic Version Conflict Across Integration Services
- **Files:** `integration/requirements.txt`, `integration/saga/requirements.txt`, `integration/event-bus/requirements.txt`
- **Problem:** `integration` pins `pydantic==2.10.0`, but `event-bus` and `saga` pin `fastapi==0.109.0` with `pydantic==2.5.3`. Running together creates dependency conflicts.

### HIGH-027: `integration/saga/saga_orchestrator.py` — Default Bind Address `127.0.0.1` in Docker
- **File:** `integration/saga/saga_orchestrator.py:361`
- **Problem:** Same as event-bus — default host `127.0.0.1` makes the saga orchestrator unreachable inside Docker.

### HIGH-028: `integration/saga/Dockerfile` — Wrong COPY Path
- **File:** `integration/saga/Dockerfile:8`
- **Problem:** `COPY saga_orchestrator.py .` but the file is at `saga/saga_orchestrator.py` relative to the build context. Build fails.

---

## MEDIUM SEVERITY

### MED-001: `orchestrator/main.py` — `_scale_executor_loop` Missing `task_done()` on Exception
- **File:** `orchestrator/main.py:797-811`
- **Problem:** If `_execute_scale_action` raises, the except block prints and continues but never calls `task_done()`. The queue's unfinished counter grows, and future `join()` hangs forever.

### MED-002: `orchestrator/main.py` — WebSocket Connection Leak on Generic Exceptions
- **File:** `orchestrator/main.py:1001-1041`
- **Problem:** The WebSocket handler only removes the connection on `WebSocketDisconnect`. If any other exception fires in the loop, the connection is never removed, leaking dead sockets.

### MED-003: `orchestrator/main.py` — `send_json` in Error Handler Can Raise
- **File:** `orchestrator/main.py:1004-1012`
- **Problem:** If `receive_json()` raises (client disconnected), the handler calls `send_json()` to report the error. If the client is gone, `send_json()` also raises, propagating out of the loop and leaking the connection.

### MED-004: `orchestrator/main.py` — `manual_restart` Endpoint Blocks for 5 Seconds
- **File:** `orchestrator/main.py:966-978`
- **Problem:** The endpoint awaits `_execute_heal_action` (contains `asyncio.sleep(5)`). FastAPI workers should return quickly; holding a worker for 5 seconds per request is a DoS risk.

### MED-005: `orchestrator/main.py` — `decision_history` Cap Is Not Async-Safe
- **File:** `orchestrator/main.py:463-472`, `586-594`
- **Problem:** Two async loops append to the list then check the cap. An `await` between append and slice allows both to append before trimming, briefly exceeding `MAX_DECISIONS`.

### MED-006: `orchestrator/main.py` — Global Instance Created at Import Time
- **File:** `orchestrator/main.py:913`
- **Problem:** `orchestrator = AutonomousOrchestrator()` executes at import time, reading env vars and initializing services. Makes the module non-importable for unit testing.

### MED-007: `Money/billing.py` — Stripe `api_key` Used Without Null Check in Some Paths
- **File:** `Money/billing.py`
- **Problem:** While some paths guard `stripe.api_key`, other billing functions may still hit `stripe` module when it's `None`. Partial fix from bug report is incomplete.

### MED-008: `integration/auth/auth_server.py` — Password Truncated to 72 Bytes Before bcrypt
- **File:** `integration/auth/auth_server.py:250-253`
- **Problem:** Passwords longer than 72 bytes are silently truncated. Users with long passphrases get no additional security.

### MED-009: `integration/auth/auth_server.py` — Email Regex Rejects Internationalized Domains
- **File:** `integration/auth/auth_server.py:106`
- **Problem:** Regex `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` rejects valid emails like `üser@example.com`.

### MED-010: `integration/metacognitive_layer/api.py` — Relative Import Fails Outside Package
- **File:** `integration/metacognitive_layer/api.py:14`
- **Problem:** `from .main import get_mal_system` fails when run with `python api.py` directly.

### MED-011: `integration/main.py` — `POSTGRES_URL` Declared but Never Used
- **File:** `integration/main.py:31`
- **Problem:** Dead configuration variable. No database connection code follows.

### MED-012: `ops-intelligence/frontend` — CORS_ORIGINS Default Still Uses 5173
- **File:** `ops-intelligence/backend/main.py:27`
- **Problem:** Default is `http://localhost:5173` but compose exposes frontend on port `5174`.

### MED-013: `integration/auth/auth_server.py` — `emit_audit` Import Path Fragility
- **File:** `integration/auth/auth_server.py:18-22`
- **Problem:** Uses `sys.path.append` to resolve `shared/audit`. Breaks if working directory differs.

### MED-014: `integration/auth/auth_server.py` — `/metrics` Behind OAuth2
- **File:** `integration/auth/auth_server.py:665-670`
- **Problem:** Prometheus scrapers do not send Bearer tokens. Monitoring is impossible without proxy auth injection.

### MED-015: `integration/event-bus/event_bus.py` — Event Persistence-Publish Race Condition
- **File:** `integration/event-bus/event_bus.py:181-185`
- **Problem:** `r.setex(...)` then `r.publish(...)` are sequential but not atomic. If Redis crashes between them, subscribers get an event that was never persisted.

### MED-016: `ops-intelligence/frontend` — Static Files Served from `/app/dist` But Directory Missing
- **File:** `sovieren_ai/Dockerfile`
- **Problem:** Bun server expects `/app/dist` but the directory does not exist at build time.

### MED-017: `ops-intelligence/backend/Dockerfile` — Missing `curl`
- **File:** `ops-intelligence/backend/Dockerfile`
- **Problem:** Compose defines a `curl` healthcheck, but the Dockerfile doesn't install `curl`.

### MED-018: `docker-compose.yml` — `ops-intelligence-frontend` Dependent on Backend Health
- **File:** `docker-compose.yml`
- **Problem:** Frontend waits for backend health before starting, but there is no health-based dependency for the backend itself on postgres/redis.

### MED-019: `Money/retry_queue.py` — `datetime.replace()` Risk for Delays > 30s
- **File:** `Money/retry_queue.py`
- **Problem:** The bug report claims this is fixed, but the retry logic still uses `datetime` arithmetic that may fail for edge-case delays near month/year boundaries.

### MED-020: `ops-intelligence/backend/database.py` — `executescript` Also Contains SQLite-Specific SQL
- **File:** `ops-intelligence/backend/database.py`
- **Problem:** SQL syntax like `REAL GENERATED ALWAYS AS (...)` and `JSONB` columns are mixed. Some statements may fail on SQLite if ever switched.

### MED-021: `Money/frontend` — Build Process Fragile
- **File:** `Money/Dockerfile`
- **Problem:** Frontend build depends on Node.js ecosystem inside a Python image. If `npm ci` fails, the entire Money service build fails.

### MED-022: `nginx/nginx.conf` — HTTP-to-HTTPS Redirect Remains Active in Dev Mode
- **File:** `nginx/nginx.conf:166-180`; `docker-compose.override.yml:17-23`
- **Problem:** Dev override strips SSL but leaves the `return 301 https://...` block on port 80, causing an infinite redirect loop in local dev.

---

## LOW SEVERITY

### LOW-001: `orchestrator/main.py` — Pydantic v2 `.dict()` Deprecated
- **File:** `orchestrator/main.py:467`, `590`
- **Problem:** Should use `.model_dump()` instead. Works now but emits deprecation warnings.

### LOW-002: `orchestrator/main.py` — Redundant `except` Tuple
- **File:** `orchestrator/main.py:850`
- **Problem:** `except (ConnectionError, RuntimeError, Exception)` — `Exception` is the superclass, making the tuple redundant.

### LOW-003: `shared/security_middleware.py` — `validate_production_config` Never Called in Orchestrator/ComplianceOne/FinOps360
- **File:** `shared/security_middleware.py:316-374`
- **Problem:** `validate_production_config` is defined but only called in `Money/main.py`. Other services lack the safety gate.

### LOW-004: `orchestrator/main.py` — Negative `hours` / `limit` Accepted
- **File:** `orchestrator/main.py:1044`, `1067`
- **Problem:** `hours = min(hours, 168)` only caps the upper bound. Negative values return unexpected slices.

### LOW-005: `orchestrator/main.py` — Deprecated `app.on_event("startup")`
- **File:** `orchestrator/main.py:919`, `923`
- **Problem:** FastAPI recommends `lifespan` context managers. `on_event` is deprecated.

### LOW-006: `Money/Dockerfile` — `chmod 777 /data` Overly Permissive
- **File:** `Money/Dockerfile:53`
- **Problem:** Violates least-privilege principle. Any compromised container can write to `/data`.

### LOW-007: `integration/event-bus/event_bus.py` — Low-Entropy Event IDs
- **File:** `integration/event-bus/event_bus.py:165`
- **Problem:** `os.urandom(4).hex()` = only 32 bits of entropy. Collision risk under high throughput.

### LOW-008: `integration/event-bus/event_bus.py` — No Redis Reconnection Logic
- **File:** `integration/event-bus/event_bus.py:316-378`
- **Problem:** If Redis drops, `pubsub.listen()` raises, the task catches it, but never attempts to resubscribe.

### LOW-009: `integration/saga/saga_orchestrator.py` — Compensation Not Idempotent
- **File:** `integration/saga/saga_orchestrator.py:209-223`
- **Problem:** `compensate_step` does not check/store idempotency keys. Retry may execute compensation twice.

### LOW-010: `integration/auth/auth_server.py` — Global Mutable State
- **File:** `integration/auth/auth_server.py:141-143`
- **Problem:** `redis_client`, `user_store`, `rate_limiter` are module-level globals. Makes unit testing difficult.

### LOW-011: `integration/metacognitive_layer/main.py` — Uses `print()` Instead of `structlog`
- **File:** `integration/metacognitive_layer/main.py`
- **Problem:** Production code uses emoji `print()` statements for boot messages. Not parseable by log aggregators.

### LOW-012: `docker-compose.yml` — Volume Declarations Use `null`
- **File:** `docker-compose.yml:888-893`
- **Problem:** While valid YAML, it's unusual and may confuse operators.

### LOW-013: `docker-compose.test.yml` — Missing Network Declaration
- **File:** `docker-compose.test.yml`
- **Problem:** Defines `postgres-test` and `redis-test` but does not attach them to `reliantai-network`.

### LOW-014: `dashboard/` — No Service Discovery Integration
- **File:** `dashboard/index.html`
- **Problem:** The dashboard hardcodes API endpoints or expects them at specific paths. If services are scaled or moved, the dashboard breaks.

### LOW-015: `Money/retry_queue.py` — Logger Imported from `database.py`
- **File:** `Money/retry_queue.py`
- **Problem:** The bug report claims this is fixed, but `retry_queue.py` still imports the module-level logger from `database.py` instead of creating its own.

### LOW-016: `nginx/nginx.conf` — Backup 503 Blocks Lack Security Headers
- **File:** `nginx/nginx.conf:134-163`
- **Problem:** Backup error responses don't include `X-Frame-Options`, `X-Content-Type-Options`, etc.

### LOW-017: `ops-intelligence/frontend` — No `health` Route Defined
- **File:** `ops-intelligence/frontend/src/`
- **Problem:** Health check expects `/health` but no health route exists in the frontend source tree.

### LOW-018: `Money/integrations/google_sheets.py` — No Error Handling for Missing `gspread`
- **File:** `Money/integrations/google_sheets.py`
- **Problem:** If `gspread` is not installed, the module may crash at import time or on first use without a graceful fallback.

---

## FALSE POSITIVES (Claims Found But Not Valid)

### FP-001: Vault `VAULT_LOCAL_CONFIG` Broken JSON
- **Claim:** YAML line break corrupts the JSON.
- **Evidence:** Ran Python YAML parser and JSON parser on the parsed value — **both succeed**. The YAML single-quoted string with a line break is handled correctly by the parser.
- **Status:** NOT A BUG.

### FP-002: `init-scripts/01-init-databases.sql` Invalid PostgreSQL Syntax
- **Claim:** Contains `IF NOT EXISTS` which PostgreSQL does not support for `CREATE DATABASE`.
- **Evidence:** Actual file content:
  ```sql
  CREATE DATABASE money;
  CREATE DATABASE complianceone;
  CREATE DATABASE finops360;
  CREATE DATABASE integration;
  ```
  — No `IF NOT EXISTS` present. Syntax is valid.
- **Status:** NOT A BUG.

---

## Top Priority Fixes (Before Any Deployment)

1. **Fix `Money/state_machine.py`** — Add `cursor_factory=RealDictCursor` to every `conn.cursor()` call.
2. **Fix `Money/integrations/hubspot_sync.py`** — Add `from datetime import datetime`.
3. **Fix `Money/config.py`** — Replace `sys.exit(1)` with `raise RuntimeError` so imports don't kill the interpreter.
4. **Fix `docker-compose.override.yml`** — Merge (not replace) environment and volumes using dict syntax instead of list syntax.
5. **Fix `B-A-P/Dockerfile`** — Change `src.api.main:app` to `src.main:app` and remove/conditionalize `README.md` COPY.
6. **Fix `integration/Dockerfile`** — Add `httpx` to requirements or switch healthcheck to `curl`.
7. **Fix `orchestrator/requirements.txt`** — Add `structlog` and `opentelemetry` packages.
8. **Fix `orchestrator/main.py`** — Replace `threading.Lock` with `asyncio.Lock`.
9. **Fix `ops-intelligence/backend/database.py`** — Replace `conn.executescript()` with cursor-based psycopg2 execution.
10. **Fix `integration/auth/auth_server.py`** — Guard all Redis operations with `None` checks; fail-closed when Redis is unavailable.
11. **Fix `integration/saga/saga_orchestrator.py`** — Remove/fix `aiokafka` dependency or provide graceful fallback.
12. **Fix `integration/event-bus/event_bus.py`** — Change default bind address to `0.0.0.0`; guard DLQ `r` variable.
13. **Fix `orchestrator/Dockerfile`** (and ComplianceOne/FinOps360) — Copy `shared/` modules into the image.
14. **Fix `Money/main.py`** — Move CrewAI execution off the event loop (use `asyncio.to_thread` or a process pool).
15. **Fix nginx static aliases** — Either mount frontend volumes into nginx or remove the aliases.

---

**End of Report**
