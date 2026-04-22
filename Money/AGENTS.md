# AGENTS.md — Houston HVAC AI Dispatch

This file provides comprehensive guidance to AI coding assistants when working with code in this repository.

---

## Project Overview

**Houston HVAC AI Dispatch** is a production-grade, multi-agent system that autonomously triages incoming HVAC service requests and dispatches technicians via SMS/WhatsApp. Built for Houston-area HVAC shops to capture after-hours leads and respond within seconds (vs. 24-48 hour industry average).

**Core Value Proposition:** Harvard Business Review research shows leads contacted within 60 minutes are 7× more likely to qualify. Most HVAC shops respond in 24–48 hours. This system responds in seconds.

## Hostile Audit Persistence

- Append every hostile-audit checkpoint and verification result to the root `PROGRESS_TRACKER.md`.
- Do not mark webhook, admin-auth, or dashboard fixes complete without real pytest output, health checks, browser proof, or request/response artifacts saved under `proof/hostile-audit/<timestamp>/`.
- Reproduce before patching. If the original exploit method fails, preserve that failed path in the notes and record the method that actually reproduced or disproved the issue.
- Keep admin auth on backend session cookies; do not reintroduce browser-stored bearer/API secrets.
- If a scanner or service cannot run, record the exact blocker and fallback review path instead of implying success.

**Request Flow:**

```
Customer SMS/WhatsApp → Twilio webhook → Safety Gate (always runs)
                                              ↓ (if safe)
                        ┌─────────────────────────────────────────┐
                        │  CrewAI 5-Agent Chain (via Gemini LLM) │
                        │  triage → intake → schedule → dispatch │
                        │  → followup                            │
                        └─────────────────────────────────────────┘
                                              ↓ (fallback if AI fails)
                        Local Triage Engine (keyword + temperature)
                                              ↓
                        SQLite persistence + SMS to tech & customer
```

---

## Technology Stack

| Layer                | Technology            | Purpose                                           |
| -------------------- | --------------------- | ------------------------------------------------- |
| **Web Framework**    | FastAPI               | Async webhooks, REST API, admin dashboard         |
| **AI Orchestration** | CrewAI                | 5-agent sequential workflow                       |
| **LLM**              | Gemini 3.1 Flash      | Deterministic triage (temperature=0.0)            |
| **Messaging**        | Twilio                | SMS/WhatsApp inbound/outbound                     |
| **Calendar**         | Composio              | Google Calendar integration for tech availability |
| **Database**         | SQLite (WAL mode)     | Zero-external-dependency persistence              |
| **Frontend**         | Jinja2 + Tailwind CSS | Admin dashboard                                   |
| **Tracing**          | LangSmith             | Optional AI workflow tracing                      |
| **Testing**          | pytest + rich         | 91 automated tests                                |

**Python Version:** 3.11+ (tested on 3.13)

---

## Project Structure

```
├── main.py                    # FastAPI server — webhooks, API, admin dashboard
├── hvac_dispatch_crew.py      # CrewAI 5-agent orchestration (lazy-loaded)
├── triage.py                  # Zero-AI fallback triage engine
├── database.py                # SQLite persistence layer (WAL mode)
├── config.py                  # Centralized config — load this FIRST
├── openclaw_integration.py    # OpenClaw automation integration helpers
│
├── templates/
│   ├── admin.html             # Admin dashboard (Jinja2 + Tailwind)
│   └── login.html             # Admin login page
│
├── tests/
│   ├── conftest.py            # Shared pytest fixtures
│   ├── test_triage.py         # 50+ Houston HVAC triage scenarios
│   ├── test_api.py            # Endpoint tests (19 tests)
│   ├── test_database.py       # CRUD + concurrency tests (9 tests)
│   └── test_security.py       # Auth, XSS, rate limiting (12 tests)
│
├── tools/
│   ├── test_suite.py          # Legacy scenario validation with rich UI
│   ├── e2e_test.sh            # End-to-end smoke test script
│   ├── roi_calculator.py      # Business ROI calculations
│   ├── smoke_test_neural.py   # Gemini connectivity smoke test
│   └── test_component_security.py  # Security component tests
│
├── docs/
│   ├── credential_setup.md    # Step-by-step credential setup
│   ├── deployment_guide.md    # Render.com deployment instructions
│   ├── USER_MANUAL.md         # End-user documentation
│   └── ...                    # Additional documentation
│
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container build (Python 3.11-slim)
├── render.yaml                # Render.com Infrastructure-as-Code
├── .env.example               # Environment variable template
└── hvac_dispatch.log          # Application logs (auto-created)
```

