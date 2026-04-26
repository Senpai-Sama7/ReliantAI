# ReliantAI Platform - Microservice Instruction Manuals

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Platform API](#1-core-platform-api-reliantai)
3. [Client Sites](#2-client-sites-reliantai-client-sites)
4. [Integration Layer](#3-integration-layer)
5. [Business Services](#4-business-services)
6. [Operations Services](#5-operations-services)
7. [Shared Components](#6-shared-components)
8. [Development & Deployment](#7-development--deployment)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RELIANTAI PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │   Nginx      │────▶│  Dashboard   │     │  Client Sites │              │
│  │  (Edge)      │     │   (Static)     │     │  (Next.js)   │              │
│  └──────────────┘     └──────────────┘     └──────────────┘              │
│         │                                                           │       │
│         ▼                                                           │       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    INTEGRATION LAYER (Port 8080)                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │ Event Bus   │  │ MCP Bridge  │  │   Auth      │  │   Saga      │ │  │
│  │  │  (8081)     │  │  (8083)     │  │  (8010)     │  │  (8020)     │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│         │                              │                                   │
│         ▼                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     CORE PLATFORM (Port 8000)                       │  │
│  │  FastAPI + Celery + SQLAlchemy + CrewAI Agents                    │  │
│  │  - Prospects API                                                  │  │
│  │  - Generated Sites API                                            │  │
│  │  - Webhooks                                                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│         │                              │                                   │
│         ▼                              ▼                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Money      │  │ GrowthEngine │  │ComplianceOne │  │  FinOps360   │ │
│  │  (:8000)     │  │  (:8003)     │  │  (:8001)     │  │  (:8002)     │ │
│  │  Revenue     │  │  Lead Gen    │  │  Compliance  │  │  Cost Opt    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                              │                                   │
│         ▼                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                   INFRASTRUCTURE LAYER                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │  Postgres   │  │   Redis     │  │   Vault     │  │ Orchestrator│ │  │
│  │  │  (:5432)    │  │  (:6379)    │  │  (:8200)    │  │  (:9000)    │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    RELIANT JIT OS (Port 8085)                         │  │
│  │            Zero-Configuration AI Operations Control                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Core Platform API (reliantai/)

### Purpose
The central FastAPI platform handling prospects, site registration, and background task pipeline. Orchestrates the GBP scraping → site generation → schema submission → review monitoring workflow.

### Architecture
- **Framework**: FastAPI 2.0 with Python 3.12
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with Redis broker
- **AI Agents**: CrewAI with Gemini 1.5 Pro (CopyAgent) / Flash (others)
- **Migrations**: Alembic

### Key Files
```
reliantai/
├── main.py                  # FastAPI entry point, health checks
├── celery_app.py           # Celery configuration, beat schedule
├── db/
│   ├── __init__.py         # Session management
│   └── models.py           # SQLAlchemy models (Prospect, GeneratedSite, etc.)
├── api/v2/
│   ├── prospects.py        # Prospect management endpoints
│   ├── generated_sites.py  # Public site content endpoint (no auth)
│   └── webhooks.py         # Inbound webhooks
├── services/
│   └── site_registration_service.py  # Site creation + ISR revalidation
├── agents/
│   ├── gbp_scraper.py      # Google Business Profile scraping
│   ├── competitor_intel.py # Competitor analysis
│   ├── copy_agent.py       # AI copywriting (Gemini 1.5 Pro)
│   └── tools/              # Agent tools (schema_builder, validator)
└── tasks/
    └── prospect_tasks.py   # Celery background tasks
```

### API Endpoints

#### Health
```
GET /health
Response: {"status": "ok", "db": true, "redis": true}
```

#### Prospects (Authenticated)
```
GET  /api/v2/prospects              # List prospects
POST /api/v2/prospects              # Create prospect
GET  /api/v2/prospects/{id}         # Get prospect details
POST /api/v2/prospects/{id}/research  # Trigger research pipeline
```

#### Generated Sites (Public)
```
GET /api/v2/generated-sites/{slug}  # Fetch site content for ISR rendering
```

#### Webhooks
```
POST /api/v2/webhooks/gbp-reviews   # Google review notifications
POST /api/v2/webhooks/inbound-sms   # Customer SMS responses
```

### Database Models

#### Prospect
```python
class Prospect(Base):
    id: str (UUID)
    place_id: str (Google Places ID)
    business_name: str
    trade: str (hvac|plumbing|electrical|roofing|painting|landscaping)
    city, state: str
    phone, email, address: str
    lat, lng: Decimal
    google_rating: Decimal
    review_count: int
    website_url: str
    status: str (identified|researched|contacted|converted)
    
    Relationships:
    - research_jobs: List[ResearchJob]
    - business_intel: BusinessIntelligence
    - competitors: List[CompetitorIntelligence]
    - generated_site: GeneratedSite
    - outreach_sequences: List[OutreachSequence]
    - outreach_messages: List[OutreachMessage]
```

#### GeneratedSite
```python
class GeneratedSite(Base):
    id: str (UUID)
    prospect_id: str (FK)
    slug: str (unique, generated from business_name + city + UUID4[:4])
    template_id: str (hvac-reliable-blue, etc.)
    preview_url: str (https://preview.reliantai.org/{slug})
    site_content: JSON (copy, seo, reviews, services)
    site_config: JSON (template_id, trade, theme)
    schema_org_json: JSON (LocalBusiness structured data)
    meta_title, meta_description: str
    lighthouse_score: int
    status: str (preview_live|published|archived)
```

### Celery Configuration
```python
# Queues:
- "agents": Research pipelines, site generation
- "outreach": SMS/email followups

# Beat Schedule:
- process_scheduled_followups: every 300 seconds
```

### Hard Constraints
- **Slug generation**: `generate_slug(business_name, city)` — never from place_id
- **CopyAgent LLM**: gemini-1.5-pro (only this agent)
- **All other agents**: gemini-1.5-flash
- **Template mapping**: Trade → Template ID via `TEMPLATE_MAP`
- **ISR Revalidation**: Triggers `POST https://preview.reliantai.org/api/revalidate`

### Commands
```bash
# Local development
uvicorn reliantai.main:app --reload --port 8000

# Celery workers
celery -A reliantai.celery_app worker -Q agents --concurrency 2
celery -A reliantai.celery_app beat

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

---

## 2. Client Sites (reliantai-client-sites/)

### Purpose
Next.js App Router with ISR. Dynamically generates branded landing pages for home service businesses at `/{slug}`. Includes interactive `/showcase` (4-view template studio) and `/preview` (template browser).

### Architecture
- **Framework**: Next.js 15 App Router + React 19
- **Rendering**: ISR (Incremental Static Regeneration) with `revalidate=3600`
- **Styling**: TailwindCSS
- **Icons**: Lucide React
- **Testing**: Playwright E2E

### Key Files
```
reliantai-client-sites/
├── app/
│   ├── [slug]/page.tsx        # ISR dynamic route - fetches from API
│   ├── showcase/page.tsx      # Interactive template studio (4 views)
│   ├── preview/page.tsx       # Simplified template browser
│   └── api/revalidate/route.ts # ISR cache purge endpoint
├── components/
│   ├── showcase/
│   │   ├── DeviceFrame.tsx    # macOS/iOS device chrome
│   │   └── CodeBlock.tsx      # Syntax highlighting
│   ├── StatsBar.tsx
│   ├── CTASection.tsx
│   └── TrustBanner.tsx
├── templates/
│   ├── hvac-reliable-blue/
│   ├── plumbing-trustworthy-navy/
│   ├── electrical-sharp-gold/
│   ├── roofing-bold-copper/
│   ├── painting-clean-minimal/
│   └── landscaping-earthy-green/
├── lib/
│   ├── api.ts                 # API client for site content
│   ├── template-meta.ts       # Template metadata + generation prompts
│   └── mock-data.ts           # SiteContent mock data per trade
├── types/
│   └── SiteContent.ts         # TypeScript interfaces
├── tests/e2e/
│   └── site-generation.spec.ts
└── playwright.config.ts
```

### Routes

| Route | Type | Purpose |
|-------|------|---------|
| `/` | Static redirect | → `/showcase` |
| `/showcase` | Static | Interactive template studio (Preview/Grid/Prompt/Compare) |
| `/preview` | Static | Simplified template browser with JSON viewer |
| `/[slug]` | ISR (3600s) | Client site page from API |
| `/api/revalidate` | Server POST | On-demand ISR cache purge |

### Data Flow
1. User visits `/{slug}`
2. `getSiteContent(slug)` fetches from `reliantai/api/v2/generated-sites/{slug}`
3. `getTemplate(template_id)` dynamically imports template component
4. Template renders with `content` prop
5. ISR caches for 3600s
6. On content update, `site_registration_service._revalidate_preview_cache()` triggers revalidation

### Template System
```typescript
// Template ID format: {trade}-{adjective}-{color}
const TEMPLATES = [
  "hvac-reliable-blue",           // Primary: #1d4ed8, Font: Outfit
  "plumbing-trustworthy-navy",    // Primary: #1e3a5f, Font: Sora
  "electrical-sharp-gold",        // Primary: #1a1a1a, Accent: #fbbf24
  "roofing-bold-copper",          // Primary: #292524, Accent: #c2713a
  "painting-clean-minimal",       // Primary: #f8fafc, Font: Playfair
  "landscaping-earthy-green",     // Primary: #14532d, Accent: #86efac
];
```

### SiteContent Interface
```typescript
interface SiteContent {
  slug: string;
  status: "preview_live" | "published" | "archived";
  business: {
    name: string;
    city: string;
    state: string;
    phone: string;
    address: string;
    lat?: number;
    lng?: number;
    rating?: number;
    review_count?: number;
  };
  hero: {
    headline: string;
    subheadline: string;
    cta_text: string;
  };
  seo: {
    title: string;
    description: string;
  };
  schema_org: object;  // LocalBusiness JSON-LD
  site_config: {
    template_id: string;
    trade: string;
    theme: {
      primary: string;
      accent: string;
      font_display: string;
      font_body: string;
    };
  };
  lighthouse_score?: number;
}
```

### Hard Constraints
- **No per-site builds** — all sites render from shared ISR cache
- **Slug**: Must match `reliantai` slug exactly
- **Preview domain**: `preview.reliantai.org` — NOT reliantai.org/preview/
- **API endpoint**: `/api/v2/generated-sites/{slug}` (no auth required)
- **Revalidation**: Requires `REVALIDATE_SECRET` env var

### Commands
```bash
# Development (Turbopack)
npm run dev

# Build & Type Check
npm run build
npx tsc --noEmit

# E2E Tests
npm run test:e2e
```

---

## 3. Integration Layer

### 3.1 Event Bus (integration/event-bus/)

#### Purpose
Redis Pub/Sub messaging backbone for cross-service communication. Provides event publishing, subscription, DLQ (Dead Letter Queue), and Prometheus metrics.

#### Architecture
- **Transport**: Redis Pub/Sub (asyncio)
- **Protocol**: HTTP REST API
- **Auth**: HTTP Bearer token (EVENT_BUS_API_KEY)
- **Metrics**: Prometheus (events_published, events_consumed, events_failed, dlq_size)

#### API Endpoints
```
POST /publish              # Publish event
GET  /event/{id}           # Retrieve event by ID
GET  /dlq?limit=100        # Get dead letter queue
POST /subscribe            # Subscribe to channel
GET  /metrics              # Prometheus metrics
GET  /health               # Health check
```

#### Event Types
```python
class EventType(str, Enum):
    LEAD_CREATED = "lead.created"
    LEAD_QUALIFIED = "lead.qualified"
    DISPATCH_REQUESTED = "dispatch.requested"
    DISPATCH_COMPLETED = "dispatch.completed"
    DOCUMENT_PROCESSED = "document.processed"
    AGENT_TASK_CREATED = "agent.task.created"
    AGENT_TASK_COMPLETED = "agent.task.completed"
    SAGA_STARTED = "saga.started"
    SAGA_COMPLETED = "saga.completed"
    SAGA_FAILED = "saga.failed"
```

#### Configuration
```python
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
EVENT_RETENTION_SECONDS = 86400  # 24 hours
DLQ_MAX_SIZE = 10000
```

### 3.2 MCP Bridge (integration/mcp-bridge/)

#### Purpose
Model Context Protocol server exposing all platform microservices as discoverable, callable tools for AI agents.

#### Architecture
- **Protocol**: MCP over HTTP
- **Registry**: In-memory with Redis backup
- **Auth**: X-API-Key header

#### API Endpoints
```
GET  /mcp/tools             # List available tools
POST /mcp/tools/call        # Execute tool
GET  /mcp/tools/{name}      # Get tool schema
POST /mcp/register          # Register new tool
GET  /health                # Health check
```

#### Tool Structure
```python
class MCPTool(BaseModel):
    name: str
    description: str
    service: str              # money, complianceone, etc.
    endpoint: str             # HTTP endpoint
    method: str              # GET, POST, etc.
    parameters: List[MCPToolParameter]
    returns: Dict[str, Any]
    rate_limit: str          # e.g., "100/min"
    timeout_ms: int
```

### 3.3 Saga Orchestrator (integration/saga/)

#### Purpose
Distributed transaction coordination with compensation support. Uses Kafka for events and Redis for idempotency.

#### Architecture
- **State Machine**: SagaStatus (PENDING → RUNNING → COMPLETED/FAILED → COMPENSATING → COMPENSATED)
- **Event Bus**: Kafka (AIOKafkaProducer)
- **Storage**: Redis for idempotency and state

#### API Endpoints
```
POST /saga                 # Create new saga
GET  /saga/{saga_id}       # Get saga status
POST /saga/{saga_id}/cancel # Cancel running saga
GET  /health               # Health check
GET  /metrics              # Prometheus metrics
```

#### Configuration
```python
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SAGA_TIMEOUT_SECONDS = 300
SAGA_MAX_RETRIES = 3
```

### 3.4 Auth Service (integration/auth/)

#### Purpose
JWT-based authentication with RBAC (Role-Based Access Control).

#### Architecture
- **Storage**: SQLite (auth.db) or Redis
- **Tokens**: JWT with RS256 signing
- **Rate Limiting**: Redis-backed sliding window

#### API Endpoints
```
POST /auth/login           # Authenticate, get JWT
POST /auth/verify          # Verify token validity
POST /auth/refresh         # Refresh access token
GET  /auth/me              # Get current user info
GET  /health               # Health check
```

#### User Model
```python
class User:
    id: str
    username: str
    roles: List[str]       # admin, operator, viewer, api
    tenant_id: str
    created_at: datetime
```

---

## 4. Business Services

### 4.1 Money Service (Money/)

#### Purpose
Revenue engine handling real-world HVAC dispatching, automated SMS triage (Twilio), AI-powered job assignment (CrewAI + Gemini), and Stripe billing.

#### Architecture
- **Framework**: FastAPI
- **Database**: PostgreSQL (isolated money DB)
- **AI**: CrewAI with Gemini for dispatch decisions
- **SMS**: Twilio (voice + text)
- **Billing**: Stripe

#### Key Endpoints
```
POST /dispatch             # API dispatch request
POST /sms                  # Twilio SMS webhook
POST /whatsapp             # Twilio WhatsApp webhook
GET  /health               # Health check
GET  /run/{id}             # Async job status
GET  /dispatches           # Recent dispatch history
```

#### Data Flow
1. Customer texts/SMS to Twilio number
2. Twilio webhook POSTs to `/sms`
3. CrewAI triage agent analyzes message
4. State machine tracks conversation
5. Dispatch crew assigns technician
6. Billing calculates via Stripe
7. Events published to Event Bus

#### Configuration
```python
DISPATCH_API_KEY = os.environ["DISPATCH_API_KEY"]
TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_TOKEN = os.environ["TWILIO_TOKEN"]
TWILIO_FROM_PHONE = os.environ["TWILIO_FROM_PHONE"]
STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]
```

### 4.2 GrowthEngine (GrowthEngine/)

#### Purpose
Autonomous lead generation using Google Places API. Finds home service businesses, filters by quality, and sends personalized SMS pitches.

#### Architecture
- **Framework**: FastAPI
- **Geocoding**: Google Places API
- **Rate Limiting**: Built-in

#### Key Endpoints
```
POST /api/prospect/scan    # Scan area for prospects
POST /api/prospect/outreach # Trigger outreach to prospect
GET  /health               # Health check
```

#### Scan Request
```python
class ScanRequest(BaseModel):
    lat: float
    lng: float
    radius_meters: int = 5000
    keyword: str = "home services"
```

#### Configuration
```python
GOOGLE_PLACES_API_KEY = os.environ["GOOGLE_PLACES_API_KEY"]
API_KEY = os.environ["API_KEY"]  # Service auth
MONEY_SERVICE_URL = "http://money:8000"
```

### 4.3 ComplianceOne (ComplianceOne/)

#### Purpose
Automated compliance tracking for SOC2, HIPAA, PCI-DSS, and GDPR.

#### Architecture
- **Framework**: FastAPI
- **Database**: PostgreSQL (isolated compliance DB)
- **Monitoring**: Continuous compliance checks

#### Key Endpoints
```
GET  /health               # Health check
GET  /compliance/status    # Overall compliance status
GET  /compliance/{framework} # Framework-specific status
POST /compliance/audit     # Trigger manual audit
```

### 4.4 FinOps360 (FinOps360/)

#### Purpose
Multi-cloud cost optimization, right-sizing recommendations, and anomaly detection.

#### Architecture
- **Framework**: FastAPI
- **Integrations**: AWS Cost Explorer, GCP Billing, Azure Cost Management
- **Database**: PostgreSQL (isolated finops DB)

#### Key Endpoints
```
GET  /health               # Health check
GET  /costs/summary        # Cost summary across clouds
GET  /recommendations      # Right-sizing recommendations
GET  /anomalies            # Detected cost anomalies
```

---

## 5. Operations Services

### 5.1 Orchestrator (orchestrator/)

#### Purpose
The "Platform Brain". Runs 6 asynchronous loops to continuously monitor health, collect metrics, and autonomously scale containers using Holt-Winters forecasting and Docker APIs.

#### Architecture
- **Framework**: FastAPI + WebSockets
- **AI**: NumPy-based Holt-Winters forecasting
- **Container Runtime**: Docker API (via docker.sock)
- **Event Streaming**: Redis Streams

#### Key Components
```python
class AutonomousOrchestrator:
    - Health check loop (30s)
    - Metrics collection loop (60s)
    - AI prediction loop (300s)
    - Auto-scaling loop (300s)
    - Auto-healing loop (60s)
    - Event streaming loop (WebSocket)
```

#### Service Registry
```python
self.services = {
    "money": Service(name="money", url="http://money:8000", critical=True),
    "complianceone": Service(...),
    "finops360": Service(...),
    "growthengine": Service(...),
}
```

#### API Endpoints
```
GET  /health               # Orchestrator health
GET  /services             # List registered services
GET  /services/{name}      # Service details
POST /services/{name}/scale # Manual scale action
GET  /metrics              # Prometheus metrics
WS   /ws                   # Real-time event stream
```

#### AI Prediction (Holt-Winters)
```python
class HoltState:
    level: float
    trend: float
    alpha: float = 0.3  # Level smoothing
    beta: float = 0.1   # Trend smoothing
```

### 5.2 Reliant JIT OS (reliant-os/)

#### Purpose
Zero-configuration AI operations system. Eliminates `.env` files through secure vault-based configuration with multi-role assistant (Auto, Support, Engineer, Sales modes).

#### Architecture
- **Backend**: FastAPI + Vault
- **Frontend**: React chat interface
- **Security**: AES-256 encryption, subprocess sandboxing
- **AI**: Multi-mode assistant with code execution

#### Backend (reliant-os/backend/)
```
backend/
├── main.py               # FastAPI entry
├── vault.py              # Vault client for secrets
├── ai_engine.py          # AI mode switching
├── code_executor.py      # Sandboxed code execution
└── service_proxy.py      # Proxy to platform services
```

#### Frontend (reliant-os/frontend/)
```
frontend/
├── src/
│   ├── components/
│   │   └── Chat.tsx      # Main chat interface
│   ├── modes/
│   │   ├── AutoMode.tsx
│   │   ├── SupportMode.tsx
│   │   ├── EngineerMode.tsx
│   │   └── SalesMode.tsx
│   └── App.tsx
```

#### Security Model
- **Encryption**: AES-256 for all API keys
- **Sandbox**: 30-second timeout on code execution
- **Blacklist**: Dangerous command validation
- **Audit**: SHA-256 code hashes for all modifications

#### Modes
| Mode | Purpose |
|------|---------|
| Auto | Autonomous platform operations |
| Support | Answer questions about services |
| Engineer | Write and deploy code |
| Sales | Find leads and send pitches |

---

## 6. Shared Components (shared/)

### 6.1 Security Middleware (security_middleware.py)

#### Features
- **SecurityHeadersMiddleware**: CSP, HSTS, X-Frame-Options, etc.
- **RateLimitMiddleware**: Redis-backed sliding window (60 req/min default)
- **InputValidationMiddleware**: Request sanitization
- **AuditLogMiddleware**: Structured audit logging
- **CORS**: Fail-closed configuration

#### Usage
```python
from shared.security_middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    create_cors_middleware,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
create_cors_middleware(app)  # Fail-closed CORS
```

### 6.2 Event Types (event_types.py)

Central event schema definitions for cross-service communication.

```python
class EventMetadata(BaseModel):
    event_id: str (max_length=64)
    event_type: EventType
    timestamp: datetime
    correlation_id: str (max_length=128)
    tenant_id: str (max_length=64)
    source_service: str (max_length=64)
    version: str = "1.0"

class Event(BaseModel):
    metadata: EventMetadata
    payload: Dict[str, Any]  # Max 64KB serialized
```

### 6.3 Graceful Shutdown (graceful_shutdown.py)

Signal handling for clean shutdowns:
- SIGTERM/SIGINT handling
- Connection draining
- In-flight request completion

### 6.4 Tracing (tracing.py)

OpenTelemetry distributed tracing configuration:
- Jaeger/Zipkin export
- Service name tagging
- Span propagation

### 6.5 Docs Branding (docs_branding.py)

ReliantAI-branded API documentation:
```python
from docs_branding import configure_docs_branding
configure_docs_branding(app, service_name="Event Bus", service_color="#DC2626")
```

---

## 7. Development & Deployment

### Environment Variables

Required for all services:
```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
POSTGRES_DB=reliantai

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=optional

# API Keys
API_SECRET_KEY=platform-api-key
EVENT_BUS_API_KEY=event-bus-key
DISPATCH_API_KEY=money-service-key
MCP_API_KEY=mcp-bridge-key
ORCHESTRATOR_API_KEY=orchestrator-key
```

### Docker Compose Services

| Service | Port | Image | Dependencies |
|---------|------|-------|--------------|
| postgres | 5432 | postgres:15-alpine | - |
| redis | 6379 | redis:7-alpine | - |
| money | 8000 | Money/Dockerfile | postgres |
| complianceone | 8001 | ComplianceOne/Dockerfile | postgres |
| finops360 | 8002 | FinOps360/Dockerfile | postgres |
| growthengine | 8003 | GrowthEngine/Dockerfile | - |
| reliant-os-backend | 8004 | reliant-os/backend/Dockerfile | - |
| reliant-os-frontend | 8085 | reliant-os/frontend/Dockerfile | reliant-os-backend |
| integration | 8080 | integration/Dockerfile | redis |
| event-bus | 8081 | integration/event-bus/Dockerfile | redis |
| mcp-bridge | 8083 | integration/mcp-bridge/Dockerfile | redis, money, growthengine |
| health-aggregator | 8086 | integration/health-aggregator/Dockerfile | redis, all services |
| orchestrator | 9000 | orchestrator/Dockerfile | redis |
| actuator | 8005 | actuator/Dockerfile | redis |
| vault | 8200 | vault:1.13 | - |
| nginx | 8880 | nginx:1.25-alpine | All services |

### Deployment Commands

```bash
# Full platform startup
docker compose up -d

# Development (single service)
uvicorn reliantai.main:app --reload --port 8000
celery -A reliantai.celery_app worker -Q agents --concurrency 2
celery -A reliantai.celery_app beat

# Client sites
cd reliantai-client-sites
npm run dev

# Health checks
./scripts/health_check.py -v

# Database migrations
cd reliantai
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Testing

```bash
# Python
PYTHONPATH=. pytest tests/ -x -v

# E2E (Client Sites)
cd reliantai-client-sites
npm run test:e2e

# Pre-commit
pre-commit run --all-files
```

---

## Service Interaction Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Customer   │────▶│   Twilio    │────▶│    Money    │
│   (SMS)     │     │             │     │  Service    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Event Bus  │
                                        └──────┬──────┘
                                               │
               ┌─────────────────────────────────┼─────────────────────────┐
               │                                 │                         │
               ▼                                 ▼                         ▼
        ┌─────────────┐                  ┌─────────────┐          ┌─────────────┐
        │GrowthEngine │                  │ComplianceOne│          │  FinOps360  │
        └─────────────┘                  └─────────────┘          └─────────────┘
               │
               ▼
        ┌─────────────┐
        │  Google API │
        └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │────▶│   Next.js   │────▶│   Reliant   │
│  (Browser)  │     │   Client    │     │    API      │
└─────────────┘     │   Sites     │     └──────┬──────┘
                    └─────────────┘            │
                                                 ▼
                                          ┌─────────────┐
                                          │  PostgreSQL │
                                          └─────────────┘
```

---

## Quick Reference: Service Responsibilities

| Service | Owns | Consumes | Produces |
|---------|------|----------|----------|
| **reliantai** | Prospects, Sites, Research | Redis, Postgres | Sites, Events |
| **client-sites** | ISR Rendering | ReliantAI API | HTML Pages |
| **money** | Dispatch, SMS, Billing | Twilio, Stripe, Event Bus | Dispatches, Events |
| **growthengine** | Lead Discovery | Google Places, Money | Prospects |
| **complianceone** | Compliance State | Internal DB | Compliance Status |
| **finops360** | Cost Data | AWS/GCP/Azure APIs | Recommendations |
| **event-bus** | Message Routing | Redis | Events |
| **mcp-bridge** | Tool Registry | All Services | Tool Catalog |
| **orchestrator** | Health, Scaling | All Services | Scale/Heal Actions |
| **reliant-os** | AI Operations | All Services | Commands |

---

*Document Version: 1.0*
*Last Updated: April 2026*
*Platform Version: 2.0*
