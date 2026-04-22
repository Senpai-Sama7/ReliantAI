# Citadel → ReliantAI HVAC Component Analysis

**Date:** 2026-03-04  
**Analyst:** AI Systems Architect  
**Source:** `/home/donovan/Projects/AI/citadel_ultimate_a_plus`  
**Target:** `/home/donovan/Projects/AI/Money` (ReliantAI HVAC Dispatch)

---

## Executive Summary

Citadel is a **lead generation and outbound outreach engine** for local service businesses. It scouts websites, qualifies leads, generates personalized outreach, and tracks pipeline state. While its primary use case is outbound sales (selling to HVAC companies), many of its architectural components can significantly enhance the ReliantAI HVAC Dispatch system.

### Reuse Potential: **HIGH**

| Component | Reuse Value | Effort | Priority |
|-----------|-------------|--------|----------|
| Lead State Machine | High | Medium | P1 |
| Dashboard Metrics API | High | Low | P1 |
| Webhook Security (HMAC) | High | Low | P1 |
| JSON Schema Validation | Medium | Low | P2 |
| Rate Limiting | Medium | Low | P2 |
| Event Sourcing | Medium | Medium | P2 |
| 7-Beat Response Model | High | Low | P1 |
| Market Intelligence | Low | Medium | P3 |

---

## 1. Lead State Machine (`lead_queue.py`)

### What It Does
Citadel implements a sophisticated state machine for lead pipeline management:

```python
PIPELINE_STATES = (
    "scouted",      # Initial discovery
    "qualified",    # Meets criteria
    "built",        # Assets generated
    "approved",     # Human approved
    "deployed",     # Live/deployed
    "emailed",      # Outreach sent
    "replied",      # Prospect responded
    "disqualified", # Terminal: rejected
)

VALID_TRANSITIONS = {
    "scouted": {"qualified", "disqualified"},
    "qualified": {"built", "disqualified"},
    "built": {"approved", "disqualified"},
    "approved": {"deployed", "disqualified"},
    "deployed": {"emailed", "disqualified"},
    "emailed": {"replied"},
    "replied": set(),           # Terminal
    "disqualified": set(),      # Terminal
}
```

### How It Applies to ReliantAI HVAC

**Current ReliantAI dispatch states:**
- `queued` → `assigned` → `dispatched` → `complete`

**Enhanced state machine for HVAC dispatch:**
```python
DISPATCH_STATES = (
    "received",        # Initial contact (SMS/WhatsApp/Email)
    "triaged",         # Urgency assessed
    "qualified",       # Address/service confirmed
    "scheduled",       # Time slot proposed
    "confirmed",       # Customer confirmed
    "dispatched",      # Tech assigned & en route
    "arrived",         # Tech on-site
    "in_progress",     # Work being done
    "completed",       # Job finished
    "followed_up",     # Post-service check
    "cancelled",       # Terminal: cancelled
    "escalated",       # Terminal: safety issue
)
```

**Benefits:**
- More granular tracking of dispatch lifecycle
- Better analytics on where dispatches get stuck
- Event sourcing for audit trails

### Implementation Notes
```python
# From lead_queue.py - reusable components:
- @contextmanager tx(): SQLite transaction handling with WAL
- upsert_lead(): Insert or update with conflict resolution
- transition(): Enforce valid state transitions
- record_event(): Audit trail logging
- funnel_counts(): Pipeline analytics
```

---

## 2. Dashboard Metrics API (`dashboard_app.py`)

### What It Does
Citadel's dashboard provides comprehensive operational metrics:

| Endpoint | Data |
|----------|------|
| `/api/funnel` | Pipeline state counts |
| `/api/verticals` | Conversion by vertical |
| `/api/leads` | Lead list with status |
| `/api/economics` | Revenue/deal summary |
| `/api/beat-compliance` | Outreach quality scores |
| `/api/lead/{slug}/timeline` | Full event history |

### How It Applies to ReliantAI HVAC

**New endpoints for HVAC dispatch dashboard:**
```python
GET /api/dispatch/funnel        # Dispatch state distribution
GET /api/dispatch/urgency       # Breakdown by urgency level
GET /api/dispatch/response-time # Average time to dispatch
GET /api/dispatch/tech-performance # Per-tech completion rates
GET /api/dispatch/lead-source   # SMS vs WhatsApp vs Sales Intel
GET /api/dispatch/economics     # Revenue per dispatch type
GET /api/dispatch/{id}/timeline # Full event history
```

