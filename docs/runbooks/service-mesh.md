# Service Mesh Architecture & Migration Runbook

**Scope**: Linkerd service mesh evaluation, migration path from Docker Compose to Kubernetes, mTLS, traffic management, and distributed tracing.  
**Owner**: Platform Infrastructure Team  
**Last Updated**: 2026-04-22

---

## 1. Current State (Docker Compose)

ReliantAI runs as a **26-service federated platform** on Docker Compose with:

- **nginx** as L7 reverse proxy + API gateway
- **Direct service-to-service HTTP** over `reliantai-network`
- **Shared secrets** via Vault (in-process sidecar pattern)
- **Circuit breakers** at nginx upstream level + application level
- **Observability** via Prometheus + Grafana + Loki + Tempo/Jaeger

### Why Docker Compose Doesn't Need a Full Service Mesh

| Feature | Docker Compose Solution | Kubernetes Need |
|---------|------------------------|-----------------|
| mTLS | Vault-issued certs + nginx SSL termination | Linkerd auto-mTLS |
| Traffic splitting | nginx upstream weights | Linkerd traffic split CRD |
| Retries/timeouts | `proxy_next_upstream` in nginx | Linkerd retry budget |
| Load balancing | `least_conn` in nginx upstream | Linkerd EWMA |
| Observability | OpenTelemetry + Tempo/Jaeger | Linkerd metrics + tap |

**Verdict**: In Docker Compose, nginx + OpenTelemetry provide 80% of service mesh value. Full mesh migration is deferred to Kubernetes.

---

## 2. Kubernetes Migration Path

### Phase 1: Linkerd Installation

```bash
# Install Linkerd CLI
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh

# Verify cluster readiness
linkerd check --pre

# Install Linkerd control plane
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -

# Verify installation
linkerd check
```

### Phase 2: Service Mesh Injection

Annotate namespaces for automatic sidecar injection:

```yaml
# manifests/namespace-reliantai.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: reliantai
  annotations:
    linkerd.io/inject: enabled
```

All pods in `reliantai` namespace get Linkerd proxy sidecars automatically.

### Phase 3: Service Profiles (Retries + Timeouts)

```yaml
# manifests/service-profile-money.yaml
apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: money.reliantai.svc.cluster.local
  namespace: reliantai
spec:
  routes:
    - name: POST /dispatch
      condition:
        method: POST
        pathRegex: /dispatch
      isRetryable: true
      timeout: 30s
      retryBudget:
        retryRatio: 0.2
        minRetriesPerSecond: 10
        ttl: 10s
    - name: GET /health
      condition:
        method: GET
        pathRegex: /health
      timeout: 5s
```

### Phase 4: Traffic Splitting (Canary / Blue-Green)

```yaml
# manifests/traffic-split-money.yaml
apiVersion: split.smi-spec.io/v1alpha4
kind: TrafficSplit
metadata:
  name: money-split
  namespace: reliantai
spec:
  service:
    name: money
    namespace: reliantai
  backends:
    - service: money-v1
      weight: 90
    - service: money-v2
      weight: 10
```

---

## 3. mTLS Between Services

### Current (Docker Compose)

- nginx terminates TLS at the edge (`443`)
- Internal traffic is plaintext over Docker network (trusted boundary)
- Vault provides secret distribution

### Kubernetes (Linkerd)

- **Automatic mTLS**: Linkerd proxies negotiate TLS automatically
- **Identity**: Each pod gets a SPIFFE identity certificate
- **Authorization**: NetworkPolicies + Linkerd ServerAuthorization resources

```yaml
# manifests/server-auth-money.yaml
apiVersion: policy.linkerd.io/v1beta1
kind: ServerAuthorization
metadata:
  namespace: reliantai
  name: money-api-auth
spec:
  server:
    name: money-api
  requiredAuthenticationRefs:
    - name: complianceone-identity
      kind: ServiceAccount
      namespace: reliantai
```

---

## 4. Advanced Traffic Management

### Circuit Breakers (Linkerd)

Linkerd provides **failure accrual** (circuit breaking) out of the box:

| Parameter | Default | ReliantAI Setting |
|-----------|---------|-------------------|
| `failureAccrual.consecutiveFailures` | 5 | 3 (matches nginx `max_fails`) |
| `failureAccrual.secsUntilOpen` | 10s | 30s (matches nginx `fail_timeout`) |
| `failureAccrual.maxRequests` | 1000 | 500 |

