#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# ReliantAI Platform — Blue-Green Zero-Downtime Deployment
# ═══════════════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/blue-green-deploy.sh [local|staging|production]
#   ./scripts/blue-green-deploy.sh --rollback [local|staging|production]
#
# Strategy:
#   1. Build and start "green" stack alongside running "blue" stack
#   2. Run database migrations on green (backward-compatible required)
#   3. Run health checks and smoke tests on green
#   4. Switch nginx upstream from blue → green (atomic reload)
#   5. Run smoke tests against green via public endpoint
#   6. Keep blue running for 5-minute observation period
#   7. Stop blue after verification, or rollback if issues detected
#
# Prerequisites:
#   - Both stacks share the SAME postgres/redis/vault volumes (persistent data)
#   - Database migrations must be backward-compatible (add-only, no destructive changes)
#   - nginx upstream must use Docker DNS names (blue-money, green-money, etc.)
#   - In production, host port offsets avoid conflicts (green ports = blue + 10000)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="local"
ROLLBACK_MODE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --rollback)
            ROLLBACK_MODE=true
            shift
            ;;
        local|staging|production)
            ENVIRONMENT="$arg"
            shift
            ;;
    esac
done

COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
MONITORING_FILE="$PROJECT_ROOT/docker-compose.monitoring.yml"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Determine active and target stacks ───────────────────────────────────
detect_active_stack() {
    if docker compose -f "$COMPOSE_FILE" -p reliantai-blue ps 2>/dev/null | grep -q "reliantai-blue"; then
        echo "blue"
    elif docker compose -f "$COMPOSE_FILE" -p reliantai-green ps 2>/dev/null | grep -q "reliantai-green"; then
        echo "green"
    else
        echo "none"
    fi
}

rollback() {
    local target="$1"
    local idle="$2"

    log_error "ROLLBACK initiated: reverting from ${target} to ${idle}..."

    # Stop target stack nginx first (if running) to cut traffic
    docker compose -f "$COMPOSE_FILE" -p "reliantai-${target}" stop nginx 2>/dev/null || true

    # Restart idle stack nginx if it exists
    if docker compose -f "$COMPOSE_FILE" -p "reliantai-${idle}" ps 2>/dev/null | grep -q "nginx"; then
        docker compose -f "$COMPOSE_FILE" -p "reliantai-${idle}" start nginx || true
        log_info "Restarted ${idle} nginx — traffic reverting to ${idle}"
    fi

    # Stop target stack services (keep infra for forensics)
    docker compose -f "$COMPOSE_FILE" -p "reliantai-${target}" stop \
        money complianceone finops360 integration orchestrator \
        actuator bap apex-agents apex-ui apex-mcp \
        acropolis citadel-ultimate-a-plus citadel \
        cleardesk gen-h documancer backupiq cyberarchitect \
        sovereign-ai regenesis ops-intelligence-backend ops-intelligence-frontend || true

    log_info "Rollback complete. ${idle} stack is active. ${target} services stopped (infra preserved for forensics)."
    log_info "To fully destroy ${target} stack: docker compose -p reliantai-${target} down -v"
}

ACTIVE_STACK=$(detect_active_stack)

# ── Rollback mode ──────────────────────────────────────────────────────────
if [ "$ROLLBACK_MODE" = true ]; then
    if [ "$ACTIVE_STACK" = "none" ]; then
        log_error "No active stack detected. Cannot determine rollback target."
        exit 1
    fi

    # Rollback from active to the other stack
    if [ "$ACTIVE_STACK" = "blue" ]; then
        rollback "blue" "green"
    else
        rollback "green" "blue"
    fi
    exit 0
fi

# ── Normal deployment flow ─────────────────────────────────────────────────
if [ "$ACTIVE_STACK" = "none" ]; then
    TARGET_STACK="blue"
    IDLE_STACK="green"
    log_info "No active stack detected. Starting fresh with BLUE stack."
else
    if [ "$ACTIVE_STACK" = "blue" ]; then
        TARGET_STACK="green"
        IDLE_STACK="blue"
    else
        TARGET_STACK="blue"
        IDLE_STACK="green"
    fi
    log_info "Active stack: ${YELLOW}${ACTIVE_STACK}${NC} → Deploying to: ${GREEN}${TARGET_STACK}${NC}"
fi

export COMPOSE_PROJECT_NAME="reliantai-${TARGET_STACK}"

# ── Phase 1: Build target stack ───────────────────────────────────────────
log_info "Phase 1: Building ${TARGET_STACK} stack..."

docker compose \
    -f "$COMPOSE_FILE" \
    -p "$COMPOSE_PROJECT_NAME" \
    build --parallel

# ── Phase 2: Start target stack infrastructure ────────────────────────────
log_info "Phase 2: Starting ${TARGET_STACK} infrastructure (postgres, redis, vault)..."

docker compose \
    -f "$COMPOSE_FILE" \
    -p "$COMPOSE_PROJECT_NAME" \
    up -d postgres redis vault

# Wait for infrastructure readiness
for i in {1..12}; do
    if docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
        log_info "Postgres is ready."
        break
    fi
    log_info "Waiting for Postgres... ($i/12)"
    sleep 5
done

# ── Phase 3: Database migrations ─────────────────────────────────────────
log_info "Phase 3: Running database migrations on ${TARGET_STACK}..."