---

## Critical Files Reference

### `main.py`

- **Purpose:** FastAPI application entry point
- **Key Endpoints:**
  - `POST /sms` — Twilio SMS webhook
  - `POST /whatsapp` — Twilio WhatsApp webhook
  - `POST /dispatch` — API-driven dispatch (JSON body, API key auth)
  - `GET /run/{id}` — Async job status
  - `GET /dispatches` — Recent dispatch history
  - `GET /health` — Liveness probe
  - `GET /admin` — Admin dashboard (session cookie auth)
- **Security:** Rate limiting, Twilio signature validation, API key auth, security headers

### `hvac_dispatch_crew.py`

- **Purpose:** CrewAI multi-agent orchestration
- **5 Agents:**
  1. `triage_agent` — Houston Emergency Triage Specialist
  2. `intake_agent` — Customer Intake Coordinator
  3. `scheduler_agent` — Houston Dispatch Optimizer
  4. `dispatch_agent` — Dispatch Closer & Customer Communicator
  5. `followup_agent` — Post-Dispatch Retention Specialist
- **Lazy Loading:** CrewAI imports happen in `_ensure_agents()` for fast module loading
- **Tools:** `triage_urgency`, `check_tech_availability`, `dispatch_to_tech`, `send_customer_update`, `escalate_to_owner`

### `triage.py`

- **Purpose:** Zero-AI fallback triage engine
- **Key Function:** `triage_urgency_local(description, outdoor_temp_f)`
- **Used By:** `main.py` when CrewAI fails, test suite for validation

### `database.py`

- **Purpose:** SQLite persistence with thread-local connections
- **Tables:** `dispatches`, `messages`
- **WAL Mode:** Enabled for better concurrent write performance
- **Key Functions:** `save_dispatch()`, `update_dispatch_status()`, `get_dispatch()`, `get_recent_dispatches()`, `log_message()`

### `config.py`

- **Purpose:** Centralized configuration — **ALWAYS import this first**
- **Loads:** `.env` file from project root
- **Validates:** Required environment variables (fails fast if missing)
- **Exports:** Constants (keywords, thresholds, Houston zones, LLM config)

---

## Development Commands

### Setup

```bash
# Copy environment template and fill in your keys
cp .env.example .env
# Edit .env with: GEMINI_API_KEY, TWILIO_SID, TWILIO_TOKEN, etc.

# Install dependencies
python3 -m pip install -r requirements.txt
```

### Testing

```bash
# Full test suite (91 tests) — no API keys required
.venv/bin/python -m pytest tests/ -v

# Specific test modules
.venv/bin/python -m pytest tests/test_triage.py -v
.venv/bin/python -m pytest tests/test_api.py -v
.venv/bin/python -m pytest tests/test_security.py -v

# Legacy scenario validation with rich UI
python3 tools/test_suite.py

# Security component tests
.venv/bin/python -m pytest tools/test_component_security.py -v

# End-to-end smoke test (requires running server)
bash tools/e2e_test.sh
```

### Running Locally

```bash
# Development server
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Production mode
ENV=production .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Admin dashboard at http://127.0.0.1:8000/admin
# Default login: admin / {DISPATCH_API_KEY value}
```

### Docker

```bash
# Build image
docker build -t hvac-dispatch .

# Run container
docker run --env-file .env -p 8000:8000 hvac-dispatch
```

### CLI Testing

```bash
# Direct CrewAI test (requires valid GEMINI_API_KEY)
.venv/bin/python hvac_dispatch_crew.py --message "AC broken, 102 degrees" --temp 102
```

---

## Configuration

### Required Environment Variables

| Variable            | Description                             | Source                 |
| ------------------- | --------------------------------------- | ---------------------- |
| `GEMINI_API_KEY`    | Gemini LLM API key                      | aistudio.google.com    |
| `LANGSMITH_API_KEY` | LangSmith tracing key                   | smith.langchain.com    |
| `TWILIO_SID`        | Twilio Account SID                      | console.twilio.com     |
| `TWILIO_TOKEN`      | Twilio Auth Token                       | console.twilio.com     |
| `TWILIO_FROM_PHONE` | Twilio phone number (+1 format)         | Twilio console         |
| `OWNER_PHONE`       | Owner phone for escalations (+1 format) | Your phone             |
| `TECH_PHONE_NUMBER` | Default technician phone (+1 format)    | Tech phone             |
| `COMPOSIO_API_KEY`  | Composio API key                        | app.composio.dev       |
| `DISPATCH_API_KEY`  | API key for admin/dashboard endpoints   | Generate strong secret |

