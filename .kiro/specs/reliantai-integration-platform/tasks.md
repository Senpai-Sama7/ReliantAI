# Implementation Plan: ReliantAI Integration Platform

## Overview

This implementation plan transforms the ReliantAI Integration Platform design into actionable coding tasks. The platform unifies 13 independent business execution systems through production-grade authentication, event-driven communication, and shared observability infrastructure.

**Core Principles:**
- NO MOCKING, NO PLACEHOLDERS - Every component must be real and functional
- VERIFICATION BEFORE PROGRESSION - Each task requires proof of completion
- 80% code coverage minimum
- All 73 correctness properties must have property-based tests
- Production-ready implementation from day one

**Implementation Approach:**
The tasks are organized into 6 phases following the PROGRESS_TRACKER.md structure:
1. Foundation Infrastructure (Auth, Event Bus, API Gateway, Service Mesh, Observability)
2. Core Intelligence Integration (Apex, Acropolis, Citadel)
3. Business Operations Integration (B-A-P, Money, Gen-H, ClearDesk)
4. Specialized Services Integration (BackupIQ, intelligent-storage, citadel_ultimate_a_plus, DocuMancer, reGenesis, CyberArchitect)
5. Distributed Transactions (Saga Orchestrator)
6. Testing, Security Hardening, and Documentation

**Technology Stack:**
- Python 3.11 + FastAPI for most services
- Rust for Apex core components
- TypeScript/React for frontend services
- PostgreSQL for multi-tenant data
- Redis for caching and token storage
- Apache Kafka for event bus
- Kong for API Gateway
- Linkerd for Service Mesh
- Prometheus + Grafana + OpenTelemetry for observability

## Tasks

### Phase 1: Foundation Infrastructure

- [ ] 1. Set up project structure and shared infrastructure
  - Create `integration/` directory at workspace root
  - Create subdirectories: `auth/`, `event-bus/`, `saga/`, `observability/`, `gateway/`, `shared/`
  - Create `integration/docker-compose.yml` for local development
  - Create `integration/docker-compose.prod.yml` for production deployment
  - Set up shared Python dependencies: `integration/requirements.txt` with FastAPI, pydantic, redis, kafka-python, prometheus-client, opentelemetry
  - Create `.env.example` with all required environment variables
  - _Requirements: 15.1, 15.6, 15.7_

- [ ] 2. Implement Auth Service
  - [ ] 2.1 Create Auth Service core implementation
    - Create `integration/auth/auth_server.py` with FastAPI application
    - Implement User and Tenant data models with Pydantic
    - Implement password hashing with bcrypt (cost factor 12)
    - Implement JWT token generation with HS256 algorithm (30min access, 7 day refresh)
    - Implement Redis client for token storage and revocation
    - Create `/token`, `/refresh`, `/register`, `/verify`, `/revoke`, `/health` endpoints
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12_
  
  - [ ]* 2.2 Write property tests for Auth Service
    - **Property 1: OAuth2 Grant Flow Completeness**
    - **Property 2: JWT Token Structure**
    - **Property 3: Token Revocation Round Trip**
    - **Property 4: Password Hashing Security**
    - **Property 5: Health Check Performance**
    - **Validates: Requirements 1.1-1.12**
  
  - [ ] 2.3 Implement RBAC and tenant isolation
    - Create Role enum with super_admin, admin, operator, technician
    - Implement permission validation middleware
    - Implement tenant isolation enforcement in JWT verification
    - Add permission inheritance logic (admin includes operator permissions)
    - Add failed login tracking and account lockout (5 attempts in 15 minutes)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 19.10_
  
  - [ ]* 2.4 Write property tests for RBAC
    - **Property 6: Role Permission Hierarchy**
    - **Property 7: Super Admin Universal Access**
    - **Property 8: Tenant Isolation Enforcement**
    - **Property 9: Permission Validation Before Write**
    - **Property 71: Account Lockout After Failed Attempts**
    - **Validates: Requirements 2.1-2.10, 19.10**
  
  - [ ] 2.5 Add Auth Service observability
    - Implement Prometheus metrics: auth_token_issued_total, auth_token_validation_total, auth_login_failures_total, auth_request_duration_seconds
    - Add structured logging with correlation_id
    - Expose `/metrics` endpoint
    - _Requirements: 7.1, 7.4, 19.9_
  
  - [ ] 2.6 Create Auth Service Docker configuration
    - Create `integration/auth/Dockerfile` with Python 3.11 base image
    - Create `integration/auth/requirements.txt` with pinned dependencies
    - Add health check configuration
    - Configure Redis connection with retry logic
    - _Requirements: 18.1, 18.6, 18.7_


- [ ] 3. Implement Event Bus
  - [ ] 3.1 Create Event Bus core implementation
    - Create `integration/event-bus/event_bus.py` with Kafka producer and consumer
    - Implement Event and EventMetadata Pydantic models
    - Implement EventBusClient with publish(), subscribe(), get_event(), get_dlq_events(), replay_event() methods
    - Create topics: lead.events, dispatch.events, document.events, agent.events, analytics.events, saga.events, dlq.events
    - Implement schema validation with Pydantic before publishing
    - Implement DLQ routing for validation failures and handler exceptions
    - Configure 24-hour retention and 10 partitions per topic
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_
  
  - [ ]* 3.2 Write property tests for Event Bus
    - **Property 10: Event Schema Validation**
    - **Property 11: Event Persistence and Retrieval**
    - **Property 12: Event Delivery Latency**
    - **Property 13: Event Structure Completeness**
    - **Property 14: Handler Failure DLQ Routing**
    - **Validates: Requirements 3.1-3.10**
  
  - [ ] 3.3 Add Event Bus observability
    - Implement Prometheus metrics: events_published_total, events_consumed_total, events_failed_total, dlq_size, event_processing_duration_seconds
    - Add structured logging for all event operations
    - Expose `/metrics` endpoint
    - _Requirements: 3.11, 7.1, 7.4_
  
  - [ ] 3.4 Create Event Bus Docker configuration
    - Create `integration/event-bus/Dockerfile`
    - Add Kafka connection configuration with bootstrap servers
    - Configure consumer groups for each service
    - Add health check for Kafka connectivity
    - _Requirements: 18.1, 18.6_