**Key metrics to track:**
- Emergency response time (goal: < 15 min)
- Standard dispatch time (goal: < 2 hours)
- Completion rate by tech
- Customer satisfaction by dispatch type
- Lead source effectiveness

### Implementation Notes
```python
# Reusable patterns from dashboard_app.py:
- Rate limiting with sliding window
- API key authentication
- CORS middleware configuration
- Health check endpoint pattern
- JSON response standardization
```

---

## 3. Webhook Security (HMAC-SHA256)

### What Citadel Has
```python
def verify_webhook_signature(raw_body: bytes, timestamp_header: str, signature_header: str) -> None:
    # HMAC-SHA256 verification
    # Timestamp skew enforcement (5 min default)
    # Format: HMAC_SHA256(secret, "{timestamp}.{raw_body}")
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"), 
        f"{ts}.".encode("utf-8") + raw_body, 
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(sent, expected):
        raise HTTPException(status_code=401, detail="Signature mismatch")
```

### Current ReliantAI Implementation
```python
# Current (basic):
if payload.get("webhook_secret") != expected_secret:
    return False
```

### Recommended Upgrade
```python
# Enhanced (Citadel-style):
def verify_webhook_signature(
    raw_body: bytes,
    timestamp_header: str,
    signature_header: str,
    secret: str,
    max_skew_seconds: int = 300
) -> bool:
    """
    Verify webhook using HMAC-SHA256 with timestamp.
    Format: sha256=HMAC(secret, "{timestamp}.{body}")
    """
    # 1. Parse timestamp
    ts = int(timestamp_header)
    
    # 2. Check timestamp skew (prevent replay attacks)
    if abs(time.time() - ts) > max_skew_seconds:
        return False
    
    # 3. Extract signature
    if not signature_header.startswith("sha256="):
        return False
    sent_sig = signature_header.split("=", 1)[1]
    
    # 4. Compute expected signature
    expected = hmac.new(
        secret.encode(),
        f"{ts}.".encode() + raw_body,
        hashlib.sha256
    ).hexdigest()
    
    # 5. Constant-time comparison
    return hmac.compare_digest(sent_sig, expected)
```

**Benefits:**
- Prevents replay attacks via timestamp
- Prevents signature timing attacks
- Industry standard (Stripe, GitHub, etc.)

---

## 4. JSON Schema Validation

### What Citadel Has
Citadel uses JSON schemas as validation gates at every pipeline stage:

```python
# Schema files:
schemas/qualifier_output.json   # Lead qualification contract
schemas/builder_input.json      # Static site generation input
schemas/build_manifest.json     # Build output summary
schemas/outreach_output.json    # 7-beat email structure

# Runtime validation:
jsonschema.validate(instance=obj, schema=schemas[name])
```

### How It Applies to ReliantAI HVAC

**New schemas for dispatch system:**
```json
// schemas/dispatch_request.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["customer_phone", "issue_summary"],
  "properties": {
    "customer_name": {"type": "string", "maxLength": 100},
    "customer_phone": {"type": "string", "pattern": "^\\+1[0-9]{10}$"},
    "issue_summary": {"type": "string", "minLength": 5, "maxLength": 1000},
    "address": {"type": "string", "maxLength": 200},
    "urgency": {"enum": ["emergency", "high", "standard", "low"]},
    "preferred_time": {"type": "string", "format": "date-time"}
  }
}

// schemas/outreach_response.json (7-beat SMS structure)
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["body", "beat_audit"],
  "properties": {
    "body": {"type": "string", "maxLength": 1600},
    "beat_audit": {
      "type": "object",
      "properties": {
        "acknowledgment": {"type": "boolean"},
        "urgency_confirmation": {"type": "boolean"},
        "next_steps": {"type": "boolean"},
        "eta_provided": {"type": "boolean"}
      }
    }
  }
}
```

---

## 5. Rate Limiting Implementation

### What Citadel Has
```python
_rate_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
_rate_lock = threading.Lock()

def _check_rate(ip: str, scope: str, limit: int) -> None:
    """Sliding window rate limiter per IP."""
    if limit <= 0:
        return
    now = time.time()
    cutoff = now - 60
    key = (ip, scope)
    with _rate_lock:
        bucket = _rate_buckets[key]
        _rate_buckets[key] = [t for t in bucket if t > cutoff]
        if len(_rate_buckets[key]) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        _rate_buckets[key].append(now)
```

