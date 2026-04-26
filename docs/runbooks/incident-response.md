# ReliantAI Platform — Incident Response Runbooks

## Severity 1: Complete Platform Down

### Symptoms
- All services unreachable
- Dashboard disconnected
- External users reporting errors

### Response Steps
1. **Check Docker daemon**: `docker ps`
2. **Check disk space**: `df -h`
3. **Restart all services**: `docker compose down && docker compose up -d`
4. **Run health checks**: `./scripts/health_check.py -v`
5. **Check orchestrator status**: `curl http://localhost:9000/status`

### Escalation
- If restart fails: Check PostgreSQL and Redis logs
- If database corruption suspected: Restore from backup

---

## Severity 2: Single Service Down

### Symptoms
- One service shows `unhealthy` or `unreachable` in health checks
- Dependent services may show degraded performance

### Response Steps
1. **Check service logs**: `docker compose logs [service-name]`
2. **Check health endpoint**: `curl http://localhost:[port]/health`
3. **Restart service**: `docker compose restart [service-name]`
4. **Check dependencies**: Verify postgres/redis are healthy
5. **Rebuild if needed**: `docker compose up -d --build [service-name]`

### Common Service Ports
| Service | Port |
|---------|------|
| money | 8000 |
| complianceone | 8001 |
| finops360 | 8002 |
| integration | 8080 |
| orchestrator | 9000 |
| bap | 8108 |
| ops-intelligence-backend | 8095 |
| apex-agents | 8109 |
| apex-ui | 8112 |
| apex-mcp | 4000 |
| acropolis | 8110 |
| citadel | 8100 |
| citadel-ultimate-a-plus | 8111 |
| cleardesk | 8101 |
| gen-h | 8102 |
| documancer | 8103 |
| backupiq | 8104 |
| cyberarchitect | 8105 |
| sovereign-ai | 8106 |
| regenesis | 8107 |

---

## Severity 3: Degraded Performance

### Symptoms
- Response times > 1000ms
- Auto-scaling triggered but not resolving
- High CPU/memory usage

### Response Steps
1. **Check orchestrator metrics**: `curl http://localhost:9000/dashboard`
2. **Review decision history**: `curl http://localhost:9000/decisions`
3. **Manual scale if needed**: `curl -X POST "http://localhost:9000/services/money/scale?target_instances=5"`
4. **Check database connection pools**: Review service logs for pool exhaustion
5. **Check Redis memory**: `docker compose exec redis redis-cli info memory`

---

## Database Recovery Runbook

### PostgreSQL Recovery

#### Minor Issue (connection pool exhausted)
1. Restart affected service: `docker compose restart [service]`
2. Check active connections: `docker compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"`

#### Major Issue (data corruption)
1. **Stop all services**: `docker compose stop`
2. **Locate latest backup**: Check `scripts/backup_database.sh` output or S3 bucket
3. **Restore backup**:
   ```bash
   docker compose exec postgres psql -U postgres -c "DROP DATABASE [db_name];"
   docker compose exec postgres psql -U postgres -c "CREATE DATABASE [db_name];"
   docker compose exec -T postgres psql -U postgres [db_name] < backup.sql
   ```
4. **Restart services**: `docker compose up -d`
5. **Verify data integrity**: Run health checks and spot-check critical tables

### Redis Recovery

#### Cache Issues
1. **Flush cache**: `docker compose exec redis redis-cli FLUSHALL`
2. **Restart services** that depend on Redis sessions

#### Persistence Issues
1. **Check AOF/RDB files**: `docker compose exec redis ls /data`
2. **If corrupted, remove and restart**: 
   ```bash
   docker compose stop redis
   docker run --rm -v reliantai_redis_data:/data busybox rm -f /data/appendonly.aof
   docker compose up -d redis
   ```

---

## Service Rollback Runbook

### Docker Image Rollback
1. **Identify previous image tag**: `docker images | grep [service]`
2. **Update compose to use previous tag**: Edit `docker-compose.yml` or use override
3. **Restart with old image**: `docker compose up -d [service]`

### Code Rollback
1. **Identify last known good commit**: `git log --oneline`
2. **Revert**: `git revert [bad-commit]` or `git checkout [good-commit]`
3. **Rebuild and restart**: `docker compose up -d --build [service]`
4. **Verify**: `./scripts/health_check.py -v`

---

## Security Incident Response

### Unauthorized Access Detected
1. **Revoke compromised tokens**: Delete from Redis `token_revoked:*`
2. **Rotate API keys**: Update `.env` and restart affected services
3. **Review audit logs**: Check `integration/auth` logs
4. **Block suspicious IPs**: Update nginx rate limiting or firewall rules

### Secrets Leaked
1. **Rotate all credentials immediately**
2. **Check `.gitleaks.toml` and run scan**: `gitleaks detect --verbose`
3. **Update CI/CD secrets**: GitHub Actions secrets, Vault, etc.

---

## Contact & Escalation

| Team | Channel | Severity |
|------|---------|----------|
| Platform | #platform-alerts | P1-P3 |
| Security | #security-alerts | P1-P2 |
| AI/ML | #ai-alerts | P2-P3 |
| On-Call | oncall@reliantai.io | P1 |