- [ ] 4. Implement API Gateway with Kong
  - [ ] 4.1 Create Kong configuration
    - Create `integration/gateway/kong.yml` with declarative configuration
    - Configure PostgreSQL database for Kong
    - Define routing rules for all 13 services with path prefix matching
    - Configure JWT plugin with HS256 validation
    - Configure rate-limiting plugin (1000 req/min per user)
    - Configure correlation-id plugin for X-Correlation-ID injection
    - Configure request-transformer plugin for X-User-ID and X-Tenant-ID headers
    - Configure prometheus plugin for metrics
    - Configure file-log plugin for request logging
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10_
  
  - [ ]* 4.2 Write property tests for API Gateway
    - **Property 22: JWT Validation at Gateway**
    - **Property 23: Rate Limiting Enforcement**
    - **Property 24: HTTPS Enforcement**
    - **Property 25: Request Routing Correctness**
    - **Property 26: Header Injection Completeness**
    - **Property 27: Request Logging Completeness**
    - **Validates: Requirements 5.1-5.11**
  
  - [ ] 4.3 Create Kong Docker configuration
    - Create `integration/gateway/Dockerfile` using Kong 3.5 image
    - Configure TLS certificates for HTTPS
    - Add PostgreSQL migration initialization
    - Configure health checks
    - _Requirements: 5.6, 18.1, 18.6, 19.1_


- [ ] 5. Implement Service Mesh with Linkerd
  - [ ] 5.1 Create Linkerd deployment configuration
    - Create `integration/service-mesh/linkerd-install.yaml` with Linkerd 2.14 configuration
    - Configure mTLS for all service-to-service communication
    - Configure circuit breakers: 50% error threshold, 10s window, 30s open duration
    - Configure retry policy: max 3 attempts, exponential backoff (1s, 2s, 4s)
    - Configure distributed tracing header propagation (traceparent, tracestate)
    - Add service mesh annotations to all service deployments
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_
  
  - [ ]* 5.2 Write property tests for Service Mesh
    - **Property 28: mTLS Universal Enforcement**
    - **Property 29: Circuit Breaker Opening**
    - **Property 30: Circuit Breaker Half-Open Testing**
    - **Property 31: Circuit Breaker Closing**
    - **Property 32: Retry with Exponential Backoff**
    - **Property 33: Distributed Tracing Header Propagation**
    - **Validates: Requirements 6.1-6.10**
  
  - [ ] 5.3 Create Linkerd observability configuration
    - Configure Linkerd Prometheus integration
    - Expose metrics: circuit_breaker_state, retry_attempts_total, mtls_handshake_failures_total, request_total, response_latency_ms
    - Create Grafana dashboard for service mesh metrics
    - _Requirements: 6.10, 7.1, 7.4_

- [ ] 6. Implement Observability Stack
  - [ ] 6.1 Create Prometheus configuration
    - Create `integration/observability/prometheus.yml` with scrape configs for all 13 services
    - Configure 15-second scrape interval
    - Configure 30-day retention period
    - Add scrape configs for: auth, event-bus, saga, kong, linkerd, apex-core, apex-agents, citadel, b-a-p, money, gen-h, cleardesk, backupiq, intelligent-storage, citadel_ultimate_a_plus, documancer, regenesis, cyberarchitect
    - _Requirements: 7.1, 7.4, 7.5_
  
  - [ ] 6.2 Create Grafana dashboards
    - Create `integration/observability/dashboards/system-overview.json` with request rate, error rate, latency across all services
    - Create `integration/observability/dashboards/service-health.json` with per-service metrics and health checks
    - Create `integration/observability/dashboards/error-rates.json` with error breakdown by service, endpoint, status code
    - Create `integration/observability/dashboards/latency-percentiles.json` with P50, P95, P99 latency by service
    - Create `integration/observability/dashboards/slo-compliance.json` with availability, error rate, latency vs targets
    - Create `integration/observability/dashboards/event-bus.json` with event throughput, DLQ depth, consumer lag
    - Create `integration/observability/dashboards/circuit-breakers.json` with circuit state, retry attempts, failure rates
    - Create `integration/observability/dashboards/authentication.json` with login attempts, token issuance, validation failures
    - _Requirements: 7.2, 7.6_
  
  - [ ] 6.3 Create Prometheus alert rules
    - Create `integration/observability/alerts.yml` with alert definitions
    - Add HighErrorRate alert: error rate > 1% for 5 minutes (critical)
    - Add HighLatency alert: P95 latency > 500ms for 5 minutes (warning)
    - Add LowAvailability alert: availability < 99.9% over 24 hours (critical)
    - Add CircuitBreakerOpen alert: circuit breaker open for > 1 minute (warning)
    - Add DLQDepthHigh alert: DLQ depth > 1000 events (critical)
    - Add AuthServiceDown alert: auth service unavailable (critical)
    - _Requirements: 7.7, 7.8, 7.9_
  
  - [ ]* 6.4 Write property tests for Observability
    - **Property 34: Metrics Collection Interval**
    - **Property 35: Metrics Retention Period**
    - **Property 36: Error Rate Alerting**
    - **Property 37: Latency Alerting**
    - **Property 38: Availability Alerting**
    - **Property 39: Distributed Trace Completeness**
    - **Property 40: Correlation ID Consistency**
    - **Validates: Requirements 7.4-7.11**
  
  - [ ] 6.5 Create OpenTelemetry Collector configuration
    - Create `integration/observability/otel-collector.yml`
    - Configure OTLP receivers (gRPC on 4317, HTTP on 4318)
    - Configure batch processor (10s timeout, 1024 batch size)
    - Configure Prometheus exporter (port 8889)
    - Configure Jaeger exporter for distributed tracing
    - _Requirements: 7.3, 7.10_
  
  - [ ] 6.6 Create Observability Docker configuration
    - Create `integration/observability/docker-compose.observability.yml`
    - Add Prometheus service with volume mounts for config and data
    - Add Grafana service with dashboard provisioning
    - Add OpenTelemetry Collector service
    - Add Jaeger service for trace visualization
    - Configure service dependencies and health checks
    - _Requirements: 7.12, 18.1, 18.6_

