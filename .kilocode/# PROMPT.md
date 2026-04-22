# PROMPT.md
---
# ReliantAI Integration Platform
---

```
You are tasked with implementing the ReliantAI Integration Platform by executing all tasks in the specification.

## CRITICAL CONTEXT FILES (Read These First)

1. **`.kiro/specs/reliantai-integration-platform/tasks.md`** - Your primary execution guide with 33 implementation tasks
2. **`.kiro/specs/reliantai-integration-platform/requirements.md`** - 20 requirements with 220+ acceptance criteria
3. **`.kiro/specs/reliantai-integration-platform/design.md`** - Technical architecture and 73 correctness properties
4. **`AGENTS.md`** - Build rules, tech stack details, and project-specific commands for all 13 projects
5. **`PROGRESS_TRACKER.md`** - Contains working code examples for Auth Service and Event Bus

## EXECUTION COMMAND

Execute all tasks in the spec:

```bash
cd /home/donovan/Projects/ReliantAI
# Start with Phase 1, Task 1
```

Use this command to run all tasks automatically:
```
run all tasks for reliantai-integration-platform
```

Or execute tasks individually starting with Task 1.

## THE 5 CORE COMMANDMENTS (MANDATORY)

### 1. NO SIMULATION, NO MOCKING, NO DEMOS
- Every component must be **real, working, and fully functional**
- ❌ FORBIDDEN: Mock implementations, TODO comments, placeholders, "will implement later"
- ✅ REQUIRED: Real database connections, real API calls, real authentication, real error handling

### 2. VERIFICATION BEFORE PROGRESSION
- **Cannot proceed to next task without verifiable proof**
- Each task requires: test results (all passing), code coverage reports (≥80%), logs, health checks
- Mark task complete ONLY after proof is documented

### 3. HOSTILE AUDIT APPROACH
- Assume every implementation will be audited by a hostile, skeptical reviewer
- Document: Decision log, failure documentation, security considerations, performance characteristics
- Someone will try to break this - build defensively

### 4. REAL-TIME TRACKING
- Update task status immediately: `[ ]` → `[~]` → `[✓]`
- Include timestamps, proof artifacts, and documentation for each task

### 5. COMPREHENSIVE CONTEXT
- Every implementation must include full context
- Document: purpose, dependencies, environment, how to run/test, troubleshooting, rollback

## EXECUTION STRATEGY

### Phase-by-Phase Approach

**Phase 1: Foundation Infrastructure (Tasks 1-7)**
- Build Auth Service, Event Bus, API Gateway, Service Mesh, Observability Stack
- CHECKPOINT: All foundation services running, health checks passing, metrics exposed

**Phase 2: Core Intelligence Integration (Tasks 8-11)**
- Integrate Apex, Citadel, Acropolis with JWT auth and event bus
- CHECKPOINT: All 3 services authenticated, events flowing between services

**Phase 3: Business Operations Integration (Tasks 12-16)**
- Integrate B-A-P, Money, Gen-H, ClearDesk
- CHECKPOINT: Event-driven workflows functional (lead → dispatch)

**Phase 4: Specialized Services Integration (Tasks 17-23)**
- Integrate remaining 6 services (BackupIQ, intelligent-storage, citadel_ultimate_a_plus, DocuMancer, reGenesis, CyberArchitect)
- CHECKPOINT: All 13 projects integrated

**Phase 5: Distributed Transactions (Tasks 24-25)**
- Implement Saga Orchestrator with compensation logic
- CHECKPOINT: Sagas execute with automatic rollback on failure

**Phase 6: Testing & Production Readiness (Tasks 26-33)**
- Property-based tests (73 properties), integration tests, load tests, security hardening, deployment automation
- CHECKPOINT: Production-ready, all tests passing, documentation complete

## VERIFICATION CHECKLIST (Use for Every Task)

Before marking any task complete:

- [ ] Implementation complete (no TODOs/placeholders)
- [ ] Unit tests pass (if applicable)
- [ ] Property tests pass (if applicable)
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing completed
- [ ] Hostile audit performed (try to break it)
- [ ] Proof documented (test output, logs, screenshots, metrics)
- [ ] Code coverage ≥ 80%
- [ ] Decision log completed (why this approach)
- [ ] Failure documentation (what didn't work)
- [ ] Security considerations documented
- [ ] Performance characteristics measured
- [ ] Task status updated in tasks.md

## PROOF REQUIREMENTS BY COMPONENT TYPE

### Infrastructure Components
- Screenshots of running services
- Health check outputs: `curl http://localhost:PORT/health`
- Configuration file contents
- Log excerpts showing successful operation
- Resource usage metrics (CPU, memory, disk)

