"""SQLite-backed user persistence for the auth service."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Any


MIGRATIONS_DIR = Path(__file__).with_name("migrations")


class UserStoreConflictError(Exception):
    """Raised when a user insert conflicts with an existing record."""


class SQLiteUserStore:
    """Persistent user store with forward-only SQL migrations."""

    def __init__(self, db_path: str | Path, migrations_dir: Path | None = None):
        self.db_path = Path(db_path)
        self.migrations_dir = migrations_dir or MIGRATIONS_DIR

    async def initialize(self) -> list[str]:
        return await asyncio.to_thread(self._initialize_sync)

    async def create_user(self, user_data: dict[str, Any]) -> None:
        await asyncio.to_thread(self._create_user_sync, user_data)

    async def get_user(self, username: str) -> dict[str, str] | None:
        return await asyncio.to_thread(self._get_user_sync, username)

    async def list_users(self) -> list[dict[str, str]]:
        return await asyncio.to_thread(self._list_users_sync)

    async def ping(self) -> dict[str, str]:
        return await asyncio.to_thread(self._ping_sync)

    async def list_applied_migrations(self) -> list[str]:
        return await asyncio.to_thread(self._list_applied_migrations_sync)

    def _initialize_sync(self) -> list[str]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )

        applied = set(self._list_applied_migrations_sync())
        pending = sorted(path for path in self.migrations_dir.glob("*.sql") if path.name not in applied)

        for migration_path in pending:
            sql = migration_path.read_text(encoding="utf-8")
            with self._connect() as connection:
                connection.executescript(sql)
                connection.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (migration_path.name, datetime.now(UTC).isoformat()),
                )
                connection.commit()

        return [path.name for path in pending]

    def _create_user_sync(self, user_data: dict[str, Any]) -> None:
        timestamp = datetime.now(UTC).isoformat()
        payload = {
            "username": user_data["username"],
            "email": user_data["email"],
            "tenant_id": user_data["tenant_id"],
            "role": user_data["role"],
            "hashed_password": user_data["hashed_password"],
            "created_at": user_data.get("created_at", timestamp),
            "updated_at": user_data.get("updated_at", timestamp),
        }

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO users (
                        username,
                        email,
                        tenant_id,
                        role,
                        hashed_password,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["username"],
                        payload["email"],
                        payload["tenant_id"],
                        payload["role"],
                        payload["hashed_password"],
                        payload["created_at"],
                        payload["updated_at"],
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise UserStoreConflictError(str(exc)) from exc

    def _get_user_sync(self, username: str) -> dict[str, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT username, email, tenant_id, role, hashed_password
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        return None if row is None else dict(row)

    def _list_users_sync(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT username, email, tenant_id, role, hashed_password
                FROM users
                ORDER BY username ASC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def _ping_sync(self) -> dict[str, str]:
        with self._connect() as connection:
            journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
            user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]

        return {"journal_mode": str(journal_mode), "user_count": str(user_count)}

    def _list_applied_migrations_sync(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version ASC"
            ).fetchall()

        return [str(row[0]) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection
