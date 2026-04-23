# ReliantAI Platform

**Autonomous, Self-Managing, AI-Powered Enterprise Platform**

A federated multi-service platform built around a central integration nervous system. Combines a real-money HVAC dispatch business (Money), enterprise SaaS analytics (B-A-P), compliance and cost management, a multi-tier agent framework (APEX), and a full observability stack — all wired through shared auth, event bus, and saga coordination.

**Platform Status**: 104 bugs fixed, production-ready, fully autonomous

---

## Platform Architecture

### Micro-Topology Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Web UI     │  │  Mobile     │  │  API        │  │  SMS/WhatsApp (Twilio)  │  │
│  │  Dashboard  │  │  Apps       │  │  Clients    │  │  Customer Interface     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
└─────────┼────────────────┼────────────────┼────────────────────┼───────────────┘
          │                │                │                    │
          └────────────────┴────────────────┴────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EDGE LAYER (nginx:80/443)                              │
│  • TLS termination with cert.pem/key.pem                                          │
│  • Rate limiting: api zone (10r/s), auth zone (5r/m)                              │
│  • Gzip compression enabled                                                       │
│  • HTTP → HTTPS redirect                                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│  Money :8000  │      │ ComplianceOne :8001  │      │  FinOps360 :8002     │
│  FinOps360    │      │                      │      │                      │
├───────────────┤      ├──────────────────────┤      ├──────────────────────┤
│• FastAPI 0.115│      │• FastAPI 0.115       │      │• FastAPI 0.115       │
│• CrewAI 0.x   │      │• PostgreSQL 15       │      │• PostgreSQL 15       │
│• Gemini API   │      │• RealDictCursor      │      │• RealDictCursor      │
│• Twilio SDK   │      │• 5 middleware layers │      │• 5 middleware layers │
│• Stripe SDK   │      │• ThreadPool 1-10    │      │• ThreadPool 1-10    │
│• Prometheus   │      │                      │      │                      │
├───────────────┤      ├──────────────────────┤      ├──────────────────────┤
│ Tables:       │      │ Tables:              │      │ Tables:              │
│• dispatches   │      │• compliance_        │      │• cloud_accounts      │
│• messages     │      │  frameworks          │      │• cost_data           │
│• customers    │      │• compliance_        │      │• budgets             │
│• customer_    │      │  controls            │      │• cost_alerts         │
│  events        │      │• compliance_audits  │      │• cost_optimization_  │
│               │      │• compliance_        │      │  recommendations     │
│ Auth: Triple  │      │  evidence            │      │• resource_utilization│
│ (JWT/API key/ │      │• compliance_        │      │                      │
│  session)     │      │  violations          │      │ Hourly background    │
│               │      │                      │      │ budget check task    │
│ SSE feed for  │      │ CORS_ORIGINS         │      │                      │
│ live dispatches│      │ required (no *)      │      │ Sample data on       │
│               │      │                      │      │ first startup        │
│ Circuit       │      │                      │      │                      │
│ breaker: 3    │      │                      │      │ CORS_ORIGINS         │
│ failures →    │      │                      │      │ required (no *)      │
│ 30s open      │      │                      │      │                      │
└───────┬───────┘      └──────────┬───────────┘      └──────────┬───────────┘
        │                         │                          │
        └─────────────────────────┼──────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER (Central Nervous System)                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │  Auth :8080         │  │  Event Bus :8081    │  │  Saga :8090         │   │
