"""
HVAC AI Dispatch — SQLite Persistence Layer
Lightweight dispatch history + message log.  Zero external dependencies.
"""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import DATABASE_PATH, setup_logging

logger = setup_logging("hvac_db")

_local = threading.local()
_connection_lock = threading.Lock()
_open_connections: set[sqlite3.Connection] = set()


def get_database_path() -> str:
    """Resolve the active database path, honoring runtime/test overrides."""
    return os.environ.get("DATABASE_PATH", DATABASE_PATH)


def _cleanup_wal_sidecars(db_path: str) -> None:
    """Remove stale WAL/SHM files so SQLite can recreate them cleanly."""
    db_file = Path(db_path)
    if db_file == Path(":memory:"):
        return

    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        try:
            sidecar.unlink()
        except FileNotFoundError:
            continue


def open_sqlite_connection(db_path: str, *, check_same_thread: bool) -> sqlite3.Connection:
    """Open a SQLite connection with the project's required pragmas."""
    db_file = Path(db_path)
    if db_file != Path(":memory:"):
        db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        conn.close()
        _cleanup_wal_sidecars(db_path)
        conn = sqlite3.connect(db_path, check_same_thread=check_same_thread)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")

    with _connection_lock:
        _open_connections.add(conn)

    return conn


def close_thread_local_connection() -> None:
    """Close and reset the current thread-local connection if one exists."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        finally:
            with _connection_lock:
                _open_connections.discard(conn)
            _local.conn = None
            _local.conn_path = None


def close_all_connections() -> None:
    """Close every tracked SQLite connection across worker threads."""
    with _connection_lock:
        connections = list(_open_connections)
        _open_connections.clear()

    for conn in connections:
        try:
            conn.close()
        except sqlite3.Error:
            continue

    _local.conn = None
    _local.conn_path = None


def _conn() -> sqlite3.Connection:
    """Thread-local SQLite connection (safe for FastAPI threadpool)."""
    db_path = get_database_path()
    current_path = getattr(_local, "conn_path", None)
    if current_path != db_path:
        close_thread_local_connection()

    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = open_sqlite_connection(db_path, check_same_thread=False)
        _local.conn_path = db_path
    return _local.conn


def init_db() -> None:
    """Create tables if they don't exist.  Call once at startup."""
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dispatches (
            dispatch_id   TEXT PRIMARY KEY,
            customer_name TEXT,
            customer_phone TEXT,
            address       TEXT,
            issue_summary TEXT,
            urgency       TEXT,
            tech_name     TEXT,
            eta           TEXT,
            status        TEXT DEFAULT 'pending',
            crew_result   TEXT,
            created_at    TEXT,
            updated_at    TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            direction     TEXT,          -- 'inbound' | 'outbound'
            phone         TEXT,
            body          TEXT,
            sms_sid       TEXT,
            channel       TEXT DEFAULT 'sms',   -- 'sms' | 'whatsapp'
            created_at    TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_dispatches_status ON dispatches(status);
        CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone);
    """)
    conn.commit()
    logger.info("Database initialized at %s", get_database_path())


# ── Dispatch CRUD ──────────────────────────────────────────────

def save_dispatch(
    dispatch_id: str,
    customer_name: str = "",
    customer_phone: str = "",
    address: str = "",
    issue_summary: str = "",
    urgency: str = "",
    tech_name: str = "",
    eta: str = "",
    status: str = "pending",
    crew_result: Optional[dict] = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()
    conn.execute(
        """INSERT OR REPLACE INTO dispatches
           (dispatch_id, customer_name, customer_phone, address,
            issue_summary, urgency, tech_name, eta, status,
            crew_result, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (dispatch_id, customer_name, customer_phone, address,
         issue_summary, urgency, tech_name, eta, status,
         json.dumps(crew_result) if crew_result else None,
         now, now),
    )
    conn.commit()


def update_dispatch_status(dispatch_id: str, status: str, result: Optional[dict] = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()
    conn.execute(
        """UPDATE dispatches SET status = ?, crew_result = ?, updated_at = ?
           WHERE dispatch_id = ?""",
        (status, json.dumps(result) if result else None, now, dispatch_id),
    )
    conn.commit()


def get_dispatch(dispatch_id: str) -> Optional[dict]:
    row = _conn().execute(
        "SELECT * FROM dispatches WHERE dispatch_id = ?", (dispatch_id,)
    ).fetchone()
    return dict(row) if row else None


def get_recent_dispatches(limit: int = 50) -> list[dict]:
    rows = _conn().execute(
        "SELECT * FROM dispatches ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# ── Message log ────────────────────────────────────────────────

def log_message(
    direction: str,
    phone: str,
    body: str,
    sms_sid: str = "",
    channel: str = "sms",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()
    conn.execute(
        """INSERT INTO messages (direction, phone, body, sms_sid, channel, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (direction, phone, body, sms_sid, channel, now),
    )
    conn.commit()
