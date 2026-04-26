# ReliantAI Platform - Complete API Reference

## Authentication

### API Key Authentication (Most Services)
```
Authorization: Bearer {API_KEY}
```

### Service-Specific Auth

| Service | Header | Key Env Var |
|---------|--------|-------------|
| ReliantAI API | `Authorization: Bearer` | `API_SECRET_KEY` |
| Event Bus | `Authorization: Bearer` | `EVENT_BUS_API_KEY` |
| MCP Bridge | `X-API-Key` | `MCP_API_KEY` |
| GrowthEngine | `X-API-Key` | `API_KEY` |
| Money | `X-API-Key` or Bearer | `DISPATCH_API_KEY` |

---

## Core Platform API (reliantai)

Base URL: `http://localhost:8000` (or `https://api.reliantai.org`)

### Health & Status

#### GET /health
Public health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "db": true,
  "redis": true
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Service unavailable (DB or Redis down)

---

### Prospects API

#### GET /api/v2/prospects
List all prospects (requires authentication).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Max results |
| `offset` | int | 0 | Pagination offset |
| `status` | string | - | Filter by status |
| `trade` | string | - | Filter by trade |

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "business_name": "ACME HVAC",
      "trade": "hvac",
      "city": "Atlanta",
      "state": "GA",
      "phone": "+1-555-1234",
      "email": "contact@acme.com",
      "address": "123 Main St",
      "lat": 33.749,
      "lng": -84.388,
      "google_rating": 4.5,
      "review_count": 127,
      "website_url": "https://acmehvac.com",
      "status": "identified",
      "created_at": "2026-04-25T12:00:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

---

#### POST /api/v2/prospects
Create a new prospect.

**Request Body:**
```json
{
  "business_name": "string (required)",
  "trade": "string (required: hvac|plumbing|electrical|roofing|painting|landscaping)",
  "city": "string (required)",
  "state": "string (required, 2 chars)",
  "place_id": "string (optional, Google Places ID)",
  "phone": "string (optional)",
  "email": "string (optional)",
  "address": "string (optional)",
  "lat": "number (optional)",
  "lng": "number (optional)",
  "google_rating": "number (optional)",
  "review_count": "integer (optional)"
}
```

**Response:**
```json
{
  "id": "uuid",
  "business_name": "ACME HVAC",
  "trade": "hvac",
  "city": "Atlanta",
  "state": "GA",
  "status": "identified",
  "created_at": "2026-04-25T12:00:00Z"
}
```

**Status Codes:**
- `201` - Created
- `400` - Invalid request body
- `401` - Unauthorized
- `409` - Duplicate (place_id or business_name + city exists)

---

#### GET /api/v2/prospects/{id}
Get prospect details by ID.

**Response:** Full prospect object with related data.

---

#### POST /api/v2/prospects/{id}/research
Trigger the research pipeline for a prospect.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Research pipeline started"
}
```

This triggers Celery tasks:
1. `gbp_scraper` - Scrapes Google Business Profile
2. `competitor_intel` - Analyzes competitors
3. `copy_agent` - Generates copy (Gemini 1.5 Pro)
4. `site_registration_service` - Creates GeneratedSite

---

### Generated Sites API (Public)

#### GET /api/v2/generated-sites/{slug}
**NO AUTHENTICATION REQUIRED** - Used by Client Sites ISR.

Fetches complete site content for rendering.

**Response:**
```json
{
  "slug": "acme-hvac-atlanta-1234",
  "status": "preview_live",
  "business": {
    "name": "ACME HVAC",
    "city": "Atlanta",
    "state": "GA",
    "phone": "+1-555-1234",
    "address": "123 Main St, Atlanta, GA",
    "lat": 33.749,
    "lng": -84.388,
    "rating": 4.5,
    "review_count": 127
  },
  "hero": {
    "headline": "Atlanta's Most Trusted HVAC Service",
    "subheadline": "24/7 Emergency Repair & Installation",
    "cta_text": "Get Free Estimate"
  },
  "services": [
    {
      "title": "Emergency Repair",
      "description": "Fast response when you need it most",
      "icon": "wrench"
    }
  ],
  "reviews": {
    "featured": [
      {
        "author": "John D.",
        "rating": 5,
        "text": "Great service! Fixed my AC in 30 minutes.",
        "date": "2026-03-15"
      }
    ],
    "average_rating": 4.5,
    "total_reviews": 127
  },
  "seo": {
    "title": "ACME HVAC - Atlanta's #1 Heating & Cooling Service",
    "description": "Professional HVAC repair..."
  },
  "schema_org": {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "ACME HVAC",
    "address": {...},
    "telephone": "+1-555-1234",
    "aggregateRating": {...}
  },
  "site_config": {
    "template_id": "hvac-reliable-blue",
    "trade": "hvac",
    "theme": {
      "primary": "#1d4ed8",
      "accent": "#93c5fd",
      "font_display": "Outfit",
      "font_body": "Inter"
    }
  },
  "lighthouse_score": 98,
  "meta_title": "...",
  "meta_description": "..."
}
```

**Status Codes:**
- `200` - Success
- `404` - Site not found

---

### Webhooks API

#### POST /api/v2/webhooks/gbp-reviews
Webhook for Google Business Profile review notifications.

**Request Body:**
```json
{
  "place_id": "string",
  "review_id": "string",
  "author": "string",
  "rating": 5,
  "text": "string",
  "timestamp": "2026-04-25T12:00:00Z"
}
```

---

#### POST /api/v2/webhooks/inbound-sms
Webhook for inbound SMS responses from prospects.

**Request Body:**
```json
{
  "from": "+1234567890",
  "body": "Yes, I'm interested!",
  "timestamp": "2026-04-25T12:00:00Z",
  "prospect_id": "uuid (if known)"
}
```

---

## Event Bus API

Base URL: `http://localhost:8081`

