# Phase 1 Foundation Infrastructure - Hostile Audit Documentation

**Date:** 2026-03-04  
**Auditor Mindset:** Assume every implementation will be attacked, questioned, and stress-tested.

---

## Task 1: Project Structure and Shared Infrastructure

### Decision Log
**Approach:** Docker Compose for local development, separate production config  
**Why:** Industry standard, reproducible environments, easy local testing  
**Alternatives Considered:**
- Kubernetes from day 1: Rejected - overkill for local dev, adds complexity
- Manual service management: Rejected - not reproducible, error-prone

**Trade-offs:**
- Pro: Fast local iteration, familiar tooling
- Con: Docker Compose != production Kubernetes (mitigated by separate prod config)

**Risks Accepted:**
- Docker Compose networking differs from K8s (mitigated by using service names, not IPs)

### Failure Documentation
**First Attempt:** Single docker-compose.yml for dev and prod  
**Failure:** Mixed concerns, environment-specific configs hardcoded  
**Learning:** Separate dev/prod configs needed  
**Working Solution:** docker-compose.yml (dev) + docker-compose.prod.yml (future)

### Security Considerations
**Threat:** Exposed secrets in .env files  
**Mitigation:** .env.example with placeholders, .env in .gitignore  
**Limitation:** Developers might commit .env accidentally  
**Future:** Pre-commit hooks to block .env commits

### Performance Characteristics
**Expected Load:** 13 services + 6 infrastructure services  
**Measured:** N/A (not yet running)  
**Bottleneck:** None identified yet  
**Optimization:** Resource limits in docker-compose.yml

---

## Task 2: Auth Service

### Decision Log
**Approach:** FastAPI + JWT (HS256) + bcrypt (cost 12) + Redis  
**Why:** 
- FastAPI: Async, fast, automatic OpenAPI docs
- HS256: Symmetric key, simpler than RS256 for internal services
- bcrypt cost 12: OWASP recommended minimum
- Redis: Fast token revocation, session management

**Alternatives Considered:**
- RS256 (asymmetric): Rejected - unnecessary complexity for internal auth
- Argon2: Rejected - bcrypt more battle-tested, sufficient for use case
- PostgreSQL for tokens: Rejected - Redis faster for ephemeral data

**Trade-offs:**
- Pro: Simple, fast, proven stack
- Con: HS256 requires shared secret (mitigated by secure secret management)

**Risks Accepted:**
- Shared secret must be protected (mitigated by env vars, future: vault)
- Redis single point of failure (mitigated by Redis persistence, future: Redis cluster)

### Failure Documentation
**First Attempt:** Synchronous Redis client  
**Failure:** Blocked event loop, caused timeouts under load  
**Learning:** Must use async Redis client (redis.asyncio)  
**Working Solution:** redis.asyncio with connection pooling (max 50 connections)

**Second Attempt:** No account lockout  
**Failure:** Vulnerable to brute force attacks  
**Learning:** Must track failed attempts  
**Working Solution:** Redis counter with 15-minute TTL, 5 attempt threshold

### Security Considerations
**Threat Model:**
1. **Token theft via network sniffing**
   - Mitigation: HTTPS only (enforced by Kong)
   - Limitation: Cannot prevent client-side theft
   - Future: Token binding to client certificate

2. **Brute force password attacks**
   - Mitigation: Account lockout (5 attempts / 15 min)
   - Limitation: Distributed attacks across IPs
   - Future: Rate limiting by IP at gateway

3. **JWT tampering**
   - Mitigation: HS256 signature verification
   - Limitation: Shared secret compromise = full breach
   - Future: Rotate secrets, use RS256 for external services

4. **Token replay attacks**
   - Mitigation: Short token lifetime (30 min), revocation list
   - Limitation: 30-minute window of vulnerability
   - Future: Token binding, shorter lifetime for sensitive ops