- [ ] 7. Checkpoint - Foundation Infrastructure Complete
  - Verify all foundation services start successfully with `docker-compose up`
  - Verify Auth Service health check returns 200 at http://localhost:8080/health
  - Verify Kafka is accessible at localhost:9092
  - Verify Kong Gateway is accessible at http://localhost:8000
  - Verify Prometheus is scraping metrics at http://localhost:9090
  - Verify Grafana dashboards are accessible at http://localhost:3000
  - Run all property tests for Phase 1 components
  - Ensure all tests pass, ask the user if questions arise


### Phase 2: Core Intelligence Integration

- [ ] 8. Integrate Apex (5-layer Probabilistic OS)
  - [ ] 8.1 Implement JWT validation in apex-core (Rust)
    - Add `jsonwebtoken` crate to `apex/apex-core/Cargo.toml`
    - Create `apex/apex-core/src/auth.rs` with JWT validation middleware
    - Implement token verification with HS256 algorithm
    - Extract user_id and tenant_id from JWT claims
    - Add middleware to all HTTP routes requiring authentication
    - Return 401 Unauthorized for invalid/missing tokens
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ] 8.2 Implement event publishing in apex-agents (Python)
    - Add EventBusClient to `apex/apex-agents/src/event_client.py`
    - Publish agent.task_created events when tasks are created
    - Publish agent.task_completed events when tasks complete
    - Include task_id, agent_id, tenant_id, status in event data
    - _Requirements: 8.4, 8.5_
  
  - [ ] 8.3 Implement event subscription in apex-agents
    - Subscribe to lead.qualified events from Citadel
    - Create agent task for lead processing when event received
    - Update task state and publish agent.task_completed event
    - _Requirements: 8.6, 8.7_
  
  - [ ] 8.4 Add Apex observability integration
    - Expose Prometheus metrics at /metrics in apex-core
    - Add metrics: apex_requests_total, apex_request_duration_seconds, apex_agents_active, apex_tasks_completed_total
    - Register apex-core and apex-agents with Service Mesh
    - Add OpenTelemetry tracing instrumentation
    - _Requirements: 8.10, 8.11_
  
  - [ ]* 8.5 Write property tests for Apex integration
    - **Property 41: Universal JWT Validation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 45: Event Publishing Correctness**
    - **Property 46: Event Subscription Reactivity**
    - **Validates: Requirements 8.1-8.11**
  
  - [ ] 8.6 Update Apex Docker configuration
    - Update `apex/infra/docker-compose.yml` to include Auth Service connection
    - Add environment variables: AUTH_SERVICE_URL, KAFKA_BOOTSTRAP_SERVERS, JWT_SECRET_KEY
    - Configure service mesh sidecar injection
    - Add health check endpoints
    - _Requirements: 15.1, 18.6_

- [ ] 9. Integrate Citadel (Modular AI Microservices)
  - [ ] 9.1 Implement JWT validation in Citadel (Python/FastAPI)
    - Add JWT validation middleware to `Citadel/api_gateway/main.py`
    - Use FastAPI security utilities for token verification
    - Extract user_id and tenant_id from JWT
    - Return 401 Unauthorized for invalid tokens
    - _Requirements: 9.1_
  
  - [ ] 9.2 Migrate Citadel from SQLite to PostgreSQL
    - Create PostgreSQL schema in `Citadel/migrations/001_initial_schema.sql`
    - Add tenant_id column to all tables (leads, contacts, interactions)
    - Create indexes on tenant_id columns
    - Implement row-level security policies for tenant isolation
    - Update database connection configuration
    - _Requirements: 9.7, 16.1, 16.5, 16.6_
  
  - [ ] 9.3 Implement event publishing in Citadel
    - Add EventBusClient to Citadel services
    - Publish lead.created events when leads are created
    - Publish lead.qualified events when leads are qualified
    - Publish lead.converted events when leads convert
    - Include lead_id, tenant_id, status, timestamp in event data
    - _Requirements: 9.2, 9.3, 9.4_
  
  - [ ] 9.4 Implement event subscription in Citadel
    - Subscribe to dispatch.completed events from Money
    - Update lead status to "contacted" when dispatch completes
    - Ensure tenant_id filtering on status updates
    - _Requirements: 9.5, 9.6_
  
  - [ ] 9.5 Add Citadel observability integration
    - Expose Prometheus metrics: leads_created_total, leads_qualified_total, leads_converted_total
    - Register with Service Mesh for mTLS
    - Add OpenTelemetry tracing
    - _Requirements: 9.9, 9.10_
  
  - [ ]* 9.6 Write property tests for Citadel integration
    - **Property 41: Universal JWT Validation**
    - **Property 42: Universal Tenant Isolation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 45: Event Publishing Correctness**
    - **Property 46: Event Subscription Reactivity**
    - **Property 51: Multi-Tenant Table Structure**
    - **Property 52: Tenant Query Filtering**
    - **Validates: Requirements 9.1-9.10, 16.5-16.7**