│  ├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤   │
│  │• OAuth2/JWT (HS256) │  │• Redis pub/sub      │  │• Kafka (aiokafka)   │   │
│  │• SQLite user store   │  │• 16 EventType enum  │  │• Redis idempotency  │   │
│  │• 4 RBAC roles        │  │• 64KB payload limit │  │• 300s timeout       │   │
│  │• Token revocation    │  │• Pydantic validation│  │• Max 3 retries      │   │
│  │• Rate limiting       │  │• 24h retention      │  │• Compensation in     │   │
│  │• Prometheus metrics  │  │• DLQ 10k cap        │  │  reverse order       │   │
│  │                     │  │• Bearer auth         │  │                     │   │
│  │ Hard fail if        │  │                     │  │                     │   │
│  │ AUTH_SECRET_KEY     │  │ EVENT_BUS_API_KEY   │  │                     │   │
│  │ < 32 chars          │  │ Bearer required     │  │                     │   │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘   │
│                                                                                 │
│  ADVANCED MODULES:                                                              │
│  • metacognitive_layer/ — Bayesian confidence (α=0.3), 5 confidence levels       │
│  • nexus-runtime/ — mmap shared memory, C++20 memory order semantics             │
│  • a2a_bridge.py — Google A2A protocol, 6 task states                            │
│  • intelligent_routing.py — 5 routing strategies                               │
│  • hitl_optimizer.py — 6 decision types requiring human review                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌─────────────────┐   ┌─────────────────────┐   ┌─────────────────────────────┐
│ Orchestrator    │   │   APEX Agents       │   │   Other Services            │
│ :9000           │   │   (Kafka direct)      │   │   • Citadel (TimescaleDB)   │
├─────────────────┤   ├─────────────────────┤   │   • ops-intelligence        │
│• 6 async loops  │   │• L2: Uncertainty     │   │   • B-A-P (Poetry only)     │
│• AI predictions │   │• L3: Specialized   │   │   • ClearDesk (browser)     │
│• Auto-scaling   │   │• L4: Quality QA     │   │   • Gen-H (React/Vite)      │
│• Self-healing   │   │• L5: Metacognitive   │   │   • soviergn_ai (Bun)       │
│• WebSocket API  │   │  (in integration/)   │   │   • DocuMancer (Electron)   │
│• Redis streams  │   │                     │   │   • CyberArchitect (Node)   │
│  for events      │   │ Kafka:9092 channel    │   │   • Acropolis (Rust)        │
├─────────────────┤   │ (separate from       │   │                             │
│ Loops:          │   │  event-bus)          │   │                             │
│• Health: 30s    │   │                     │   │                             │
│• Metrics: 60s   │   │                     │   │                             │
│• Scaling: 2min  │   │                     │   │                             │
│• Healing: 60s   │   │                     │   │                             │
│• AI: 5min       │   │                     │   │                             │
│• Optimization:  │   │                     │   │                             │
│  hourly         │   │                     │   │                             │
├─────────────────┤   └─────────────────────┘   └─────────────────────────────┘
│ Scaling Bounds: │
│• Money: 2-10   │
│• Compliance:   │
│  1-5            │
│• FinOps: 1-5   │
│• Integration:  │
│  1-3 (no auto)  │
└─────────────────┘
         │
         └──────────────────────────────────────────────────────┐
                                                              │
┌─────────────────────────────────────────────────────────────┴─────────────────┐
│                         INFRASTRUCTURE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │ PostgreSQL :5432    │  │ Redis :6379         │  │ Vault :8200         │   │
│  │ postgres:15-alpine  │  │ redis:alpine        │  │ HashiCorp Vault     │   │
│  ├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤   │
│  │• money DB           │  │• Pub/sub            │  │• File storage at    │   │
│  │• complianceone DB   │  │• Sessions           │  │  /vault/data        │   │
│  │• finops360 DB       │  │• Rate limiting      │  │• TLS enforced       │   │
│  │• integration DB     │  │• Token revocation   │  │• UI enabled         │   │
│  │                     │  │• 3 Redis streams    │   │• Default lease 168h │   │
│  │ RealDictCursor      │  │  (scale/heal/events)│   │• Max lease 720h     │   │
│  │ mandatory           │  │                     │  │                     │   │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘   │
│                                                                                 │
│  MONITORING STACK (docker-compose.monitoring.yml):                              │
│  • Prometheus :9090 — 15s scrape, all services + postgres                         │
│  • Grafana :3000 — Dashboards                                                   │
│  • Alertmanager :9093 — Alert routing                                           │
│  • Loki + Promtail — Log aggregation                                            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Full Service Map

