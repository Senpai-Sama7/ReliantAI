"""Memory module for agent context persistence."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any


class AgentMemory:
    """SQLite-backed memory for agent context and learned patterns."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get(
            "AGENTS_MEMORY_DB", os.path.expanduser("~/.local/share/reliantai/agents/memory.db")
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(agent, key)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def remember(self, agent: str, key: str, value: Any) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO memories (agent, key, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(agent, key) DO UPDATE SET value=?, updated_at=?""",
                (agent, key, json.dumps(value), now, now, json.dumps(value), now),
            )
            conn.commit()

    def recall(self, agent: str, key: str) -> Any | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM memories WHERE agent=? AND key=?",
                (agent, key),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def recall_all(self, agent: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT key, value FROM memories WHERE agent=?", (agent,)
            ).fetchall()
        return {k: json.loads(v) for k, v in rows}

    def log_event(self, agent: str, event_type: str, data: Any) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO events (agent, event_type, data, created_at) VALUES (?, ?, ?, ?)",
                (agent, event_type, json.dumps(data), now),
            )
            conn.commit()

    def get_events(self, agent: str, event_type: str | None = None, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            if event_type:
                rows = conn.execute(
                    "SELECT event_type, data, created_at FROM events WHERE agent=? AND event_type=? ORDER BY created_at DESC LIMIT ?",
                    (agent, event_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT event_type, data, created_at FROM events WHERE agent=? ORDER BY created_at DESC LIMIT ?",
                    (agent, limit),
                ).fetchall()
        return [{"type": t, "data": json.loads(d), "at": a} for t, d, a in rows]
