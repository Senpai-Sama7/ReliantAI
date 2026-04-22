# Phase 5.3 Proof — B-A-P to Event Bus Integration

Artifacts captured in this directory:
- `bap_event_tests.txt`: focused B-A-P test run for auth, API, and event-bus integration (`37 passed, 2 skipped`).
- `bap_ruff.txt`: Ruff output for the B-A-P event-bus wiring changes.
- `bap_mypy.txt`: mypy output for the changed B-A-P source files.
- `bap_health.json`: live `/health` response from B-A-P running against real Postgres and Redis.
- `event_bus_health.json`: live `/health` response from the Redis-backed event bus.
- `live_dataset.csv`: uploaded dataset used for the live proof.
- `upload_headers.txt`: upload response headers showing emitted event-bus metadata.
- `upload_response.json`: live upload response from B-A-P.
- `document_event.json`: retrieved `document.processed` event for the uploaded dataset.
- `pipeline_run_response.json`: live ETL run response.
- `pipeline_status.json`: persisted pipeline job status including event-bus metadata.
- `analytics_event.json`: retrieved `analytics.recorded` event for the completed ETL job.
- `live_event_bus_test.txt`: env-gated live pytest for the B-A-P event-bus flow (`1 passed`).

Verification summary:
- Focused B-A-P verification passed:
  - `poetry run pytest tests/test_auth_integration.py tests/test_event_bus_integration.py tests/test_api.py -q`
  - `poetry run ruff check src/api/auth_integration.py src/api/routes/data.py src/etl/pipeline.py src/core/event_bus.py tests/conftest.py tests/test_auth_integration.py tests/test_event_bus_integration.py`
  - `poetry run mypy src/api/auth_integration.py src/api/routes/data.py src/etl/pipeline.py src/core/event_bus.py`
- Live B-A-P ran on `127.0.0.1:18000` with:
  - Postgres `127.0.0.1:55433`
  - Redis `127.0.0.1:56381`
  - Event bus `http://127.0.0.1:18082`
  - `CELERY_TASK_ALWAYS_EAGER=true`
- Uploading `live_dataset.csv` returned dataset `ds-524a5c9ac1c0` and response headers:
  - `X-EventBus-EventId: evt_1772784829.866293_dd9a2ed3`
  - `X-EventBus-Channel: events:document`
- Retrieving that event from `/event/{id}` confirmed:
  - `event_type=document.processed`
  - `tenant_id=bap-live`
  - payload `dataset_id=ds-524a5c9ac1c0`
- Running the ETL pipeline created job `job-62cddfd23cc0` and persisted:
  - `event_bus_event_id=evt_1772784846.183231_1980db54`
  - `event_bus_channel=events:analytics`
- Retrieving that event from `/event/{id}` confirmed:
  - `event_type=analytics.recorded`
  - payload `dataset_id=ds-524a5c9ac1c0`
  - payload `job_id=job-62cddfd23cc0`

Decision log:
- B-A-P now uses a shared async publisher in `src/core/event_bus.py` so upload and ETL code paths publish through one contract instead of embedding per-route HTTP calls.
- Upload responses expose event metadata via headers for traceability without changing the response schema.
- ETL job results persist the emitted analytics event metadata so downstream status queries can prove publication after the job completes.

Failure documentation:
- The first route-level pipeline test failed because the global ETL pipeline was still bound to the application session factory instead of the pytest database. The test harness was corrected to use `StaticPool` for the in-memory SQLite engine and to override the global ETL pipeline session factory during route tests.
- Initial `mypy` failures came from `auth_integration.py` annotations and `upload_data()` reusing the `response` variable name for the serialized dataset response. Those were corrected before the live proof.
