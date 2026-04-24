"""
Test harness for the Money service.

Runs *before* any ``main``/``config``/``database`` import so that:
  * all required secrets are present in ``os.environ``
  * the log file handler cannot touch ``/data``
  * heavy third-party modules (CrewAI, LangSmith) are neutralised
  * the Money package directory and the workspace ``shared/`` directory
    are on ``sys.path`` exactly as in production.
"""

from __future__ import annotations

import logging
import os
import sys
import types
from pathlib import Path

# ── Path setup (mirror production imports) ─────────────────────
_MONEY_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _MONEY_DIR.parent
_SHARED_DIR = _REPO_ROOT / "shared"

for p in (str(_MONEY_DIR), str(_SHARED_DIR), str(_REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Required env vars for ``config.py`` ────────────────────────
os.environ.setdefault("ENV", "test")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("LANGSMITH_API_KEY", "test-langsmith-key")
os.environ.setdefault("TWILIO_SID", "ACtest0000000000000000000000000000")
os.environ.setdefault("TWILIO_TOKEN", "test-twilio-token-32chars-1234567890")
os.environ.setdefault("TWILIO_FROM_PHONE", "+15005550006")
os.environ.setdefault("COMPOSIO_API_KEY", "test-composio-key")
os.environ.setdefault("OWNER_PHONE", "+15005550001")
os.environ.setdefault("TECH_PHONE_NUMBER", "+15005550002")
os.environ.setdefault("DISPATCH_API_KEY", "test-dispatch-key-0123456789abcdef")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-32-chars-ok-go")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASS", "admin-pass-test-0000000000000000")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("MAKE_WEBHOOK_SECRET", "test-make-webhook-secret-32chars!")
os.environ.setdefault("HUBSPOT_WEBHOOK_SECRET", "test-hubspot-webhook-secret-32cx!")
# Skip Twilio signature validation for most webhook tests;
# individual signature tests flip this off explicitly.
os.environ.setdefault("SKIP_TWILIO_VALIDATION", "true")

# ── Redirect ``FileHandler`` away from ``/data`` ──────────────
# ``config.setup_logging`` opens ``/data/hvac_dispatch.log`` which does not exist
# on typical developer machines.  Alias FileHandler to NullHandler so tests work
# without root-level filesystem access.
_original_file_handler = logging.FileHandler


class _NullFileHandler(logging.NullHandler):  # type: ignore[misc]
    def __init__(self, *args, **kwargs) -> None:  # noqa: D401
        super().__init__()


logging.FileHandler = _NullFileHandler  # type: ignore[assignment]


# ── Stub heavy third-party modules (CrewAI / LangSmith) ────────
def _install_crewai_stubs() -> None:
    if "crewai" in sys.modules:
        return

    crewai = types.ModuleType("crewai")

    class _Stub:  # noqa: D401 — minimal placeholder
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        def kickoff(self, *args, **kwargs):
            return {"status": "stubbed"}

    crewai.Agent = _Stub
    crewai.Task = _Stub
    crewai.Crew = _Stub

    class _Process:
        sequential = "sequential"
        hierarchical = "hierarchical"

    crewai.Process = _Process

    tools_mod = types.ModuleType("crewai.tools")

    def _tool_decorator(*args, **kwargs):
        if args and callable(args[0]) and not kwargs:
            return args[0]

        def wrap(func):
            return func

        return wrap

    tools_mod.tool = _tool_decorator

    sys.modules["crewai"] = crewai
    sys.modules["crewai.tools"] = tools_mod


def _install_langsmith_stub() -> None:
    if "langsmith" in sys.modules:
        return
    mod = types.ModuleType("langsmith")

    def traceable(*args, **kwargs):
        if args and callable(args[0]) and not kwargs:
            return args[0]

        def wrap(func):
            return func

        return wrap

    mod.traceable = traceable
    sys.modules["langsmith"] = mod


_install_crewai_stubs()
_install_langsmith_stub()


# ── Pytest fixtures ────────────────────────────────────────────
import pytest  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402


class _FakeCursor:
    """Mimic ``psycopg2`` cursor behaviour well enough for Money's queries."""

    def __init__(self, store: dict) -> None:
        self._store = store
        self._last_result: list[dict] = []
        self.rowcount = 0
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql: str, params=None) -> None:
        # Collapse whitespace so multi-line SQL literals are easy to pattern-match.
        normalized = " ".join(sql.lower().split())
        if normalized.startswith("select 1"):
            self._last_result = [{"?column?": 1}]
            self.rowcount = 1
            return
        if "count(*)" in normalized and "customer_events" in normalized:
            self._last_result = [(self._store.get("dispatch_count", 0),)]
            self.rowcount = 1
            return
        if "from customers where api_key" in normalized:
            key = params[0] if params else None
            row = self._store.get("customers_by_key", {}).get(key)
            self._last_result = [row] if row else []
            self.rowcount = len(self._last_result)
            return
        if "from dispatches where dispatch_id" in normalized:
            dispatch_id = params[0] if params else None
            row = self._store.get("dispatches", {}).get(dispatch_id)
            self._last_result = [row] if row else []
            return
        if normalized.startswith("insert into dispatches"):
            dispatch_id = params[0] if params else None
            self._store.setdefault("dispatches", {})[dispatch_id] = {
                "dispatch_id": dispatch_id,
                "status": params[8] if params and len(params) > 8 else "queued",
            }
            self.rowcount = 1
            return
        if normalized.startswith("insert into messages"):
            self.rowcount = 1
            return
        if normalized.startswith("insert into customer_events"):
            self._last_result = [{"id": 1, "customer_id": params[0] if params else 0}]
            self.rowcount = 1
            return
        if normalized.startswith("update dispatches"):
            self.rowcount = 1
            return
        if "from dispatches" in normalized:
            self._last_result = list(self._store.get("dispatches", {}).values())
            self.rowcount = len(self._last_result)
            return
        # Default: empty result
        self._last_result = []
        self.rowcount = 0

    def fetchone(self):
        return self._last_result[0] if self._last_result else None

    def fetchall(self):
        return list(self._last_result)


