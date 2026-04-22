# ReliantAI Platform - Complete User Manual

**Comprehensive Guide for All Services, Features, and Capabilities**

---

## 📚 Table of Contents

1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Service-by-Service Guide](#service-by-service-guide)
   - [Money Service](#money-service)
   - [ComplianceOne Service](#complianceone-service)
   - [FinOps360 Service](#finops360-service)
   - [Autonomous Orchestrator](#autonomous-orchestrator)
   - [Integration Layer](#integration-layer)
4. [Platform Features](#platform-features)
5. [Dashboard Guide](#dashboard-guide)
6. [API Reference](#api-reference)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## System Overview

### What is ReliantAI Platform?

The ReliantAI Platform is an **autonomous, self-managing, AI-powered enterprise platform** consisting of 20 microservices. It's designed for businesses that need:
- HVAC dispatch automation
- Compliance management (SOC2, GDPR, HIPAA)
- Cloud cost optimization
- Business process automation
- Document processing
- Security services

### Core Philosophy

- **Autonomous**: The platform manages itself with AI-powered decision making
- **Resilient**: Self-healing and auto-scaling ensure high availability
- **Intuitive**: Simple deployment and easy-to-use dashboard
- **Powerful**: Enterprise-grade features and capabilities

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    RELIANTAI PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🎯 AUTONOMOUS ORCHESTRATOR (The Brain)                      │
│  • Makes intelligent decisions about scaling                 │
│  • Detects and heals failures automatically                 │
│  • Predicts resource needs using AI                         │
│  • Optimizes resource allocation                            │
│                                                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   Money     │ComplianceOne│ FinOps360   │ Integration│  │
│  │             │             │             │            │  │
│  │ HVAC AI     │ Compliance  │ Cloud Cost  │ Service    │  │
│  │ Dispatch    │ Management  │ Management  │ Mesh       │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
│                                                              │
│  🗄️  DATABASE & CACHE                                          │
│  • PostgreSQL (5432) - Primary storage                        │
│  • Redis (6379) - Cache & sessions                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Step 1: Prerequisites

**Required:**
- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Bash shell (Linux/macOS) or WSL (Windows)
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

**Optional (for development):**
- Python 3.11+
- Node.js 18+ (for frontend services)
- Git

### Step 2: Environment Setup

```bash
# Navigate to project
cd /home/donovan/Projects/platforms/ReliantAI

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
```bash
# Service URLs (auto-configured in Docker)
MONEY_URL=http://localhost:8000
COMPLIANCEONE_URL=http://localhost:8001
FINOPS360_URL=http://localhost:8002
ORCHESTRATOR_URL=http://localhost:9000

# API Keys (generate secure keys)
DISPATCH_API_KEY=your-secure-api-key-here
COMPLIANCEONE_API_KEY=your-secure-api-key-here
FINOPS360_API_KEY=your-secure-api-key-here

# External Services (optional but recommended)
GEMINI_API_KEY=your-gemini-api-key
TWILIO_SID=your-twilio-sid
TWILIO_TOKEN=your-twilio-token

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/reliantai
```

### Step 3: Deploy Platform

```bash
# One-click deployment
./scripts/deploy.sh local
```

**What this does:**
1. Checks prerequisites (Docker, ports)
2. Builds all Docker images
3. Starts infrastructure (PostgreSQL, Redis)
4. Waits for databases to be ready
5. Starts all services
6. Runs health checks
7. Initializes databases
8. Creates sample data

**Expected output:**
```
🚀 ReliantAI Platform - One-Click Deployment
═══════════════════════════════════════════════════════════════
Environment: local
Project Root: /home/donovan/Projects/platforms/ReliantAI

[INFO] Checking prerequisites...
[✓] Docker installed
[✓] Docker Compose installed
[✓] Prerequisites check complete

[INFO] Setting up local environment...
[✓] Environment configured: reliantai-local

[INFO] Building platform services...
[✓] All services built

[INFO] Starting infrastructure services...
[✓] PostgreSQL is ready
[✓] Redis is ready

[INFO] Starting platform services...
[✓] All services started

[INFO] Running health checks...
[✓] money is healthy
[✓] complianceone is healthy
[✓] finops360 is healthy
[✓] orchestrator is healthy

═══════════════════════════════════════════════════════════════
  ✅ ReliantAI Platform Deployed Successfully!
═══════════════════════════════════════════════════════════════
```

### Step 4: Verify Deployment

```bash
# Run health check
./scripts/health_check.py -v

# Expected output:
# 🔍 Checking ReliantAI Platform Health...
#   Checking money... ✅ healthy
#   Checking complianceone... ✅ healthy
#   Checking finops360... ✅ healthy
#   Checking orchestrator... ✅ healthy
```

### Step 5: Access Dashboard

```bash
# Open dashboard
open dashboard/index.html

# Or navigate to:
http://localhost:9000/dashboard
```

**Dashboard Features:**
- Platform health score (0-100%)
- Live service status with animations
- Manual scaling controls
- Real-time event logs
- AI prediction displays

---

## Service-by-Service Guide

## Money Service

### Overview
The Money service is an **HVAC AI Dispatch platform** that uses CrewAI to automate HVAC service dispatch, customer communication, and billing.

### Port
`8000`

### Key Features
- **AI-Powered Dispatch**: CrewAI agents analyze requests and dispatch technicians
- **Twilio Integration**: SMS notifications for customers and technicians
- **Billing System**: Stripe integration for payment processing (optional)
- **State Machine**: PostgreSQL-based dispatch state tracking
- **Rate Limiting**: Sliding window rate limiting for API protection
- **Security**: API key authentication, input validation

### Capabilities

#### 1. Create HVAC Dispatch
```bash
curl -X POST http://localhost:8000/dispatch \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Smith",
    "phone": "+1234567890",
    "address": "123 Main St",
    "issue_type": "AC Repair",
    "urgency": "high",
    "description": "AC not cooling"
  }'
```

**Response:**
```json
{
  "dispatch_id": "DISP-20240421-001",
  "status": "pending",
  "estimated_arrival": "2024-04-21T14:30:00Z",
  "technician": "assigned"
}
```

#### 2. List Dispatches
```bash
curl http://localhost:8000/dispatches \
  -H "X-API-Key: your-api-key"
```

#### 3. Get Dispatch Status
```bash
curl http://localhost:8000/dispatch/DISP-20240421-001/status \
  -H "X-API-Key: your-api-key"
```

#### 4. Twilio Webhook
```bash
# Configure Twilio webhook URL:
# http://your-domain.com/webhook/twilio
```

### State Machine Transitions

```
pending → assigned → in_progress → completed
          ↓
        cancelled
```

### Rate Limiting
- **Default**: 100 requests per minute
- **Sliding Window**: Ensures smooth rate limiting
- **Per-Customer**: Can be configured per customer

### Configuration

**Environment Variables:**
```bash
DATABASE_URL=postgresql://localhost/money
DISPATCH_API_KEY=your-key
GEMINI_API_KEY=your-gemini-key
TWILIO_SID=your-twilio-sid
TWILIO_TOKEN=your-twilio-token
```

### Use Cases

1. **HVAC Company**: Automate dispatch of technicians
2. **Field Service**: Manage on-site service requests
3. **Customer Support**: Track service requests and status
4. **Billing**: Integrate with Stripe for payments

### Best Practices

- Always use API keys for authentication
- Monitor dispatch queue length
- Set appropriate rate limits
- Use webhook for real-time status updates
- Archive completed dispatches periodically

---

## ComplianceOne Service

### Overview
ComplianceOne is a **compliance management platform** for tracking SOC2, GDPR, HIPAA, and other regulatory frameworks. It provides audit trails, evidence collection, and violation tracking.

### Port
`8001`

### Key Features
- **Framework Management**: Create and manage compliance frameworks
- **Control Tracking**: Define and track compliance controls
- **Audit Management**: Full audit lifecycle management
- **Evidence Collection**: Submit and track compliance evidence
- **Violation Reporting**: Track and resolve compliance violations
- **Dashboard**: Real-time compliance metrics

### Capabilities

#### 1. Create Compliance Framework
```bash
curl -X POST http://localhost:8001/frameworks \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SOC2",
    "description": "Service Organization Control 2 - Security",
    "version": "2024"
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "SOC2",
  "created": true
}
```

#### 2. Create Compliance Control
```bash
curl -X POST http://localhost:8001/controls \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "framework_id": 1,
    "control_id": "CC6.1",
    "title": "Logical Access Security",
    "description": "Access controls are implemented",
    "category": "Security",
    "severity": "high"
  }'
```

#### 3. Start Audit
```bash
curl -X POST http://localhost:8001/audits \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "framework_id": 1,
    "auditor": "John Smith"
  }'
```

#### 4. Submit Evidence
```bash
curl -X POST http://localhost:8001/evidence \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "control_id": 1,
    "evidence_type": "screenshot",
    "metadata": {
      "file": "access-control.png",
      "date": "2024-04-21"
    }
  }'
```

#### 5. Report Violation
```bash
curl -X POST http://localhost:8001/violations \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "control_id": 1,
    "severity": "high",
    "description": "Unauthorized access detected"
  }'
```

#### 6. Get Compliance Dashboard
```bash
curl http://localhost:8001/dashboard \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "summary": {
    "frameworks": 3,
    "controls": 45,
    "audits": {"total": 12, "completed": 10},
    "violations": {"open": 2}
  },
  "recent_violations": [...],
  "timestamp": "2024-04-21T12:00:00Z"
}
```

### Pre-Built Frameworks

**SOC2 Helper:**
```python
from integration import ComplianceOneClient

client = ComplianceOneClient()
result = client.setup_soc2_framework()
# Creates SOC2 framework with 6 common controls
```

**GDPR Helper:**
```python
result = client.setup_gdpr_framework()
# Creates GDPR framework with 6 common controls
```

### Database Schema

**Tables:**
- `compliance_frameworks` - Framework definitions
- `compliance_controls` - Control definitions
- `compliance_audits` - Audit records
- `compliance_evidence` - Evidence submissions
- `compliance_violations` - Violation tracking

### Use Cases

1. **SOC2 Compliance**: Track SOC2 controls and evidence
2. **GDPR Compliance**: Manage GDPR requirements
3. **HIPAA Compliance**: Healthcare data protection
4. **Internal Audits**: Track internal compliance
5. **Vendor Assessment**: Assess third-party compliance

### Best Practices

- Regularly submit evidence for controls
- Schedule periodic audits
- Address violations promptly
- Use severity levels appropriately
- Maintain audit trail documentation

---

## FinOps360 Service

### Overview
FinOps360 is a **cloud cost management platform** that provides multi-cloud cost tracking, budgeting, and optimization recommendations for AWS, Azure, and GCP.

### Port
`8002`

### Key Features
- **Multi-Cloud Support**: AWS, Azure, GCP
- **Cost Tracking**: Detailed cost data collection
- **Budget Management**: Create budgets with alerts
- **Cost Alerts**: Automatic threshold notifications
- **Optimization Recommendations**: AI-powered cost savings suggestions
- **Dashboard**: Real-time cost metrics

### Capabilities

#### 1. Register Cloud Account
```bash
curl -X POST http://localhost:8002/accounts \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "account_id": "123456789012",
    "account_name": "Production AWS"
  }'