### GET /health
**Response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "service": "event-bus"
}
```

---

### POST /publish
Publish an event to the bus.

**Headers:**
```
Authorization: Bearer {EVENT_BUS_API_KEY}
Content-Type: application/json
```

**Request Body:**
```json
{
  "event_type": "lead.created",
  "payload": {
    "prospect_id": "uuid",
    "source": "manual"
  },
  "correlation_id": "corr-123",
  "tenant_id": "default",
  "source_service": "api-client"
}
```

**Event Types:**
- `lead.created` - New prospect identified
- `lead.qualified` - Prospect qualified via research
- `dispatch.requested` - Money service dispatch initiated
- `dispatch.completed` - Dispatch finished
- `document.processed` - DocuMancer processed document
- `agent.task.created` - CrewAI task started
- `agent.task.completed` - CrewAI task finished
- `saga.started` - Distributed transaction started
- `saga.completed` - Transaction completed
- `saga.failed` - Transaction failed

**Response:**
```json
{
  "event_id": "evt_1234567890_abc123",
  "status": "published",
  "channel": "events:lead"
}
```

**Status Codes:**
- `200` - Published
- `401` - Invalid API key
- `422` - Validation error (payload > 64KB)
- `500` - Internal error (queued to DLQ)

---

### GET /event/{event_id}
Retrieve a specific event by ID.

**Response:**
```json
{
  "metadata": {
    "event_id": "evt_1234567890_abc123",
    "event_type": "lead.created",
    "timestamp": "2026-04-25T12:00:00Z",
    "correlation_id": "corr-123",
    "tenant_id": "default",
    "source_service": "api-client"
  },
  "payload": {...}
}
```

---

### GET /dlq
Get Dead Letter Queue events.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Max entries (max 1000) |

**Response:**
```json
{
  "dlq_size": 5,
  "events": [
    {
      "error": "ValidationError: Invalid payload",
      "timestamp": "2026-04-25T12:00:00Z",
      "request": {...}
    }
  ]
}
```

---

### GET /metrics
Prometheus metrics endpoint.

**Response (text/plain):**
```
# HELP events_published_total Total events published
# TYPE events_published_total counter
events_published_total{channel="events:lead",event_type="lead.created"} 42

# HELP events_consumed_total Total events consumed
# TYPE events_consumed_total counter
events_consumed_total{channel="events:lead",event_type="lead.created"} 42

# HELP dlq_size Dead letter queue size
# TYPE dlq_size gauge
dlq_size 0

# HELP event_processing_duration_seconds Event processing duration
# TYPE event_processing_duration_seconds histogram
event_processing_duration_seconds_bucket{channel="events:lead",le="0.005"} 10
```

---

## MCP Bridge API

Base URL: `http://localhost:8083`

### GET /health
**Response:**
```json
{
  "status": "healthy",
  "service": "mcp-bridge",
  "tools_registered": 15
}
```

---

### GET /mcp/tools
List all registered tools.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `service` | string | Filter by service name |
| `capability` | string | Filter by capability tag |