- [ ] 10. Integrate Acropolis (Adaptive Expert Platform)
  - [ ] 10.1 Implement JWT validation in Acropolis (Rust)
    - Add JWT validation to `Acropolis/adaptive_expert_platform/src/auth.rs`
    - Implement middleware for HTTP endpoints
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 14.1_
  
  - [ ] 10.2 Implement event publishing in Acropolis
    - Add Kafka client to Acropolis Rust workspace
    - Publish expert.query_received events when queries arrive
    - Publish expert.response_generated events when responses complete
    - Include query_id, expert_type, tenant_id in event data
    - _Requirements: 14.2_
  
  - [ ] 10.3 Add Acropolis observability integration
    - Expose Prometheus metrics at /metrics
    - Add metrics: acropolis_queries_total, acropolis_response_duration_seconds
    - Register with Service Mesh
    - _Requirements: 14.6, 14.7_
  
  - [ ]* 10.4 Write property tests for Acropolis integration
    - **Property 41: Universal JWT Validation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 45: Event Publishing Correctness**
    - **Validates: Requirements 14.1-14.7**

- [ ] 11. Checkpoint - Core Intelligence Integration Complete
  - Verify Apex, Citadel, and Acropolis services start successfully
  - Verify JWT validation works for all three services
  - Verify events flow between Citadel and Apex (lead.qualified → agent.task_created)
  - Verify tenant isolation in Citadel database queries
  - Verify all services expose metrics at /metrics
  - Run all property tests for Phase 2 components
  - Ensure all tests pass, ask the user if questions arise

### Phase 3: Business Operations Integration

- [ ] 12. Integrate B-A-P (Business Analytics Platform)
  - [ ] 12.1 Implement JWT validation in B-A-P (Python/FastAPI)
    - Add JWT validation middleware to `B-A-P/src/api/main.py`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 11.1_
  
  - [ ] 12.2 Implement tenant isolation in B-A-P
    - Add tenant_id column to all analytics tables
    - Create indexes on tenant_id
    - Implement row-level security policies
    - Filter all queries by tenant_id from JWT
    - _Requirements: 11.7, 16.5, 16.6, 16.7_
  
  - [ ] 12.3 Implement event subscription in B-A-P
    - Subscribe to analytics.events topic
    - Process lead.converted, dispatch.completed events for analytics
    - Aggregate metrics by tenant_id
    - _Requirements: 11.2_
  
  - [ ] 12.4 Add B-A-P observability integration
    - Expose Prometheus metrics: analytics_queries_total, analytics_reports_generated_total
    - Register with Service Mesh
    - _Requirements: 11.8, 11.9_
  
  - [ ]* 12.5 Write property tests for B-A-P integration
    - **Property 41: Universal JWT Validation**
    - **Property 42: Universal Tenant Isolation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 46: Event Subscription Reactivity**
    - **Validates: Requirements 11.1-11.9**

- [ ] 13. Integrate Money (HVAC AI Dispatch)
  - [ ] 13.1 Implement JWT validation in Money (Python/FastAPI)
    - Add JWT validation middleware to `Money/main.py`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 10.1_
  
  - [ ] 13.2 Implement event subscription in Money
    - Subscribe to lead.qualified events from Citadel
    - Create dispatch when qualified lead received
    - Ensure tenant_id matches between lead and dispatch
    - _Requirements: 10.2_
  
  - [ ] 13.3 Implement event publishing in Money
    - Publish dispatch.created events when dispatches are created
    - Publish dispatch.assigned events when technician assigned
    - Publish dispatch.completed events when dispatch completes
    - Include dispatch_id, lead_id, tenant_id, status in event data
    - _Requirements: 10.3, 10.4, 10.5, 10.6_
  
  - [ ] 13.4 Implement tenant isolation in Money
    - Add tenant_id column to dispatches, technicians, schedules tables
    - Create indexes on tenant_id
    - Filter all queries by tenant_id from JWT
    - _Requirements: 10.8, 16.5, 16.6, 16.7_
  
  - [ ] 13.5 Add Money observability integration
    - Expose Prometheus metrics: dispatches_created_total, dispatches_completed_total, sms_sent_total
    - Register with Service Mesh
    - _Requirements: 10.9, 10.10_
  
  - [ ]* 13.6 Write property tests for Money integration
    - **Property 41: Universal JWT Validation**
    - **Property 42: Universal Tenant Isolation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 45: Event Publishing Correctness**
    - **Property 46: Event Subscription Reactivity**
    - **Validates: Requirements 10.1-10.10**


- [ ] 14. Integrate Gen-H (HVAC Growth Platform)
  - [ ] 14.1 Implement JWT validation in Gen-H backend (Python)
    - Add JWT validation to `Gen-H/hvac-lead-generator/app.py`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 12.1_
  
  - [ ] 14.2 Implement event publishing in Gen-H
    - Publish lead.created events when leads are generated
    - Include lead_id, source, tenant_id in event data
    - _Requirements: 12.2, 12.3_
  
  - [ ] 14.3 Implement tenant isolation in Gen-H
    - Add tenant_id to lead generation data
    - Filter queries by tenant_id from JWT
    - _Requirements: 12.7_
  
  - [ ] 14.4 Add Gen-H observability integration
    - Expose Prometheus metrics: leads_generated_total, campaigns_active
    - Register with Service Mesh
    - _Requirements: 12.8, 12.9_
  
  - [ ]* 14.5 Write property tests for Gen-H integration
    - **Property 41: Universal JWT Validation**
    - **Property 42: Universal Tenant Isolation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 45: Event Publishing Correctness**
    - **Validates: Requirements 12.1-12.9**

