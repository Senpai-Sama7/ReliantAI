"""
Database tests — CRUD operations and concurrency.
Each test gets a fresh isolated database via unique temp paths.
"""

import os
import sqlite3
import threading
import importlib
import uuid
import tempfile
import pytest


@pytest.fixture(autouse=True)
def isolated_db():
    """Give each test a completely fresh database."""
    db_path = os.path.join(tempfile.mkdtemp(), f"test_{uuid.uuid4().hex[:8]}.db")
    os.environ["DATABASE_PATH"] = db_path

    # Force config to re-read DATABASE_PATH
    import config
    importlib.reload(config)

    import database
    database.close_all_connections()
    # Close any existing thread-local connection
    if hasattr(database._local, "conn") and database._local.conn:
        try:
            database._local.conn.close()
        except Exception:
            pass
        database._local.conn = None
    # Reload database module to pick up new DATABASE_PATH from config
    importlib.reload(database)
    database.init_db()
    yield db_path
    # Cleanup
    database.close_all_connections()
    if hasattr(database._local, "conn") and database._local.conn:
        try:
            database._local.conn.close()
        except Exception:
            pass
        database._local.conn = None


class TestInitDb:
    def test_creates_tables(self, isolated_db):
        conn = sqlite3.connect(isolated_db)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "dispatches" in tables
        assert "messages" in tables
        conn.close()


class TestSaveAndGetDispatch:
    def test_save_and_retrieve(self):
        from database import save_dispatch, get_dispatch
        save_dispatch(dispatch_id="test-1", issue_summary="AC broken", status="queued")
        row = get_dispatch("test-1")
        assert row is not None
        assert row["dispatch_id"] == "test-1"
        assert row["issue_summary"] == "AC broken"

    def test_get_nonexistent_returns_none(self):
        from database import get_dispatch
        assert get_dispatch("nonexistent") is None

    def test_save_with_all_fields(self):
        from database import save_dispatch, get_dispatch
        save_dispatch(
            dispatch_id="test-full", customer_name="John",
            customer_phone="+15551234567", address="123 Main St",
            issue_summary="Gas leak", urgency="LIFE_SAFETY",
            tech_name="Tech_Alex", eta="30 min", status="dispatched",
            crew_result={"urgency_level": "LIFE_SAFETY"},
        )
        row = get_dispatch("test-full")
        assert row["customer_name"] == "John"
        assert row["urgency"] == "LIFE_SAFETY"


class TestUpdateDispatchStatus:
    def test_update_status(self):
        from database import save_dispatch, update_dispatch_status, get_dispatch
        save_dispatch(dispatch_id="test-upd", issue_summary="test", status="queued")
        update_dispatch_status("test-upd", "complete", {"result": "ok"})
        row = get_dispatch("test-upd")
        assert row["status"] == "complete"


class TestGetRecentDispatches:
    def test_returns_correct_count(self):
        from database import save_dispatch, get_recent_dispatches
        for i in range(5):
            save_dispatch(dispatch_id=f"recent-{i}", issue_summary=f"Issue {i}")
        results = get_recent_dispatches(10)
        assert len(results) == 5

    def test_respects_limit(self):
        from database import save_dispatch, get_recent_dispatches
        for i in range(10):
            save_dispatch(dispatch_id=f"lim-{i}", issue_summary=f"Issue {i}")
        results = get_recent_dispatches(3)
        assert len(results) == 3


class TestLogMessage:
    def test_log_and_query(self, isolated_db):
        from database import log_message
        log_message(direction="inbound", phone="+15551234567", body="AC broken", sms_sid="SM1")
        conn = sqlite3.connect(isolated_db)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM messages").fetchall()
        assert len(rows) == 1
        assert rows[0]["phone"] == "+15551234567"
        conn.close()


class TestConcurrency:
    def test_concurrent_writes(self):
        """Multiple threads writing dispatches simultaneously."""
        from database import save_dispatch, get_recent_dispatches
        errors = []

        def writer(thread_id):
            try:
                for i in range(10):
                    save_dispatch(dispatch_id=f"t{thread_id}-{i}", issue_summary=f"Thread {thread_id} item {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent write errors: {errors}"
        results = get_recent_dispatches(100)
        assert len(results) == 40