| Service | Port | Stack | Purpose |
|---------|------|-------|---------|
| Money | 8000 | FastAPI + CrewAI + Gemini + Twilio | HVAC AI dispatch (revenue service) |
| ComplianceOne | 8001 | FastAPI + PostgreSQL | SOC2/GDPR/HIPAA compliance tracking |
| FinOps360 | 8002 | FastAPI + PostgreSQL | Cloud cost management (AWS/Azure/GCP) |
| integration/auth | 8080 | FastAPI + SQLite + Redis | OAuth2/JWT, RBAC (4 roles) |
| integration/event-bus | 8081 | FastAPI + Redis pub/sub | Async event distribution, DLQ |
| integration/saga | 8090 | FastAPI + Kafka + Redis | Distributed transaction coordination |
| orchestrator | 9000 | FastAPI + WebSocket + aiohttp | AI predictions, auto-scaling, self-healing |
| ops-intelligence | 8095 | FastAPI + SQLite | Operations monitoring (8 domain routers) |
| apex/apex-ui | 3000 | Next.js 15 | Agent platform UI |
| Citadel | — | Flask + TimescaleDB:5433 + Redis:6380 | Security & observability (11 services) |
| PostgreSQL | 5432 | postgres:15-alpine | Platform primary DB |
| Redis | 6379 | redis:7-alpine | Cache, sessions, rate limiting |
| Vault | 8200 | HashiCorp Vault | Secrets management (TLS enforced) |
| Prometheus | 9090 | prom/prometheus | Metrics (monitoring compose) |
| Grafana | 3000 | grafana/grafana | Dashboards (monitoring compose) |

---

## Core Services

### Money — HVAC AI Dispatch
The primary revenue service. Houston HVAC customers text or WhatsApp a problem; CrewAI agents backed by Google Gemini perform 4-level urgency triage (`LIFE_SAFETY → 911`, `EMERGENCY`, `URGENT`, `ROUTINE`), assign a technician, and send SMS confirmation via Twilio.

**Three auth methods handled simultaneously:** Bearer JWT (verified against integration/auth:8080), `X-API-Key` header, or session cookie (CSRF-protected login form). Twilio webhook endpoints independently validate `X-Twilio-Signature` HMAC.

**Key capabilities:**
- Stripe billing (free/starter $99/professional $299/enterprise $999) with per-plan dispatch quotas
- SSE live dispatch feed with thread-safe queue fan-out
- Event-sourced state machine with `/api/dispatch/{id}/timeline` endpoint
- Make.com and HubSpot HMAC-signed webhook receivers
- Full Prometheus metrics at `/metrics`
- Jinja2 admin dashboards at `/admin`
- Circuit breaker on auth service calls (3 failures → 30s open)

**Publishes** `EventType.DISPATCH_COMPLETED` to integration/event-bus on every completed dispatch.

### ComplianceOne — Compliance Management
SOC2/GDPR/HIPAA compliance tracking. Manages frameworks, controls, audits, evidence, and violations. Applies the full `shared/security_middleware.py` stack. Refuses to start if `CORS_ORIGINS` is unset or contains `*`.

### FinOps360 — Cloud Cost Management
Multi-cloud cost tracking and optimization. Budgets with threshold alerts checked hourly via `asyncio.create_task`. AI-generated optimization recommendations. Sample AWS/Azure/GCP accounts inserted on first startup. Same security constraints as ComplianceOne.

### Orchestrator — Platform Brain
Single-file `main.py`. Six background async loops: health checks (30s), metrics collection (60s), scaling decisions (2 min — serialized via `asyncio.Queue`), auto-healing (60s), AI predictions via Holt's double exponential smoothing (5 min), optimization reports (hourly).

Scaling bounds: Money 2–10 instances, ComplianceOne/FinOps360 1–5, integration 1–3 (no auto-scale). Scale-up triggers: response_time > 1000ms OR cpu > 75% OR error_rate > 5%. WebSocket endpoint broadcasts real-time events to the dashboard.

---

## Micro-Topology Deep Dive

### Database Schema Architecture

#### Money Service Tables (`money` database)
| Table | Columns | Purpose | Indexes |
|-------|---------|---------|---------|
| **dispatches** | dispatch_id (PK), customer_name, customer_phone, address, issue_summary, urgency, tech_name, eta, status, crew_result, created_at, updated_at | Core dispatch records | idx_dispatches_status |
| **messages** | id (SERIAL PK), direction (inbound/outbound), phone, body, sms_sid, channel (sms/whatsapp), created_at | SMS/WhatsApp message log | idx_messages_phone |
| **customers** | id (SERIAL PK), stripe_customer_id (UNIQUE), stripe_subscription_id, api_key (UNIQUE), email, name, company, plan (free/starter/professional/enterprise), dispatch_quota, created_at | Multi-tenant billing | — |
| **customer_events** | id (SERIAL PK), customer_id (FK), event_type, event_data, created_at | Event sourcing for billing | idx_customer_events_customer_id |