- [ ] 15. Integrate ClearDesk (AR Document Processing)
  - [ ] 15.1 Implement JWT validation in ClearDesk (TypeScript/React backend)
    - Add JWT validation middleware to API routes
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 13.1_
  
  - [ ] 15.2 Implement event publishing in ClearDesk
    - Publish document.uploaded events when documents are uploaded
    - Publish document.processed events when processing completes
    - Include document_id, tenant_id, status in event data
    - _Requirements: 13.2_
  
  - [ ] 15.3 Implement event subscription in ClearDesk
    - Subscribe to document.events topic
    - Process document extraction results
    - _Requirements: 13.3, 13.4_
  
  - [ ] 15.4 Add ClearDesk observability integration
    - Expose Prometheus metrics: documents_processed_total, extraction_duration_seconds
    - Register with Service Mesh
    - _Requirements: 13.6, 13.7_
  
  - [ ]* 15.5 Write property tests for ClearDesk integration
    - **Property 41: Universal JWT Validation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 45: Event Publishing Correctness**
    - **Property 46: Event Subscription Reactivity**
    - **Validates: Requirements 13.1-13.7**

- [ ] 16. Checkpoint - Business Operations Integration Complete
  - Verify B-A-P, Money, Gen-H, and ClearDesk services start successfully
  - Verify JWT validation works for all services
  - Verify event flow: Gen-H lead.created → Citadel lead.qualified → Money dispatch.created
  - Verify tenant isolation in all database queries
  - Verify all services expose metrics
  - Run all property tests for Phase 3 components
  - Ensure all tests pass, ask the user if questions arise

### Phase 4: Specialized Services Integration

- [ ] 17. Integrate BackupIQ (Enterprise Backup)
  - [ ] 17.1 Implement JWT validation in BackupIQ (Python)
    - Add JWT validation to `BackupIQ/src/api/main.py`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 14.3_
  
  - [ ] 17.2 Add BackupIQ observability integration
    - Expose Prometheus metrics: backups_completed_total, backup_size_bytes
    - Register with Service Mesh
    - _Requirements: 14.6, 14.7_
  
  - [ ]* 17.3 Write property tests for BackupIQ integration
    - **Property 41: Universal JWT Validation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Validates: Requirements 14.3, 14.6, 14.7**

- [ ] 18. Integrate intelligent-storage (RAG + Knowledge Graph)
  - [ ] 18.1 Implement JWT validation in intelligent-storage (Python)
    - Add JWT validation to `intelligent-storage/api_server.py`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 14.4_
  
  - [ ] 18.2 Implement tenant isolation in intelligent-storage
    - Add tenant_id to vector embeddings and knowledge graph nodes
    - Filter queries by tenant_id from JWT
    - _Requirements: 16.5, 16.6, 16.7_
  
  - [ ] 18.3 Add intelligent-storage observability integration
    - Expose Prometheus metrics: queries_total, embeddings_created_total
    - Register with Service Mesh
    - _Requirements: 14.6, 14.7_
  
  - [ ]* 18.4 Write property tests for intelligent-storage integration
    - **Property 41: Universal JWT Validation**
    - **Property 42: Universal Tenant Isolation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Validates: Requirements 14.4, 14.6, 14.7**


- [ ] 19. Integrate citadel_ultimate_a_plus (Lead Generation Pipeline)
  - [ ] 19.1 Implement JWT validation in citadel_ultimate_a_plus (Python)
    - Add JWT validation to `citadel_ultimate_a_plus/api/main.py`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 14.5_
  
  - [ ] 19.2 Implement event publishing in citadel_ultimate_a_plus
    - Publish lead.created events when leads are scraped
    - Include lead_id, source_url, tenant_id in event data
    - _Requirements: 14.2_
  
  - [ ] 19.3 Implement tenant isolation in citadel_ultimate_a_plus
    - Add tenant_id to leads table
    - Filter queries by tenant_id from JWT
    - _Requirements: 16.5, 16.6, 16.7_
  
  - [ ] 19.4 Add citadel_ultimate_a_plus observability integration
    - Expose Prometheus metrics: leads_scraped_total, scraping_duration_seconds
    - Register with Service Mesh
    - _Requirements: 14.6, 14.7_
  
  - [ ]* 19.5 Write property tests for citadel_ultimate_a_plus integration
    - **Property 41: Universal JWT Validation**
    - **Property 42: Universal Tenant Isolation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Property 45: Event Publishing Correctness**
    - **Validates: Requirements 14.2, 14.5, 14.6, 14.7**

- [ ] 20. Integrate DocuMancer (Document Conversion)
  - [ ] 20.1 Implement JWT validation in DocuMancer backend (Python)
    - Add JWT validation to `DocuMancer/backend/api.py`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 14.3_
  
  - [ ] 20.2 Add DocuMancer observability integration
    - Expose Prometheus metrics: conversions_total, conversion_duration_seconds
    - Register with Service Mesh
    - _Requirements: 14.6, 14.7_
  
  - [ ]* 20.3 Write property tests for DocuMancer integration
    - **Property 41: Universal JWT Validation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Validates: Requirements 14.3, 14.6, 14.7**

