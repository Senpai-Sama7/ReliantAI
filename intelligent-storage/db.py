import logging
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg

from config import (
    DB_COMMAND_TIMEOUT_SEC,
    DB_DSN,
    DB_POOL_MAX,
    DB_POOL_MIN,
)

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Initialize per-connection codecs and settings."""
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool(
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    command_timeout: Optional[int] = None,
) -> asyncpg.Pool:
    """Initialize the asyncpg connection pool.

    Args:
        min_size: Minimum number of connections in the pool
        max_size: Maximum number of connections in the pool
        command_timeout: Timeout for SQL commands in seconds

    Returns:
        Initialized connection pool
    """
    global _pool

    if _pool is not None:
        logger.warning("Pool already initialized, returning existing pool")
        return _pool

    resolved_min = DB_POOL_MIN if min_size is None else min_size
    resolved_max = DB_POOL_MAX if max_size is None else max_size
    resolved_timeout = (
        DB_COMMAND_TIMEOUT_SEC if command_timeout is None else command_timeout
    )

    if resolved_min < 1:
        resolved_min = 1
    if resolved_max < resolved_min:
        resolved_max = resolved_min

    _pool = await asyncpg.create_pool(
        dsn=DB_DSN,
        min_size=resolved_min,
        max_size=resolved_max,
        command_timeout=resolved_timeout,
        init=_init_connection,
    )

    logger.info(
        f"✅ Asyncpg pool initialized (min={resolved_min}, max={resolved_max}, timeout={resolved_timeout}s)"
    )
    return _pool


async def close_pool() -> None:
    """Close the connection pool gracefully."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("✅ Asyncpg pool closed")


@asynccontextmanager
async def get_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """Async context manager for acquiring a database connection.

    Usage:
        async with get_conn() as conn:
            row = await conn.fetchrow("SELECT * FROM files WHERE id = $1", file_id)
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")

    async with _pool.acquire() as conn:
        yield conn


async def test_connection() -> bool:
    """Test database connectivity with a simple query.

    Returns:
        True if connection succeeds, False otherwise
    """
    try:
        async with get_conn() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM files")
            logger.info(
                f"✅ Database connection test passed: {result} files in database"
            )
            return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False


# Convenience function for FastAPI lifespan
def get_pool() -> Optional[asyncpg.Pool]:
    """Get the current connection pool (for FastAPI dependency injection)."""
    return _pool
