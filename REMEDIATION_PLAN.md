# ReliantAI Platform - Complete Remediation Plan
**31 Issues | 40-60 Hours | Single PR Implementation**

---

## REMEDIATION PROGRESS

**Overall**: 0/31 complete (0%)

### CRITICAL ISSUES (7) - Production Blockers
- [ ] 1.1: Fix hardcoded `/home/donovan/` path in Gen-H auth_middleware.py
- [ ] 1.2: Fix hardcoded `/home/donovan/` path in apex-agents test
- [ ] 1.3-1.6: Create missing `__init__.py` in 6 directories
- [ ] 2.1: Fix LANGSMITH_API_KEY placeholder in docker-compose.yml
- [ ] 2.2: Fix EVENT_BUS_API_KEY placeholder in docker-compose.yml
- [ ] 2.3: Fix JWT_SECRET placeholder in docker-compose.yml
- [ ] 3.1: Fix CORS wildcard + credentials in integration/main.py

### HIGH ISSUES (13) - Security/Reliability Gaps
- [ ] 2.4: Fix ENVIRONMENT vs ENV variable mismatch (5 files)
- [ ] 2.5: Fix REDIS_PASSWORD defaults to None
- [ ] 2.6: Harden DISPATCH_API_KEY validation (min 32 chars)
- [ ] 2.7: Add JWT secret length validation in Gen-H
- [ ] 3.2: Fix rate limiter thread-safety (add threading.Lock)
- [ ] 3.3: Fix Citadel exec() with AST whitelist
- [ ] 3.4: Remove bare except clauses (2 files)
- [ ] 3.5: Cap JWT revocation cache at 10k entries
- [ ] 4.1: Add curl to apex/apex-ui and ops-intelligence frontends
- [ ] 4.2: Add HEALTHCHECK to B-A-P Dockerfile
- [ ] 4.3: Fix Acropolis health check (use HTTP instead of --version)
- [ ] 4.6: Add database transaction rollback on errors
- [ ] 4.7: Add dispatch idempotency checking

### MEDIUM ISSUES (9) - Operational Excellence
- [ ] 2.8: Safe env var int coercion (wrap in try/except)
- [ ] 4.4: Better Redis connection error handling
- [ ] 4.5: Make DB pool size configurable via env vars
- [ ] 5.1: Add audit log failure tracking
- [ ] 5.2: Add Redis/Auth env vars to integration service (if needed)
- [ ] 5.3: Validate Ops-Intelligence PORT env var
- [ ] 6.1: Document diskcache CVE remediation
- [ ] (Plus 2 more rolled into other categories)

---

## CATEGORY 1: IMPORTS & PATHS (6 FIXES)

### 1.1 Fix Hardcoded Path in Gen-H auth_middleware.py

**Files**: `Gen-H/hvac-lead-generator/auth_middleware.py` (lines 19, 157)

**Current**:
```python
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/shared')
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/apex/apex-agents')
```

**Fix**:
```python
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_shared = os.path.join(_root, 'integration', 'shared')
_apex = os.path.join(_root, 'apex', 'apex-agents')
if _shared not in sys.path:
    sys.path.insert(0, _shared)
if _apex not in sys.path:
    sys.path.insert(0, _apex)
```

**Reference**: `integration/event-bus/event_bus.py:5-12` has same pattern

**Status**: ⚠️ IN PROGRESS (started fixing)

---

### 1.2 Fix Hardcoded Path in apex-agents test

**Files**: `apex/apex-agents/api/test_auth_integration.py` (lines 10-11)

**Current**:
```python
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/shared')
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/apex/apex-agents/api')
```

**Fix**: Same relative-path pattern as 1.1

---

### 1.3-1.6 Create Missing `__init__.py` Files

**Directories**:
- `integration/saga/` → Create empty file
- `integration/gateway/` → Create empty file
- `integration/event-bus/` → Create empty file
- `integration/auth/` → Create empty file
- `integration/services/` → Create empty file
- `Money/schemas/` → Create empty file

**Why**: Python 3.10+ treats directories without `__init__.py` as namespace packages; explicit imports fail.

**Status**: ✅ DONE (committed as `22ec41dc`)

---

## CATEGORY 2: CONFIGURATION & ENV VARIABLES (8 FIXES)