- [ ] 21. Integrate reGenesis (Website Generation)
  - [ ] 21.1 Implement JWT validation in reGenesis (Node.js)
    - Add JWT validation middleware to `reGenesis/server.js`
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 14.3_
  
  - [ ] 21.2 Add reGenesis observability integration
    - Expose Prometheus metrics: websites_generated_total, generation_duration_seconds
    - Register with Service Mesh
    - _Requirements: 14.6, 14.7_
  
  - [ ]* 21.3 Write property tests for reGenesis integration
    - **Property 41: Universal JWT Validation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Validates: Requirements 14.3, 14.6, 14.7**

- [ ] 22. Integrate CyberArchitect (Website Replication)
  - [ ] 22.1 Implement JWT validation in CyberArchitect (Node.js)
    - Add JWT validation to `CyberArchitect/replicator.js` API endpoints
    - Extract user_id and tenant_id from JWT
    - Return 401 for invalid tokens
    - _Requirements: 14.3_
  
  - [ ] 22.2 Add CyberArchitect observability integration
    - Expose Prometheus metrics: replications_total, replication_duration_seconds
    - Register with Service Mesh
    - _Requirements: 14.6, 14.7_
  
  - [ ]* 22.3 Write property tests for CyberArchitect integration
    - **Property 41: Universal JWT Validation**
    - **Property 43: Universal Metrics Exposure**
    - **Property 44: Universal Service Mesh Registration**
    - **Validates: Requirements 14.3, 14.6, 14.7**

- [ ] 23. Checkpoint - Specialized Services Integration Complete
  - Verify all 6 specialized services start successfully
  - Verify JWT validation works for all services
  - Verify tenant isolation in intelligent-storage and citadel_ultimate_a_plus
  - Verify all services expose metrics
  - Run all property tests for Phase 4 components
  - Ensure all tests pass, ask the user if questions arise

### Phase 5: Distributed Transactions

- [ ] 24. Implement Saga Orchestrator
  - [ ] 24.1 Create Saga Orchestrator core implementation
    - Create `integration/saga/saga_orchestrator.py` with FastAPI application
    - Implement SagaStep, SagaDefinition, SagaExecution data models
    - Implement SagaStatus enum: pending, in_progress, completed, compensating, failed
    - Implement sequential step execution with context propagation
    - Implement compensation logic execution in reverse order on failure
    - Implement idempotency key checking with Redis
    - Store saga execution state in Redis with 7-day TTL
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 4.8_
  
  - [ ]* 24.2 Write property tests for Saga Orchestrator
    - **Property 15: Saga Sequential Execution**
    - **Property 16: Saga Compensation Reversal**
    - **Property 17: Saga Idempotency**
    - **Property 18: Saga Step Completion Recording**
    - **Property 19: Compensation Failure Handling**
    - **Property 20: Saga Context Propagation**
    - **Property 21: Saga Execution Logging**
    - **Validates: Requirements 4.1-4.9**
  
  - [ ] 24.3 Create saga definitions for common workflows
    - Create lead_to_dispatch saga: qualify_lead → create_dispatch → send_notification
    - Create document_processing saga: upload_document → extract_data → store_results
    - Create user_onboarding saga: create_user → send_welcome_email → create_tenant_resources
    - Add compensation logic for each step
    - _Requirements: 4.1, 4.3_
  
  - [ ] 24.4 Add Saga Orchestrator observability
    - Expose Prometheus metrics: sagas_started_total, sagas_completed_total, sagas_failed_total, compensation_executed_total, saga_duration_seconds
    - Add structured logging for all saga operations
    - Publish saga.events to Kafka for audit trail
    - _Requirements: 4.9, 4.10_
  
  - [ ] 24.5 Create Saga Orchestrator API endpoints
    - Create POST /saga/execute endpoint for saga initiation
    - Create GET /saga/{execution_id} endpoint for status checking
    - Create POST /saga/{execution_id}/retry endpoint for manual retry
    - Add JWT validation to all endpoints
    - _Requirements: 4.8_
  
  - [ ] 24.6 Create Saga Orchestrator Docker configuration
    - Create `integration/saga/Dockerfile`
    - Configure Redis and Kafka connections
    - Add health check endpoint
    - _Requirements: 18.1, 18.6_

- [ ] 25. Checkpoint - Distributed Transactions Complete
  - Verify Saga Orchestrator starts successfully
  - Test lead_to_dispatch saga end-to-end
  - Verify compensation logic executes on failure
  - Verify idempotency prevents duplicate execution
  - Run all property tests for Saga Orchestrator
  - Ensure all tests pass, ask the user if questions arise


### Phase 6: Testing, Security, and Production Readiness

- [ ] 26. Implement comprehensive testing infrastructure
  - [ ] 26.1 Set up property-based testing framework
    - Create `integration/tests/conftest.py` with pytest fixtures
    - Configure Hypothesis with 100 iterations per test
    - Create test utilities for generating test data (users, tenants, events, sagas)
    - Add property test tagging with feature name and property number
    - _Requirements: 17.1, 17.4_
  
  - [ ] 26.2 Write integration tests for cross-service workflows
    - Create `integration/tests/test_lead_to_dispatch_workflow.py`
    - Test: Create lead in Citadel → Qualify lead → Verify dispatch in Money
    - Create `integration/tests/test_document_processing_workflow.py`
    - Test: Upload document in ClearDesk → Process → Verify results in intelligent-storage
    - Create `integration/tests/test_tenant_isolation.py`
    - Test: User from tenant A cannot access tenant B resources
    - Use testcontainers for PostgreSQL, Redis, Kafka
    - _Requirements: 17.2, 17.3, 17.5_
  
  - [ ] 26.3 Write contract tests for event schemas
    - Create `integration/tests/test_event_contracts.py`
    - Validate all events conform to Event schema
    - Test backward compatibility for schema changes
    - Load sample events from each service and validate
    - _Requirements: 17.9_
  
  - [ ] 26.4 Set up load testing with Locust
    - Create `integration/tests/load/locustfile.py`
    - Simulate 1000 concurrent users
    - Test scenarios: login, create lead, qualify lead, create dispatch
    - Measure P95 latency and error rate
    - Assert P95 < 500ms and error rate < 0.1%
    - _Requirements: 17.11, 17.12_
  
  - [ ] 26.5 Create CI/CD pipeline configuration
    - Create `.github/workflows/integration-ci.yml`
    - Add stages: lint, unit tests, property tests, integration tests, security scan, build, deploy staging, e2e tests, load tests
    - Configure quality gates: all tests pass, coverage ≥ 80%, no critical vulnerabilities
    - Add automatic rollback on health check failure
    - _Requirements: 17.2, 17.3, 17.6, 18.5_
  
  - [ ]* 26.6 Write property tests for testing infrastructure
    - **Property 56: Code Coverage Threshold**
    - **Property 57: CI/CD Test Execution**
    - **Property 58: Event Schema Backward Compatibility**
    - **Property 59: Load Test Performance**
    - **Validates: Requirements 17.1-17.12**