**Connection Pool:** `ThreadedConnectionPool(1, 20)` — 1 min, 20 max connections  
**Cursor Factory:** `RealDictCursor` mandatory (prevents tuple/dict crashes)

#### ComplianceOne Tables (`complianceone` database)
| Table | Columns | Purpose |
|-------|---------|---------|
| **compliance_frameworks** | id (SERIAL PK), name (UNIQUE), description, version, created_at | SOC2, GDPR, HIPAA frameworks |
| **compliance_controls** | id (SERIAL PK), framework_id (FK), control_id, title, description, category, severity (CHECK: low/medium/high/critical) | Individual controls |
| **compliance_audits** | id (SERIAL PK), framework_id (FK), status, started_at, completed_at, findings_count | Audit records |
| **compliance_evidence** | id (SERIAL PK), control_id (FK), evidence_type, file_path, description, submitted_by, submitted_at | Evidence storage |
| **compliance_violations** | id (SERIAL PK), control_id (FK), severity, description, status, detected_at, resolved_at | Violation tracking |

**Connection Pool:** `ThreadedConnectionPool(1, 10)`  
**Security:** CORS_ORIGINS required, 5-layer middleware stack

#### FinOps360 Tables (`finops360` database)
| Table | Columns | Purpose |
|-------|---------|---------|
| **cloud_accounts** | id (SERIAL PK), provider (aws/azure/gcp), account_id, account_name, status, created_at | Cloud account registry |
| **cost_data** | id (SERIAL PK), account_id (FK), service_name, cost_amount, usage_quantity, unit, recorded_at | Time-series cost data |
| **budgets** | id (SERIAL PK), account_id (FK), budget_name, limit_amount, alert_threshold, period, start_date, end_date | Budget definitions |
| **cost_alerts** | id (SERIAL PK), budget_id (FK), alert_type, severity, message, acknowledged, created_at | Alert records |
| **cost_optimization_recommendations** | id (SERIAL PK), account_id (FK), recommendation_type, description, potential_savings, implementation_steps, status, created_at | AI-generated recommendations |
| **resource_utilization** | id (SERIAL PK), account_id (FK), resource_id, resource_type, region, cpu_avg, memory_avg, recorded_at | Resource metrics |

**Background Task:** Hourly budget check via `asyncio.create_task()`  
**Sample Data:** Auto-inserted on first startup

### API Endpoint Topology