```yaml
# Add to ServiceProfile
spec:
  failureAccrual:
    consecutiveFailures: 3
    secsUntilOpen: 30
```

### Retry Budgets

Prevents retry storms during cascading failures:

```yaml
spec:
  routes:
    - retryBudget:
        retryRatio: 0.2      # Max 20% of requests can be retries
        minRetriesPerSecond: 10
        ttl: 10s
```

---

## 5. Observability Integration

### Linkerd + Existing Stack

| Signal | Current | With Linkerd |
|--------|---------|--------------|
| Metrics | Prometheus (custom) | Prometheus + Linkerd metrics |
| Traces | OpenTelemetry → Tempo/Jaeger | Same (Linkerd adds proxy spans) |
| Logs | Loki (structured JSON) | Same |
| Topology | Manual | Linkerd tap + topology dashboard |

### Linkerd Dashboard

```bash
# Port-forward Linkerd viz dashboard
linkerd viz dashboard &

# Real-time traffic between services
linkerd viz top deployment/money --namespace reliantai

# Tap (live packet capture)
linkerd viz tap deploy/money --namespace reliantai
```

---

## 6. Migration Checklist

### Pre-Migration (Docker Compose)

- [x] All services have health checks (`/health` or `/api/health`)
- [x] All containers have `curl` installed
- [x] OpenTelemetry tracing configured in core services
- [x] Prometheus metrics endpoints exposed
- [x] nginx upstream circuit breakers configured

### Migration Steps

1. **Containerize for Kubernetes**
   - Convert `docker-compose.yml` to Kubernetes manifests (or use Kompose)
   - Ensure all images are multi-arch (AMD64 + ARM64)
   - Add `readinessProbe` and `livenessProbe` to all Deployments

2. **Install Linkerd**
   - Control plane + viz extension
   - Jaeger extension (for trace collection)

3. **Enable Injection**
   - Annotate `reliantai` namespace
   - Verify sidecars injected: `kubectl get pods -n reliantai -o jsonpath='{.items[*].spec.containers[*].name}'`

4. **Configure ServiceProfiles**
   - One per service (based on current nginx timeout/retry settings)
   - Match existing circuit breaker parameters

5. **TrafficSplit for Blue-Green**
   - Replace nginx upstream switching with Linkerd TrafficSplit
   - Gradual rollout: 1% → 10% → 50% → 100%

6. **Remove nginx (Optional)**
   - Linkerd can handle L7 routing via Ingress + ServiceProfiles
   - Or keep nginx as Linkerd-aware ingress: `nginx.ingress.kubernetes.io/service-upstream: "true"`

7. **Verify**
   - `linkerd check`
   - `linkerd viz stat deployment/ --namespace reliantai`
   - All services healthy in Grafana
   - Traces show Linkerd proxy spans

---

## 7. Docker Compose Simulation (Current)

For development and staging, `docker-compose.servicemesh.yml` provides a **conceptual** Linkerd overlay using the Linkerd proxy as a standalone container:

```bash
# NOT for production — demonstrates proxy configuration
docker compose -f docker-compose.yml -f docker-compose.servicemesh.yml up -d
```

**Limitations**:
- No automatic mTLS (certificates must be mounted manually)
- No service discovery (DNS resolution only)
- No TrafficSplit (nginx handles routing)

**Use case**: Testing proxy configuration, header injection, timeout behavior before Kubernetes migration.

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Linkerd control plane failure | Low | High | HA control plane (3 replicas), Prometheus alerts |
| Sidecar resource overhead | Medium | Medium | 100m CPU / 128Mi memory per pod, right-sized |
| mTLS certificate expiry | Low | High | Automatic rotation (24h default), alert on < 7 days |
| Traffic split misconfiguration | Medium | High | Test in staging first, gradual rollout |
| Sidecar injection failure | Low | Medium | `linkerd check --proxy`, fallback to direct communication |

---

## 9. Contact & Escalation

| Issue | Contact | Response Time |
|-------|---------|---------------|
| Linkerd control plane down | Platform Infrastructure On-Call | 15 min |
| mTLS certificate issues | Security Team | 30 min |
| Traffic split rollback needed | Platform Ops | 15 min |
| Sidecar performance regression | Platform Infrastructure | 1 hour |