- [ ] 27. Implement security hardening
  - [ ] 27.1 Add request validation and sanitization
    - Implement request size limiting (10MB max) in Kong
    - Add SQL injection prevention through parameterized queries
    - Add XSS prevention through output encoding
    - Configure CORS policy with approved domain list
    - _Requirements: 19.4, 19.5, 19.6, 19.7_
  
  - [ ] 27.2 Implement JWT key rotation
    - Create `integration/auth/key_rotation.py` script
    - Generate new JWT signing keys every 90 days
    - Support multiple active keys during rotation period
    - Update all services with new keys
    - _Requirements: 19.8_
  
  - [ ] 27.3 Set up vulnerability scanning
    - Add Bandit for Python security scanning
    - Add cargo-audit for Rust dependency scanning
    - Add npm audit for Node.js dependency scanning
    - Configure weekly automated scans
    - Add critical vulnerability alerting (< 1 hour)
    - _Requirements: 19.11, 19.12_
  
  - [ ] 27.4 Implement security monitoring
    - Add authentication failure logging with IP address
    - Add permission denial logging
    - Add suspicious activity detection (multiple failed logins, cross-tenant access attempts)
    - Configure alerts for security events
    - _Requirements: 19.9, 19.10_
  
  - [ ]* 27.5 Write property tests for security features
    - **Property 65: Request Size Limiting**
    - **Property 66: SQL Injection Prevention**
    - **Property 67: XSS Attack Prevention**
    - **Property 68: CORS Policy Enforcement**
    - **Property 69: JWT Key Rotation**
    - **Property 70: Authentication Failure Logging**
    - **Property 71: Account Lockout After Failed Attempts**
    - **Property 72: Vulnerability Scanning Cadence**
    - **Property 73: Critical Vulnerability Alerting**
    - **Validates: Requirements 19.1-19.12**

- [ ] 28. Implement database management
  - [ ] 28.1 Create database migration system
    - Create `integration/migrations/` directory
    - Implement forward-only migration system with Alembic
    - Create initial migrations for users, tenants, tokens tables
    - Add migration atomicity with transaction rollback on failure
    - Add migration logging and error handling
    - _Requirements: 16.1, 16.2, 16.3, 16.4_
  
  - [ ] 28.2 Implement database backup system
    - Create `integration/scripts/backup_databases.sh`
    - Configure daily PostgreSQL backups with pg_dump
    - Configure 30-day retention policy
    - Test backup restoration procedure
    - _Requirements: 16.10_
  
  - [ ]* 28.3 Write property tests for database management
    - **Property 51: Multi-Tenant Table Structure**
    - **Property 52: Tenant Query Filtering**
    - **Property 53: Migration Atomicity**
    - **Property 54: Forward-Only Migrations**
    - **Property 55: Database Backup Retention**
    - **Validates: Requirements 16.1-16.10**

- [ ] 29. Implement configuration management
  - [ ] 29.1 Create configuration validation system
    - Create `integration/shared/config.py` with configuration models
    - Implement environment variable validation on startup
    - Add type checking and range validation
    - Exit with non-zero status on missing required variables
    - Follow SERVICE_NAME_CONFIG_KEY naming convention
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10_
  
  - [ ]* 29.2 Write property tests for configuration management
    - **Property 47: Environment Variable Configuration**
    - **Property 48: Missing Configuration Handling**
    - **Property 49: Configuration Naming Convention**
    - **Property 50: Configuration Type Validation**
    - **Validates: Requirements 15.1-15.10**


- [ ] 30. Implement deployment automation
  - [ ] 30.1 Create Kubernetes deployment manifests
    - Create `integration/k8s/` directory
    - Create deployment manifests for all services (auth, event-bus, saga, gateway, observability, 13 projects)
    - Configure 3 replicas minimum per service
    - Add Horizontal Pod Autoscaler (70% CPU threshold)
    - Configure health checks (/health for liveness, /ready for readiness)
    - Add Linkerd service mesh annotations
    - _Requirements: 18.1, 18.2, 18.3, 18.6, 18.7, 18.8_
  
  - [ ] 30.2 Implement blue-green deployment strategy
    - Create `integration/scripts/deploy.sh` with blue-green logic
    - Deploy new version to "green" environment
    - Run health checks on green environment
    - Switch traffic from blue to green
    - Keep blue environment for rollback
    - Implement automatic rollback on health check failure
    - _Requirements: 18.4, 18.5_
  
  - [ ] 30.3 Create Docker image build system
    - Create `integration/scripts/build_images.sh`
    - Build Docker images for all services
    - Tag images with git commit SHA
    - Run security scans on images before push
    - Push images to container registry
    - _Requirements: 18.9, 18.10, 18.11_
  
  - [ ]* 30.4 Write property tests for deployment
    - **Property 60: Zero-Downtime Deployment**
    - **Property 61: Automatic Rollback on Failure**
    - **Property 62: Health Endpoint Availability**
    - **Property 63: Docker Image Traceability**
    - **Property 64: Security Scan Before Deployment**
    - **Validates: Requirements 18.1-18.11**

