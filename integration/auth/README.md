# Authentication Service

OAuth2/JWT authentication service for ReliantAI platform.

## Features

- OAuth2 authorization code and client credentials flows
- JWT access and refresh tokens
- Role-Based Access Control (RBAC)
- User and service account management
- SQLite-backed persistent user storage with WAL mode
- Redis-backed token revocation, login lockout tracking, and warm user cache

## Setup

```bash
pip install -r requirements.txt
export AUTH_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python migrate.py
python auth_server.py
```

## Testing

```bash
pytest test_auth_properties.py test_rbac_properties.py test_persistence.py test_rate_limit.py test_lifespan.py test_verify_endpoint.py -v
```

## Configuration

- `AUTH_SECRET_KEY`: required, minimum 32 characters
- `AUTH_DB_PATH`: optional SQLite path, defaults to `integration/auth/auth.db`
- `REDIS_HOST`: optional Redis host, defaults to `localhost`
- `REDIS_PORT`: optional Redis port, defaults to `6379`
- `AUTH_RATE_LIMIT_WINDOW_SECONDS`: optional sliding window length, defaults to `60`
- `AUTH_REGISTER_RATE_LIMIT`: optional `/register` requests per window, defaults to `5`
- `AUTH_TOKEN_RATE_LIMIT`: optional `/token` requests per window, defaults to `10`

## Persistence Model

- SQLite is the source of truth for registered users.
- Redis remains the fast path for user lookups plus the storage layer for revocation and lockout counters.
- Redis also stores the sliding-window rate limit state for `/register` and `/token`.
- On startup, the service runs forward-only migrations and hydrates Redis user hashes from SQLite.
- On cache miss, user lookups fall back to SQLite and repopulate Redis automatically.

## Rate Limits

- `POST /register`: 5 requests per 60 seconds per client IP
- `POST /token`: 10 requests per 60 seconds per client IP
- Rejected requests return `429 Too Many Requests` with a `Retry-After` header

## Migrations

```bash
python migrate.py
```

This applies all SQL files in `integration/auth/migrations/` and records them in `schema_migrations`.

## API Endpoints

- `POST /register` - Register new user
- `POST /token` - Login and get tokens
- `POST /refresh` - Refresh access token
- `GET /verify` - Verify token validity
- `POST /verify` - Verify token validity (service-to-service)

`/verify` returns the identity envelope used by shared validators:

```json
{
  "valid": true,
  "user_id": "alice",
  "username": "alice",
  "tenant_id": "tenant-123",
  "role": "admin",
  "roles": ["admin"]
}
```

See PROGRESS_TRACKER.md Task 0.2.1 for complete implementation.