### Code Components
- Test execution results (all passing)
- Code coverage reports (≥80%)
- Integration test logs
- Performance benchmark results
- Static analysis output (linting, type checking)

### API Components
- cURL command outputs with full responses
- Response payload examples (success + error cases)
- Error handling demonstrations
- Rate limiting verification

### Database Components
- Schema verification queries
- Data insertion/retrieval tests
- Connection pool statistics
- Query performance metrics

## TECHNOLOGY STACK

- **Python 3.11** + FastAPI for most services
- **Rust** for Apex core components
- **TypeScript/React** for frontend services
- **PostgreSQL** for multi-tenant data
- **Redis** for caching and token storage
- **Apache Kafka** for event bus
- **Kong** for API Gateway
- **Linkerd** for Service Mesh
- **Prometheus + Grafana + OpenTelemetry** for observability

## KEY IMPLEMENTATION PATTERNS

### Authentication Flow
1. User sends credentials to Auth Service
2. Auth Service returns JWT (30min access, 7 day refresh)
3. Client includes JWT in Authorization header
4. API Gateway validates JWT, adds X-User-ID, X-Tenant-ID, X-Correlation-ID headers
5. Service enforces tenant isolation using tenant_id from JWT

### Event-Driven Communication
1. Service publishes event to Kafka topic
2. Event validated against Pydantic schema
3. Kafka persists event for 24 hours
4. Subscribed services receive event within 100ms
5. Failed events go to Dead Letter Queue

### Saga Pattern (Distributed Transactions)
1. Orchestrator executes steps sequentially
2. Each step stores idempotency key in Redis
3. On failure, execute compensation logic in reverse order
4. Saga completes with status: completed or failed

### Multi-Tenancy
1. Add tenant_id column to all multi-tenant tables
2. Create index on tenant_id
3. Filter all queries by tenant_id from JWT
4. Use PostgreSQL row-level security policies

## COMMON PITFALLS TO AVOID

1. ❌ Skipping verification - Never mark task complete without proof
2. ❌ Using placeholders - All code must be real and functional
3. ❌ Forgetting to update task status - Update in real-time
4. ❌ Not documenting failures - Document what didn't work and why
5. ❌ Assuming knowledge - Document everything, assume nothing
6. ❌ Skipping security - Every task needs security considerations
7. ❌ Ignoring performance - Measure and document performance
8. ❌ Not testing edge cases - Hostile audit means testing failure scenarios
9. ❌ Working on multiple tasks simultaneously - Sequential execution only
10. ❌ Not preserving original code - Always keep backups before modifying

## SUCCESS CRITERIA

The platform is complete when:

✅ All 13 projects integrated with JWT authentication
✅ All services communicate via event bus
✅ All services expose metrics and traces
✅ All 73 property tests pass
✅ Code coverage ≥ 80%
✅ Load tests meet targets (P95 < 500ms, error rate < 0.1%)
✅ Security controls validated
✅ Documentation complete
✅ Deployment automation functional
✅ Zero-downtime deployment verified

## YOUR FIRST COMMAND

```bash
cd /home/donovan/Projects/ReliantAI
cat .kiro/specs/reliantai-integration-platform/tasks.md
```

Then execute: **run all tasks for reliantai-integration-platform**

Or start with Task 1: "Set up project structure and shared infrastructure"

---

**Remember: Build something real. Build something great. Build something that works.**
```

---

