"""Shared test fixtures for HVAC AI Dispatch test suite."""

import os, sys
import tempfile
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment BEFORE any project imports
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DISPATCH_API_KEY", "test-key-123")
os.environ.setdefault("GEMINI_API_KEY", "dummy")
os.environ.setdefault("LANGSMITH_API_KEY", "dummy")
os.environ.setdefault("TWILIO_SID", "dummy")
os.environ.setdefault("TWILIO_TOKEN", "dummy")
os.environ.setdefault("TWILIO_FROM_PHONE", "+10000000000")
os.environ.setdefault("COMPOSIO_API_KEY", "dummy")
os.environ.setdefault("OWNER_PHONE", "+10000000001")
os.environ.setdefault("TECH_PHONE_NUMBER", "+10000000002")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def isolated_runtime(monkeypatch: pytest.MonkeyPatch):
    """Give each test an isolated SQLite database and clean in-memory stores."""
    db_dir = Path(tempfile.mkdtemp(prefix="money-tests-"))
    db_path = db_dir / "dispatch.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    from database import close_all_connections, close_thread_local_connection, init_db

    close_all_connections()
    close_thread_local_connection()
    init_db()

    if "main" in sys.modules:
        import main

        main.job_store.clear()
        main.rate_limit_store.clear()
        main._rate_counters.clear()

    yield str(db_path)

    close_all_connections()
    close_thread_local_connection()

    if "main" in sys.modules:
        import main

        main.job_store.clear()
        main.rate_limit_store.clear()
        main._rate_counters.clear()


@pytest.fixture
def client(isolated_runtime: str):
    """FastAPI TestClient with isolated database state."""
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_headers():
    """Headers with valid API key."""
    return {"x-api-key": "test-key-123"}


@pytest.fixture
def session_cookies():
    """Session cookie for authenticated admin access."""
    from main import _create_session_cookie, _SESSION_COOKIE
    return {_SESSION_COOKIE: _create_session_cookie("admin")}


@pytest.fixture
def tmp_db(tmp_path):
    """Temporary SQLite database for isolated tests."""
    db_path = str(tmp_path / "test_dispatch.db")
    os.environ["DATABASE_PATH"] = db_path
    from database import close_all_connections, close_thread_local_connection, init_db
    close_all_connections()
    close_thread_local_connection()
    init_db()
    yield db_path
    close_all_connections()
    close_thread_local_connection()
    os.environ.pop("DATABASE_PATH", None)
