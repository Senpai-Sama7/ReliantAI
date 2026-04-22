# Task 5.1 Proof Artifacts

- `auth_health.json`: live auth-service health response with Redis and SQLite connected.
- `bap_health.json`: live B-A-P health response from the running FastAPI service.
- `register_response.txt`: live auth-service registration request for the phase 5 test user.
- `token_response.txt`: live auth-service login response containing the issued access and refresh tokens.
- `bap_datasets_authorized.txt`: live `GET /api/data/datasets` response from B-A-P with a valid bearer token, returning `200 OK`.
- `bap_datasets_missing_token.txt`: live unauthenticated `GET /api/data/datasets` response, returning `401 Unauthorized`.
- `bap_datasets_expired_token.txt`: live `GET /api/data/datasets` response with an expired token, returning `401 Unauthorized`.
- `live_auth_flow_test.txt`: automated cross-service test run for `test_live_shared_auth_flow`, executed against the live auth service.
- `bap_auth_tests.txt`: focused B-A-P auth integration test run, including missing-token and expired-token coverage.
- `bap_ruff.txt`: Ruff output for the B-A-P auth middleware and auth integration tests.
- `auth_verify_tests.txt`: auth-service verify-endpoint tests confirming both `GET /verify` and `POST /verify`.
- `runtime/auth_service.log`: auth-service log from the live cross-service proof run.
- `runtime/bap_service.log`: B-A-P service log from the live cross-service proof run.
- `runtime/username.txt`: generated username used for the phase 5 auth flow.
- `runtime/access_token.txt`: issued live access token used for the authorized B-A-P request.
- `runtime/expired_token.txt`: locally generated expired access token used to verify rejection behavior.

## Notes

- The real integration bug was a contract mismatch: the shared validator used `GET /verify`, while the auth service only exposed `POST /verify`. Task 5.1 resolves that by supporting both methods and returning the shared identity envelope expected by downstream services.
- B-A-P middleware now converts validator-raised `HTTPException` values into deterministic JSON `401/503` responses instead of relying on generic middleware exception handling.
- The live proof used real Postgres and Redis containers, a live auth service on `127.0.0.1:18080`, and a live B-A-P service on `127.0.0.1:18000`.