### 2.1 Fix LANGSMITH_API_KEY Placeholder

**File**: `docker-compose.yml:48` (Money service)

**Current**:
```yaml
- LANGSMITH_API_KEY=${LANGSMITH_API_KEY:-placeholder}
```

**Fix**:
```yaml
- LANGSMITH_API_KEY=${LANGSMITH_API_KEY:?LANGSMITH_API_KEY must be set}
```

**Impact**: Service will fail to start if env var not set (fail-closed behavior)

---

### 2.2 Fix EVENT_BUS_API_KEY Placeholder

**File**: `docker-compose.yml:418` (ops-intelligence-backend service)

**Current**:
```yaml
- EVENT_BUS_API_KEY=${EVENT_BUS_API_KEY:-change-me-event-bus-api-key}
```

**Fix**:
```yaml
- EVENT_BUS_API_KEY=${EVENT_BUS_API_KEY:?EVENT_BUS_API_KEY must be set}
```

---

### 2.3 Fix JWT_SECRET Placeholder

**File**: `docker-compose.yml:419` (ops-intelligence-backend service)

**Current**:
```yaml
- JWT_SECRET=${JWT_SECRET:-change-in-production}
```

**Fix**:
```yaml
- JWT_SECRET=${JWT_SECRET:?JWT_SECRET must be set}
```

---

### 2.4 Fix ENVIRONMENT vs ENV Variable Mismatch

**Files**: 5 files (all byte-for-byte identical):
- `shared/security_middleware.py:58,322`
- `Money/security_middleware.py:58,322`
- `FinOps360/security_middleware.py:58,322`
- `ComplianceOne/security_middleware.py:58,322`
- `orchestrator/security_middleware.py:58,322`

**Issue**: Code checks `os.getenv('ENVIRONMENT')` but docker-compose sets `ENV=production`

**Current** (line 58):
```python
if os.getenv('ENVIRONMENT') in ['staging', 'production']:
    response.headers['Strict-Transport-Security'] = ...
```

**Fix**:
```python
if os.getenv('ENV', '').lower() in ['staging', 'production']:
    response.headers['Strict-Transport-Security'] = ...
```

**Also line 322**: Same change in `validate_production_config()` function

**Impact**: HSTS headers never set in production without this fix

---

### 2.5 Fix REDIS_PASSWORD Defaults to None

**File**: `integration/event-bus/event_bus.py:33`

**Current**:
```python
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
```

**Fix**:
```python
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
if not REDIS_PASSWORD:
    raise RuntimeError(
        "REDIS_PASSWORD environment variable must be set. "
        "Redis requires authentication (docker-compose enforces requirepass)."
    )
```

**Impact**: Event bus won't fail silently on missing password

---

### 2.6 Harden DISPATCH_API_KEY Validation

**File**: `Money/config.py:41`

**Current**:
```python
DISPATCH_API_KEY: str = os.environ.get("DISPATCH_API_KEY", "")
```

**Fix** (matching `integration/auth/auth_server.py:41-42` pattern):
```python
DISPATCH_API_KEY: str = os.environ.get("DISPATCH_API_KEY", "")
if not DISPATCH_API_KEY or len(DISPATCH_API_KEY) < 32:
    raise RuntimeError(
        "DISPATCH_API_KEY must be at least 32 characters. "
        "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
```

---

### 2.7 Add JWT Secret Length Validation in Gen-H

**File**: `Gen-H/hvac-lead-generator/auth_middleware.py:29`

**Current**:
```python
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
```

**Fix**:
```python
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if JWT_SECRET_KEY and len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters for security")
```

---

### 2.8 Safe Env Var int() Coercion

**Files**: Multiple (e.g., `orchestrator/main.py:44`, `integration/auth/auth_server.py:44`)

**Current**:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
```

**Fix**:
```python
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
except ValueError:
    raise RuntimeError(
        "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES must be an integer, got: "
        f"{os.getenv('AUTH_ACCESS_TOKEN_EXPIRE_MINUTES')}"
    )
```

---

## CATEGORY 3: SECURITY HARDENING (6 FIXES)

### 3.1 Fix CORS Wildcard + Credentials

**File**: `integration/main.py:39-46`

**Current**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Fix** (port from `Money/main.py:216-248`):
```python
# Parse CORS origins from environment
_cors_raw = os.environ.get("CORS_ORIGINS", "")
if not _cors_raw:
    _cors_origins = ["http://localhost:5173", "http://localhost:3000"]  # dev defaults
