#!/bin/bash
# PostgreSQL Replica - Initialization Script
# This runs on replica container to set up streaming replication

set -e

PRIMARY_HOST="${PRIMARY_HOST:-postgres-primary}"
PRIMARY_PORT="${PRIMARY_PORT:-5432}"
REPLICATOR_USER="${REPLICATOR_USER:-replicator}"
REPLICATOR_PASSWORD="${REPLICATOR_PASSWORD:-replpass}"

# Wait for primary to be ready
echo "Waiting for primary at ${PRIMARY_HOST}:${PRIMARY_PORT}..."
until pg_isready -h ${PRIMARY_HOST} -p ${PRIMARY_PORT} -U ${REPLICATOR_USER}; do
    echo "Primary not ready, waiting..."
    sleep 2
done

# Stop PostgreSQL if running (needed for base backup)
pg_ctl stop -D "$PGDATA" || true

# Clean data directory for fresh replica
rm -rf "$PGDATA"/*

# Take base backup from primary
echo "Taking base backup from primary..."
pg_basebackup -h ${PRIMARY_HOST} -p ${PRIMARY_PORT} \
    -U ${REPLICATOR_USER} \
    -D "$PGDATA" \
    -Fp -Xs -P -v \
    -W

# Create standby.signal to indicate this is a replica
touch "$PGDATA/standby.signal"

# Configure primary connection for streaming replication
cat > "$PGDATA/postgresql.auto.conf" <<EOF
# Streaming replication configuration
primary_conninfo = 'host=${PRIMARY_HOST} port=${PRIMARY_PORT} user=${REPLICATOR_USER} password=${REPLICATOR_PASSWORD}'
hot_standby = on
EOF

# Start PostgreSQL
echo "Starting replica PostgreSQL..."
pg_ctl start -D "$PGDATA"

# Verify replication status
echo "Replica setup complete. Checking status..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_is_in_recovery();"