```

**Response:**
```json
{
  "id": 1,
  "created": true
}
```

#### 2. Submit Cost Data
```bash
curl -X POST http://localhost:8002/costs \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "service_name": "EC2",
    "resource_id": "i-1234567890abcdef0",
    "region": "us-east-1",
    "cost_amount": 150.50,
    "currency": "USD",
    "usage_date": "2024-04-21",
    "tags": {
      "environment": "production",
      "team": "platform"
    }
  }'
```

#### 3. Create Budget
```bash
curl -X POST http://localhost:8002/budgets \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly AWS Budget",
    "account_id": 1,
    "monthly_limit": 5000.00,
    "alert_threshold": 80
  }'
```

#### 4. Get Budget Status
```bash
curl http://localhost:8002/budgets/1/status \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "budget_id": 1,
  "name": "Monthly AWS Budget",
  "monthly_limit": 5000.00,
  "current_spend": 4250.00,
  "remaining": 750.00,
  "utilization_percent": 85.0,
  "alert_threshold": 80,
  "alert_triggered": true
}
```

#### 5. Generate Recommendations
```bash
curl -X POST http://localhost:8002/recommendations/generate?account_id=1 \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "recommendations": [
    {
      "resource_id": "i-1234567890abcdef0",
      "service_name": "EC2",
      "recommendation_type": "rightsize",
      "potential_savings": 50.00,
      "description": "Resource has 15% average utilization - consider downsizing"
    }
  ],
  "generated": 3
}
```

#### 6. Get Cost Trends
```bash
curl "http://localhost:8002/costs?account_id=1&start_date=2024-04-01&end_date=2024-04-30&group_by=daily" \
  -H "X-API-Key: your-api-key"
