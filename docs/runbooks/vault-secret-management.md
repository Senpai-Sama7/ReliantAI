# Vault Secret Management Runbook

**Scope**: HashiCorp Vault integration, secret rotation, audit logging, and sidecar migration path.
**Owner**: Platform Security Team  
**Last Updated**: 2026-04-22

---

## 1. Architecture Overview

### In-Process Sidecar Pattern (Docker Compose)

Because Docker Compose does not support native Kubernetes-style sidecar containers, each service uses `shared/vault_client.py` as an **in-process sidecar**:

- A background daemon thread refreshes cached secrets before TTL expiry.
- The hot path (`get_secret()`) reads from an in-memory LRU cache with no network latency.
- If Vault is unreachable, the service continues operating with cached secrets until TTL expires.
- Every access is audit-logged as structured JSON to stdout (captured by Promtail → Loki).

### Kubernetes Sidecar Migration (Future)

When migrating to Kubernetes, replace the in-process thread with the official Vault Agent Injector:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "money"
  vault.hashicorp.com/agent-inject-secret-db: "secret/data/money/db"
  vault.hashicorp.com/agent-inject-template-db: |
    {{ with secret "secret/data/money/db" }}
    DATABASE_URL=postgresql://{{ .Data.data.user }}:{{ .Data.data.password }}@{{ .Data.data.host }}:{{ .Data.data.port }}/{{ .Data.data.dbname }}
    {{ end }}
```

The init container writes secrets to a shared `emptyDir` volume before the app container starts.

---

## 2. Secret Rotation Procedure

### Principle: Zero-Downtime Rotation

All ReliantAI services must support **two-secret rotation** (active + pending). This allows a new secret to be deployed while the old one remains valid for a brief overlap period.

### Rotation Steps

1. **Write new secret version** to Vault KV v2 (Vault keeps version history):
   ```bash
   export VAULT_TOKEN=<admin-token>
   python3 -c "
   from shared.vault_client import VaultClient
   vc = VaultClient()
   vc.rotate_secret('money/db', {
       'host': 'postgres',
       'port': 5432,
       'dbname': 'money',
       'user': 'money',
       'password': '<new-strong-password>'
   })
   print('Secret rotated')
   "
   ```

2. **Signal services to refresh** (optional — they auto-refresh within `refresh_interval_seconds`):
   ```bash
   # Hitting the /health endpoint does NOT refresh secrets.
   # If you need immediate refresh, restart the service containers:
   docker compose restart money complianceone finops360
   ```

3. **Verify connectivity** with new credentials:
   ```bash
   ./scripts/health_check.py -v
   ```

4. **Destroy old secret version** (after 24-hour overlap):
   ```bash
   curl -X DELETE \
     -H "X-Vault-Token: $VAULT_TOKEN" \
     "${VAULT_ADDR}/v1/secret/destroy/money/db" \
     -d '{"versions": [1]}'
   ```

### Rotation Cadence

| Secret Type | Rotation Frequency | Responsible Team |
|-------------|-------------------|------------------|
| Database passwords | 90 days | Platform Ops |
| API keys (Stripe, Twilio) | 180 days or on employee departure | Security |
| JWT signing keys | 365 days | Security |
| Event bus API keys | 90 days | Platform Ops |
| AWS/GCP service accounts | 90 days | FinOps |

---

## 3. Audit Logging

### Log Format

Every `get_secret`, `secret_refresh`, and `secret_rotate` action emits a structured JSON line:

```json
{
  "event": "vault_audit",
  "action": "secret_access",
  "timestamp": "2026-04-22T14:30:00Z",
  "correlation_id": "req-abc-123",
  "path": "money/db",
  "field": "password",
  "source": "cache"
}
```

### Querying Audit Logs in Loki

```logql
{service="money"} | json | action="secret_access"
```

### Alerting

Promtail + Loki + Grafana alert on:
- **Unusual secret access patterns** (>100 accesses/minute from a single pod)
- **Failed Vault reads** (source="vault" but 403/404 errors in service logs)
- **Secret rotation without change ticket** (manual query during off-hours)

---

## 4. Disaster Recovery

### Vault Unreachable

`shared/vault_client.py` is designed to **fail gracefully**:

- Cached secrets remain usable until TTL expires (default 5 minutes).
- Background refresh stops but does not crash the service.
- `get_secret(use_cache=False)` will raise `RuntimeError` if Vault is down and the secret is not cached.

### Vault Data Corruption

Vault data is stored on a Docker volume (`vault_data`). Back up this volume alongside PostgreSQL backups:

```bash
# Backup Vault data volume
docker run --rm -v reliantai-vault_data:/source -v $(pwd)/backups:/backup alpine \
  tar czf /backup/vault-data-$(date +%Y%m%d-%H%M%S).tar.gz -C /source .
```

### Re-initializing Vault After Catastrophic Loss

If Vault data is lost but PostgreSQL/Redis data survives:

1. Re-initialize Vault (`vault operator init`).
2. Re-create KV v2 mount and ACL policies (`./scripts/vault-setup.sh`).
3. Restore secrets from the last backup or re-seed from `.env` (local dev only).
4. **Rotate ALL secrets immediately** after recovery (assume compromise).

---

## 5. Security Checklist

- [ ] Vault container runs with `IPC_LOCK` capability (prevents memory from being swapped to disk).
- [ ] Vault TLS is enabled in production (see `vault/vault-config.hcl`).
- [ ] Dev root token (`VAULT_DEV_ROOT_TOKEN_ID`) is removed from `.env` before production deployment.
- [ ] Service tokens are scoped to least-privilege policies (one policy per service).
- [ ] Audit device is enabled in production (`vault audit enable file file_path=/vault/logs/audit.log`).
- [ ] `.gitleaks.toml` flags `VAULT_DEV_ROOT_TOKEN_ID` and `VAULT_TOKEN` patterns.

---

## 6. Contact & Escalation

| Issue | Contact | Response Time |
|-------|---------|---------------|
| Vault seal/unseal | Platform On-Call | 15 min |
| Secret rotation request | Security Team | 1 hour |
| Audit log anomaly | Security Team | 30 min |
| Vault data corruption | Platform Ops + Security | 1 hour |
