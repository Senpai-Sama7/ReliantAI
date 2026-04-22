"""Apply forward-only SQLite migrations for the auth service."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from user_store import SQLiteUserStore


def default_db_path() -> Path:
    return Path(os.getenv("AUTH_DB_PATH", Path(__file__).with_name("auth.db")))


async def main() -> None:
    store = SQLiteUserStore(default_db_path())
    applied_now = await store.initialize()
    metadata = await store.ping()
    applied_versions = await store.list_applied_migrations()

    print(f"database={default_db_path()}")
    print(f"journal_mode={metadata['journal_mode']}")
    print(f"user_count={metadata['user_count']}")
    print(f"applied_now={','.join(applied_now) if applied_now else 'none'}")
    print(f"applied_versions={','.join(applied_versions) if applied_versions else 'none'}")


if __name__ == "__main__":
    asyncio.run(main())