**Response:**
```json
[
  {
    "name": "money_dispatch",
    "description": "Create a new dispatch request",
    "service": "money",
    "endpoint": "http://money:8000/dispatch",
    "method": "POST",
    "parameters": [
      {
        "name": "customer_phone",
        "type": "string",
        "description": "Customer phone number",
        "required": true
      },
      {
        "name": "address",
        "type": "string",
        "description": "Service address",
        "required": true
      }
    ],
    "returns": {
      "type": "object",
      "properties": {
        "dispatch_id": {"type": "string"},
        "status": {"type": "string"}
      }
    },
    "rate_limit": "100/min",
    "timeout_ms": 30000
  }
]
```

---

### GET /mcp/tools/{name}
Get schema for a specific tool.

---

### POST /mcp/tools/call
Execute a registered tool.

**Headers:**
```
X-API-Key: {MCP_API_KEY}
Content-Type: application/json
```

**Request Body:**
```json
{
  "tool": "money_dispatch",
  "parameters": {
    "customer_phone": "+1234567890",
    "address": "123 Main St"
  },
  "correlation_id": "corr-456",
  "requesting_agent": "orchestrator"
}
```

**Response:**
```json
{
  "tool": "money_dispatch",
  "status": "success",
  "result": {
    "dispatch_id": "disp_123",
    "status": "queued"
  },
  "execution_time_ms": 245,
  "correlation_id": "corr-456",
  "timestamp": "2026-04-25T12:00:00Z"
}
```

**Status Values:**
- `success` - Tool executed successfully
- `error` - Tool execution failed
- `timeout` - Tool timed out
- `rate_limited` - Rate limit exceeded

---

### POST /mcp/register
Register a new tool (service self-registration).

**Request Body:** MCPTool schema (see GET /mcp/tools response)

---

## Money Service API

Base URL: `http://localhost:8000` (accessed via nginx proxy)

### GET /health
**Response:**
```json
{
  "status": "healthy",
  "twilio": "connected",
  "stripe": "connected",
  "database": "connected"
}
```

---

### POST /dispatch
Create a new dispatch request.

**Auth:** `Authorization: Bearer {DISPATCH_API_KEY}` or `X-API-Key: {DISPATCH_API_KEY}`

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "address": "123 Main St, Atlanta, GA",
  "service_type": "hvac_repair",
  "description": "AC not cooling",
  "urgency": "high",
  "preferred_time": "2026-04-26T09:00:00Z"
}
```

**Response:**
```json
{
  "dispatch_id": "disp_abc123",
  "status": "queued",
  "estimated_response": "15 minutes",
  "tracking_url": "https://track.reliantai.org/disp_abc123"
}
```

---

### POST /sms
Twilio SMS webhook endpoint. **Do not call directly** - Twilio calls this.

---

### GET /dispatches
List recent dispatches.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max results |
| `status` | string | - | Filter by status |
| `date_from` | string | - | ISO date filter |

**Response:**
```json
{
  "items": [
    {
      "dispatch_id": "disp_abc123",
      "customer_name": "John Doe",
      "status": "completed",
      "service_type": "hvac_repair",
      "created_at": "2026-04-25T12:00:00Z",
      "completed_at": "2026-04-25T12:45:00Z"
    }
  ],
  "total": 150
}
```

---

### GET /run/{id}
Get async job status.

**Response:**
```json
{
  "job_id": "run_xyz789",
  "status": "completed",
  "progress": 100,
  "result": {...},
  "created_at": "2026-04-25T12:00:00Z",
  "completed_at": "2026-04-25T12:15:00Z"
}
```

---

## GrowthEngine API

Base URL: `http://localhost:8003`

### GET /health
**Response:** `{"status": "healthy"}`

---

### POST /api/prospect/scan
Scan an area for prospects using Google Places API.

**Headers:** `X-API-Key: {API_KEY}`

**Request Body:**
```json
{
  "lat": 33.7490,
  "lng": -84.3880,
  "radius_meters": 5000,
  "keyword": "hvac"
}
```

**Response:**
```json
{
  "scan_id": "scan_123",
  "total_found": 25,
  "prospects": [
    {
      "place_id": "ChIJ...",
      "name": "ABC Heating & Cooling",
      "address": "456 Peachtree St, Atlanta, GA",
      "phone": "+1-555-5678",
      "rating": 4.2,
      "review_count": 89,
      "website": "https://abcheating.com",
      "location": {
        "lat": 33.7501,
        "lng": -84.3892
      }
    }
  ],
  "quality_score": 0.78
}
```

---

### POST /api/prospect/outreach
Trigger outreach to a prospect.

**Headers:** `X-API-Key: {API_KEY}`

**Request Body:**
```json
{
  "place_id": "ChIJ...",
  "name": "ABC Heating & Cooling",
  "phone": "+1-555-5678",
  "rating": 4.2,
  "review_count": 89
}
```