### Optional Environment Variables

| Variable                 | Default       | Description                           |
| ------------------------ | ------------- | ------------------------------------- |
| `ENV`                    | `dev`         | Set to `production` for live mode     |
| `LOG_LEVEL`              | `INFO`        | `DEBUG`, `INFO`, `WARNING`, `ERROR`   |
| `DATABASE_PATH`          | `dispatch.db` | SQLite database location              |
| `CORS_ORIGINS`           | —             | Comma-separated allowed origins       |
| `SKIP_TWILIO_VALIDATION` | `false`       | Skip Twilio sig validation (dev only) |
| `STUB_TWILIO`            | `false`       | Stub SMS sends (dev/testing)          |

### Houston-Specific Constants (in `config.py`)

```python
# Temperature thresholds for emergency classification
EMERGENCY_HEAT_THRESHOLD_F = 95.0    # AC failure above this = emergency
EMERGENCY_COLD_THRESHOLD_F = 42.0    # Heat failure below this = emergency

# Safety keywords (LIFE_SAFETY escalation)
SAFETY_KEYWORDS = ["gas", "co ", "carbon monoxide", "smoke", "fire", "explosion"]

# Houston service zones
HOUSTON_ZONES = [
    "Katy/West Houston", "Sugar Land/SW Houston", "The Woodlands/North",
    "Heights/Inner Loop", "Pearland/South", "Pasadena/East",
    "Cypress/NW Houston", "Spring/Klein", "Humble/Kingwood/NE",
    "Missouri City/Fort Bend"
]
```

---

## Important Behaviors

### Safety Escalation (Hardcoded, Non-Configurable)

- **Trigger:** Gas, CO, smoke, fire keywords in customer message
- **Action:** `escalate_to_owner()` sends SMS to owner, returns 911 directive to customer
- **Rule:** NEVER auto-dispatch for LIFE_SAFETY. Never. Not configurable.

### Weather-Aware Triage

- **Heat Emergency:** AC/AC-related keywords + temp > 95°F
- **Cold Emergency:** Heat/furnace keywords + temp < 42°F
- **Houston-Calibrated:** Thresholds set for Houston metro danger zones

### Three-Layer Reliability

1. **Full AI:** CrewAI + Gemini LLM orchestration
2. **Local Triage:** Keyword + temperature rules (if AI fails)
3. **Safety Gate:** Always runs, independent of AI layers

### Twilio Signature Validation

- **Production:** Required (checked via `X-Twilio-Signature` header)
- **Development:** Can skip with `SKIP_TWILIO_VALIDATION=true` (blocked in production)

### Stub Technicians

- **Dev/Test:** `check_tech_availability()` returns stub tech data
- **Production:** Returns `unavailable` if Composio API fails

### Rate Limiting

- **Global:** 60 requests per 60 seconds per API key/IP
- **Per-Phone:** 5-second cooldown between SMS from same number
- **TTL Pruning:** Automatic cleanup of stale rate limit entries

---

## Testing Strategy

### Test Organization

| Module             | Count  | Coverage                                            |
| ------------------ | ------ | --------------------------------------------------- |
| `test_triage.py`   | 51     | Urgency classification, temp boundaries, edge cases |
| `test_api.py`      | 19     | All endpoints, error handling, auth                 |
| `test_database.py` | 9      | CRUD, concurrent writes (4 threads × 10 writes)     |
| `test_security.py` | 12     | Auth, XSS, SQL injection, rate limiting             |
| **Total**          | **91** | —                                                   |

### Test Fixtures (conftest.py)

- `client` — FastAPI TestClient with test environment
- `api_headers` — Headers with valid test API key
- `session_cookies` — Session cookie for authenticated admin access
- `tmp_db` — Temporary SQLite database for isolated tests

### Running Tests Without API Keys

All tests run without real API keys. The test environment (`ENV=test`) automatically:

- Uses mock values for required secrets
- Disables LangSmith tracing
- Uses stub Twilio client
- Falls back to local triage engine

---

## Security Considerations

### Authentication

