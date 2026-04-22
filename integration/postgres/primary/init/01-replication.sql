-- PostgreSQL Primary - Replication Setup
-- Run on primary to configure replication user and slots

-- Create replication user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'replicator') THEN
        CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD '${REPLICATOR_PASSWORD}';
    END IF;
END
$$;

-- Grant replication permissions
ALTER USER replicator WITH REPLICATION;

-- Create replication slot for each replica
-- This prevents WAL files from being removed before replica consumes them
SELECT pg_create_physical_replication_slot('replica_1_slot', true);

-- Verify configuration
SELECT name, setting FROM pg_settings WHERE name IN (
    'wal_level',
    'hot_standby',
    'max_wal_senders',
    'max_replication_slots',
    'wal_keep_size'
);
