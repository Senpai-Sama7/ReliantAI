#!/bin/bash

# ReliantAI - Automated Database Backup Script
# Performs a pg_dump of the production database and handles rotation

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_NAME="${POSTGRES_DB:-reliantai}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-localhost}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "[$TIMESTAMP] Starting database backup for $DB_NAME..."

# Execute pg_dump
# Note: If running inside docker, this script should be modified to use 'docker exec'
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "Warning: POSTGRES_PASSWORD not set. Assuming pg_hba.conf handles authentication or using PGPASSWORD."
fi

# Perform backup
if [ "$(docker ps -q -f name=reliantai-postgres)" ]; then
    echo "Detected running Docker container: reliantai-postgres. Using docker exec..."
    docker exec reliantai-postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
else
    echo "Docker container not found. Attempting local pg_dump..."
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
fi

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Successfully created backup: $BACKUP_FILE"
    
    # Cleanup old backups
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "${DB_NAME}_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -exec rm {} \;
    echo "Cleanup complete."
else
    echo "Error: Database backup failed!"
    exit 1
fi

echo "[$TIMESTAMP] Backup process finished."
