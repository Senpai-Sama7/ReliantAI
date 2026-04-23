#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# ReliantAI Platform — Automated Multi-Database Backup & Verification
# ═══════════════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/backup_database.sh              # Backup all platform DBs
#   ./scripts/backup_database.sh money        # Backup single DB
#   ./scripts/backup_database.sh --verify    # Verify latest backups
#   ./scripts/backup_database.sh --restore money 20250422_120000  # Restore
#
# Cron (daily at 2 AM):
#   0 2 * * * cd /opt/reliantai && ./scripts/backup_database.sh >> /var/log/reliantai-backup.log 2>&1
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASS="${POSTGRES_PASSWORD:-}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# All platform databases
ALL_DBS=(
    money
    complianceone
    finops360
    integration
    reliantai
    bap
    apex
    citadel
)

CONTAINER_NAME="reliantai-postgres"

# ── Helpers ────────────────────────────────────────────────────────────
log_info()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]  $*"; }
log_warn()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN]  $*" >&2; }
log_error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2; }

detect_postgres() {
    if docker ps -q -f "name=$CONTAINER_NAME" >/dev/null 2>&1; then
        echo "docker"
    elif command -v pg_dump >/dev/null 2>&1; then
        echo "local"
    else
        echo "none"
    fi
}

backup_db() {
    local db_name="$1"
    local backup_file="${BACKUP_DIR}/${db_name}_backup_${TIMESTAMP}.sql.gz"
    local mode
    mode=$(detect_postgres)

    mkdir -p "$BACKUP_DIR"

    log_info "Starting backup of database: $db_name (mode=$mode)"

    case "$mode" in
        docker)
            docker exec -e PGPASSWORD="$DB_PASS" "$CONTAINER_NAME" \
                pg_dump -U "$DB_USER" -h localhost "$db_name" 2>/dev/null | gzip > "$backup_file"
            ;;
        local)
            PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -U "$DB_USER" "$db_name" 2>/dev/null | gzip > "$backup_file"
            ;;
        none)
            log_error "No PostgreSQL available (neither docker container '$CONTAINER_NAME' nor local pg_dump)"
            return 1
            ;;
    esac

    # Verify backup file is non-empty
    if [ -s "$backup_file" ]; then
        local size
        size=$(du -h "$backup_file" | cut -f1)
        log_info "Backup complete: $backup_file ($size)"
        echo "$backup_file"
        return 0
    else
        log_error "Backup failed: $backup_file is empty or missing"
        rm -f "$backup_file"
        return 1
    fi
}

verify_backup() {
    local db_name="$1"
    local latest_backup
    latest_backup=$(ls -1t "${BACKUP_DIR}/${db_name}_backup_"*.sql.gz 2>/dev/null | head -1)

    if [ -z "$latest_backup" ]; then
        log_warn "No backup found for $db_name to verify"
        return 1
    fi

    log_info "Verifying backup: $(basename "$latest_backup")"

    # Check gzip integrity
    if ! gzip -t "$latest_backup" 2>/dev/null; then
        log_error "Backup file is corrupted (gzip integrity check failed): $latest_backup"
        return 1
    fi

    # Check that it contains valid SQL
    local sql_sample
    sql_sample=$(gunzip -c "$latest_backup" 2>/dev/null | head -c 1024)
    if ! echo "$sql_sample" | grep -q 'PostgreSQL database dump'; then
        log_warn "Backup may be incomplete (missing PostgreSQL dump header): $latest_backup"
        return 1
    fi

    log_info "Backup verified OK: $(basename "$latest_backup")"
    return 0
}

cleanup_old_backups() {
    local db_name="$1"
    log_info "Cleaning up backups older than $RETENTION_DAYS days for $db_name..."
    find "$BACKUP_DIR" -name "${db_name}_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -exec rm -v {} \; 2>/dev/null || true
}

restore_db() {
    local db_name="$1"
    local backup_timestamp="$2"
    local backup_file="${BACKUP_DIR}/${db_name}_backup_${backup_timestamp}.sql.gz"
    local mode
    mode=$(detect_postgres)

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    log_warn "RESTORING database '$db_name' from $backup_file"
    log_warn "This will OVERWRITE existing data. Press ENTER to continue or Ctrl+C to abort..."
    read -r

    case "$mode" in
        docker)
            gunzip -c "$backup_file" | docker exec -i -e PGPASSWORD="$DB_PASS" "$CONTAINER_NAME" \
                psql -U "$DB_USER" -h localhost -d "$db_name"
            ;;
        local)
            gunzip -c "$backup_file" | PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$db_name"
            ;;
        none)
            log_error "No PostgreSQL available for restore"
            return 1
            ;;
    esac

    log_info "Restore complete for $db_name"
}

backup_all() {
    local failed=0
    for db in "${ALL_DBS[@]}"; do
        if ! backup_db "$db"; then
            ((failed++)) || true
        fi
        cleanup_old_backups "$db"
    done

    if [ "$failed" -gt 0 ]; then
        log_error "$failed database backup(s) failed"
        exit 1
    fi

    log_info "All database backups completed successfully"
}

verify_all() {
    local failed=0
    for db in "${ALL_DBS[@]}"; do
        if ! verify_backup "$db"; then
            ((failed++)) || true
        fi
    done

    if [ "$failed" -gt 0 ]; then
        log_warn "$failed database backup verification(s) failed"
        return 1
    fi

    log_info "All backup verifications passed"
}

# ── Main ─────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $0 [options] [database] [timestamp]

Commands:
  (no args)              Backup ALL platform databases
  <db_name>              Backup single database
  --verify               Verify integrity of latest backups
  --restore <db> <ts>    Restore database from backup timestamp (YYYYMMDD_HHMMSS)
  --list                 List available backups
  --help                 Show this help

Databases: ${ALL_DBS[*]}

Environment:
  BACKUP_DIR             Backup storage directory (default: ./backups)
  POSTGRES_USER          DB username (default: postgres)
  POSTGRES_PASSWORD      DB password
  POSTGRES_HOST          DB host (default: localhost)
  BACKUP_RETENTION_DAYS  Days to keep backups (default: 30)

Examples:
  $0                           # Backup everything
  $0 money                     # Backup only money DB
  $0 --verify                  # Verify all latest backups
  $0 --restore money 20250422_120000
EOF
}

case "${1:-}" in
    --help|-h)
        usage
        exit 0
        ;;
    --verify)
        verify_all
        ;;
    --restore)
        if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
            log_error "Usage: $0 --restore <db_name> <timestamp>"
            exit 1
        fi
        restore_db "$2" "$3"
        ;;
    --list)
        log_info "Available backups in $BACKUP_DIR:"
        ls -la "$BACKUP_DIR"/*.sql.gz 2>/dev/null || log_info "No backups found"
        ;;
    "")
        backup_all
        ;;
    *)
        backup_db "$1"
        cleanup_old_backups "$1"
        ;;
esac
