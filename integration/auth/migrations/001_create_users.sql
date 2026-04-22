CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    tenant_id TEXT NOT NULL,
    role TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users (tenant_id);