#### Money Endpoints (21 endpoints, `main.py:1-1258`)
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/health` | GET | None | Service health + DB connectivity check |
| `/metrics` | GET | API key | Prometheus metrics export |
| `/dispatch` | POST | API key + billing check | Create new dispatch with quota enforcement |
| `/sms`, `/whatsapp` | POST | Twilio HMAC | Webhook handlers for incoming messages |
| `/api/dispatch/{id}/timeline` | GET | API key | Event-sourced state transitions |
| `/api/dispatch/funnel` | GET | API key | Pipeline funnel metrics |
| `/api/metrics` | GET | API key | Live dashboard metrics |
| `/api/dispatches/search` | GET | API key | Full-text search + filtering |
| `/api/stream/dispatches` | GET | API key | **SSE live feed** — thread-safe queue fan-out |
| `/billing/*` | various | Stripe webhook | Checkout, plans, webhook handling |
| `/webhooks/make/*` | POST | Make.com HMAC | Sales lead ingestion |
| `/webhooks/hubspot/*` | POST | HubSpot HMAC | Contact update handling |
| `/admin`, `/legacy-admin` | GET | Session | Jinja2 admin dashboards |
| `/login`, `/logout` | GET/POST | Session | CSRF-protected authentication |

#### ComplianceOne Endpoints (10 endpoints, `main.py:1-400`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health |
| `/frameworks` | GET/POST | List/create compliance frameworks |
| `/controls` | GET/POST | List/create controls |
| `/audits` | GET/POST | List/create audits |
| `/audits/{id}/complete` | POST | Complete an audit |
| `/evidence` | POST | Submit evidence |
| `/violations` | GET/POST | List/report violations |
| `/dashboard` | GET | Overview dashboard |

#### Orchestrator Six Async Loops (single-file `main.py:1-1133`)
| Loop | Interval | Function | Implementation |
|------|----------|----------|----------------|
| **Health Check** | 30s | `_health_check_loop()` | Polls all services, updates `Service.status` |
| **Metrics Collection** | 60s | `_metrics_collection_loop()` | CPU, memory, response_time, error_rate |
| **Scaling Decisions** | 2min | `_scaling_decision_loop()` | Serialized via `asyncio.Queue`, prevents race conditions |
| **Auto-Healing** | 60s | `_healing_loop()` | Detects failures, publishes heal intents to Redis stream |
| **AI Predictions** | 5min | `_ai_prediction_loop()` | Holt's double exponential smoothing (α=0.3, β=0.1) |
| **Optimization** | 1hour | `_optimization_loop()` | Resource allocation, cleanup, report generation |

**Redis Streams:**
- `reliantai:scale_intents` — Scale actions published here
- `reliantai:heal_intents` — Heal actions published here
- `reliantai:platform_events` — General platform events

### Data Flow Traces

#### 1. SMS Dispatch Flow (Full Stack Trace)
```
Customer SMS
    ↓
Twilio Webhook (POST /sms)
    ↓
Twilio HMAC validation (X-Twilio-Signature)
    ↓
CrewAI dispatch (hvac_dispatch_crew.py:run_hvac_crew)
    ↓
Gemini API (triage_urgency tool)
    ↓
4-level urgency classification (LIFE_SAFETY/EMERGENCY/URGENT/ROUTINE)
    ↓
Stripe billing check (check_dispatch_quota)
    ↓
PostgreSQL save (database.py:save_dispatch)
    ↓
Event bus publish (EventType.DISPATCH_COMPLETED)
    ↓
Redis SETEX + PUBLISH (integration/event-bus/event_bus.py:publish_sync)
    ↓
SSE broadcast to connected clients (/api/stream/dispatches)
    ↓
Twilio SMS confirmation sent (notify_technician tool)
```

#### 2. Auth Flow (Triple Auth Pattern)
```
Request arrives
    ↓
RateLimitMiddleware (100 rpm sliding window)
    ↓
_security_middleware.SecurityHeadersMiddleware
    ↓
Money._authorize_request(x_api_key, request)
    ↓
├── API Key path: x_api_key == DISPATCH_API_KEY
├── JWT path: Bearer token → integration/auth:8080 validation
└── Session path: Cookie → check Redis for revocation
    ↓
Proceed to endpoint handler
```

#### 3. Orchestrator Scaling Flow
```
_metrics_collection_loop (every 60s)
    ↓
Collect CPU, memory, response_time, error_rate
    ↓
_holt_states[service_name]["cpu"].update(cpu_value) (α=0.3, β=0.1)
    ↓
_ai_prediction_loop (every 5min)
    ↓
Two-step-ahead forecast: level + 2*trend
    ↓
If predicted > 80%: Queue scale-up
If predicted < 25%: Queue scale-down
    ↓
_scale_queue.put(ScaleAction)
    ↓
_scaling_decision_loop processes queue (serialized)
    ↓
Publish to Redis stream: reliantai:scale_intents
    ↓
WebSocket broadcast to dashboard clients
```

### Connection Topology

```
Service → PostgreSQL (RealDictCursor mandatory)
    ├── Money: pool.ThreadedConnectionPool(1, 20)
    ├── ComplianceOne: pool.ThreadedConnectionPool(1, 10)
    └── FinOps360: pool.ThreadedConnectionPool(1, 10)

Service → Redis (redis-py 5.x)
    ├── Money: sessions, rate limiting buckets
    ├── Auth: token revocation list
    ├── Event Bus: pub/sub, streams, DLQ
    └── Orchestrator: aioredis, streams, metrics

Service → External APIs
    ├── Money → Twilio (HMAC-signed webhooks)
    ├── Money → Stripe (webhook secrets)
    ├── Money → Gemini (API key)
    ├── Apex → Kafka (aiokafka publisher)
    └── All Python → integration/auth (JWT validation)
```

---

## Integration Layer

### Auth Contract
```python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "integration", "shared")))
from jwt_validator import get_current_user   # FastAPI Depends() injection
```
Auth service hard-fails at startup if `AUTH_SECRET_KEY` is unset or < 32 chars.

### Event Contract
```python
from integration.shared.event_types import EventType   # 16 canonical event types
from integration.shared.event_bus_client import publish_sync
```

**16 event types:** `lead.created`, `lead.qualified`, `dispatch.requested`, `dispatch.completed`, `document.processed`, `agent.task.created`, `agent.task.completed`, `analytics.recorded`, `saga.started`, `saga.completed`, `saga.failed`, `user.created`, `user.updated`, `user.deleted`, `audit.log.recorded`

All `EventMetadata` fields have `max_length` constraints (hardening against memory exhaustion attacks).

### Advanced Integration Modules
- **`a2a_bridge.py`** — Google's A2A (Agent-to-Agent) protocol for cross-system agent communication between APEX, Money, Citadel, and Acropolis. Task lifecycle: `submitted → working → input_required → completed | canceled | failed`.
- **`intelligent_routing.py`** — Routes tasks using metacognitive layer predictions. Strategies: FASTEST, MOST_CAPABLE, COST_OPTIMIZED, MAL_PREDICTED, FALLBACK_SAFE.
- **`hitl_optimizer.py`** — Human-in-the-loop review queue. Auto-approves patterns with confidence > 0.65 that aren't safety/compliance type. Priority-queued for human review: LOW_CONFIDENCE, HIGH_STAKES, NOVEL_DOMAIN, DISPUTED, SAFETY_CHECK, COMPLIANCE.
- **`metacognitive_layer/`** — Layer 5 of APEX. Learns from observations using Bayesian confidence updates with exponential smoothing (alpha=0.3). Confidence: CRITICAL (0.95), HIGH (0.85), MEDIUM (0.70), LOW (0.50).
- **`nexus-runtime/`** — mmap-based shared memory with atomic synchronization matching C++20 memory order semantics (RELAXED, ACQUIRE, RELEASE, ACQ_REL, SEQ_CST).

---

## Agent Frameworks

### APEX (5-Layer Probabilistic System)
- **L2** — Uncertainty calibration
- **L3** — Specialized agents: analytics, creative, research, sales, cross-system dispatch
- **L4** — Quality assurance: debate, evolution, hostile auditor
- **L5** — Metacognitive engine (in `integration/metacognitive_layer/`): learns patterns, predicts intents, orchestrates autonomous healing

APEX agents publish to Kafka directly (`apex/apex-agents/event_publisher.py`). This is a **separate channel** from the HTTP event-bus service used by Money/ComplianceOne/FinOps360.

### CrewAI (Money Service)
4-agent crew with Google Gemini. Houston HVAC-specific urgency classifier. Tenacity retry on all Twilio sends (3 attempts, 2s wait). LangSmith tracing on all agent calls.

### Acropolis (Rust)
Polyglot agent orchestration with Julia FFI bridge for numerical computing. CLI: `serve | run <batch> | init-admin`. Admin password enforced ≥ 12 chars. OTLP telemetry export. `sled` embedded DB for auth storage.

---

## Frontend & Design

### ClearDesk
Browser-only React SPA. Parses DOCX (mammoth), PDF (pdfjs-dist), images (Tesseract.js OCR), XLSX (xlsx) in-browser. No backend. Deployed to Vercel.

### Gen-H
React SPA with Radix UI + Tailwind. HVAC lead capture flows → feeds into Money dispatch.

### reGenesis (Design System)
pnpm workspace (Node ≥ 20). `@cyberarchitect/design-tokens` is the canonical source of truth. Build order is strictly enforced: tokens first, packages second (sequential, `--parallel=false` is intentional).

### soviergn_ai
Astro static site served via Bun. Rust compiled to WASM for in-browser graph visualization. **Requires** `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp` — only `bun-server.ts` provides these. Without them, `SharedArrayBuffer` (required by WASM threading) throws a `TypeError` in all modern browsers.

---

## Security Architecture

**CORS (fail-closed):** ComplianceOne, FinOps360, and Orchestrator raise `RuntimeError` at startup if `CORS_ORIGINS` is unset or contains `*`. The platform refuses to start in an insecure configuration.

**nginx rate limiting:** `api` zone (10 req/s), `auth` zone (5 req/min).

**Vault:** TLS enforced. No `tls_disable = true`. Default lease 168h, max 720h.

**Hostile Audit Protocol:** Every code change requires `Proof: <command> → <output> @ <timestamp>` stored in `proof/hostile-audit/`. Enforced in CI via `.github/workflows/ci-cd.yml`.

---

## Quick Start

### Prerequisites
Docker, Docker Compose, Bash.

### 1. Configure Environment
```bash
cp .env.example .env
# Required keys — service will hard-fail at startup if any are missing:
# POSTGRES_USER, POSTGRES_PASSWORD
# DISPATCH_API_KEY, GEMINI_API_KEY, TWILIO_SID, TWILIO_TOKEN
# COMPLIANCEONE_API_KEY, FINOPS360_API_KEY
# REDIS_PASSWORD
# CORS_ORIGINS (comma-separated, no wildcards)
# AUTH_SECRET_KEY, JWT_SECRET (generate: python -c "import secrets; print(secrets.token_urlsafe(64))")
```

### 2. Deploy
```bash
./scripts/deploy.sh local
```

### 3. Verify
```bash
./scripts/health_check.py -v
./scripts/verify_integration.py
```

### 4. Access
- **Dashboard:** `http://localhost:9000/dashboard`
- **Money admin:** `http://localhost:8000/admin`
- **With monitoring:** `docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d`
  - Prometheus: `http://localhost:9090`
  - Grafana: `http://localhost:3000`

---

## Development Reference

### Package Managers
| Project | Manager | Constraint |
|---------|---------|-----------|
| B-A-P | **Poetry only** | pip corrupts virtualenv |
| Money, ComplianceOne, FinOps360, orchestrator, apex-agents | pip + requirements.txt | |
| ClearDesk, Gen-H, DocuMancer, apex-ui, apex-mcp | npm | |
| reGenesis | **pnpm 9.7.0** (Node ≥ 20) | workspace protocol |
| soviergn_ai | bun | runtime + Astro |
| Acropolis | cargo | Rust workspace |

### Database Ownership (no cross-service SQL)
| DB | Owner | Engine |
|----|-------|--------|
| `money` | Money | PostgreSQL 15 |
| `complianceone` | ComplianceOne | PostgreSQL 15 |
| `finops360` | FinOps360 | PostgreSQL 15 |
| `integration` | integration/auth | PostgreSQL 15 + SQLite (user store) |
| `reliantai` | root Alembic migrations | PostgreSQL 15 |
| B-A-P DB | B-A-P | PostgreSQL (asyncpg, own connection) |
| Citadel | Citadel | TimescaleDB :5433 |
| ops-intelligence | ops-intelligence | SQLite |
| citadel_ultimate_a_plus | citadel_ultimate_a_plus | SQLite |
| Acropolis | Acropolis | sled (embedded) |

### Testing
```bash
./scripts/verify_integration.py                          # platform-wide (requires running services)
cd Money && pytest tests/test_integration_suite.py -v
cd integration/auth && pytest -v
cd integration/event-bus && pytest test_event_bus_properties.py -v
cd integration/metacognitive_layer && pytest tests/ -v
cd B-A-P && poetry run pytest
cd DocuMancer && npm test && npm run test:python
cd reGenesis && pnpm run test && pnpm run test:e2e
cd Acropolis && cargo test
```

### Adding a New Python Service
1. `sys.path.append("../integration/shared")` → import `get_current_user`, `EventType`, `publish_sync`
2. `sys.path.append("../shared")` → import from `security_middleware`
3. Set `CORS_ORIGINS` env var (required; no wildcards)
4. Add to `docker-compose.yml` with health check
5. Add Prometheus scrape config to `monitoring/prometheus.yml`
6. Add upstream to `nginx/nginx.conf`
7. Capture proof in `proof/hostile-audit/`

---

## Documentation

- [`PLATFORM_GUIDE.md`](./PLATFORM_GUIDE.md) — Full architecture and operations guide
- [`USER_MANUAL.md`](./USER_MANUAL.md) — Service-by-service user manual
- [`AGENTS.md`](./AGENTS.md) — Agent operational guide (deployment, health, service control commands)
- [`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md) — Command cheat sheet
- [`PRODUCTION_CHECKLIST.md`](./PRODUCTION_CHECKLIST.md) — Pre-production checklist
- [`CLAUDE.md`](./CLAUDE.md) — Deep per-service reference for AI-assisted development
- [`integration/saga/SAGA_GUIDE.md`](./integration/saga/SAGA_GUIDE.md) — Distributed transaction guide
