# Task 5.2 Proof Artifacts

- `event_bus_health.json`: live event-bus health response with Redis connected.
- `money_health.json`: live Money service health response during the integration proof.
- `dispatch_response.txt`: live Money `POST /dispatch` response showing `status: complete` plus `event_bus_event_id` and `event_bus_channel`.
- `event_response.txt`: live event-bus retrieval of the published `dispatch.completed` event by ID.
- `live_event_bus_test.txt`: env-gated live Money event-bus integration test output (`1 passed`).
- `money_event_tests.txt`: focused Money API and event-bus test run showing the dispatch path passes with the new integration.
- `money_ruff.txt`: Ruff output for the Money event-bus changes.
- `runtime/event_bus.log`: event-bus log from the live verification run.
- `runtime/money.log`: Money service log from the live verification run, including the repaired state progression and event publication.
- `runtime/event_id.txt`: event ID extracted from the live Money dispatch response.

## Notes

- The dispatch path could not emit a completion event reliably until the Money state machine stopped attempting the invalid `triaged -> completed` jump. Task 5.2 fixes that by advancing the synchronous dispatch workflow through valid states up to `dispatched` before marking the job complete.
- Event publication is opt-in via `EVENT_BUS_URL`. When configured, successful dispatches now publish `dispatch.completed` with `dispatch_id`, `status`, and the dispatch result metadata, and Money includes the resulting event ID in the dispatch response for traceability.
- Live verification used a real Redis-backed event bus on `127.0.0.1:18081` and a live Money service on `127.0.0.1:18001`.
