-- setup_db.sql
-- Run as postgres superuser to prepare the environment
-- Example: sudo -u postgres psql -p 5433 -f setup_db.sql

\set ON_ERROR_STOP on

SELECT 'Checking roles...' as info;
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'storage_admin') THEN
        CREATE ROLE storage_admin WITH LOGIN PASSWORD 'storage_local_2026';
        ALTER ROLE storage_admin WITH SUPERUSER;
        RAISE NOTICE 'Role "storage_admin" created.';
    ELSE
        ALTER ROLE storage_admin WITH PASSWORD 'storage_local_2026';
        ALTER ROLE storage_admin WITH SUPERUSER;
        RAISE NOTICE 'Role "storage_admin" updated.';
    END IF;
END
$$;

SELECT 'Checking database...' as info;
-- We can't use IF NOT EXISTS for CREATE DATABASE in a DO block easily 
-- because it cannot run inside a transaction block. 
-- So we use a separate check or just let it fail gracefully if we use -v ON_ERROR_STOP=off
-- But let's try a safer way from shell if possible, or just ignore error.

-- Create database
SELECT 'Attempting to create database intelligent_storage (ignoring if exists)...' as info;
-- This will be handled by the shell command or we can use this trick:
-- (But \c doesn't work in DO block)
\set ON_ERROR_STOP off
CREATE DATABASE intelligent_storage OWNER storage_admin;
\set ON_ERROR_STOP on

SELECT 'Configuring extensions in intelligent_storage...' as info;
\c intelligent_storage

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- Ensure public schema is owned by storage_admin or reachable
ALTER SCHEMA public OWNER TO storage_admin;

SELECT 'Database preparation complete.' as info;