else:
    _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["x-api-key", "content-type", "authorization"],
    expose_headers=["x-ratelimit-limit"],
    max_age=3600,
)
```

**Impact**: Prevents CORS credential theft

---

### 3.2 Fix Rate Limiter Thread Safety

**File**: `shared/security_middleware.py:71-127` (+ 4 duplicate copies)

**Issue**: `self._local` dict modified without locking on line 120-123

**Current** (lines 120-123):
```python
self._local = {k: v for k, v in self._local.items() if any(...)}
if len(self._local) > self._local_max_ips:
    sorted_ips = sorted(self._local.keys(), ...)
    for old_ip in sorted_ips[:...]:
        del self._local[old_ip]  # ← NOT THREAD-SAFE
```

**Fix**:

1. Add to `__init__` method:
```python
import threading
self._lock = threading.Lock()
```

2. Wrap `_check_local` method:
```python
def _check_local(self, ip: str, now: float) -> bool:
    with self._lock:
        window_start = now - 60
        # Clean old entries
        self._local = {
            k: v for k, v in self._local.items()
            if any(t > window_start for t in v)
        }
        # Evict oldest IPs if needed
        if len(self._local) > self._local_max_ips:
            sorted_ips = sorted(
                self._local.keys(),
                key=lambda k: min(self._local[k]) if self._local[k] else 0
            )
            for old_ip in sorted_ips[:len(self._local) - self._local_max_ips]:
                del self._local[old_ip]
        
        bucket = self._local.setdefault(ip, [])
        self._local[ip] = [t for t in bucket if t > window_start]
        self._local[ip].append(now)
        return len(self._local[ip]) > self.requests_per_minute
```

**Apply to**: All 5 files (shared + 4 service copies)

---

### 3.3 Fix Citadel exec() with AST Whitelist

**File**: `Citadel/desktop_gui.py:329`

**Current**:
```python
def run_script(self, script: str) -> str:
    """Executes user-provided Python code that references `driver`."""
    local_vars = {"driver": self.driver}
    try:
        exec(script, {}, local_vars)
        return "✅ Selenium script executed."
    except Exception as e:
        return f"❌ {e}"
```

**Fix** (AST-based whitelist):
```python
import ast

def run_script(self, script: str) -> str:
    """Execute whitelisted Selenium driver method calls only."""
    try:
        tree = ast.parse(script)
        
        # Whitelist: only allow driver.method(...) calls
        for node in ast.walk(tree):
            # Only allow Expr nodes containing Call nodes
            if isinstance(node, ast.Expr):
                if not isinstance(node.value, ast.Call):
                    raise SyntaxError("Only function calls allowed")
                call = node.value
                # Verify call is on driver object
                if not (isinstance(call.func, ast.Attribute) and
                        isinstance(call.func.value, ast.Name) and
                        call.func.value.id == 'driver'):
                    raise SyntaxError(
                        f"Only driver.method(...) calls allowed, got: {ast.unparse(call)}"
                    )
            elif isinstance(node, (ast.Module, ast.Expr, ast.Call, ast.Attribute, 
                                   ast.Name, ast.Constant, ast.List, ast.Tuple)):
                continue  # Allowed nodes
            else:
                raise SyntaxError(
                    f"Not allowed in script: {node.__class__.__name__}"
                )
        
        # Execute only whitelisted code
        local_vars = {"driver": self.driver}
        exec(compile(tree, '<script>', 'exec'), {}, local_vars)
        return "✅ Selenium script executed."
    except SyntaxError as e:
        return f"❌ Script rejected: {e}"
    except Exception as e:
        return f"❌ Execution error: {e}"
```

**Impact**: Prevents arbitrary Python execution while allowing Selenium driver calls

---

### 3.4 Remove Bare except Clauses

**File 1**: `integration/gateway/test_gateway_properties.py:38`

**Current**:
```python
except:
    is_valid = False
```

**Fix**:
```python
except Exception as e:
    is_valid = False
    logging.error(f"Validation error: {e}")