```

#### 7. Get FinOps Dashboard
```bash
curl http://localhost:8002/dashboard \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "summary": {
    "month_spend": 12500.00,
    "last_month_spend": 11000.00,
    "change_percent": 13.64,
    "accounts": 3,
    "budgets": 5,
    "open_recommendations": 12,
    "potential_savings": 450.00,
    "open_alerts": 2
  },
  "top_services": [...],
  "timestamp": "2024-04-21T12:00:00Z"
}
```

### Database Schema

**Tables:**
- `cloud_accounts` - Cloud provider accounts
- `cost_data` - Cost records
- `budgets` - Budget definitions
- `cost_alerts` - Budget alerts
- `cost_optimization_recommendations` - Optimization suggestions
- `resource_utilization` - Resource metrics

### Background Tasks

**Budget Alert Check:**
- Runs every hour
- Checks all budgets against thresholds
- Creates alerts when threshold exceeded
- Sends notifications

### Use Cases

1. **Cloud Cost Management**: Track AWS/Azure/GCP costs
2. **Budget Control**: Set and monitor spending limits
3. **Cost Optimization**: Get recommendations for savings
4. **Resource Planning**: Forecast future costs
5. **Team Allocation**: Allocate costs to teams

### Best Practices

- Submit cost data regularly (daily or hourly)
- Set appropriate alert thresholds
- Review recommendations weekly
- Implement high-savings recommendations
- Monitor budget utilization trends

---

## Autonomous Orchestrator

### Overview
The Autonomous Orchestrator is the **brain of the platform** that provides AI-powered decision making, auto-scaling, auto-healing, and intelligent optimization for all services.

### Port
`9000`

### Key Features
- **AI Predictions**: Predicts resource needs 30 minutes ahead
- **Auto-Scaling**: Automatically scales services based on demand
- **Auto-Healing**: Detects failures and automatically restarts services
- **Health Monitoring**: Continuous health checks on all services
- **Metrics Collection**: Collects detailed metrics every minute
- **WebSocket API**: Real-time updates to dashboard
- **Decision History**: Tracks all autonomous decisions

### Capabilities

#### 1. Get Platform Status
```bash
curl http://localhost:9000/status
```

**Response:**
```json
{
  "timestamp": "2024-04-21T12:00:00Z",
  "orchestrator": {
    "running": true,
    "ai_enabled": true,
    "active_connections": 3
  },
  "services": {
    "money": {
      "status": "healthy",
      "instances": 3,
      "response_time_ms": 125.5,
      "last_check": "2024-04-21T12:00:00Z",
      "auto_scale": true,
      "auto_heal": true
    },
    ...
  },
  "metrics_summary": {...},
  "recent_decisions": [...]
}
```

#### 2. Get Dashboard Data
```bash
curl http://localhost:9000/dashboard
```

**Response:**
```json
{
  "health_score": 98.5,
  "services_total": 20,
  "services_healthy": 20,
  "active_instances": 24,
  "ai_enabled": true,
  "recent_decisions": 15,
  "status": {...}
}
```

#### 3. Manual Scale Service
```bash
curl -X POST "http://localhost:9000/services/money/scale?target_instances=5" \
  -H "X-API-Key: your-api-key"