**Response:**
```json
{
  "outreach_id": "out_456",
  "status": "sent",
  "channel": "sms",
  "preview_url": "https://preview.reliantai.org/abc-heating-cooling-atlanta-1234",
  "message_sent": "Hi from ReliantAI..."
}
```

---

## Orchestrator API

Base URL: `http://localhost:9000`

### GET /health
**Response:**
```json
{
  "status": "healthy",
  "orchestrator": "running",
  "services_monitored": 8,
  "active_sagas": 0
}
```

---

### GET /services
List all registered services.

**Response:**
```json
{
  "services": [
    {
      "name": "money",
      "url": "http://money:8000",
      "status": "healthy",
      "critical": true,
      "current_instances": 2,
      "min_instances": 1,
      "max_instances": 5,
      "response_time_ms": 45,
      "error_rate": 0.001
    }
  ]
}
```

---

### GET /services/{name}
Get details for a specific service.

---

### POST /services/{name}/scale
Manually scale a service.

**Request Body:**
```json
{
  "target_instances": 3,
  "reason": "High load detected"
}
```

**Response:**
```json
{
  "action_id": "scale_789",
  "service": "money",
  "from": 2,
  "to": 3,
  "status": "scaling",
  "estimated_completion": "2026-04-25T12:05:00Z"
}
```

---

### GET /metrics
Prometheus metrics for all services.

---

### WebSocket /ws
Real-time event stream.

**Connection:** `ws://localhost:9000/ws`

**Events:**
```json
{"type": "health_update", "service": "money", "status": "healthy"}
{"type": "scale_intent", "service": "money", "from": 2, "to": 3}
{"type": "heal_intent", "service": "growthengine", "action": "restart"}
{"type": "metric", "service": "money", "name": "cpu_usage", "value": 0.75}
```

---

## Auth Service API

Base URL: `http://localhost:8010`

### POST /auth/login
Authenticate and get JWT tokens.

**Request Body:**
```json
{
  "username": "admin",
  "password": "secret"
}
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### POST /auth/verify
Verify token validity.

**Headers:** `Authorization: Bearer {access_token}`

**Response:**
```json
{
  "valid": true,
  "user": {
    "id": "uuid",
    "username": "admin",
    "roles": ["admin", "operator"]
  }
}
```

---

### POST /auth/refresh
Refresh access token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbG..."
}
```

---

### GET /auth/me
Get current user info.

**Headers:** `Authorization: Bearer {access_token}`

---

## Client Sites API (Next.js)

Base URL: `https://preview.reliantai.org` (or `http://localhost:3000` for dev)

### GET /{slug}
Dynamic ISR route for client sites.

**Examples:**
- `https://preview.reliantai.org/acme-hvac-atlanta-1234`
- `https://preview.reliantai.org/plumbing-pros-dallas-5678`

**Response:** Rendered HTML page

---

### POST /api/revalidate
On-demand ISR cache purge.

**Headers:** `Authorization: Bearer {REVALIDATE_SECRET}`

**Request Body:**
```json
{
  "slug": "acme-hvac-atlanta-1234"
}
```

**Response:**
```json
{
  "revalidated": true,
  "slug": "acme-hvac-atlanta-1234",
  "timestamp": "2026-04-25T12:00:00Z"
}
```

---

### GET /showcase
Interactive template studio.

**Features:**
- 4 view modes (Preview, Grid, Prompt, Compare)
- Device frame simulation (macOS, iOS)
- Live data editing
- Template comparison

---

### GET /preview
Simplified template browser with JSON viewer.

---

## Saga Orchestrator API

Base URL: `http://localhost:8020`

### GET /health
**Response:** `{"status": "healthy"}`

---

### POST /saga
Create a new saga (distributed transaction).

**Request Body:**
```json
{
  "saga_type": "onboarding",
  "steps": [
    {
      "name": "create_user",
      "service": "auth",
      "action": "POST /users",
      "compensation_action": "DELETE /users/{id}",
      "payload": {"username": "john", "email": "john@example.com"}
    },
    {
      "name": "create_billing",
      "service": "money",
      "action": "POST /customers",
      "compensation_action": "DELETE /customers/{id}",
      "payload": {"user_id": "{steps.create_user.result.id}"}
    }
  ],
  "correlation_id": "onboard-123",
  "tenant_id": "default"
}
```

**Response:**
```json
{
  "saga_id": "saga_xyz789",
  "status": "pending",
  "created_at": "2026-04-25T12:00:00Z"
}
```

---

### GET /saga/{saga_id}
Get saga status.