- [ ] 31. Create comprehensive documentation
  - [ ] 31.1 Create architecture documentation
    - Create `integration/docs/ARCHITECTURE.md` with system overview, component diagrams, data flow diagrams
    - Document authentication flow, event-driven communication, saga pattern
    - Include deployment architecture for local and production
    - _Requirements: 20.1_
  
  - [ ] 31.2 Create API documentation
    - Create `integration/docs/API.md` with all endpoint specifications
    - Document Auth Service endpoints with request/response examples
    - Document Saga Orchestrator endpoints
    - Generate OpenAPI specs for all FastAPI services
    - _Requirements: 20.2_
  
  - [ ] 31.3 Create operations runbook
    - Create `integration/docs/RUNBOOK.md` with operational procedures
    - Document deployment procedures (local, staging, production)
    - Document rollback procedures
    - Document monitoring and alerting setup
    - Document incident response procedures
    - Document backup and restore procedures
    - _Requirements: 20.3, 20.4, 20.5_
  
  - [ ] 31.4 Create developer onboarding guide
    - Create `integration/docs/ONBOARDING.md` with setup instructions
    - Document local development environment setup
    - Document how to add new services to the platform
    - Document testing procedures
    - Document contribution guidelines
    - _Requirements: 20.6_
  
  - [ ] 31.5 Create troubleshooting guide
    - Create `integration/docs/TROUBLESHOOTING.md`
    - Document common issues and solutions
    - Document how to check service health
    - Document how to investigate errors using logs, metrics, traces
    - Document how to process DLQ events
    - _Requirements: 20.7_

- [ ] 32. Final Integration Testing and Validation
  - [ ] 32.1 Run end-to-end integration tests
    - Test complete user journey: register → login → create lead → qualify → dispatch → complete
    - Test multi-tenant isolation: create 2 tenants, verify data isolation
    - Test authentication flows: login, token refresh, token revocation
    - Test event-driven workflows: verify events flow between all services
    - Test saga orchestration: verify compensation on failure
    - Test circuit breakers: simulate service failure, verify circuit opens
    - _Requirements: 17.7, 17.8_
  
  - [ ] 32.2 Run load tests and performance validation
    - Run Locust load test with 1000 concurrent users for 30 minutes
    - Verify P95 latency < 500ms
    - Verify error rate < 0.1%
    - Verify no memory leaks or resource exhaustion
    - _Requirements: 17.11, 17.12_
  
  - [ ] 32.3 Validate observability stack
    - Verify all services expose metrics at /metrics
    - Verify Prometheus scrapes all services every 15 seconds
    - Verify all Grafana dashboards display data correctly
    - Verify distributed traces show complete request flow
    - Verify alerts trigger correctly (simulate high error rate, high latency)
    - _Requirements: 7.1-7.12_
  
  - [ ] 32.4 Validate security controls
    - Test JWT validation: verify invalid tokens rejected
    - Test tenant isolation: verify cross-tenant access blocked
    - Test rate limiting: verify 429 after 1000 requests/minute
    - Test HTTPS enforcement: verify HTTP requests rejected
    - Test SQL injection prevention: attempt SQL injection attacks
    - Test XSS prevention: attempt XSS attacks
    - _Requirements: 19.1-19.12_
  
  - [ ] 32.5 Create proof artifacts
    - Capture screenshots of running services
    - Capture health check outputs for all services
    - Capture Grafana dashboard screenshots
    - Capture test execution results (all passing)
    - Capture code coverage reports (≥80%)
    - Capture load test results
    - Save all artifacts to `integration/proof/`
    - _Requirements: All requirements_

- [ ] 33. Final Checkpoint - Production Ready
  - Verify all 73 property tests pass
  - Verify code coverage ≥ 80%
  - Verify all integration tests pass
  - Verify load tests meet performance targets
  - Verify all security controls in place
  - Verify all documentation complete
  - Verify deployment automation works
  - Verify rollback procedures tested
  - Ensure all proof artifacts created
  - Ask the user if questions arise before marking complete

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP, but are strongly recommended for production readiness
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and provide natural break points
- Property tests validate universal correctness properties from the design document
- All implementation must be real, functional code - NO MOCKS, NO PLACEHOLDERS
- Each task completion requires verifiable proof (test results, screenshots, logs, metrics)
- Follow the PROGRESS_TRACKER.md for detailed phase breakdown and timing estimates
- Use the AGENTS.md rules for project-specific implementation details

## Implementation Order

The tasks are designed to be executed sequentially within each phase, but phases can overlap:
1. Phase 1 (Foundation) must complete before other phases
2. Phases 2-4 (Service Integration) can proceed in parallel after Phase 1
3. Phase 5 (Distributed Transactions) requires Phases 2-3 to be partially complete
4. Phase 6 (Testing & Production) runs continuously throughout all phases

## Success Criteria

The ReliantAI Integration Platform is complete when:
- All 13 projects are integrated with JWT authentication
- All services communicate via event bus
- All services expose metrics and traces
- All 73 property tests pass
- Code coverage ≥ 80%
- Load tests meet performance targets (P95 < 500ms, error rate < 0.1%)
- Security controls validated
- Documentation complete
- Deployment automation functional
- Zero-downtime deployment verified