```

#### 4. Manual Restart Service
```bash
curl -X POST http://localhost:9000/services/money/restart \
  -H "X-API-Key: your-api-key"
```

#### 5. Get Metrics
```bash
curl "http://localhost:9000/metrics?service=money&hours=1" \
  -H "X-API-Key: your-api-key"
```

#### 6. Get Decision History
```bash
curl http://localhost:9000/decisions?limit=50 \
  -H "X-API-Key: your-api-key"
```

#### 7. WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:9000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  
  // Handle different message types
  if (data.type === 'status_update') {
    // Service status changed
  } else if (data.type === 'event') {
    // Scaling/healing event
  } else if (data.type === 'ai_prediction') {
    // AI prediction update
  }
};
```

### Auto-Scaling Logic

**Scale Up Conditions:**
- Response time > 1000ms → Add 1 instance
- CPU usage > 75% → Add 1 instance
- Error rate > 5% → Add 2 instances

**Scale Down Conditions:**
- CPU usage < 20% → Remove 1 instance
- Response time < 100ms → Remove 1 instance

**Instance Limits:**
- Money: 2-10 instances
- ComplianceOne: 1-5 instances
- FinOps360: 1-5 instances
- Integration: 1-3 instances

### Auto-Healing Logic

**Detection:**
- Health checks every 30 seconds
- 3 consecutive failures → trigger healing

