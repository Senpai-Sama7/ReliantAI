# Authentication Service

OAuth2/JWT authentication service for ReliantAI platform.

## Features

- OAuth2 authorization code and client credentials flows
- JWT access and refresh tokens
- Role-Based Access Control (RBAC)
- User and service account management

## Setup

```bash
pip install -r requirements.txt
python auth_server.py
```

## Testing

```bash
pytest test_auth.py -v
```

## API Endpoints

- `POST /register` - Register new user
- `POST /token` - Login and get tokens
- `POST /refresh` - Refresh access token
- `GET /verify` - Verify token validity

See PROGRESS_TRACKER.md Task 0.2.1 for complete implementation.