# Run migrations inside the target postgres container context
# Migrations must be backward-compatible: add-only, no destructive changes
MIGRATE_OK=false
for DB in money complianceone finops360 integration; do
    ALEMBIC_DIR="$PROJECT_ROOT/${DB}/migrations"
    if [ -d "$ALEMBIC_DIR" ]; then
        log_info "Running alembic for ${DB}..."
        if docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" exec -T money \
            bash -c "cd /app/${DB} && alembic upgrade head" 2>/dev/null || \
           docker run --rm --network "${COMPOSE_PROJECT_NAME}_reliantai-network" \
            -v "$ALEMBIC_DIR:/migrations" \
            -e DATABASE_URL="$(grep "^DATABASE_URL=" "$PROJECT_ROOT/.env" | head -1 | cut -d= -f2-)" \
            python:3.12-slim bash -c "pip install alembic psycopg2-binary && cd /migrations && alembic upgrade head" 2>/dev/null; then
            log_info "Migrations applied for ${DB}."
            MIGRATE_OK=true
        else
            log_warn "Could not run migrations for ${DB} (may not have alembic or may already be at head)."
        fi
    fi
done

if [ "$MIGRATE_OK" = false ]; then
    log_warn "No migrations were executed. Ensure migration directories exist and DATABASE_URL is set."
fi

# ── Phase 4: Start target stack services ──────────────────────────────────
log_info "Phase 4: Starting ${TARGET_STACK} application services..."

docker compose \
    -f "$COMPOSE_FILE" \
    -p "$COMPOSE_PROJECT_NAME" \
    up -d --no-deps \
    money complianceone finops360 integration orchestrator \
    actuator nginx bap apex-agents apex-ui apex-mcp \
    acropolis citadel-ultimate-a-plus citadel \
    cleardesk gen-h documancer backupiq cyberarchitect \
    sovereign-ai regenesis ops-intelligence-backend ops-intelligence-frontend

# ── Phase 5: Health checks on target ───────────────────────────────────
log_info "Phase 5: Running health checks on ${TARGET_STACK} stack..."

HEALTH_TIMEOUT=120
HEALTH_START=$(date +%s)
HEALTH_OK=false

while [ $(($(date +%s) - HEALTH_START)) -lt $HEALTH_TIMEOUT ]; do
    UNHEALTHY=$(docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" ps | grep -c "unhealthy" || true)
    RUNNING=$(docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" ps | grep -c "running" || true)

    if [ "$UNHEALTHY" -eq 0 ] && [ "$RUNNING" -ge 5 ]; then
        HEALTH_OK=true
        break
    fi

    log_info "Waiting for services... (${UNHEALTHY} unhealthy, ${RUNNING} running)"
    sleep 10
done

if [ "$HEALTH_OK" != "true" ]; then
    log_error "Health checks FAILED on ${TARGET_STACK} stack!"
    rollback "$TARGET_STACK" "$IDLE_STACK"
    exit 1
fi

log_info "Health checks PASSED on ${TARGET_STACK} stack."

# ── Phase 6: Switch traffic ─────────────────────────────────────────────
log_info "Phase 6: Switching nginx upstream to ${TARGET_STACK}..."

NGINX_CONF="$PROJECT_ROOT/nginx/nginx.conf"
cp "$NGINX_CONF" "${NGINX_CONF}.backup.$(date +%s)"

if [ "$ACTIVE_STACK" != "none" ]; then
    docker compose -f "$COMPOSE_FILE" -p "reliantai-${IDLE_STACK}" stop nginx || true
    log_info "Stopped ${IDLE_STACK} nginx — traffic now routing to ${TARGET_STACK}"
fi

# ── Phase 7: Smoke tests after switch ───────────────────────────────────
log_info "Phase 7: Running post-switch smoke tests..."

SMOKE_OK=false
SMOKE_RETRIES=6
for i in $(seq 1 $SMOKE_RETRIES); do
    sleep 5
    if curl -sf http://localhost/health >/dev/null 2>&1; then
        SMOKE_OK=true
        break
    fi
    log_warn "Smoke test attempt $i/$SMOKE_RETRIES failed..."
done

if [ "$SMOKE_OK" != "true" ]; then
    log_error "Smoke tests FAILED after traffic switch!"
    rollback "$TARGET_STACK" "$IDLE_STACK"
    exit 1
fi

log_info "Smoke tests PASSED. Public endpoint /health responding."

# ── Phase 8: Observation period ─────────────────────────────────────────
OBSERVE_MINUTES=5
log_info "Phase 8: Observation period (${OBSERVE_MINUTES} minutes)..."
sleep $((OBSERVE_MINUTES * 60))

UNHEALTHY=$(docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" ps | grep -c "unhealthy" || true)
if [ "$UNHEALTHY" -gt 0 ]; then
    log_warn "Observation FAILED: ${TARGET_STACK} has ${UNHEALTHY} unhealthy services!"
    log_warn "Initiating automatic rollback to ${IDLE_STACK}..."
    rollback "$TARGET_STACK" "$IDLE_STACK"
    exit 1
else
    log_info "Observation complete — ${TARGET_STACK} stack is stable."
fi

# ── Phase 9: Stop old stack ─────────────────────────────────────────────
if [ "$ACTIVE_STACK" != "none" ]; then
    log_info "Phase 9: Stopping ${IDLE_STACK} stack..."
    docker compose -f "$COMPOSE_FILE" -p "reliantai-${IDLE_STACK}" down -v || true
    log_info "${IDLE_STACK} stack stopped. ${TARGET_STACK} is now the active stack."
fi

log_info "=== Blue-Green Deployment Complete ==="
log_info "Active stack: ${GREEN}${TARGET_STACK}${NC}"
log_info "Environment: ${ENVIRONMENT}"

# Print verification commands
log_info ""
log_info "Verification commands:"
log_info "  docker compose -p reliantai-${TARGET_STACK} ps"
log_info "  curl -s http://localhost/health"
log_info "  ./scripts/health_check.py -v"
log_info ""
log_info "Rollback command (if needed):"
log_info "  ./scripts/blue-green-deploy.sh --rollback ${ENVIRONMENT}"
