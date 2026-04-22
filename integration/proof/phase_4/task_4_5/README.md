# Task 4.5 Proof Artifacts

- `test_run.txt`: exact tracker command output for `./.venv/bin/python -m pytest auth/ event-bus/ tests/ -v`.

## Notes

- Historical note: this proof snapshot predated the later `/register` RBAC hardening.
- On 2026-03-10, the `/verify` regression failed again because `integration/auth/test_verify_endpoint.py` still tried to self-register `role=admin`, which the auth service now correctly rejects with `403`.
- The current verified state is restored by registering an allowed role (`operator`) in the test fixture; targeted rerun: `./.venv/bin/pytest auth/test_verify_endpoint.py tests/test_rate_limiter_edges.py tests/test_jwt_validator_edges.py tests/test_event_bus_dlq.py -q` → `8 passed, 2 warnings`.
- Treat this directory as historical proof plus correction context, not as the sole source of truth for the current suite status.
