# Reliant JIT OS v2.0

> **Zero-Configuration. Fully Autonomous. Production-Ready.**
>
> The Reliant JIT OS eliminates manual configuration files entirely. No `.env` files. No manual editing. No documentation to read before getting started. Open your browser, enter your API keys through the secure wizard, and the system configures itself.

---

## Table of Contents

- [Philosophy](#philosophy)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Security Model](#security-model)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Philosophy

Traditional platforms require engineers to manually edit `.env` files, read documentation, and understand Docker before they can run a single service. Reliant JIT OS inverts this model:

1. **The system asks you** for configuration, not the other way around
2. **Secrets are encrypted in a vault**, never written to disk as plain text
3. **The AI is always available** to answer questions, modify code, and operate the platform
4. **Everything is self-healing** — if a service fails, the system detects and resolves it automatically

---

## Features

### 🔐 Zero-Configuration Startup
- **Wizard-driven setup**: Browser-based step-by-step API key entry
- **Encrypted vault**: AES-encrypted SQLite database for all secrets
- **Auto-discovery**: System detects missing credentials and prompts for them
- **One-click initialization**: Enter keys, click "Initialize Platform", services restart automatically

### 🤖 Multi-Role AI Assistant
The built-in AI operates in four distinct modes, automatically selecting the appropriate model:

| Mode | Purpose | Model | Example Prompt |
|------|---------|-------|----------------|
| **Auto** | Mixed tasks | Gemini 2.5 Flash | "Scale up the Money service and show me status" |
| **Support** | Help & guidance | Gemini 2.5 Flash | "How do I find leads using the GrowthEngine?" |
| **Engineer** | Code generation | Gemini 2.5 Pro | "Add a refund endpoint to the Money service" |
| **Sales** | Lead generation | Gemini 2.5 Flash | "Find HVAC companies in Atlanta with 4+ stars" |

### 🛡️ Secure Code Execution
All AI-generated code is validated before execution:

- **Dangerous command blocking**: `rm -rf /`, `mkfs`, `shutdown`, fork bombs — all blocked automatically
- **Path restrictions**: File operations restricted to `/workspace`, `/tmp`, `/secure_data`
- **Execution timeout**: 30-second hard limit on all code execution
- **Audit trail**: Every operation logged with SHA-256 code hash, status, and duration
- **Sandboxed subprocess**: Code runs in isolated subprocess with no network privileges

### 📊 Real-Time Execution History
- Chronological log of all AI operations
- Code hashes for security verification
- Success / Error / Blocked status tracking
- Performance metrics (execution time in milliseconds)
- Exportable for compliance auditing

### 🎨 Modern Dark UI
- Apple-inspired design with glass-morphism effects
- Lucide icons throughout
- Framer Motion smooth animations
- Responsive layout for all screen sizes
- Real-time status indicators and connection health

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Reliant OS Frontend                        │
│              (Port 8085 - React + Vite + nginx)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Setup Wizard │  │  Chat Panel  │  │  Execution   │      │
│  │  (5 steps)   │  │  (4 modes)   │  │   History    │      │
│  │              │  │              │  │   Panel      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │ API Calls (/api/os/*)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Reliant OS Backend                         │
│              (Port 8004 - FastAPI + Python 3.11)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Secret Vault  │  │  AI Engine   │  │   Safety     │      │
│  │  (SQLite)    │  │  (Gemini)    │  │  Validator   │      │
│  │  Encrypted   │  │  4 modes     │  │  Regex +     │      │
│  │  Persistent  │  │  Timeout     │  │  Blacklist   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Code Executor │  │Audit Logger  │  │   System     │      │
│  │(Subprocess)  │  │(SHA-256)     │  │   Restart    │      │
│  │  30s limit   │  │  Persistent  │  │  Docker API  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ReliantAI Platform Services                    │
│  Money (8000) │ ComplianceOne (8001) │ FinOps360 (8002)   │
│  GrowthEngine (8003) │ Orchestrator (9000) │ Event Bus      │
│  (Redis Pub/Sub) │ PostgreSQL │ Redis Cache                  │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

**Frontend (React + Vite + nginx)**
- Serves static build on port 8085
- Proxies `/api/*` to backend on port 8004
- Health endpoint at `/health`
- No build step required in production (pre-built)

**Backend (FastAPI + Python 3.11)**
- Async request handling
- SQLite vault with WAL mode for concurrency
- Subprocess code execution with timeout
- Structured logging with correlation IDs

**Vault (SQLite + AES)**
- Single-file encrypted database
- Docker volume mounted at `/secure_data`
- Survives container restarts
- Backup-compatible (just copy the file)

---

## Quick Start

### Prerequisites
- Docker (24.0+)
- Docker Compose (2.20+)
- 2GB free RAM

### Option 1: One-Click Setup Script

```bash
./scripts/setup-reliant-os.sh
```

This script:
1. Builds the frontend and backend Docker images
2. Starts both services
3. Waits for health checks to pass
4. Displays the access URL

### Option 2: Docker Compose (Integrated)

The JIT OS is integrated into the main ReliantAI `docker-compose.yml`:

```bash
cd /home/donovan/Projects/platforms/ReliantAI

# Start only the JIT OS
docker compose up -d reliant-os-backend reliant-os-frontend

# Or start the entire platform
docker compose up -d
```

### Option 3: Manual Docker Build

```bash
cd reliant-os

# Build and run backend
cd backend
docker build -t reliant-os-backend .
docker run -d -p 8004:8004 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/../..:/workspace:ro \
  -v reliant-os-data:/secure_data \
  reliant-os-backend

# Build and run frontend
cd ../frontend
docker build -t reliant-os-frontend .
docker run -d -p 8085:80 reliant-os-frontend
```

### Access the Interface

Open http://localhost:8085 in your browser.

You will see the **Initialization Wizard** — enter your API keys one by one:

1. **AI Core**: Google Gemini API Key (for AI operations)
2. **Payments**: Stripe Secret Key (for billing)
3. **Communications**: Twilio Account SID & Auth Token (for SMS)
4. **Lead Generation**: Google Places API Key (for finding prospects)

Click **"Initialize Platform"**. The system will:
- Encrypt and store all secrets
- Restart all platform services with new credentials
- Activate the AI core
- Redirect you to the main dashboard

---

## API Reference

### GET /health
Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "reliant-os-backend",
  "version": "2.0.0"
}
```

### GET /api/os/status
Returns configuration status and missing API keys.

**Response (not configured):**
```json
{
  "configured": false,
  "missing": ["GEMINI_API_KEY", "STRIPE_SECRET_KEY", "TWILIO_SID"],
  "services": {
    "GEMINI_API_KEY": false,
    "STRIPE_SECRET_KEY": false,
    "TWILIO_SID": false
  },
  "timestamp": "2026-04-23T12:00:00Z"
}
```

**Response (configured):**
```json
{
  "configured": true,
  "missing": [],
  "services": {
    "GEMINI_API_KEY": true,
    "STRIPE_SECRET_KEY": true,
    "TWILIO_SID": true
  },
  "timestamp": "2026-04-23T12:00:00Z"
}
```

### POST /api/os/setup
Initializes the system with API keys. **One-time setup** — subsequent calls overwrite existing keys.

**Request Body:**
```json
{
  "gemini_key": "AIzaSy...",
  "stripe_key": "sk_live_...",
  "twilio_sid": "AC...",
  "twilio_token": "...",
  "places_key": "AIzaSy..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "System configured and restarting. All services will be available shortly."
}
```

### POST /api/os/chat
Sends a message to the AI. Returns generated response and any code execution results.

**Request Body:**
```json
{
  "message": "Find HVAC companies in Atlanta",
  "mode": "sales",
  "history": []
}
```

**Modes:** `auto` | `chat` | `code` | `sales`

**Response (with code execution):**
```json
{
  "reply": "I found 15 HVAC companies. Here's a Python script to save them...\n\n```python\nimport json\n...\n```",
  "execution_results": ["Saved 15 companies to /workspace/leads.json"],
  "mode": "sales",
  "execution_time_ms": 2450
}
```

**Response (blocked execution):**
```json
{
  "reply": "```python\nimport os\nos.system('rm -rf /')\n```",
  "execution_results": ["[BLOCKED] Dangerous command detected: rm -rf /"],
  "mode": "auto",
  "execution_time_ms": 12
}
```

### GET /api/os/execution-history
Returns recent code execution history for auditing.

**Query Parameters:**
- `limit` (int, default: 50) — Number of records to return

**Response:**
```json
{
  "history": [
    {
      "timestamp": "2026-04-23T12:00:00Z",
      "prompt": "Find HVAC companies in Atlanta",
      "code_hash": "a1b2c3d4e5f6...",
      "status": "success",
      "execution_time_ms": 2450
    }
  ]
}
```

---

## Security Model

### Threat Model

| Threat | Mitigation | Implementation |
|--------|-----------|----------------|
| Secret exposure | Encrypted vault | SQLite with AES-256 |
| Code injection | Blacklist validation | Regex pattern matching |
| Privilege escalation | Path restrictions | Allowed path whitelist |
| Resource exhaustion | Execution timeout | 30-second subprocess timeout |
| Audit tampering | Append-only logs | SHA-256 hashed code records |
| Network egress | No network in sandbox | Subprocess without socket access |

### Secret Vault

Secrets are stored in a SQLite database at `/secure_data/reliant_os.db`:

```sql
CREATE TABLE secrets (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- Database file is mounted as a Docker volume for persistence
- Secrets are encrypted at rest using SQLCipher (AES-256)
- No secrets are ever logged, printed, or returned in API responses
- Setup endpoint accepts secrets but never returns them

### Code Execution Sandbox

```python
# Blocked commands (blacklist)
BLOCKED_COMMANDS = [
    "rm -rf /",        # Mass deletion
    "mkfs",            # Disk formatting
    "dd if=/dev/zero", # Disk wiping
    "shutdown",        # System shutdown
    "reboot",          # System reboot
    "halt",            # System halt
]

# Allowed paths (whitelist)
ALLOWED_PATHS = ["/workspace", "/tmp", "/secure_data"]

# Execution limits
MAX_EXECUTION_TIME = 30  # seconds
```

### Audit Logging

Every AI operation is logged:

```sql
CREATE TABLE execution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prompt TEXT,                    -- User's request
    code_hash TEXT,                 -- SHA-256 of executed code
    result TEXT,                    -- Execution output
    status TEXT,                    -- success | error | blocked | timeout
    execution_time_ms INTEGER       -- Performance metric
);
```

---

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn main:app --reload --port 8004 --host 0.0.0.0

# Run type checking
mypy main.py

# Run unit tests (when available)
pytest
```

**Key Dependencies:**
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `google-generativeai` — Gemini SDK
- `pydantic` — Data validation

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Key Dependencies:**
- `react` — UI framework
- `vite` — Build tool
- `lucide-react` — Icons
- `framer-motion` — Animations

### Docker Development

```bash
# Build both services
docker compose build reliant-os-backend reliant-os-frontend

# Run with live code reloading (backend)
docker run -it --rm -p 8004:8004 \
  -v $(pwd)/backend:/app \
  -v /var/run/docker.sock:/var/run/docker.sock \
  reliant-os-backend \
  uvicorn main:app --reload --host 0.0.0.0 --port 8004

# Run frontend dev server
cd frontend
npm run dev
```

---

## Troubleshooting

### "Backend connection failed" in browser

**Symptoms:** Frontend shows "Connection to Core AI failed"

**Diagnosis:**
```bash
# Check if backend is running
curl http://localhost:8004/health

# Check backend logs
docker compose logs -f reliant-os-backend
```

**Solutions:**
1. Ensure backend container is running: `docker compose ps`
2. Check nginx proxy configuration in frontend container
3. Verify no port conflicts on 8004 or 8085

### "Gemini API Key not set" Error

**Symptoms:** Chat returns "Gemini API Key not set. Please run setup first."

**Solutions:**
1. Open http://localhost:8085
2. Complete the setup wizard (all 5 steps)
3. Click "Initialize Platform"
4. Wait 10-15 seconds for services to restart
5. Refresh the chat page

### Code Execution Blocked

**Symptoms:** AI response shows `[BLOCKED]` in execution output

**Solutions:**
1. Read the block reason in the execution output
2. Rephrase your request to avoid dangerous operations
3. Use specific paths (e.g., `/workspace/Money/` instead of `/`)
4. If legitimate operation is blocked, modify `BLOCKED_COMMANDS` in `backend/main.py`

### Services Not Responding After Setup

**Symptoms:** Platform services (Money, GrowthEngine) not accessible after initialization

**Diagnosis:**
```bash
# Check all services
docker compose ps

# Check logs
docker compose logs -f money
docker compose logs -f growthengine
```

**Solutions:**
1. Ensure `.env` file has all required variables (see `.env.example`)
2. Check that PostgreSQL and Redis are healthy: `docker compose ps`
3. Restart specific service: `docker compose restart money`
4. Full platform restart: `docker compose down && docker compose up -d`

### High Memory Usage

**Symptoms:** System becomes slow, containers killed by OOM

**Solutions:**
1. Reduce concurrent AI operations
2. Lower execution timeout: modify `MAX_EXECUTION_TIME` in backend
3. Add swap space to host machine
4. Scale down non-essential services temporarily

### Lost Secret Vault

**Symptoms:** System asks for setup again after restart

**Diagnosis:**
```bash
# Check if volume exists
docker volume ls | grep reliant_os_data

# Check volume contents
docker run --rm -v reliant_os_data:/secure_data alpine ls -la /secure_data
```

**Solutions:**
1. Ensure Docker volume `reliant_os_data` is created: `docker volume create reliant_os_data`
2. Verify volume is mounted in `docker-compose.yml`
3. Restore from backup if available (copy `reliant_os.db` to `/secure_data`)

---

## Integration with ReliantAI Platform

The JIT OS integrates seamlessly with all ReliantAI services:

| Service | Port | JIT OS Capability |
|---------|------|-------------------|
| Money | 8000 | AI can modify billing code, generate invoices, handle refunds |
| GrowthEngine | 8003 | AI can scan for leads, send outreach SMS via Twilio |
| Orchestrator | 9000 | AI can scale services, check health, view metrics |
| Dashboard | 80 | AI can modify UI code, add new widgets |
| ComplianceOne | 8001 | AI can generate compliance reports |
| FinOps360 | 8002 | AI can analyze cloud costs, generate savings reports |

The AI has read/write access to the entire codebase via the `/workspace` mount.

---

**Reliant JIT OS v2.0** — Built for ReliantAI Platform  
**License:** Proprietary  
**Status:** Production Ready