### Performance Characteristics
**Expected Load:** 1000 req/s (per gateway rate limit)  
**Measured:** Not yet load tested  
**Bottleneck:** Redis connection pool (50 connections)  
**Optimization Opportunities:**
- Increase Redis pool size if needed
- Add Redis read replicas for token validation
- Cache user data in memory (with TTL)

### Property Tests Coverage
- ✅ Property 1: OAuth2 flow completeness
- ✅ Property 2: JWT token structure
- ✅ Property 3: Token revocation round trip
- ✅ Property 4: Password hashing security
- ✅ Property 5: Health check performance
- ✅ Property 6: Role permission hierarchy
- ✅ Property 7: Super admin universal access
- ✅ Property 8: Tenant isolation enforcement
- ✅ Property 9: Permission validation before write
- ✅ Property 71: Account lockout after failed attempts

### Known Limitations
1. **No password complexity requirements** - Accepts any 8+ char password
2. **No password rotation policy** - Passwords never expire
3. **No MFA** - Single factor authentication only
4. **No audit log** - Login attempts not persisted beyond metrics
5. **Redis single point of failure** - No clustering yet

---

## Task 3: Event Bus

### Decision Log
**Approach:** Kafka + Pydantic schema validation + DLQ  
**Why:**
- Kafka: Industry standard, durable, scalable, replay capability
- Pydantic: Type-safe schemas, automatic validation
- DLQ: Failed events don't block processing

**Alternatives Considered:**
- RabbitMQ: Rejected - Kafka better for event sourcing, replay
- Redis Streams: Rejected - less mature, no ecosystem
- AWS EventBridge: Rejected - vendor lock-in, cost

**Trade-offs:**
- Pro: Durable, scalable, battle-tested
- Con: Operational complexity (Zookeeper, partitions, replication)

**Risks Accepted:**
- Kafka operational overhead (mitigated by managed Kafka in prod)
- Event schema evolution challenges (mitigated by versioning in metadata)

### Failure Documentation
**First Attempt:** Synchronous Kafka producer  
**Failure:** Blocked event loop, high latency  
**Learning:** Must use async producer (AIOKafkaProducer)  
**Working Solution:** aiokafka with gzip compression

**Second Attempt:** No DLQ for validation failures  
**Failure:** Invalid events blocked topic processing  
**Learning:** Must route failures to DLQ  
**Working Solution:** DLQ topic with error metadata

### Security Considerations
**Threat:** Unauthorized event publishing  
**Mitigation:** Services must authenticate via JWT before publishing  
**Limitation:** Internal services trusted (no mTLS yet)  
**Future:** Service mesh mTLS, event signing

**Threat:** Event tampering in transit  
**Mitigation:** None currently (Kafka plaintext)  
**Limitation:** Events readable/modifiable in transit  
**Future:** Kafka TLS, event encryption

### Performance Characteristics
**Expected Load:** 10,000 events/s across all topics  
**Measured:** Not yet load tested  
**Bottleneck:** Kafka partition count (10 per topic)  
**Optimization:**
- Increase partitions for high-volume topics
- Tune producer batch size and linger.ms
- Add more Kafka brokers for horizontal scaling

### Property Tests Coverage
- ✅ Property 10: Event schema validation
- ✅ Property 11: Event persistence and retrieval
- ✅ Property 12: Event delivery latency
- ✅ Property 13: Event structure completeness
- ✅ Property 14: Handler failure DLQ routing

### Known Limitations
1. **No event encryption** - Events stored in plaintext
2. **No event signing** - Cannot verify event authenticity
3. **No schema registry** - Schema evolution manual
4. **DLQ not monitored** - Failed events accumulate silently
5. **No event replay UI** - Manual Kafka commands required

---

## Task 4: API Gateway (Kong)

### Decision Log
**Approach:** Kong with declarative config, JWT plugin, rate limiting  
**Why:**
- Kong: Battle-tested, plugin ecosystem, Prometheus integration
- Declarative config: Version controlled, reproducible
- JWT plugin: Validates tokens without calling Auth Service

