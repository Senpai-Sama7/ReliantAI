# ReliantAI Platform - Operational Runbook

## Table of Contents
1. [Daily Operations](#daily-operations)
2. [Incident Response](#incident-response)
3. [Deployment Procedures](#deployment-procedures)
4. [Backup & Recovery](#backup--recovery)
5. [Performance Tuning](#performance-tuning)
6. [Security Operations](#security-operations)

---

## Daily Operations

### Morning Health Check

```bash
#!/bin/bash
# Run this script daily to verify platform health

echo "=== ReliantAI Morning Health Check ==="

# 1. Check all services are running
echo "Checking service status..."
docker compose ps | grep -E "Exit|Restarting" && echo "⚠️  Some services are down!" || echo "✅ All services running"

# 2. Health endpoint checks
echo "Checking health endpoints..."
for service in 8000 8001 8002 8003 8080 8081 8083 9000; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$service/health 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo "✅ Port $service: Healthy"
    else
        echo "❌ Port $service: Unhealthy (HTTP $response)"
    fi
done

# 3. Check database connectivity
echo "Checking PostgreSQL..."
docker exec -it reliantai-postgres pg_isready -U postgres > /dev/null 2>&1 && echo "✅ PostgreSQL ready" || echo "❌ PostgreSQL not responding"

# 4. Check Redis
echo "Checking Redis..."
docker exec -it reliantai-redis redis-cli ping 2>/dev/null | grep -q "PONG" && echo "✅ Redis responding" || echo "❌ Redis not responding"

# 5. Check Celery queue depth
echo "Checking Celery queues..."
docker exec -it $(docker compose ps -q money) celery -A reliantai.celery_app inspect reserved 2>/dev/null | grep -q " OK" && echo "✅ Celery workers responding" || echo "⚠️  Check Celery workers"

# 6. Check disk space
echo "Checking disk space..."
df -h | awk '$5 > 80 {print "⚠️  High disk usage: " $0}' || echo "✅ Disk space OK"

echo "=== Health Check Complete ==="
```

### Monitoring Dashboards

| Metric | Command/URL | Alert Threshold |
|--------|-------------|-----------------|
| Service Health | `curl http://localhost:8000/health` | HTTP != 200 |
| Response Time | `curl -w "%{time_total}" http://localhost:8000/health` | > 500ms |
| Queue Depth | `redis-cli LLEN celery` | > 1000 |
| DB Connections | `psql -c "SELECT count(*) FROM pg_stat_activity;"` | > 80% max |
| Memory Usage | `docker stats --no-stream` | > 80% |
| CPU Usage | `docker stats --no-stream` | > 80% for 5m |
| Disk Usage | `df -h` | > 80% |
| DLQ Size | `curl http://localhost:8081/dlq?limit=1` | > 0 |

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **SEV-1** | Platform down / Data loss | 15 min | All services down |
| **SEV-2** | Major feature impaired | 1 hour | Money service down |
| **SEV-3** | Minor feature impaired | 4 hours | GrowthEngine degraded |
| **SEV-4** | Cosmetic / Non-urgent | 24 hours | Log noise |

### Incident Response Playbooks

#### SEV-1: Complete Platform Outage

```bash
# 1. VERIFY THE OUTAGE
curl -I http://localhost:8880/health  # Nginx
curl -I http://localhost:8000/health  # Core API
docker compose ps

# 2. CHECK INFRASTRUCTURE
docker compose logs --tail=100 postgres
docker compose logs --tail=100 redis

# 3. EMERGENCY RESTART
docker compose down
docker compose up -d postgres redis  # Start core infra first
sleep 10
docker compose up -d  # Start remaining services

# 4. VERIFY RECOVERY
./scripts/health_check.py -v

# 5. CHECK DATA INTEGRITY
docker exec -it reliantai-postgres psql -U postgres -d reliantai -c "SELECT count(*) FROM prospects;"
```

#### SEV-2: Money Service Down (Revenue Impact)

```bash
# 1. CHECK SERVICE STATUS
docker compose ps money
docker compose logs --tail=200 money | grep -i error

# 2. CHECK DEPENDENCIES
curl http://localhost:5432  # Postgres (should fail, check container)
docker exec -it reliantai-postgres psql -U postgres -c "SELECT 1"

# 3. COMMON FIXES

# Database connection issue
docker compose restart postgres
docker compose restart money

# Memory/CPU issue
docker stats --no-stream  # Check resource usage
docker compose up -d --scale money=1  # Reset to single instance

# 4. VERIFY
curl http://localhost:8000/health
curl http://localhost:8000/dispatches?limit=1
```

#### SEV-2: Celery Tasks Not Processing

```bash
# 1. CHECK WORKERS
celery -A reliantai.celery_app inspect active
celery -A reliantai.celery_app inspect stats

# 2. CHECK QUEUE DEPTH
redis-cli LLEN celery  # Default queue
redis-cli LLEN agents   # Agents queue
redis-cli LLEN outreach # Outreach queue

# 3. CHECK REDIS
docker compose logs --tail=50 redis
docker exec -it reliantai-redis redis-cli INFO memory

# 4. RESTART WORKERS
docker compose restart money  # Workers run in money service
docker compose logs -f money | grep celery

# 5. MONITOR RECOVERY
watch -n 5 'redis-cli LLEN celery'
```

#### SEV-3: ISR Cache Stale (Client Sites)

```bash
# 1. CHECK CACHE HIT RATE
# (Check Next.js analytics or Cloudflare)

# 2. MANUAL REVALIDATION
# Revalidate specific slug
curl -X POST https://preview.reliantai.org/api/revalidate \
  -H "Authorization: Bearer $REVALIDATE_SECRET" \
  -d '{"slug": "acme-hvac-atlanta-1234"}'

# 3. BULK REVALIDATION
# Revalidate all sites
docker exec -it reliantai-postgres psql -U postgres -d reliantai -t -c \
  "SELECT slug FROM generated_sites WHERE status='preview_live';" | \
  while read slug; do
    curl -X POST https://preview.reliantai.org/api/revalidate \
      -H "Authorization: Bearer $REVALIDATE_SECRET" \
      -d "{\"slug\": \"$slug\"}"
  done

# 4. RESTART CLIENT SITES
docker compose restart reliant-os-frontend
docker compose restart nginx
```

#### SEV-3: Event Bus Message Loss

```bash
# 1. CHECK DLQ
curl http://localhost:8081/dlq?limit=100

# 2. CHECK REDIS PUB/SUB
docker exec -it reliantai-redis redis-cli PUBSUB CHANNELS

# 3. CHECK EVENT BUS HEALTH
curl http://localhost:8081/health
docker compose logs --tail=100 event-bus

# 4. RESTART EVENT BUS
docker compose restart event-bus

# 5. PROCESS DLQ (manual)
# Review DLQ events and re-publish if needed
curl http://localhost:8081/dlq?limit=10 | jq '.events[] | select(.request.event_type == "lead.created")'
```

### Post-Incident Checklist

- [ ] Incident documented in incident log
- [ ] Root cause identified
- [ ] Fix implemented and verified
- [ ] Monitoring/alerting improved to catch earlier
- [ ] Post-mortem scheduled (for SEV-1/2)
- [ ] Customer communication sent (if external impact)

---

## Deployment Procedures

### Standard Deployment

```bash
# 1. VERIFY PRE-CONDITIONS
./scripts/health_check.py -v
git status  # Ensure clean working directory

# 2. BACKUP DATABASE (production only)
docker exec -it reliantai-postgres pg_dumpall -U postgres > backup-$(date +%Y%m%d-%H%M%S).sql

# 3. PULL CHANGES
git pull origin main

# 4. DATABASE MIGRATIONS
cd reliantai
alembic upgrade head

# 5. ROLLING RESTART
docker compose up -d --build --no-deps reliantai
docker compose up -d --build --no-deps money
docker compose up -d --build --no-deps growthengine
# ... etc for other services

# 6. VERIFY
curl http://localhost:8000/health
curl http://localhost:8000/api/v2/prospects?limit=1

# 7. SMOKE TESTS
./scripts/smoke_tests.sh
```

### Database Migration Rollback

```bash
# If migration fails:

# 1. CHECK MIGRATION STATUS
alembic current
alembic history

# 2. ROLLBACK ONE VERSION
alembic downgrade -1

# 3. VERIFY
docker exec -it reliantai-postgres psql -U postgres -d reliantai -c "\dt"

# 4. FIX ISSUE, RE-MIGRATE
# ... fix code ...
alembic upgrade head
```

### Blue-Green Deployment (Zero Downtime)

```bash
# Using docker compose override files

# 1. START GREEN ENVIRONMENT
docker compose -f docker-compose.yml -f docker-compose.green.yml up -d

# 2. VERIFY GREEN
curl http://localhost:8001/health  # Green listens on 8001

# 3. SWITCH TRAFFIC (nginx config update)
# Edit nginx/integrated.conf to point to green upstream

# 4. RELOAD NGINX
docker compose exec nginx nginx -s reload

# 5. VERIFY TRAFFIC FLOWING
watch -n 1 'curl -s http://localhost:8000/health'

# 6. STOP BLUE (old) ENVIRONMENT
docker compose stop money
docker compose rm money
```

---

## Backup & Recovery

### Automated Backup Strategy

```bash
# Add to crontab for automated backups

# PostgreSQL - Daily at 2 AM
0 2 * * * docker exec -i reliantai-postgres pg_dumpall -U postgres > /backups/postgres-$(date +\%Y\%m\%d).sql

# Redis - Daily at 2:30 AM
30 2 * * * docker exec -i reliantai-redis redis-cli BGSAVE
30 2 * * * cp /var/lib/docker/volumes/reliantai_redis_data/_data/dump.rdb /backups/redis-$(date +%Y%m%d).rdb

# Clean old backups (keep 7 days)
0 3 * * * find /backups -name "*.sql" -mtime +7 -delete
0 3 * * * find /backups -name "*.rdb" -mtime +7 -delete
```

### Manual Backup

```bash
# PostgreSQL Full Backup
docker exec -it reliantai-postgres pg_dumpall -U postgres > full-backup-$(date +%Y%m%d-%H%M%S).sql

# Single Database
docker exec -it reliantai-postgres pg_dump -U postgres reliantai > reliantai-backup.sql

# Redis (RDB)
docker exec -it reliantai-redis redis-cli BGSAVE
docker cp $(docker compose ps -q redis):/data/dump.rdb ./redis-backup.rdb

# Configuration Backup
tar -czf config-backup.tar.gz .env docker-compose.yml nginx/ reliantai/alembic.ini
```

### Database Recovery

```bash
# FULL RESTORE (DESTROYS CURRENT DATA)

# 1. STOP SERVICES
docker compose down

# 2. REMOVE OLD VOLUME (DANGER!)
docker volume rm reliantai_postgres_data

# 3. START POSTGRES
docker compose up -d postgres

# 4. WAIT FOR READY
sleep 10

# 5. RESTORE BACKUP
docker exec -i reliantai-postgres psql -U postgres < full-backup-20260425.sql

# 6. VERIFY
docker exec -it reliantai-postgres psql -U postgres -d reliantai -c "SELECT count(*) FROM prospects;"

# 7. START REMAINING SERVICES
docker compose up -d
```

### Point-in-Time Recovery (if WAL archiving enabled)

```bash
# Stop PostgreSQL
docker compose stop postgres

# Restore base backup
# ... restore backup file ...

# Apply WAL files
# ... recovery.conf configuration ...

# Start and verify
docker compose start postgres
```

---

## Performance Tuning

### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Check table bloat
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
WHERE n_tup_del > n_tup_ins * 0.1;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_tup_read, n_tup_fetch
FROM pg_stats
WHERE schemaname = 'public'
AND n_tup_read > 10000;

-- Add recommended indexes
CREATE INDEX CONCURRENTLY idx_prospects_status ON prospects(status);
CREATE INDEX CONCURRENTLY idx_prospects_trade ON prospects(trade);
CREATE INDEX CONCURRENTLY idx_generated_sites_slug ON generated_sites(slug);
CREATE INDEX CONCURRENTLY idx_research_jobs_status ON research_jobs(status);

-- Vacuum analyze
VACUUM ANALYZE;
```

### Redis Optimization

```bash
# Check memory usage
docker exec -it reliantai-redis redis-cli INFO memory

# Check key count
docker exec -it reliantai-redis redis-cli DBSIZE

# Find large keys
docker exec -it reliantai-redis redis-cli --bigkeys

# Set maxmemory policy (in redis.conf or docker-compose)
# maxmemory-policy allkeys-lru

# Clear old events manually
docker exec -it reliantai-redis redis-cli EVAL "
  local keys = redis.call('keys', 'event:*')
  for i=1,#keys,5000 do
    redis.call('del', unpack(keys, i, math.min(i+4999, #keys)))
  end
  return #keys
" 0
```

### Celery Optimization

```python
# Increase concurrency for I/O bound tasks
# In docker-compose.yml:
command: celery -A reliantai.celery_app worker -Q agents --concurrency 4

# Enable task acknowledgment after completion (for long tasks)
# In celery_app.py:
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Set prefetch multiplier to 1 for fair distribution
app.conf.worker_prefetch_multiplier = 1

# Use Redis as result backend for better performance
app.conf.result_backend = os.environ.get("REDIS_URL")
app.conf.result_expires = 3600  # 1 hour TTL
```

### Client Sites (Next.js) Optimization

```typescript
// Reduce ISR revalidation time for high-traffic pages
// In app/[slug]/page.tsx:
export const revalidate = 1800;  // 30 minutes instead of 3600

// Use dynamic imports for heavy components
const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  ssr: false,
  loading: () => <Skeleton />
});

// Enable image optimization
// In next.config.ts:
images: {
  remotePatterns: [
    { hostname: '**.googleusercontent.com' },
  ],
  formats: ['image/webp', 'image/avif'],
}
```

---

## Security Operations

### Security Audit Checklist

```bash
# Run monthly

echo "=== Security Audit ==="

# 1. Check for exposed secrets
git log --all --source --full-history -S 'password\|secret\|key\|token' -- .env
grep -r "sk_live_\|AKIA\|ghp_" . --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null || echo "✅ No hardcoded secrets found"

# 2. Check Docker images for vulnerabilities
docker scout quickview  # Requires Docker Scout
docker images | grep -E "reliantai" | awk '{print $3}' | xargs -I {} docker scan {} 2>/dev/null || echo "⚠️  Docker scan not available"

# 3. Check SSL/TLS certificates (production)
openssl s_client -connect reliantai.org:443 -servername reliantai.org < /dev/null 2>/dev/null | openssl x509 -noout -dates

# 4. Check rate limiting is active
curl -I http://localhost:8000/health  # Check X-RateLimit headers

# 5. Verify security headers
curl -I http://localhost:8000/health | grep -i "content-security\|x-frame\|x-content-type\|hsts"

# 6. Check audit logs
docker compose logs --since=24h | grep -i "audit\|unauthorized\|forbidden" | tail -50

echo "=== Audit Complete ==="
```

### API Key Rotation

```bash
# 1. Generate new keys
NEW_API_KEY=$(openssl rand -hex 32)
NEW_EVENT_BUS_KEY=$(openssl rand -hex 32)

# 2. Update Vault/secrets (do NOT update .env yet)
echo "NEW_API_KEY=$NEW_API_KEY"

# 3. Update services gradually (blue-green style)
docker compose up -d --no-deps -e API_SECRET_KEY=$NEW_API_KEY reliantai

# 4. Verify new key works
curl -H "Authorization: Bearer $NEW_API_KEY" http://localhost:8000/api/v2/prospects

# 5. Revoke old keys after grace period (1 hour)
# Update .env for next restart
echo "API_SECRET_KEY=$NEW_API_KEY" >> .env.new
```

### Log Analysis

```bash
# Find errors in last hour
docker compose logs --since=1h | grep -i error | tail -50

# Find slow requests (Money service)
docker compose logs money | grep -E "[0-9]+ms" | grep -E "[0-9]{4,}ms" | tail -20

# Find authentication failures
docker compose logs | grep -i "401\|403\|unauthorized\|forbidden" | tail -20

# Aggregate by endpoint
docker compose logs money | grep -oE "(GET|POST|PUT|DELETE) [^ ]+" | sort | uniq -c | sort -rn | head -20
```

---

## Capacity Planning

### Scaling Triggers

| Metric | Scale Up At | Scale Down At |
|--------|-------------|---------------|
| CPU Usage | > 70% for 5m | < 20% for 10m |
| Memory Usage | > 80% for 5m | < 30% for 10m |
| Response Time | P95 > 500ms | P95 < 100ms |
| Queue Depth | > 1000 | < 100 |
| Error Rate | > 1% | < 0.1% |

### Manual Scaling

```bash
# Scale Money service
docker compose up -d --scale money=3

# Update nginx upstream for load balancing
# Edit nginx/integrated.conf:
upstream money_backend {
    least_conn;
    server money:8000;
    server money_2:8000;
    server money_3:8000;
}

# Reload nginx
docker compose exec nginx nginx -s reload
```

---

## Contact & Escalation

| Role | Contact | When to Contact |
|------|---------|-----------------|
| On-Call Engineer | PagerDuty | SEV-1, SEV-2 incidents |
| Platform Lead | Slack: #platform | Architecture decisions |
| Security Team | security@reliantai.org | Security incidents |
| Product Team | Slack: #product | Feature issues |

---

*Operational Runbook Version: 1.0*
*Review Schedule: Monthly*
*Last Updated: April 2026*
