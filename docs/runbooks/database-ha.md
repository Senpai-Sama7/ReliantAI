# PostgreSQL High Availability Runbook

**Scope**: Primary-replica failover, PgPool-II operation, and connection string management.  
**Owner**: Platform Database Team  
**Last Updated**: 2026-04-22

---

## 1. Architecture

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────┐
│   Money     │      │   PgPool-II     │      │   Primary   │
│ Compliance  │──────▶│  (read/write    │─────▶│  (read+     │
│  FinOps     │      │   split +       │      │   write)    │
│     ...     │      │   failover)     │      └─────────────┘
└─────────────┘      └─────────────────┘            │
                          │                        │ streaming
                          │               ┌──────┘ replication
                          │               ▼
                          │         ┌─────────────┐
                          └────────▶│   Replica   │
                           (reads)  │  (read-only│
                                    │  failover)│
                                    └─────────────┘
```

- **Primary** (`postgres-primary`): Accepts all writes. Synchronous replication to replica (`remote_apply`).
- **Replica** (`postgres-replica`): Hot standby for read queries. Promoted automatically on primary failure.
- **PgPool-II** (`pgpool`): Connection pooler with load balancing. Routes writes to primary, reads to replica. Automatic failover detection.
- **repmgr**: Monitors replication lag and orchestrates failover (~30s promotion time).

---

## 2. Deployment Modes

### Standard Mode (Single Instance)

```bash
docker compose up -d
```

Services connect to `postgres:5432`.

### HA Mode (Primary-Replica)

```bash
# 1. Ensure .env has REPMGR_PASSWORD and PGPOOL_ADMIN_PASSWORD set
# 2. Update service DATABASE_URLs to use pgpool (see .env.example comments)
# 3. Start with HA overlay
docker compose -f docker-compose.yml -f docker-compose.ha.yml up -d

# Verify replication status
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec postgres-primary repmgr cluster show
```

In HA mode, **all services must use `pgpool:5432` as the database host**.
PgPool-II transparently routes queries and handles failover.

---

## 3. Failover Procedure

### Automatic Failover (Default)

1. **repmgr** detects primary unavailability (3 retries, 5s interval).
2. **repmgr** promotes replica to primary (`repmgr standby promote`).
3. **PgPool-II** health check marks old primary as down.
4. **PgPool-II** redirects all traffic to new primary.

**Total expected downtime**: ~30-60 seconds.

### Verify Failover Status

```bash
# Cluster topology
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec postgres-primary repmgr cluster show

# PgPool-II node status
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec pgpool pcp_node_info -h localhost -p 9898 -U admin -w 0
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec pgpool pcp_node_info -h localhost -p 9898 -U admin -w 1

# Replication lag
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec postgres-replica psql -U postgres -c "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;"
```

### Manual Failover (Emergency)

If automatic failover does not occur:

```bash
# On the replica container, force promotion
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec postgres-replica repmgr standby promote

# Reattach old primary as new replica (after it recovers)
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec postgres-primary repmgr node rejoin -d 'host=postgres-replica user=repmgr dbname=repmgr'
```

---

## 4. Application Connection Strings

### Standard Mode

| Service | DATABASE_URL |
|---------|--------------|
| Money | `postgresql://postgres:5432/money` |
| ComplianceOne | `postgresql://postgres:5432/complianceone` |
| FinOps360 | `postgresql://postgres:5432/finops360` |
| Integration | `postgresql://postgres:5432/integration` |

### HA Mode

| Service | DATABASE_URL |
|---------|--------------|
| Money | `postgresql://pgpool:5432/money` |
| ComplianceOne | `postgresql://pgpool:5432/complianceone` |
| FinOps360 | `postgresql://pgpool:5432/finops360` |
| Integration | `postgresql://pgpool:5432/integration` |

**Important**: PgPool-II runs inside the `reliantai-network` Docker network. Services resolve `pgpool` via Docker DNS just like they resolve `postgres`.

---

## 5. Monitoring & Alerting

### Prometheus Metrics

PgPool-II exposes metrics on port 9719 (if `PGPOOL_ENABLE_POOL_HA` is set). Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'pgpool'
    static_configs:
      - targets: ['pgpool:9719']
```

### Key Metrics

| Metric | Healthy Range | Alert Threshold |
|--------|---------------|-----------------|
| Replication lag | < 1s | > 5s (warning) |
| PgPool-II backend status | 1 (up) | 0 (down) |
| Primary connections | < 80% max | > 90% (critical) |
| Replica connections | < 80% max | > 90% (warning) |

### Grafana Dashboard

Import dashboard ID `9628` (PostgreSQL Overview) and add PgPool-II panels from dashboard ID `15187`.

---

## 6. Backup in HA Mode

Run backups against the **replica** to avoid load on the primary:

```bash
# Read-only backup from replica
docker compose -f docker-compose.yml -f docker-compose.ha.yml exec postgres-replica pg_dump -U postgres -h localhost -Fc money > money_backup_$(date +%Y%m%d).dump
```

Or use `scripts/backup_database.sh` which detects Docker and uses the `DATABASE_URL` host (set to `pgpool` in HA mode; PgPool-II will route to primary for `pg_dump` since it uses a single connection).

---

## 7. Disaster Recovery

### Total Primary+Replica Loss

If both PostgreSQL nodes are lost but backups exist:

1. Stop HA stack: `docker compose -f docker-compose.yml -f docker-compose.ha.yml down`
2. Remove volumes (destructive): `docker volume rm reliantai-postgres_primary_data reliantai-postgres_replica_data`
3. Restore from backup: `pg_restore -d postgresql://pgpool:5432/money money_backup_YYYYMMDD.dump`
4. Re-initialize HA: `docker compose -f docker-compose.yml -f docker-compose.ha.yml up -d`
5. Verify replication: `repmgr cluster show`

### PgPool-II Failure

If PgPool-II fails but databases are healthy:

1. Services can temporarily connect directly to `postgres-primary:5432`.
2. Restart PgPool-II: `docker compose -f docker-compose.yml -f docker-compose.ha.yml restart pgpool`
3. No data loss; PgPool-II is stateless.

---

## 8. Performance Tuning

### PgPool-II Tuning

| Parameter | Default | Recommendation |
|-----------|---------|------------------|
| `PGPOOL_MAX_POOL` | 32 | Increase to 64 for >50 concurrent services |
| `PGPOOL_NUM_INIT_CHILDREN` | 32 | Match to `PGPOOL_MAX_POOL` |
| `PGPOOL_CHILD_LIFE_TIME` | 300 | Lower to 60 for rapid recycling |
| `PGPOOL_CONNECTION_LIFE_TIME` | 0 | Set to 3600 for connection freshness |

### PostgreSQL Tuning

Edit `docker-compose.ha.yml` environment variables:

```yaml
environment:
  POSTGRESQL_SHARED_PRELOAD_LIBRARIES: "pg_stat_statements,repmgr"
  POSTGRESQL_MAX_CONNECTIONS: 200
```

---

## 9. Contact & Escalation

| Issue | Contact | Response Time |
|-------|---------|---------------|
| Automatic failover | Automated (repmgr + PgPool) | 30-60s |
| Manual failover needed | Platform On-Call | 15 min |
| Replication lag > 5s | Database Team | 30 min |
| Total data loss (both nodes) | Database Team + Security | 1 hour |