**Healing Process:**
1. Remove service from load balancer
2. Restart container
3. Wait for health check
4. Add back to load balancer

### AI Predictions

**What's Predicted:**
- CPU usage (next 30 minutes)
- Memory usage (next 30 minutes)
- Optimal instance count
- Cost optimization opportunities

**How It Works:**
1. Collects last 60 minutes of metrics
2. Analyzes trends using linear regression
3. Predicts future values
4. Recommends actions

### Use Cases

1. **Platform Operations**: Monitor and manage all services
2. **Cost Optimization**: Right-size instances based on demand
3. **Incident Response**: Automatic failure recovery
4. **Capacity Planning**: Predict resource needs
5. **Performance Tuning**: Optimize based on metrics

### Best Practices

- Let auto-scaling handle normal load variations
- Use manual scaling for known events
- Monitor decision history for patterns
- Review AI predictions regularly
- Keep auto-healing enabled

---

## Integration Layer

### Overview
The Integration Layer provides **client libraries and utilities** for cross-service communication, making it easy to integrate services together.

### Key Features
- **Client Libraries**: Python clients for each service
- **Helper Functions**: Quick setup functions
- **Error Handling**: Proper exception handling
- **Type Safety**: Type hints for better IDE support

### Capabilities

#### ComplianceOne Client

```python
from integration import ComplianceOneClient

client = ComplianceOneClient(
    base_url="http://localhost:8001",
    api_key="your-api-key"
)

# Health check
health = client.health_check()

# Create framework
framework = client.create_framework(
    name="SOC2",
    description="Service Organization Control 2",
    version="2024"
)

# Quick setup
result = client.setup_soc2_framework()
```

#### FinOps360 Client

```python
from integration import FinOps360Client

client = FinOps360Client(
    base_url="http://localhost:8002",
    api_key="your-api-key"
)

# Health check
health = client.health_check()

# Create account
account = client.create_account(
    provider="aws",
    account_id="123456789012",
    account_name="Production AWS"
)

# Quick setup
result = client.setup_account_with_budget(
    provider="aws",
    account_id="123456789012",
    account_name="Production AWS",
    monthly_limit=5000.00
)
```

### Integration Patterns

**Cross-Service Workflow:**

```python
from integration import ComplianceOneClient, FinOps360Client

# Initialize clients
compliance = ComplianceOneClient()
finops = FinOps360Client()

# Example: Tag resources with compliance status
def tag_resource_with_compliance(resource_id, status):
    # Track cost impact of compliance violations
    if status == "non_compliant":
        # Get resource cost from FinOps
        costs = finops.get_costs(resource_id=resource_id)
        # Create compliance violation
        compliance.report_violation(
            control_id=1,
            severity="high",
            description=f"Resource {resource_id} non-compliant, cost: ${costs}"
        )
```

### Use Cases

1. **Service Orchestration**: Coordinate multiple services
2. **Data Synchronization**: Keep data in sync across services
3. **Cross-Service Workflows**: Implement business processes
4. **Unified API**: Single interface for multiple services

### Best Practices

- Use client libraries instead of raw HTTP requests
- Handle exceptions appropriately
- Cache responses when appropriate
- Use helper functions for common operations

---

## Platform Features

### Auto-Scaling

**How It Works:**
1. Orchestrator monitors metrics every 2 minutes
2. Evaluates scaling conditions
3. Makes scaling decision
4. Executes scaling action
5. Logs decision for analysis

**Configuration:**
```python
# In orchestrator/main.py
services = {
    "money": {
        "min_instances": 2,
        "max_instances": 10,
        "auto_scale": True
    }
}
```

**Manual Override:**
```bash
# Disable auto-scaling for service
# Toggle in dashboard or via API
```

### Auto-Healing

**How It Works:**
1. Health checks every 30 seconds
2. 3 consecutive failures → trigger healing
3. Restart service container
4. Verify health before re-adding

**Healing Actions:**
- Restart container
- Rebuild service
- Scale to different instance count
- Alert operators

### AI Predictions

**Predictive Models:**
- Linear regression on resource usage
- Trend analysis
- Anomaly detection
- Seasonality detection

