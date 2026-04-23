# 📖 ReliantAI Platform — User Manual

Welcome to the **ReliantAI Platform**. This manual is designed to provide you with an intuitive, comprehensive understanding of the platform's features, architecture, and operational procedures. Whether you are an engineer, an operator, or a product manager, this guide will help you navigate and utilize the system effectively.

---

## 📑 Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Core Concepts & Architecture](#2-core-concepts--architecture)
3. [Service Deep Dives](#3-service-deep-dives)
   - [💰 Money (Revenue & Dispatch)](#-money-revenue--dispatch)
   - [🛡️ ComplianceOne (Governance)](#-complianceone-governance)
   - [💸 FinOps360 (Cost Optimization)](#-finops360-cost-optimization)
   - [🧠 Orchestrator (Platform Brain)](#-orchestrator-platform-brain)
   - [🤖 Apex Framework (AI Agents)](#-apex-framework-ai-agents)
   - [🏢 Gen-H (Lead Gen)](#-gen-h-lead-gen)
   - [📊 Ops-Intelligence & Citadel](#-ops-intelligence--citadel)
   - [🔌 Integration & Auth (Event Bus)](#-integration--auth-event-bus)
4. [Deployment & Operations](#4-deployment--operations)
5. [API & Authentication](#5-api--authentication)
6. [Troubleshooting Guide](#6-troubleshooting-guide)

---

## 1. Platform Overview

ReliantAI is an enterprise-grade, event-driven microservices ecosystem. It is designed to autonomously run a business (like an HVAC service company) while simultaneously providing enterprise SaaS capabilities (Compliance, Cloud Cost Optimization, AI orchestration).

**Key Capabilities:**
- **Autonomous Dispatching:** SMS messages from customers are triaged by AI (CrewAI + Gemini) and automatically routed to technicians.
- **Self-Healing Infrastructure:** The platform monitors its own CPU/Memory metrics and uses predictive algorithms (Holt-Winters) to scale services up or down dynamically.
- **Strict Data Isolation:** Every service has its own dedicated PostgreSQL database. Services communicate *only* via HTTP REST or the Redis Event Bus.

---

## 2. Core Concepts & Architecture

To use or develop on ReliantAI, you must understand three core patterns:

### Event-Driven CQRS
We strictly separate reads and writes. When a service (e.g., `Money`) updates a record, it publishes an event (`dispatch_completed`) to the **Event Bus**. Other services subscribe to these events to update their own read models.

### Distributed Sagas
For transactions spanning multiple services (e.g., *Register User -> Bill Credit Card -> Provision Cloud Account*), we use the **Saga Pattern**. If a step fails, the Saga Orchestrator triggers compensating (rollback) events in reverse order.

### Circuit Breakers
External integrations (Twilio, Stripe, Cloud APIs) are wrapped in Circuit Breakers. If an API fails 3 times, the breaker "opens" for 30 seconds, immediately returning 503s to prevent system lockup and queue exhaustion.

---

## 3. Service Deep Dives

### 💰 Money (Revenue & Dispatch)
**Purpose:** Handles incoming customer requests, job dispatching, and billing.
**Key Features:**
- **Twilio SMS Webhook:** Receives SMS messages.
- **AI Triage:** Uses CrewAI agents and Gemini to assess emergency levels (e.g., "My AC is leaking!" -> Emergency).
- **Stripe Integration:** Handles customer invoicing.

### 🛡️ ComplianceOne (Governance)
**Purpose:** Continuously tracks organizational compliance against frameworks like SOC2, HIPAA, and GDPR.
**Key Features:**
- **Automated Evidence Collection:** Ingests events from other services to prove compliance (e.g., user access logs).
- **Gap Analysis:** Identifies missing controls and generates remediation reports.

### 💸 FinOps360 (Cost Optimization)
**Purpose:** Analyzes cloud provider infrastructure costs.
**Key Features:**
- **Right-Sizing:** Recommends downgrading underutilized instances.
- **Automated Tagging:** Integrates with AWS/Azure/GCP to apply compliance tags to cloud resources.
- **Anomaly Detection:** Alerts on sudden spikes in cloud spending.

### 🧠 Orchestrator (Platform Brain)
**Purpose:** The autonomic nervous system of the platform.
**Key Features:**
- **Six Async Loops:** Continuously runs loops for Health, Metrics, Scaling, Healing, AI Predictions, and Reporting.
- **Docker API Integration:** Automatically scales up containers (`docker scale`) when load increases.
- **WebSocket Feeds:** Pushes live system metrics to the dashboard.

### 🤖 Apex Framework (AI Agents)
**Purpose:** A comprehensive suite for deploying, managing, and interacting with AI agents.
**Components:**
- `apex-ui`: The Next.js frontend for agent interaction.
- `apex-agents`: The backend routing engine.
- `apex-mcp`: Integrates the Model Context Protocol (MCP) to allow agents to utilize external tools seamlessly.

### 🏢 Gen-H (Lead Gen)
**Purpose:** High-conversion templating library and lead generation for home service professionals.
**Key Features:**
- Pre-built, customizable UI templates.
- Lead capture forms routed directly into the `Money` service CRM.

### 📊 Ops-Intelligence & Citadel
**Purpose:** Analytics, telemetry, and market intelligence.
**Key Features:**
- `Ops-Intelligence`: Aggregates logs, metrics, and traces for operator dashboards.
- `Citadel Ultimate A+`: Ingests census data and market metrics to rank territories and prioritize ad spend.

### 🔌 Integration & Auth (Event Bus)
**Purpose:** The central nervous system.
**Key Features:**
- **Event Bus (`:8081`):** Redis-backed pub/sub system with strict 64KB payload validation.
- **Auth Server (`:8080`):** Issues and validates JWTs using RS256 asymmetric keys.
- **Saga Orchestrator:** Manages distributed rollbacks.

---

## 4. Deployment & Operations

### Local Development
To spin up the entire platform locally:
```bash
# 1. Setup environment variables
cp .env.example .env

# 2. Run the deployment script
./scripts/deploy.sh local

# 3. Verify Health
./scripts/health_check.py -v
```

### Production Deployment
Production deployments use `docker-compose.yml` merged with `docker-compose.prod.yml` (if applicable), enforcing strict security, HSTS, and TLS.
```bash
./scripts/deploy.sh production
```

### Managing Services
- **View Logs:** `docker compose logs -f <service_name>`
- **Restart a Service:** `docker compose restart <service_name>`
- **Manually Scale:** `docker compose up -d --scale money=3`

---

## 5. API & Authentication

### Authentication Flow
All public endpoints are protected by `SecurityHeadersMiddleware` and `RateLimitMiddleware`. 
1. Obtain a token via `POST /api/auth/login`.
2. Pass the token in the `Authorization: Bearer <token>` header.
3. Services validate the JWT locally using the public key provided by the Auth Service.

### Cross-Origin Resource Sharing (CORS)
CORS is strictly enforced. In `.env`, ensure `CORS_ORIGINS` accurately reflects your frontend domains (e.g., `https://app.reliantai.com`). Wildcards (`*`) are prohibited in production.

---

## 6. Troubleshooting Guide

**1. Service X shows as `(unhealthy)` in Docker**
- **Cause:** The Docker healthcheck failed.
- **Fix:** Check the logs: `docker compose logs <service>`. Ensure the service is actually listening on the port. Verify that the `.env` variables are correctly populated.

**2. Authentication returns 503 Unavailable**
- **Cause:** The service cannot reach the `integration` Auth Server, or the JWT public key is missing.
- **Fix:** Ensure the `integration` container is healthy. Check the `AUTH_SERVICE_URL` variable.

**3. "invalid command line string" for Redis**
- **Cause:** Historically an issue with empty passwords in compose files.
- **Fix:** Ensure your repository is up to date (this was resolved in v3.0). Ensure `.env` is loaded correctly.

**4. Event Bus Payload Errors**
- **Cause:** You attempted to publish a message larger than 64KB.
- **Fix:** Truncate large strings or offload large payloads to a blob store (S3/GCS) and pass the URI in the event instead.

---
*For further assistance, please consult the `Bug-Report.md` registry or reach out to the platform engineering team.*