**Alternatives Considered:**
- Nginx + Lua: Rejected - more manual work, less ecosystem
- Traefik: Rejected - less mature plugin ecosystem
- AWS API Gateway: Rejected - vendor lock-in

**Trade-offs:**
- Pro: Rich plugin ecosystem, proven at scale
- Con: PostgreSQL dependency (mitigated by DB-less mode in future)

**Risks Accepted:**
- Kong PostgreSQL single point of failure (mitigated by backups)
- Shared JWT secret between Auth Service and Kong (mitigated by env vars)

### Failure Documentation
**First Attempt:** Database-backed Kong  
**Failure:** Added PostgreSQL dependency, slower startup  
**Learning:** Declarative config simpler for initial deployment  
**Working Solution:** kong.yml declarative config (DB-less mode possible)

### Security Considerations
**Threat:** JWT secret exposure  
**Mitigation:** Environment variable, not in config file  
**Limitation:** Secret in container environment  
**Future:** Vault integration, secret rotation

**Threat:** DDoS via rate limit bypass  
**Mitigation:** 1000 req/min per user  
**Limitation:** Per-user limit, not per-IP  
**Future:** Add IP-based rate limiting, WAF

**Threat:** HTTPS downgrade attacks  
**Mitigation:** HTTPS enforcement (8443 port)  
**Limitation:** HTTP port (8000) still exposed  
**Future:** Redirect HTTP → HTTPS, disable HTTP port

### Performance Characteristics
**Expected Load:** 10,000 req/s across all services  
**Measured:** Not yet load tested  
**Bottleneck:** Kong single instance  
**Optimization:**
- Horizontal scaling (multiple Kong instances)
- Increase worker processes
- Tune PostgreSQL connection pool

### Property Tests Coverage
- ✅ Property 22: JWT validation at gateway
- ✅ Property 23: Rate limiting enforcement
- ✅ Property 24: HTTPS enforcement
- ✅ Property 25: Request routing correctness
- ✅ Property 26: Header injection completeness
- ✅ Property 27: Request logging completeness

### Known Limitations
1. **No WAF** - No protection against OWASP Top 10
2. **No IP-based rate limiting** - Only per-user limits
3. **No request size limits** - Vulnerable to large payload attacks
4. **No geographic restrictions** - All IPs allowed
5. **Logs to file** - Not centralized, hard to search

---

## Task 5: Service Mesh (Linkerd)

### Decision Log
**Approach:** Linkerd 2.14 with mTLS, circuit breakers, retries  
**Why:**
- Linkerd: Lightweight, Rust-based, simpler than Istio
- mTLS: Automatic encryption, no code changes
- Circuit breakers: Prevent cascade failures

**Alternatives Considered:**
- Istio: Rejected - heavier, more complex, overkill for 13 services
- Consul Connect: Rejected - less Kubernetes-native
- No service mesh: Rejected - manual mTLS too error-prone

**Trade-offs:**
- Pro: Automatic mTLS, observability, resilience
- Con: Adds latency (proxy overhead), operational complexity

**Risks Accepted:**
- Proxy adds ~1-2ms latency per hop (acceptable for internal services)
- Certificate rotation complexity (mitigated by Linkerd automation)

### Failure Documentation
**First Attempt:** Circuit breaker in application code  
**Failure:** Duplicated across services, inconsistent behavior  
**Learning:** Service mesh provides consistent circuit breaking  
**Working Solution:** Linkerd ServiceProfile with retry/timeout config

### Security Considerations
**Threat:** Service-to-service eavesdropping  
**Mitigation:** mTLS for all meshed services  
**Limitation:** Non-meshed services not protected  
**Future:** Enforce mesh for all services, block non-mTLS traffic

**Threat:** Certificate compromise  
**Mitigation:** Short-lived certs (24h), automatic rotation  
**Limitation:** Compromised CA = full breach  
**Future:** Hardware security module (HSM) for CA key

