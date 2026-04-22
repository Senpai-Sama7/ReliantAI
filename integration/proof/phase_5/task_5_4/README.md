# Phase 5.4 Proof — End-to-End Integration Smoke Test

Artifacts captured in this directory:
- `auth_health.json`: live auth-service health response.
- `event_bus_health.json`: live event-bus health response.
- `bap_health.json`: live B-A-P health response from the token-protected instance.
- `money_health.json`: live Money health response.
- `username.txt`: generated smoke-test username.
- `register_response.json`: auth-service registration response.
- `token_response.json`: auth-service login response with bearer token.
- `smoke_dataset.csv`: dataset uploaded through B-A-P using the bearer token.
- `bap_upload_headers.txt`: B-A-P upload response headers showing emitted event-bus metadata.
- `bap_upload_response.json`: B-A-P upload response body.
- `document_event.json`: retrieved `document.processed` event for the uploaded dataset.
- `money_dispatch_response.json`: Money dispatch response using the same bearer token.
- `dispatch_event.json`: retrieved `dispatch.completed` event for the live Money dispatch.

Live stack:
- Redis: `127.0.0.1:56381`
- Postgres: `127.0.0.1:55433`
- Auth service: `http://127.0.0.1:18080`
- Event bus: `http://127.0.0.1:18082`
- B-A-P: `http://127.0.0.1:18003`
- Money: `http://127.0.0.1:18001`

Smoke-test results:
- Registered user `smoke_1772785326` in tenant `smoke-tenant`.
- Logged in through the auth service and received a bearer token with `expires_in=1800`.
- Uploaded `smoke_dataset.csv` to B-A-P with `Authorization: Bearer <token>`.
- B-A-P returned dataset `ds-b6f63f018c45` and event headers:
  - `x-eventbus-eventid: evt_1772785337.005954_1ee0feb8`
  - `x-eventbus-channel: events:document`
- Retrieving that event from the bus confirmed:
  - `event_type=document.processed`
  - `tenant_id=smoke-tenant`
  - payload `created_by=smoke_1772785326`
- Sent the same bearer token to Money `POST /dispatch`.
- Money returned dispatch `46415d38-4e5c-46b1-82a2-854ee94a3577` with:
  - `status=complete`
  - `result.event_bus_event_id=evt_1772785483.74151_55418028`
  - `result.event_bus_channel=events:dispatch`
- Retrieving that event from the bus confirmed:
  - `event_type=dispatch.completed`
  - `tenant_id=smoke-tenant`
  - payload `dispatch_id=46415d38-4e5c-46b1-82a2-854ee94a3577`
  - payload `status=complete`

Decision log:
- The smoke test uses one JWT minted by the auth service and reuses it across both B-A-P and Money, proving a shared auth boundary rather than a per-service secret.
- B-A-P remained pointed at the real event bus and real Postgres/Redis stack used in Task 5.3 so the smoke test exercised actual persistence and publication behavior.
- Money now accepts the shared bearer token in addition to its legacy API key so it can participate in platform-level service auth without breaking existing dashboard and API-key flows.

Failure documentation:
- The first live Money bearer-token request failed with a `sqlite3.OperationalError: disk I/O error`. Root cause: the dispatch state machine still defaulted to a hardcoded `dispatch.db` path while the rest of the service honored `DATABASE_PATH`, so live requests split persistence across two SQLite files. The fix was to make `state_machine.py` use `config.DATABASE_PATH` consistently.
