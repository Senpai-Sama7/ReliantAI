# ReliantAI Platform Architecture Map

## System Topology

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    EXTERNAL LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │   End User   │  │   End User   │  │    Twilio    │  │   Google     │                │
│  │   (Browser)  │  │   (Mobile)   │  │   (SMS/Voice)│  │    Places    │                │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │
└─────────┼─────────────────┼───────────────────┼─────────────────┼──────────────────────┘
          │                 │                   │                 │
          ▼                 ▼                   ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    EDGE LAYER                                            │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                              Nginx (Port 8880)                                │      │
│  │  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐    │      │
│  │  │  /              │  /showcase      │  /preview       │  /api/*         │    │      │
│  │  │  → Dashboard    │  → Showcase     │  → Preview      │  → Proxy to     │    │      │
│  │  │                 │                 │                 │    Services     │    │      │
│  │  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘    │      │
│  │                                                                               │      │
│  │  TLS Termination • Rate Limiting • Security Headers • Static Assets          │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT SITES LAYER                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                      Next.js App Router (ISR)                                  │      │
│  │                                                                               │      │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │      │
│  │  │  Route                    │ Type    │ Purpose                         │     │      │
│  │  ├─────────────────────────────────────────────────────────────────────┤     │      │
│  │  │  /showcase                │ Static  │ 4-view template studio          │     │      │
│  │  │  /preview                 │ Static  │ Template browser + JSON         │     │      │
│  │  │  /[slug]                  │ ISR     │ Dynamic client sites            │     │      │
│  │  │  /api/revalidate          │ API     │ Cache purge endpoint            │     │      │
│  │  └─────────────────────────────────────────────────────────────────────┘     │      │
│  │                                                                               │      │
│  │  Templates: hvac-reliable-blue • plumbing-trustworthy-navy                    │      │
│  │             electrical-sharp-gold • roofing-bold-copper                       │      │
│  │             painting-clean-minimal • landscaping-earthy-green               │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
          │
          │  HTTP GET /api/v2/generated-sites/{slug}
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CORE PLATFORM LAYER                                       │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                    ReliantAI API (Port 8000) - FastAPI                       │      │
│  │                                                                              │      │
│  │  ┌────────────────────────────────────────────────────────────────────┐     │      │
│  │  │  ENDPOINT                          │ AUTH        │ PURPOSE        │     │      │
│  │  ├────────────────────────────────────────────────────────────────────┤     │      │
│  │  │  GET /health                       │ None        │ Health check   │     │      │
│  │  │  GET /api/v2/generated-sites/*     │ None        │ Public content │     │      │
│  │  │  GET /api/v2/prospects             │ API Key     │ List prospects │     │      │
│  │  │  POST /api/v2/prospects            │ API Key     │ Create prospect│     │      │
│  │  │  POST /api/v2/prospects/{id}/research │ API Key  │ Trigger pipeline│    │      │
│  │  │  POST /api/v2/webhooks/*           │ Webhook Sig │ Inbound events │     │      │
│  │  └────────────────────────────────────────────────────────────────────┘     │      │
│  │                                                                              │      │
│  │  ┌────────────────────────────────────────────────────────────────────┐     │      │
│  │  │                    Celery Workers                                   │     │      │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │     │      │
│  │  │  │ gbp_scraper  │  │copy_agent    │  │competitor_intel│            │     │      │
│  │  │  │ (Gemini Flash)│  │(Gemini Pro) │  │(Gemini Flash) │            │     │      │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘              │     │      │
│  │  │                                                                     │     │      │
│  │  │  Queues: "agents" (research) • "outreach" (followups)           │     │      │
│  │  │  Beat: process_scheduled_followups every 300s                     │     │      │
│  │  └────────────────────────────────────────────────────────────────────┘     │      │
│  │                                                                              │      │
│  │  ┌────────────────────────────────────────────────────────────────────┐     │      │
│  │  │                    Database Models                                  │     │      │
│  │  │                                                                     │     │      │
│  │  │  Prospect → ResearchJob → BusinessIntelligence                      │     │      │
│  │  │       ↓                                                               │     │      │
│  │  │  GeneratedSite (slug → preview.reliantai.org/{slug})               │     │      │
│  │  │       ↓                                                               │     │      │
│  │  │  OutreachSequence → OutreachMessage                                 │     │      │
│  │  └────────────────────────────────────────────────────────────────────┘     │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
          │
          │  Events via HTTP
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              INTEGRATION LAYER                                         │
│                                                                                         │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐               │
│  │    EVENT BUS       │  │   MCP BRIDGE       │  │  SAGA ORCHESTRATOR │               │
│  │    (Port 8081)     │  │   (Port 8083)      │  │   (Port 8020)      │               │
│  │                    │  │                    │  │                    │               │
│  │  Redis Pub/Sub     │  │  Tool Registry     │  │  Distributed Tx    │               │
│  │  DLQ Support       │  │  AI Agent Bridge   │  │  Compensation      │               │
│  │  Prometheus Metrics│  │  Schema Discovery  │  │  Kafka Events      │               │
│  └──────────┬─────────┘  └──────────┬─────────┘  └──────────┬─────────┘               │
│             │                       │                       │                           │
│             └───────────────────────┼───────────────────────┘                           │
│                                     │                                                   │
│                                     ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                         AUTH SERVICE (Port 8010)                               │      │
│  │                                                                              │      │
│  │    JWT Tokens (RS256) • RBAC • Rate Limiting • SQLite/Redis                   │      │
│  │                                                                              │      │
│  │    POST /auth/login    → JWT Access + Refresh                                │      │
│  │    POST /auth/verify   → Token validation                                    │      │
│  │    GET  /auth/me       → User profile                                        │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              BUSINESS SERVICES LAYER                                   │
│                                                                                         │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐    │
│  │       MONEY            │  │    GROWTHENGINE        │  │    COMPLIANCEONE       │    │
│  │     (Port 8000)        │  │     (Port 8003)        │  │     (Port 8001)        │    │
│  │                        │  │                        │  │                        │    │
│  │  💰 Revenue Engine     │  │  🎯 Lead Generation    │  │  🛡️ Compliance         │    │
│  │                        │  │                        │  │                        │    │
│  │  • Twilio SMS/Voice    │  │  • Google Places API   │  │  • SOC2 Tracking       │    │
│  │  • CrewAI Dispatch     │  │  • Prospect Scanning   │  │  • HIPAA Audits        │    │
│  │  • Stripe Billing      │  │  • SMS Outreach        │  │  • GDPR Compliance     │    │
│  │  • State Machine       │  │  • Quality Filtering   │  │  • PCI-DSS Monitoring  │    │
│  │                        │  │                        │  │                        │    │
│  │  POST /dispatch        │  │  POST /api/prospect/scan│  │  GET /compliance/status│   │
│  │  POST /sms (webhook)   │  │  POST /api/prospect/outreach                    │    │
│  │  GET /health           │  │  GET /health            │  │  GET /health           │    │
│  └────────────────────────┘  └────────────────────────┘  └────────────────────────┘    │
│                                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                           FINOPS360 (Port 8002)                              │      │
│  │                                                                              │      │
│  │  ☁️ Multi-Cloud Cost Optimization                                            │      │
│  │                                                                              │      │
│  │  • AWS Cost Explorer      • Right-sizing Recommendations                     │      │
│  │  • GCP Billing            • Anomaly Detection                                │      │
│  │  • Azure Cost Mgmt        • Budget Alerts                                    │      │
│  │                                                                              │      │
│  │  GET /costs/summary     GET /recommendations    GET /anomalies               │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OPERATIONS LAYER                                          │
│                                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                      ORCHESTRATOR (Port 9000)                                │      │
│  │                                                                              │      │
│  │  🧠 The "Platform Brain" - Autonomous Operations                             │      │
│  │                                                                              │      │
│  │  ┌────────────────────────────────────────────────────────────────────┐     │      │
│  │  │  6 ASYNC LOOPS                       │ INTERVAL  │ PURPOSE        │     │      │
│  │  ├────────────────────────────────────────────────────────────────────┤     │      │
│  │  │  Health Check Loop                   │ 30s       │ Service health │     │      │
│  │  │  Metrics Collection Loop             │ 60s       │ Gather metrics │     │      │
│  │  │  AI Prediction Loop (Holt-Winters)   │ 300s      │ Forecast load│     │      │
│  │  │  Auto-Scaling Loop                   │ 300s      │ Scale services │     │      │
│  │  │  Auto-Healing Loop                   │ 60s       │ Fix failures │     │      │
│  │  │  Event Streaming Loop                │ Real-time │ WebSocket push │   │      │
│  │  └────────────────────────────────────────────────────────────────────┘     │      │
│  │                                                                              │      │
│  │  Capabilities:                                                               │      │
│  │  • Docker API Integration (via docker.sock)                                   │      │
│  │  • Holt-Winters Forecasting (α=0.3, β=0.1)                                  │      │
│  │  • Redis Streams for event distribution                                     │      │
│  │  • WebSocket real-time dashboard                                            │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
│                                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                    RELIANT JIT OS (Port 8085)                                │      │
│  │                                                                              │      │
│  │  🤖 Zero-Configuration AI Operations                                         │      │
│  │                                                                              │      │
│  │  Backend:  FastAPI + Vault (AES-256) + Sandboxed Code Execution              │      │
│  │  Frontend: React Chat Interface                                               │      │
│  │                                                                              │      │
│  │  Modes:  Auto (autonomous) • Support (Q&A) • Engineer (coding) • Sales (leads)│     │
│  │                                                                              │      │
│  │  Security: 30s timeout • Command blacklist • SHA-256 audit trail             │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
│                                                                                         │
│  ┌────────────────────────┐  ┌────────────────────────┐                                │
│  │      ACTUATOR          │  │  HEALTH AGGREGATOR     │                                │
│  │     (Port 8005)        │  │    (Port 8086)         │                                │
│  │                        │  │                        │                                │
│  │  Docker Container      │  │  Multi-service health  │                                │
│  │  Control (start/stop/  │  │  aggregation + status    │                                │
│  │  restart/scale)        │  │  dashboard endpoint    │                                │
│  └────────────────────────┘  └────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              INFRASTRUCTURE LAYER                                      │
│                                                                                         │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐    │
│  │     POSTGRESQL         │  │       REDIS            │  │       VAULT            │    │
│  │     (Port 5432)        │  │     (Port 6379)        │  │     (Port 8200)        │    │
│  │                        │  │                        │  │                        │    │
│  │  • Isolated DB per     │  │  • Celery Broker       │  │  • Secret Management   │    │
│  │    service             │  │  • Caching Layer       │  │  • AES-256 Encryption  │    │
│  │  • SQLAlchemy ORM      │  │  • Session Store       │  │  • Dynamic credentials │    │
│  │  • Alembic Migrations  │  │  • Pub/Sub Events      │  │  • Audit Logging       │    │
│  │                        │  │  • Rate Limiting       │  │                        │    │
│  │  Databases:            │  │                        │  │                        │    │
│  │  - reliantai           │  │  Streams:              │  │                        │    │
│  │  - money               │  │  - reliantai:scale_intents                                    │
│  │  - complianceone       │  │  - reliantai:heal_intents                                   │
│  │  - finops360           │  │  - reliantai:platform_events                                  │
│  │  - growthengine        │  │                        │  │                        │    │
│  └────────────────────────┘  └────────────────────────┘  └────────────────────────┘    │
│                                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────┐      │
│  │                         KAFKA (Event Streaming)                              │      │
│  │                                                                              │      │
│  │  Topics:                                                                     │      │
│  │  • saga.events        • platform.telemetry                                 │      │
│  │  • service.metrics    • audit.logs                                         │      │
│  └──────────────────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### 1. New Prospect → Generated Site

```
┌─────────┐     ┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User   │────▶│ GrowthEngine  │────▶│  ReliantAI API  │────▶│   Celery Task   │
│         │     │ /prospect/scan│     │  POST /prospects│     │  (ResearchJob)  │
└─────────┘     └───────────────┘     └─────────────────┘     └─────────────────┘
                                                                           │
                                                                           ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────┐
│  Client Sites   │◀────│  ISR Revalidate │◀────│ GeneratedSite   │◀────│   AI    │
│   /{slug}       │     │   API Call      │     │   (DB Record)   │     │ Agents  │
│  (Renders Page) │     │                 │     │                 │     │         │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────┘
```

### 2. Customer SMS → Dispatch

```
┌──────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Customer │────▶│   Twilio    │────▶│    Money    │────▶│   CrewAI    │
│  (SMS)   │     │   Webhook   │     │  /sms POST  │     │  Triage Agent│
└──────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                                                                   ▼
┌──────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SMS    │◀────│   State     │◀────│  Dispatch   │◀────│  Decision   │
│ Response │     │   Machine   │     │   Crew      │     │  (Assign)   │
└──────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 3. Platform Auto-Healing

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Service    │────▶│Orchestrator │────▶│   Health    │────▶│   Action    │
│  (Failed)   │     │Health Check │     │  Analysis   │     │  Decision   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Service   │◀────│   Docker    │◀────│   Restart   │◀────│   Heal      │
│  (Healthy)  │     │    API      │     │  Container  │     │  Action     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     reliantai-network (bridge)                  │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Service    │◀────▶│   Service    │◀────▶│   Service    │ │
│  │   (Port)     │      │   (Port)     │      │   (Port)     │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                     │                     │           │
│         └─────────────────────┼─────────────────────┘           │
│                               │                                 │
│                               ▼                                 │
│                    ┌──────────────────────┐                     │
│                    │      REDIS           │                     │
│                    │   (Message Bus)      │                     │
│                    └──────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Port Reference

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Nginx | 80 | 8880 | Edge routing |
| ReliantAI API | 8000 | 8000 | Core platform |
| Money | 8000 | 8000 | Revenue engine |
| ComplianceOne | 8001 | 8001 | Compliance |
| FinOps360 | 8002 | 8002 | Cost optimization |
| GrowthEngine | 8003 | 8003 | Lead generation |
| Reliant OS Backend | 8004 | 8004 | AI operations API |
| Actuator | 8005 | 8005 | Container control |
| Auth | 8010 | 8010 | JWT authentication |
| Saga | 8020 | 8020 | Distributed transactions |
| Integration | 8080 | 8080 | Service mesh |
| Event Bus | 8081 | 8081 | Event messaging |
| MCP Bridge | 8083 | 8083 | AI tool registry |
| Reliant OS Frontend | 80 | 8085 | AI operations UI |
| Health Aggregator | 8086 | 8086 | Health dashboard |
| Orchestrator | 9000 | 9000 | Auto-scaling |
| PostgreSQL | 5432 | 5432 | Primary database |
| Redis | 6379 | 6380 (configurable) | Cache/messaging |
| Vault | 8200 | 8200 | Secret management |

## Environment Dependencies

```
postgres
    ├── money
    ├── complianceone
    ├── finops360
    └── growthengine

redis
    ├── integration
    ├── event-bus
    ├── orchestrator
    ├── mcp-bridge
    ├── health-aggregator
    └── actuator

money
    └── mcp-bridge (depends_on)
    
orchestrator
    └── docker.sock (volume mount)
    
nginx
    └── all services (waits for start)
```

---

*This architecture map provides a complete visual reference for the ReliantAI platform topology.*