```

**File 2**: `scripts/health_check.py:192`

Same pattern - replace `except:` with `except Exception as e:` + logging

---

### 3.5 Cap JWT Revocation Cache

**File**: `integration/shared/jwt_validator.py:73-79`

**Current**:
```python
self._cache = {}  # Unbounded growth!
```

**Fix** (using OrderedDict for LRU):
```python
from collections import OrderedDict

class JWTValidator:
    MAX_CACHE_SIZE = 10_000
    
    def __init__(self):
        self._cache = OrderedDict()  # For LRU eviction
        self._cache_lock = threading.Lock()
    
    def _cache_get(self, key):
        with self._cache_lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                return self._cache[key]
            return None
    
    def _cache_set(self, key, value):
        with self._cache_lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            # Evict oldest if over limit
            while len(self._cache) > self.MAX_CACHE_SIZE:
                self._cache.popitem(last=False)
```

---

## CATEGORY 4: RELIABILITY & RESOURCES (7 FIXES)

### 4.1 Add curl to Frontend Dockerfiles

**Files**:
- `apex/apex-ui/Dockerfile`
- `ops-intelligence/frontend/Dockerfile`

**Current**: No curl in apt-get install

**Fix**: Add to Dockerfile RUN command:
```dockerfile
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

---

### 4.2 Add HEALTHCHECK to B-A-P Dockerfile

**File**: `B-A-P/Dockerfile` (curl already installed on line 8)

**Fix**: Add before CMD:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

---

### 4.3 Fix Acropolis Health Check

**File**: `docker-compose.yml:596-602`

**Current**:
```yaml
healthcheck:
  test:
  - CMD
  - acropolis-cli
  - --version
```

**Fix**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

### 4.4 Better Redis Connection Error Handling

**File**: `orchestrator/main.py:287-293`

**Current**:
```python
except Exception as e:
    print(f"⚠️  Redis unavailable ({e}) -- scale intents will be local-only")
    self._redis = None
```

**Fix**:
```python
except Exception as e:
    logger.error("redis_connection_failed", error=str(e), fallback="local_only")
    # Expose via metrics
    self._redis_unavailable_counter.inc()
    self._redis = None
```

---

### 4.5 Make DB Pool Size Configurable

**File**: `Money/database.py:41`

**Current**:
```python
_pool = pool.ThreadedConnectionPool(1, 20, dsn=db_url)
```

**Fix**:
```python
_db_pool_min = int(os.getenv("DB_POOL_MIN", "1"))
_db_pool_max = int(os.getenv("DB_POOL_MAX", "20"))
_pool = pool.ThreadedConnectionPool(_db_pool_min, _db_pool_max, dsn=db_url)
logger.info(f"Database pool initialized: {_db_pool_min}-{_db_pool_max} connections")
```

---

### 4.6 Add Database Transaction Rollback

**File**: `Money/database.py` (save_dispatch, update_dispatch_status, etc.)

**Current**:
```python
cursor.execute(...)
conn.commit()
```

**Fix**:
```python
try:
    cursor.execute(...)
    conn.commit()
except psycopg2.Error as e:
    conn.rollback()
    logger.error(f"Database transaction failed: {e}")
    raise HTTPException(status_code=503, detail="Database error")
```

---

### 4.7 Add Dispatch Idempotency

**File**: `Money/database.py` save_dispatch function

**Current**: Just uses `ON CONFLICT (dispatch_id) DO UPDATE`

**Fix**: Add idempotency validation:

1. Add `idempotency_key` column to dispatches table
2. Add unique index: `CREATE UNIQUE INDEX IF NOT EXISTS idx_idempotency_key ON dispatches(idempotency_key) WHERE idempotency_key IS NOT NULL`
3. In save_dispatch:
```python
cursor.execute("""
    INSERT INTO dispatches (dispatch_id, idempotency_key, ...)
    VALUES (%s, %s, ...)
    ON CONFLICT (dispatch_id) DO NOTHING
    RETURNING dispatch_id;
""", (dispatch_id, idempotency_key, ...))

result = cursor.fetchone()
if not result:
    # Duplicate detected - return existing
    cursor.execute("SELECT * FROM dispatches WHERE dispatch_id = %s", (dispatch_id,))
    return cursor.fetchone()
```

---

## CATEGORY 5: OPERATIONAL CORRECTNESS (3 FIXES)

### 5.1 Add Audit Log Failure Tracking