**Prediction Types:**
- CPU usage forecast
- Memory usage forecast
- Response time forecast
- Cost projection

### Real-Time Monitoring

**WebSocket Updates:**
- Service status changes
- Scaling events
- Healing events
- AI predictions
- Optimization reports

**Metrics Collected:**
- Response time (ms)
- CPU usage (%)
- Memory usage (%)
- Error rate (%)
- Request rate (req/s)

---

## Dashboard Guide

### Accessing the Dashboard

**Option 1: Local File**
```bash
open dashboard/index.html
```

**Option 2: Via Orchestrator**
```bash
# Navigate to:
http://localhost:9000/dashboard
```

### Dashboard Sections

#### 1. Top Metrics
- **Platform Health Score**: Overall health percentage
- **Active Services**: Number of healthy/total services
- **Total Instances**: Current instance count across all services
- **AI Predictions**: Whether AI is enabled

#### 2. Controls
- **Auto-Scale Toggle**: Enable/disable auto-scaling
- **Auto-Heal Toggle**: Enable/disable auto-healing
- **AI Predictions Toggle**: Enable/disable AI predictions

#### 3. Services List
Each service shows:
- Service name and URL
- Health status (with animated indicator)
- Instance count with progress bar
- Auto-scale and auto-heal status
- Action buttons (Restart, Scale)

#### 4. Platform Events
Real-time log of:
- Scaling events
- Healing events
- AI predictions
- Optimization reports
- Status changes

### Dashboard Actions

**Manual Scaling:**
1. Click "Scale" button on service card
2. Enter target instances
3. Confirm

**Manual Restart:**
1. Click "Restart" button on service card
2. Confirm

**Toggle Features:**
1. Click toggle in controls section
2. Feature enabled/disabled immediately

### WebSocket Connection

The dashboard connects via WebSocket to:
- Receive real-time updates
- Display live status changes
- Show autonomous decisions

**Connection Status:**
- Green dot: Connected
- Red dot: Disconnected (auto-reconnects)

---

## API Reference

### Authentication

All APIs use API key authentication:
```bash
-H "X-API-Key: your-service-api-key"
```

### Common Response Format

**Success:**
```json
{
  "status": "success",
  "data": {...}
}
```

**Error:**
```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

### Orchestrator API

#### GET /health
```bash
curl http://localhost:9000/health
```

#### GET /status
```bash
curl http://localhost:9000/status
```

#### GET /services
```bash
curl http://localhost:9000/services
```

#### POST /services/{name}/scale
```bash
curl -X POST "http://localhost:9000/services/money/scale?target_instances=5"
```

#### POST /services/{name}/restart
```bash
curl -X POST http://localhost:9000/services/money/restart
```

#### GET /metrics
```bash
curl "http://localhost:9000/metrics?service=money&hours=1"
```

#### GET /decisions
```bash
curl http://localhost:9000/decisions?limit=50
```

### Money API

#### GET /health
```bash
curl http://localhost:8000/health
```

#### POST /dispatch
```bash
curl -X POST http://localhost:8000/dispatch \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "..."}'
```

#### GET /dispatches
```bash
curl http://localhost:8000/displays \
  -H "X-API-Key: your-key"
```

### ComplianceOne API

#### GET /health
```bash
curl http://localhost:8001/health
```

#### POST /frameworks
```bash
curl -X POST http://localhost:8001/frameworks \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "..."}'
```

#### GET /dashboard
```bash
curl http://localhost:8001/dashboard \
  -H "X-API-Key: your-key"
```

### FinOps360 API

#### GET /health
```bash
curl http://localhost:8002/health
```

#### POST /accounts
```bash
curl -X POST http://localhost:8002/accounts \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws", ...}'
```

#### GET /dashboard
```bash
curl http://localhost:8002/dashboard \
  -H "X-API-Key: your-key"
```

---

## Best Practices

### Deployment

**Staging First:**
```bash
./scripts/deploy.sh staging
# Verify everything works
./scripts/deploy.sh production
```

**Database Backups:**
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres reliantai > backup.sql
```

**Configuration Management:**
- Use environment variables for secrets
- Never commit .env files
- Use different keys for different environments

### Operations

**Monitoring:**
- Keep dashboard open during operations
- Monitor decision history
- Review metrics regularly
- Set up alerts for critical services