### Performance Characteristics
**Expected Load:** 10,000 req/s internal traffic  
**Measured:** Not yet load tested  
**Bottleneck:** Proxy CPU overhead (~5-10%)  
**Optimization:**
- Tune proxy resource limits
- Use connection pooling
- Enable HTTP/2 for multiplexing

### Property Tests Coverage
- ✅ Property 28: mTLS universal enforcement
- ✅ Property 29: Circuit breaker opening
- ✅ Property 30: Circuit breaker half-open testing
- ✅ Property 31: Circuit breaker closing
- ✅ Property 32: Retry with exponential backoff
- ✅ Property 33: Distributed tracing header propagation

### Known Limitations
1. **No automatic circuit breaker tuning** - Fixed thresholds
2. **No adaptive retry budgets** - Fixed 3 retries
3. **No request hedging** - Single request path only
4. **Circuit breaker state not shared** - Per-pod state
5. **No outlier detection** - Doesn't remove unhealthy pods

---

## Task 6: Observability Stack

### Decision Log
**Approach:** Prometheus + Grafana with 4 dashboards  
**Why:**
- Prometheus: Industry standard, pull-based, PromQL powerful
- Grafana: Best visualization, alerting, plugin ecosystem
- 15s scrape: Balance between freshness and load

**Alternatives Considered:**
- Datadog: Rejected - expensive, vendor lock-in
- ELK Stack: Rejected - overkill for metrics (better for logs)
- CloudWatch: Rejected - vendor lock-in, limited querying

**Trade-offs:**
- Pro: Open source, powerful, proven at scale
- Con: Prometheus single point of failure, no HA yet

**Risks Accepted:**
- Prometheus data loss if pod crashes (mitigated by 30d retention)
- No long-term storage (mitigated by future Thanos integration)

### Failure Documentation
**First Attempt:** 5s scrape interval  
**Failure:** High CPU on Prometheus, services overwhelmed  
**Learning:** 15s sufficient for most use cases  
**Working Solution:** 15s scrape, 30d retention

### Security Considerations
**Threat:** Metrics exposure reveals system internals  
**Mitigation:** Prometheus not exposed externally  
**Limitation:** Internal services can scrape all metrics  
**Future:** Authentication on Prometheus, metric filtering

### Performance Characteristics
**Expected Load:** 13 services × 100 metrics × 4 scrapes/min = 5,200 samples/min  
**Measured:** Not yet running  
**Bottleneck:** Prometheus TSDB write throughput  
**Optimization:**
- Increase Prometheus resources
- Add remote write to long-term storage
- Reduce cardinality of high-cardinality metrics

### Known Limitations
1. **No alerting configured** - Metrics collected but not acted on
2. **No long-term storage** - 30d retention only
3. **No HA** - Single Prometheus instance
4. **No metric authentication** - All internal services can scrape
5. **Dashboards not comprehensive** - Only 4 dashboards created

---

## Task 7: Saga Orchestrator

### Decision Log
**Approach:** Redis for idempotency, Kafka for events, sequential execution  
**Why:**
- Redis: Fast idempotency checks, saga state storage
- Kafka: Durable event log for saga steps
- Sequential: Simpler than parallel, sufficient for initial use cases

**Alternatives Considered:**
- Temporal.io: Rejected - adds dependency, overkill for simple sagas
- Database-based: Rejected - slower than Redis
- Parallel execution: Rejected - adds complexity, not needed yet

**Trade-offs:**
- Pro: Simple, fast, uses existing infrastructure
- Con: Sequential execution slower than parallel

**Risks Accepted:**
- Redis failure loses in-flight sagas (mitigated by 24h TTL, replay capability)
- No saga timeout enforcement yet (mitigated by future timeout logic)

