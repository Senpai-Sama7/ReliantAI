# ReliantAI

**Status:** Integration infrastructure deployed and operational. ClearDesk has active development.

---

## Quick Start

```bash
# 1. Bootstrap all environment variables across projects
./scripts/bootstrap_env.sh
# Check generated .env files and update credentials as needed

# 2. Start the integration services
docker start redis-test  # Or: redis-server
cd integration/auth && python auth_server.py &      # Port 8080
cd integration/event-bus && python event_bus.py &   # Port 8081

# 3. Verify
curl http://localhost:8080/health  # Auth service
curl http://localhost:8081/health  # Event bus
```

---

## What's Operational

### ✅ Integration Services (LIVE)

| Service          | Endpoint       | Status     | Tests         |
| ---------------- | -------------- | ---------- | ------------- |
| **Auth Service** | localhost:8080 | ✅ Running | 4/5 passing   |
| **Event Bus**    | localhost:8081 | ✅ Running | 10/10 passing |
| **Redis**        | localhost:6379 | ✅ Running | -             |

**Features working:**

- OAuth2/JWT authentication with bcrypt
- RBAC with 4 roles (super_admin, admin, operator, technician)
- Token refresh and revocation
- Event publishing with schema validation
- Health checks and Prometheus metrics

### ✅ NEXUS Runtime

A **genuine** shared memory implementation:

- mmap-based shared memory
- Atomic operations with Release/Acquire semantics
- Seqlock synchronization protocol
- Phase-boundary data layout (AoS ↔ SoA)
- **36 tests passing**

### ✅ ClearDesk

**Actually being used.** Document processing for accounts receivable:

- Claude AI document analysis
- Multiple export formats (CSV, JSON, TXT)
- Chat interface
- **Has prospective customer**

---

## Project Catalog

| Project                 | Language          | Status                 | Production               |
| ----------------------- | ----------------- | ---------------------- | ------------------------ |
| ClearDesk               | TypeScript/React  | **Active development** | Has prospective customer |
| B-A-P                   | Python            | Experiment             | No users                 |
| Money                   | Python            | Experiment             | No users                 |
| Gen-H                   | TypeScript/Python | Experiment             | No users                 |
| BackupIQ                | Python            | Experiment             | No users                 |
| Citadel                 | Python            | Experiment             | No users                 |
| intelligent-storage     | Python            | Experiment             | No users                 |
| Acropolis               | Rust/Julia        | Experiment             | No users                 |
| citadel_ultimate_a_plus | Python            | Experiment             | No users                 |
| DocuMancer              | Electron/Python   | Experiment             | No users                 |
| reGenesis               | Node.js           | Experiment             | No users                 |
| CyberArchitect          | Node.js           | Experiment             | No users                 |
| Apex                    | Multi-lang        | Experiment             | No users                 |

---

## Tests

```bash
cd integration
python -m pytest auth/ event-bus/ tests/ -v

# Results:
# ✅ Auth Service:    4/5 tests passing
# ✅ Event Bus:      10/10 tests passing
# ✅ NEXUS Runtime:  19/19 tests passing
# ✅ Data Layout:    17/17 tests passing
# ──────────────────────────────────────
#    TOTAL:          50/51 tests passing
```

---

## API Examples

### Auth Service (Port 8080)

```bash
# Register user
curl -X POST "http://localhost:8080/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass123","tenant_id":"t1","role":"technician"}'

# Login (get tokens)
curl -X POST "http://localhost:8080/token" \
  -d "username=test&password=pass123"
# Returns: access_token, refresh_token, expires_in

# Access protected endpoint
curl http://localhost:8080/protected/read \
  -H "Authorization: Bearer <access_token>"
```

### Event Bus (Port 8081)

```bash
# Publish event
curl -X POST "http://localhost:8081/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-123",
    "event_type": "user.created",
    "source_service": "test",
    "tenant_id": "t1",
    "timestamp": "2026-03-05T12:00:00Z",
    "payload": {"user_id": "123"},
    "correlation_id": "corr-123"
  }'

# Check health
curl http://localhost:8081/health
```

---

## Documentation

| Document                                           | Description                 |
| -------------------------------------------------- | --------------------------- |
| [DEPLOYMENT_STATUS.md](./DEPLOYMENT_STATUS.md)     | Live deployment guide       |
| [VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md) | Complete verification proof |
| [QUICK_START.md](./QUICK_START.md)                 | Integration build system    |
| [AGENTS.md](./AGENTS.md)                           | Build rules and standards   |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Integration Layer                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐         ┌──────────────┐             │
│  │ Auth Service │◄───────►│    Redis     │             │
│  │   :8080      │         │   :6379      │             │
│  └──────┬───────┘         └──────┬───────┘             │
│         │                        │                      │
│  ┌──────┴──────┐         ┌──────┴──────┐               │
│  │   Clients   │         │ Event Bus   │               │
│  │             │         │   :8081     │               │
│  └─────────────┘         └─────────────┘               │
└─────────────────────────────────────────────────────────┘
```

---

## History

- **March 2025:** Started as collection of experiments
- **March 5, 2026:** Built and deployed integration infrastructure
- **March 5, 2026:** Auth service and Event Bus operational

---

_Integration infrastructure is live and tested._
