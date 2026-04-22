# Task 4.4 Proof Artifacts

- `security_tests.txt`: targeted security test run showing `14 passed`, including CSRF issuance, rejection, and success cases for `/login`.
- `coverage.txt`: full Money test suite with coverage enabled. Result: `91 passed, 23 warnings` and `TOTAL 42%` coverage across the service.
- `compileall.txt`: `python -m compileall main.py tests` output confirming the modified login path compiles cleanly.
- `health.txt`: live `GET /health` response from the Money service during CSRF verification.
- `login_get.txt`: live `GET /login` response showing the signed `dispatch_login_csrf` cookie and matching hidden `csrf_token` field.
- `login_missing_csrf.txt`: live `POST /login` without the CSRF field, returning `403 Forbidden` and a fresh login form.
- `login_valid_csrf.txt`: live `POST /login` with a valid CSRF token, returning `302 Found`, setting `dispatch_session`, and clearing the login CSRF cookie.
- `csrf_token.txt`: extracted token used for the successful live login submission.
- `runtime/cookies.txt`: cookie jar from the live `GET /login` request.
- `runtime/cookies_after_login.txt`: cookie jar after successful login, proving the session cookie was issued.
- `runtime/server.log`: tail of the application log from the live verification run.
- `runtime/live_dispatch.db`: SQLite file created during live verification.

## Notes

- The CSRF protection is a signed double-submit pattern using the existing `itsdangerous` serializer: the token is rendered into the form and mirrored in an `HttpOnly` cookie, and both are required on `POST /login`.
- Coverage is measured, not optimized yet. The service is still at `42%` total coverage because several integration-heavy modules remain untested; that is tracked work for later hardening phases.
- The warnings in `coverage.txt` predate the CSRF change and are still real:
  - FastAPI `@app.on_event("startup")` deprecation in `main.py`
  - SQLite `ResourceWarning` instances during the existing test suite