### Current ReliantAI Implementation
```python
# Current (simplistic):
rate_limit_store: dict[str, float] = {}
if now_time - last_hit < 5.0:
    return _twiml_response("")
```

### Recommended Upgrade
```python
# Enhanced (Citadel-style sliding window):
class RateLimiter:
    def __init__(self, default_limit: int = 60, window_seconds: int = 60):
        self.buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
        self.lock = threading.Lock()
        self.default_limit = default_limit
        self.window = window_seconds
    
    def check(self, key: str, scope: str = "default", limit: Optional[int] = None) -> bool:
        """Check if request is within rate limit."""
        limit = limit or self.default_limit
        now = time.time()
        cutoff = now - self.window
        
        with self.lock:
            bucket = self.buckets[(key, scope)]
            # Prune old entries
            self.buckets[(key, scope)] = [t for t in bucket if t > cutoff]
            # Check limit
            if len(self.buckets[(key, scope)]) >= limit:
                return False
            self.buckets[(key, scope)].append(now)
            return True

# Usage:
rate_limiter = RateLimiter()

@app.post("/sms")
async def sms_webhook(request: Request, From: str = Form(...)):
    if not rate_limiter.check(From, "sms", limit=5):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    # ...
```

---

## 6. Event Sourcing Pattern

### What Citadel Has
Every state transition creates an immutable event record:

```python
CREATE TABLE lead_events (
    id           INTEGER PRIMARY KEY,
    lead_id      INTEGER NOT NULL,
    event_type   TEXT    NOT NULL,
    from_status  TEXT,
    to_status    TEXT,
    actor        TEXT    NOT NULL,
    run_id       TEXT,
    payload_json TEXT    NOT NULL DEFAULT '{}',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

### How It Applies to ReliantAI HVAC

**Enhanced events table:**
```sql
CREATE TABLE dispatch_events (
    id              INTEGER PRIMARY KEY,
    dispatch_id     TEXT    NOT NULL,
    event_type      TEXT    NOT NULL,  -- 'received', 'triaged', 'assigned', etc.
    from_status     TEXT,
    to_status       TEXT,
    actor           TEXT    NOT NULL,  -- 'system', 'customer', 'tech_name'
    payload_json    TEXT,              -- {temperature, urgency_score, etc.}
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

**Benefits:**
- Complete audit trail for compliance
- Debuggability: trace exactly what happened
- Analytics: time-in-state metrics
- Replay capability for testing

---

## 7. The 7-Beat Outreach Model

### What Citadel Has
Every outreach draft follows a proven 7-beat structure:

| Beat | Purpose | Example |
|------|---------|---------|
| 1. Pattern Break | Stop the scroll | "Your emergency page doesn't have a click-to-call button" |
| 2. Cost of Inaction | Quantify doing nothing | "$3K–$6K/month in lost calls" |
| 3. Belief Shift | Challenge assumption | "Shared leads aren't cheaper" |
| 4. Mechanism | How it works | "We find businesses that need you" |
| 5. Proof Unit | Evidence | "14 replies from 147 contacts" |
| 6. Offer | What they get | "$1,500/mo, no contract" |
| 7. Action | Next step | "Reply for a 2-min video" |

### How It Applies to ReliantAI HVAC (SMS/WhatsApp Responses)

**Current ReliantAI response:**
```
"Thanks for contacting Houston HVAC AI! We're processing your request..."
```

**Enhanced 4-beat SMS response:**
```
Beat 1 (Acknowledge): "Got it — AC not working in this heat is urgent."
Beat 2 (Confirm): "Emergency dispatch flagged for Houston area."
Beat 3 (Next Steps): "Checking tech availability now..."  
Beat 4 (CTA): "Reply CONFIRM to lock in priority queue."
```

**Benefits:**
- More professional, structured responses
- Higher customer confidence
- Consistent brand voice
- Can be validated via schema

---

## 8. Market Intelligence (Census Ranker)

### What It Does
Pulls US Census Bureau data to rank target markets by business density:

```python
# Fetches establishment counts by NAICS code
fetch_establishments(naics="238220", state_fips="48", county_fips="201")  # HVAC
# Returns: 1,247 establishments in Harris County, TX
```

### Potential Use for ReliantAI HVAC

**Limited direct applicability** — ReliantAI is a dispatch system, not a lead gen system. However:

**Could be used for:**
1. **Market expansion planning**: "Where should we launch next?"
2. **Tech density optimization**: Match tech coverage to business density
3. **Sales intelligence integration**: Your Sales Intel system could use this

**Not recommended for core dispatch system.**

---

## Implementation Priority Matrix

### P1: Immediate Value, Low Effort

| Component | File | Lines | Action |
|-----------|------|-------|--------|
| HMAC Webhook Security | `integrations/webhook_security.py` | ~50 | New file |
| 7-Beat Response Model | `config.py` (RESPONSE_TEMPLATES) | ~30 | Add templates |
| Dashboard Metrics API | `main.py` (new endpoints) | ~100 | Add routes |

### P2: Medium Value, Medium Effort

| Component | File | Lines | Action |
|-----------|------|-------|--------|
| Enhanced State Machine | `database.py` (refactor) | ~200 | Update schema |
| JSON Schema Validation | `schemas/` (new dir) | ~150 | New schemas |
| Sliding Window Rate Limit | `main.py` (refactor) | ~50 | Replace existing |
| Event Sourcing | `database.py` (add table) | ~50 | Add events table |

### P3: Future Consideration

| Component | File | Action |
|-----------|------|--------|
| Census Market Ranker | N/A | Not applicable to dispatch |
| Static Site Builder | N/A | Out of scope |
| Email Outreach | N/A | Out of scope |

---

## Direct Code Reuse Candidates

### 1. Webhook Signature Verification (`tests/conftest.py`)
```python
# Can copy-paste directly:
def sign_webhook(secret: str, payload: dict) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode("utf-8"), f"{ts}.".encode("utf-8") + raw, hashlib.sha256).hexdigest()
    return raw, {
        "X-Citadel-Timestamp": ts,
        "X-Citadel-Signature": f"sha256={sig}",
        "Content-Type": "application/json",
    }
```

### 2. SQLite Transaction Context Manager (`lead_queue.py`)
```python
# Can adapt directly:
@contextmanager
def tx(self) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(self.db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=5000")
    con.execute("PRAGMA synchronous=NORMAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
```

### 3. Rate Limiting (`dashboard_app.py`)
```python
# Can copy-paste with minor adaptations:
_rate_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
_rate_lock = threading.Lock()

def _check_rate(ip: str, scope: str, limit: int) -> None:
    if limit <= 0:
        return
    now = time.time()
    cutoff = now - 60
    key = (ip, scope)
    with _rate_lock:
        bucket = _rate_buckets[key]
        _rate_buckets[key] = [t for t in bucket if t > cutoff]
        if len(_rate_buckets[key]) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        _rate_buckets[key].append(now)
```

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ReliantAI HVAC Dispatch                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Current    │◄──►│   Citadel    │◄──►│   Enhanced   │      │
│  │   Features   │    │  Components  │    │   Features   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
│  • SMS/Webhooks      • HMAC Security     • Audit Trail          │
│  • CrewAI Dispatch   • State Machine     • Metrics Dashboard    │
│  • SQLite DB         • Rate Limiting     • 7-Beat Responses     │
│  • Twilio SMS        • Event Sourcing    • Schema Validation    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recommended Next Steps

1. **Immediate (This Week):**
   - Copy HMAC webhook verification to secure Make.com webhooks
   - Implement 7-beat response templates for SMS

2. **Short Term (Next 2 Weeks):**
   - Add dashboard metrics endpoints (`/api/dispatch/*`)
   - Implement enhanced state machine with event sourcing
   - Add JSON schema validation for dispatch requests

3. **Medium Term (Next Month):**
   - Replace simple rate limiting with sliding window
   - Build comprehensive analytics dashboard
   - Add per-tech performance tracking

---

## Conclusion

Citadel contains **significant architectural value** that can elevate ReliantAI HVAC from a functional dispatch system to a professional-grade operations platform. The state machine, event sourcing, and security patterns are battle-tested and production-ready.

**Estimated code reuse:** 500-800 lines (mostly security, validation, and analytics patterns)

**Estimated development time savings:** 2-3 weeks

**Risk level:** Low — all components are modular and can be adopted incrementally.