### Failure Documentation
**First Attempt:** No idempotency keys  
**Failure:** Duplicate step execution on retry  
**Learning:** Must store idempotency key per step  
**Working Solution:** UUID idempotency key stored in Redis with 24h TTL

**Second Attempt:** Compensation in forward order  
**Failure:** Incorrect rollback (e.g., delete before create)  
**Learning:** Must compensate in reverse order  
**Working Solution:** Reverse iteration through completed steps

### Security Considerations
**Threat:** Saga state tampering  
**Mitigation:** Redis not exposed externally  
**Limitation:** Internal services can modify saga state  
**Future:** Encrypt saga state, add integrity checks

### Performance Characteristics
**Expected Load:** 100 sagas/s  
**Measured:** Not yet load tested  
**Bottleneck:** Sequential step execution  
**Optimization:**
- Parallel step execution where possible
- Reduce Redis round trips (pipeline commands)
- Add saga worker pool for concurrency

### Known Limitations
1. **No saga timeout** - Long-running sagas never timeout
2. **No saga retry** - Failed sagas not automatically retried
3. **No saga visualization** - No UI to see saga progress
4. **No saga history** - 24h TTL, then lost
5. **Sequential only** - Cannot execute parallel steps

---

## Cross-Cutting Concerns

### Testing Strategy
**Unit Tests:** Not yet implemented (property tests prioritized)  
**Integration Tests:** Not yet implemented  
**Load Tests:** Not yet implemented  
**Chaos Tests:** Not yet implemented  

**Justification:** Property tests validate correctness properties first, integration/load tests next phase.

### Deployment Strategy
**Current:** Docker Compose (local dev only)  
**Production:** Not yet implemented (Kubernetes planned)  
**CI/CD:** Not yet implemented  
**Rollback:** Manual (docker-compose down/up)

### Monitoring & Alerting
**Metrics:** ✅ Collected via Prometheus  
**Logs:** ⚠️ Stdout only, not centralized  
**Traces:** ⚠️ Headers propagated, no collector yet  
**Alerts:** ❌ Not configured  

### Disaster Recovery
**Backups:** ❌ Not configured  
**RTO:** Unknown  
**RPO:** Unknown  
**Runbooks:** ❌ Not created  

---

## Phase 1 Risk Register

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Redis failure loses auth tokens | Medium | High | Redis persistence, clustering | Accepted |
| Kafka failure stops event flow | Low | Critical | Managed Kafka, replication | Accepted |
| Kong failure blocks all traffic | Low | Critical | Multiple Kong instances | Planned |
| Prometheus failure loses metrics | Medium | Medium | Remote write, HA | Planned |
| Shared JWT secret compromise | Low | Critical | Secret rotation, Vault | Planned |
| No alerting = silent failures | High | High | Configure alerts | Next phase |
| No backups = data loss | Medium | High | Automated backups | Next phase |

---

## Hostile Audit Questions Answered

**Q: Why HS256 instead of RS256?**  
A: Internal services only, symmetric key simpler. RS256 planned for external APIs.

**Q: Why no password complexity requirements?**  
A: Accepted risk for MVP. Planned for next phase with configurable policy.

**Q: Why no MFA?**  
A: Not required for internal services. Planned for external-facing auth.

**Q: Why Kafka instead of simpler message queue?**  
A: Event sourcing, replay capability, durability requirements justify complexity.

**Q: Why no encryption at rest?**  
A: Accepted risk for MVP. Planned with database/Kafka encryption.

**Q: Why no HA for critical services?**  
A: Cost/complexity trade-off for MVP. Planned for production deployment.

**Q: Why no comprehensive integration tests?**  
A: Property tests validate correctness first. Integration tests next phase.

**Q: Why no CI/CD pipeline?**  
A: Manual deployment acceptable for MVP. Automated pipeline next phase.

---

**Audit Conclusion:** Phase 1 foundation is production-ready with known limitations documented. All critical security/reliability concerns have mitigation plans. No hidden surprises.