**Response:**
```json
{
  "saga_id": "saga_xyz789",
  "saga_type": "onboarding",
  "status": "completed",
  "steps": [
    {
      "step_id": "step_1",
      "name": "create_user",
      "status": "completed",
      "result": {"id": "user_123"}
    },
    {
      "step_id": "step_2",
      "name": "create_billing",
      "status": "completed",
      "result": {"id": "cust_456"}
    }
  ],
  "started_at": "2026-04-25T12:00:00Z",
  "completed_at": "2026-04-25T12:00:05Z"
}
```

**Status Values:**
- `pending` - Waiting to start
- `running` - Currently executing
- `completed` - All steps successful
- `failed` - Step failed, compensation not started
- `compensating` - Running compensation actions
- `compensated` - All compensations completed

---

### POST /saga/{saga_id}/cancel
Cancel a running saga.

---

### GET /metrics
Prometheus metrics.

**Metrics:**
- `saga_started_total` - Counter by saga_type
- `saga_completed_total` - Counter by saga_type
- `saga_failed_total` - Counter by saga_type, reason
- `saga_compensated_total` - Counter by saga_type
- `saga_duration_seconds` - Histogram by saga_type
- `active_sagas` - Gauge

---

## ComplianceOne API

Base URL: `http://localhost:8001`

### GET /health
**Response:** `{"status": "healthy"}`

---

### GET /compliance/status
Overall compliance status.

**Response:**
```json
{
  "overall_status": "compliant",
  "last_audit": "2026-04-24T00:00:00Z",
  "frameworks": {
    "soc2": {"status": "compliant", "score": 98},
    "hipaa": {"status": "compliant", "score": 95},
    "gdpr": {"status": "compliant", "score": 97},
    "pci_dss": {"status": "compliant", "score": 99}
  }
}
```

---

### GET /compliance/{framework}
Framework-specific details.

**Frameworks:** `soc2`, `hipaa`, `gdpr`, `pci_dss`

---

## FinOps360 API

Base URL: `http://localhost:8002`

### GET /health
**Response:** `{"status": "healthy"}`

---

### GET /costs/summary
Multi-cloud cost summary.

**Response:**
```json
{
  "period": "2026-04-01 to 2026-04-30",
  "total": 12500.50,
  "by_cloud": {
    "aws": 8500.00,
    "gcp": 2500.50,
    "azure": 1500.00
  },
  "by_service": {
    "compute": 8000.00,
    "storage": 2000.00,
    "networking": 1500.00,
    "database": 1000.50
  },
  "trend": {
    "direction": "up",
    "change_percent": 5.2
  }
}
```

---

### GET /recommendations
Right-sizing recommendations.

**Response:**
```json
{
  "recommendations": [
    {
      "id": "rec_123",
      "type": "resize",
      "resource": "i3.2xlarge",
      "current_cost": 450.00,
      "recommended": "i3.xlarge",
      "new_cost": 225.00,
      "savings": 225.00,
      "confidence": 0.95,
      "reason": "CPU utilization avg 12% over 30 days"
    }
  ],
  "total_potential_savings": 1250.00
}
```

---

### GET /anomalies
Detected cost anomalies.

**Response:**
```json
{
  "anomalies": [
    {
      "id": "anom_456",
      "detected_at": "2026-04-25T08:00:00Z",
      "service": "S3",
      "expected_cost": 500.00,
      "actual_cost": 1200.00,
      "deviation_percent": 140,
      "severity": "high"
    }
  ]
}
```

---

## Error Response Format

All APIs use a consistent error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "correlation_id": "corr-abc123",
    "timestamp": "2026-04-25T12:00:00Z"
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing credentials |
| `FORBIDDEN` | 403 | Valid credentials, insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependency (DB, Redis) unavailable |

---

## Pagination

List endpoints use consistent pagination:

```json
{
  "items": [...],
  "total": 1000,
  "limit": 100,
  "offset": 0,
  "has_more": true,
  "next_offset": 100
}
```

**Query Parameters:**
- `limit` - Max items (default 100, max 1000)
- `offset` - Skip N items

---

## Rate Limits

| Service | Default Limit | Header |
|---------|---------------|--------|
| ReliantAI API | 100/min | `X-RateLimit-Remaining` |
| Event Bus | 1000/min | `X-RateLimit-Remaining` |
| Money | 60/min | `X-RateLimit-Remaining` |
| GrowthEngine | 60/min | `X-RateLimit-Remaining` |
| MCP Bridge | 100/min | `X-RateLimit-Remaining` |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1714042800
```

---

*API Reference Version: 1.0*
*Last Updated: April 2026*