class _FakeConn:
    def __init__(self, store: dict) -> None:
        self._store = store
        self.committed = False
        self.rolled_back = False

    def cursor(self, cursor_factory=None):  # noqa: ARG002 — accepted for RealDictCursor
        return _FakeCursor(self._store)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        pass


class _FakePool:
    """Stand-in for ``psycopg2.pool.ThreadedConnectionPool``."""

    def __init__(self) -> None:
        self.store: dict = {"dispatches": {}, "customers_by_key": {}, "dispatch_count": 0}
        self._conn = _FakeConn(self.store)

    def getconn(self):
        return self._conn

    def putconn(self, conn) -> None:
        return None

    def closeall(self) -> None:
        return None


@pytest.fixture
def fake_pool():
    return _FakePool()


@pytest.fixture(autouse=True)
def _patch_database_pool(monkeypatch, fake_pool):
    """
    Every test gets a fresh fake PostgreSQL pool.
    Patched at the ``database`` module level so both the
    ``database.get_pool`` callers *and* ``billing.get_pool`` (which imports
    lazily inside ``check_dispatch_quota``) see the fake.
    """
    import database

    monkeypatch.setattr(database, "_pool", fake_pool, raising=False)
    monkeypatch.setattr(database, "get_pool", lambda: fake_pool)
    yield fake_pool


@pytest.fixture(autouse=True)
def _reset_rate_limit_and_circuit(monkeypatch):
    """Clear sliding-window rate counters and the auth circuit breaker between tests."""
    import main

    main._rate_counters.clear()
    main.job_store.clear()
    main.rate_limit_store.clear()
    main.auth_circuit_breaker.state = "CLOSED"
    main.auth_circuit_breaker.failures = 0
    main.auth_circuit_breaker.last_failure_time = 0.0
    yield
    main._rate_counters.clear()
    main.job_store.clear()
    main.rate_limit_store.clear()


@pytest.fixture
def app():
    """Return the FastAPI application — import lazily so env setup above runs first."""
    import main
    return main.app


@pytest.fixture
def client(app):
    """
    Plain TestClient (no lifespan).  Lifespan runs only when the client is used
    as a context manager — we skip it to avoid warm-up / ``init_db`` side effects.
    """
    from fastapi.testclient import TestClient
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def async_client(app):
    """httpx.AsyncClient wired to the app via ASGI transport."""
    import httpx
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture
def mock_crew(monkeypatch):
    """Replace ``run_hvac_crew`` with a deterministic fake."""
    import hvac_dispatch_crew

    fake = MagicMock(
        return_value={
            "status": "complete",
            "raw": "Dispatched Tech_Alex to 123 Main St",
            "timestamp": "2026-04-24T12:00:00+00:00",
        }
    )
    monkeypatch.setattr(hvac_dispatch_crew, "run_hvac_crew", fake)
    return fake


@pytest.fixture
def mock_state_machine(monkeypatch):
    """Fake state machine so transitions don't touch PostgreSQL."""
    import state_machine

    sm = MagicMock()
    sm.get_current_state.return_value = None
    sm.get_time_in_state.return_value = 0.0
    sm.get_timeline.return_value = []
    sm.funnel_counts.return_value = {"received": 1, "completed": 1}
    sm.transition.return_value = MagicMock()
    sm.record_event.return_value = MagicMock()

    monkeypatch.setattr(state_machine, "get_state_machine", lambda: sm)
    return sm


@pytest.fixture
def disable_event_bus(monkeypatch):
    """Clear EVENT_BUS_URL so ``_publish_dispatch_completed_event`` becomes a no-op."""
    monkeypatch.delenv("EVENT_BUS_URL", raising=False)