- **API Endpoints:** `x-api-key` header required (except `/health` and webhooks)
- **Admin Dashboard:** Session cookie auth (24-hour TTL)
- **Webhook Validation:** Twilio signature verification in production

### Input Validation

- Message length: 1–1,000 characters
- Temperature range: -50°F to 150°F
- XML escaping for TwiML responses (prevents injection)

### Security Headers

- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

### XSS Prevention

- Jinja2 auto-escaping enabled for all templates
- No manual HTML construction with user input

### CORS

- Explicit allowlist only (`CORS_ORIGINS` env var)
- No wildcard (`*`) default

---

## Deployment

### Render.com (Recommended)

1. Push repo to GitHub
2. Connect to [Render.com](https://render.com)
3. Set all required environment variables in dashboard
4. `render.yaml` handles build/start commands automatically
5. Disk mounted at `/data` for SQLite persistence

**Render.yaml Configuration:**

- Plan: `starter` (512MB RAM minimum for CrewAI)
- Region: `ohio` (US Central, good latency for Houston)
- Health Check: `/health`
- Persistent Disk: 1GB at `/data`

### Docker

```bash
docker build -t hvac-dispatch .
docker run --env-file .env -p 8000:8000 hvac-dispatch
```

**Dockerfile Features:**

- Base: `python:3.11-slim`
- Healthcheck: HTTP check to `/health` every 30s
- Port: 8000 exposed
- Command: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`

---

## Code Style Guidelines

### Python Conventions

- Use `python3` to invoke all commands (not `py -3.11` or `python`)
- Type hints encouraged for function signatures
- Docstrings for all public functions
- Import `config` first in every module that needs environment

### Module Organization

- One logical module per file
- Lazy imports for heavy dependencies (e.g., CrewAI in `_ensure_agents()`)
- Thread-local storage for SQLite connections

### Logging

- Use `setup_logging()` from `config.py` for all loggers
- Log files written to `hvac_dispatch.log`
- Format: `%(asctime)s [%(levelname)s] %(name)s — %(message)s`

### Error Handling

- Fail fast on missing required env vars (in `config.py`)
- Use tenacity for retrying external API calls (Twilio, Composio)
- Graceful fallback to local triage if CrewAI fails

---

## Database Schema

### `dispatches` Table

```sql
dispatch_id   TEXT PRIMARY KEY
customer_name TEXT
customer_phone TEXT
address       TEXT
issue_summary TEXT
urgency       TEXT
tech_name     TEXT
eta           TEXT
status        TEXT DEFAULT 'pending'
crew_result   TEXT
created_at    TEXT
updated_at    TEXT
```

### `messages` Table

```sql
id            INTEGER PRIMARY KEY AUTOINCREMENT
direction     TEXT  -- 'inbound' | 'outbound'
phone         TEXT
body          TEXT
sms_sid       TEXT
channel       TEXT DEFAULT 'sms'  -- 'sms' | 'whatsapp'
created_at    TEXT
```

---

## Troubleshooting

### Common Issues

**Import errors for CrewAI:**

- CrewAI is lazy-loaded. First request will trigger initialization.
- Check `GEMINI_API_KEY` is valid if agents fail to initialize.

**Database locked errors:**

- SQLite uses WAL mode by default. Ensure `DATABASE_PATH` directory is writable.

**Twilio signature validation fails:**

- In dev, set `SKIP_TWILIO_VALIDATION=true`
- In production, ensure Twilio webhook URL matches exactly (including https)

**Rate limit exceeded:**

- Check `_rate_counters` in memory (resets on restart)
- Adjust `RATE_LIMIT_COUNT` and `RATE_LIMIT_WINDOW` in `main.py` if needed

---

## External Dependencies

| Service   | Free Tier Limits    | Paid Tier                      |
| --------- | ------------------- | ------------------------------ |
| Gemini    | Provider-managed    | Pay-per-use                    |
| Twilio    | Trial credits       | ~$0.0079/msg + $1.15/mo/number |
| Render    | Free tier (sleeps)  | $7/mo always-on                |
| Composio  | Free tier available | Pro plans                      |
| LangSmith | 5,000 traces/mo     | Pro plans                      |

---

## Contact & License

- **Author:** PharaohDoug AI Agency
- **Location:** Houston, TX
- **License:** MIT

For credential setup help, see `docs/credential_setup.md`.
For deployment help, see `docs/deployment_guide.md`.