**File**: `integration/auth/auth_server.py` (background tasks)

**Current**:
```python
background_tasks.add_task(emit_audit, ...)
```

**Fix**:
```python
from prometheus_client import Counter

audit_log_failures = Counter('audit_log_failures_total', 'Failed audit log emissions')

async def safe_emit_audit(event_type, data, user_id=None):
    try:
        await emit_audit(event_type, data, user_id)
    except Exception as e:
        logger.error(f"Audit log emission failed: {e}")
        audit_log_failures.inc()

background_tasks.add_task(safe_emit_audit, event_type, data)
```

---

### 5.2 Verify Integration Service Redis Config (if needed)

**File**: `docker-compose.yml:146-184` (integration service)

**Check**: Does integration/main.py use Redis? If yes, add:
```yaml
environment:
  - REDIS_URL=redis://:${REDIS_PASSWORD:?REDIS_PASSWORD must be set}@redis:6379
  - AUTH_SECRET_KEY=${AUTH_SECRET_KEY:?AUTH_SECRET_KEY must be set}
```

If no Redis usage, skip this fix.

---

### 5.3 Validate Ops-Intelligence PORT

**File**: `ops-intelligence/backend/main.py`

**Current**: Hardcoded fallback or no validation

**Fix**:
```python
PORT = int(os.getenv("PORT"))  # Remove default; fail if unset
if PORT < 1 or PORT > 65535:
    raise ValueError(f"PORT must be 1-65535, got {PORT}")
```

---

## CATEGORY 6: DOCUMENTATION & HYGIENE (1 FIX)

### 6.1 Document diskcache CVE

**File**: `Money/requirements.txt:39`

**Current**:
```
diskcache>=5.6.3  # CVE-2025-69872
```

**Fix**:
```
diskcache>=5.6.3  # CVE-2025-69872 — monitor for patched version; upgrade when available (https://github.com/grantjenks/python-diskcache/issues/...)
```

Or if fixed version available:
```
diskcache>=5.6.4  # CVE-2025-69872 fixed in 5.6.4+
```

---

## IMPLEMENTATION CHECKLIST

**Phase 1: Unblock Core** (15 mins)
- [x] Create __init__.py files
- [ ] Fix hardcoded paths (Gen-H, apex-agents)
- [ ] Create placeholder secrets in docker-compose

**Phase 2: Security** (60 mins)
- [ ] Fix ENV/ENVIRONMENT (5 files)
- [ ] Fix CORS wildcard
- [ ] Fix rate limiter threading
- [ ] Sandbox Citadel exec()
- [ ] Remove bare excepts

**Phase 3: Reliability** (90 mins)
- [ ] Fix REDIS_PASSWORD
- [ ] Add Dockerfile curl installs
- [ ] Fix health checks
- [ ] Add transaction rollback
- [ ] Make DB pool configurable

**Phase 4: Polish** (45 mins)
- [ ] JWT validation tightening
- [ ] Audit log safety
- [ ] CVE documentation
- [ ] Update AUDIT_REPORT.md checklist

---

## VERIFICATION

After each category:

```bash
# Static validation
docker compose config > /dev/null

# Python imports
python -c "from integration.saga import saga_orchestrator"
python -c "from integration.auth import auth_server"

# Start services
./scripts/deploy.sh local

# Health check
./scripts/health_check.py -v

# Integration tests
./scripts/verify_integration.py
```

---

## COMMIT STRATEGY

Each fix = 1 focused commit. Format:
```
fix(category): brief description [#N.N]

Detailed explanation of what changed and why.
Fixes audit finding #N.N from AUDIT_REPORT.md.

https://claude.ai/code/session_015vBVRAiajCJ1m1dc3updK5
```

Example:
```
fix(config): enforce REDIS_PASSWORD at startup [2.5]

Previously REDIS_PASSWORD defaulted to None, causing silent
connection failures in production. Now raises RuntimeError
if unset in environments where Redis requires authentication.

Matches pattern used by other services.
```

---

## FINAL STEPS

1. All 31 fixes committed to `claude/audit-system-bugs-kq85v`
2. Push to origin
3. PR #1 updated with checklist showing 31/31 complete
4. Remove draft status from PR
5. Ready for team review

**Estimated total time**: 40-60 hours
**Estimated review time**: 2-3 hours