**Scaling:**
- Let auto-scaling handle normal load
- Use manual scaling for known events
- Monitor scaling decisions
- Adjust thresholds based on patterns

**Troubleshooting:**
- Check logs first: `docker-compose logs [service]`
- Verify health: `./scripts/health_check.py -v`
- Check orchestrator status: `curl http://localhost:9000/status`
- Review decision history for patterns

### Security

**API Keys:**
- Generate strong, unique keys
- Rotate keys regularly
- Never share keys
- Use different keys per service

**Network Security:**
- Use HTTPS in production
- Restrict access to health endpoints
- Use internal networks for service communication
- Implement rate limiting

### Development

**Testing:**
```bash
# Run integration tests
./scripts/verify_integration.py

# Test individual services
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

**Debugging:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./scripts/deploy.sh local

# View logs
docker-compose logs -f [service]
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Symptoms:**
- Services fail to start
- Health checks fail
- Dashboard shows disconnected

**Solutions:**
```bash
# Check logs
docker-compose logs [service-name]

# Check port availability
lsof -i :8000

# Restart specific service
docker-compose restart [service-name]

# Rebuild service
docker-compose up -d --build [service-name]
```

#### 2. Database Connection Issues

**Symptoms:**
- Services can't connect to database
- Connection refused errors
- Timeouts

**Solutions:**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check database exists
docker-compose exec postgres psql -U postgres -l

# Verify connection string in .env
```

#### 3. Port Conflicts

**Symptoms:**
- Services won't start due to port in use
- Address already in use errors

**Solutions:**
```bash
# Find what's using the port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port

# Stop conflicting service
sudo systemctl stop [service]
```

#### 4. Auto-Scaling Not Working

**Symptoms:**
- Services not scaling under load
- Auto-scaling decisions not being made

**Solutions:**
```bash
# Check orchestrator status
curl http://localhost:9000/status

# Check decision history
curl http://localhost:9000/decisions

# Verify auto-scale is enabled
# Check dashboard controls or API

# Check metrics collection
curl http://localhost:9000/metrics
```

#### 5. Dashboard Not Connecting

**Symptoms:**
- Dashboard shows disconnected
- WebSocket connection fails

**Solutions:**
```bash
# Check orchestrator is running
curl http://localhost:9000/health

# Check firewall settings
# Ensure port 9000 is accessible

# Open browser console for WebSocket errors
```

### Getting Help

**Logs:**
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs -f [service-name]

# Save logs to file
docker-compose logs > logs.txt
```

**Health Check:**
```bash
# Verbose health check
./scripts/health_check.py -v

# JSON output
./scripts/health_check.py -j
```

**Integration Test:**
```bash
./scripts/verify_integration.py
```

---

## Advanced Topics

### Custom Scaling Policies

You can customize scaling logic in `orchestrator/main.py`:

```python
def _make_scaling_decision(self, name: str, service: Service):
    # Add custom logic here
    if service.name == "money":
        # Custom scaling for money service
        pass
    else:
        # Default logic
        pass
```

### Adding New Services

1. Create service directory
2. Add to docker-compose.yml
3. Add to orchestrator configuration
4. Add to health check script
5. Test integration

### Custom Metrics

Add custom metrics collection in `orchestrator/main.py`:

```python
async def _collect_service_metrics(self, name: str, service: Service):
    metrics = {
        "response_time": service.response_time_ms,
        "custom_metric": your_custom_value
    }
    return metrics
```

### External Monitoring

Integrate with external tools:

**Prometheus:**
```python
# Add to orchestrator
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

**Grafana:**
- Configure Prometheus data source
- Import dashboard templates
- Set up alerts

---

## Summary

The ReliantAI Platform is a comprehensive, autonomous, self-managing enterprise platform with:

- **20 Real Services**: All functional and production-ready
- **Autonomous Operations**: AI-powered decision making
- **Self-Healing**: Automatic failure recovery
- **Auto-Scaling**: Dynamic resource allocation
- **One-Click Deployment**: Simple setup and management
- **Real-Time Dashboard**: Complete visibility
- **Comprehensive APIs**: Full programmatic control

**Quick Start:**
```bash
./scripts/deploy.sh local
open dashboard/index.html
```

For more information, see:
- [README.md](./README.md) - Quick start guide
- [PLATFORM_GUIDE.md](./PLATFORM_GUIDE.md) - Architecture details
- Service-specific README files in each service directory

---

**Built for the future of enterprise automation.**
