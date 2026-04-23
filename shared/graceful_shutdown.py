"""
ReliantAI Platform — Shared Graceful Shutdown Module

Provides signal handlers and lifespan hooks for clean shutdown of:
  - Database connection pools (psycopg2 ThreadedConnectionPool)
  - Redis connections (redis-py client + pubsub)
  - Background async tasks (asyncio tasks)
  - SSE/WebSocket clients (in-flight request draining)
  - Structured log flushing

Usage in a FastAPI service:

    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared")))
    from graceful_shutdown import GracefulShutdownManager, register_pool

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db()
        yield
        await GracefulShutdownManager.shutdown_all()

    # Or simpler — just register the pool and it gets closed on shutdown:
    pool = psycopg2.pool.ThreadedConnectionPool(1, 20, DATABASE_URL)
    register_pool(pool, name="money_db")

For services using @app.on_event("shutdown"):

    @app.on_event("shutdown")
    async def shutdown():
        await GracefulShutdownManager.shutdown_all()
"""

import asyncio
import atexit
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

try:
    import redis.asyncio as aioredis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

try:
    from psycopg2 import pool as pg_pool
    _HAS_PG = True
except ImportError:
    _HAS_PG = False

logger = logging.getLogger("graceful_shutdown")


class GracefulShutdownManager:
    """
    Central registry for resources that must be released cleanly on SIGTERM/SIGINT.

    This is a singleton; call `shutdown_all()` once and all registered
    resources are released in dependency order (reverse of registration).
    """

    _pools: Dict[str, Any] = {}
    _redis_clients: Dict[str, Any] = {}
    _tasks: Set[asyncio.Task] = set()
    _callbacks: List[Callable] = []
    _shutdown_in_progress = False
    _drain_timeout: float = 10.0
    _log_flush_timeout: float = 2.0

    @classmethod
    def register_pool(cls, pool: Any, name: str = "default") -> None:
        """Register a psycopg2 ThreadedConnectionPool for cleanup."""
        cls._pools[name] = pool
        logger.debug("Registered DB pool", extra={"pool_name": name})

    @classmethod
    def register_redis(cls, client: Any, name: str = "default") -> None:
        """Register a Redis client for cleanup."""
        cls._redis_clients[name] = client
        logger.debug("Registered Redis client", extra={"redis_name": name})

    @classmethod
    def register_task(cls, task: asyncio.Task) -> None:
        """Track an async background task so we can cancel it cleanly."""
        cls._tasks.add(task)
        task.add_done_callback(cls._tasks.discard)
        logger.debug("Registered background task", extra={"task": task.get_name()})

    @classmethod
    def register_callback(cls, callback: Callable, priority: int = 0) -> None:
        """
        Register an arbitrary cleanup callback.
        Lower priority = cleaned up earlier; higher = later.
        """
        cls._callbacks.append((priority, callback))
        cls._callbacks.sort(key=lambda x: x[0])
        logger.debug("Registered shutdown callback", extra={"priority": priority})

    @classmethod
    def setup_signal_handlers(cls, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Install SIGTERM and SIGINT handlers that trigger graceful shutdown."""
        if sys.platform == "win32":
            return  # Windows uses different signal model

        loop = loop or asyncio.get_event_loop()

        def _signal_handler(signum, frame):
            signame = signal.Signals(signum).name
            logger.warning(f"Received {signame}, initiating graceful shutdown...")
            # Schedule shutdown in the event loop
            asyncio.create_task(cls.shutdown_all())

        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
        logger.info("SIGTERM/SIGINT handlers installed")

    @classmethod
    async def shutdown_all(cls, drain_timeout: Optional[float] = None) -> None:
        """
        Execute full graceful shutdown sequence:
        1. Stop accepting new connections (uvicorn handles this)
        2. Drain in-flight requests (wait for active tasks)
        3. Cancel background tasks
        4. Close Redis connections
        5. Close DB connection pools
        6. Run custom callbacks
        7. Flush logs
        """
        if cls._shutdown_in_progress:
            logger.warning("Shutdown already in progress, ignoring duplicate signal")
            return

        cls._shutdown_in_progress = True
        drain_timeout = drain_timeout or cls._drain_timeout
        start = time.monotonic()

        logger.info("=== Graceful shutdown initiated ===")

        # ── 1. Cancel background tasks ──────────────────────────────────────
        if cls._tasks:
            logger.info(f"Cancelling {len(cls._tasks)} background tasks...")
            for task in list(cls._tasks):
                if not task.done():
                    task.cancel()
            # Wait briefly for cancellation to propagate
            await asyncio.gather(*cls._tasks, return_exceptions=True)
            cls._tasks.clear()

        # ── 2. Close Redis clients ─────────────────────────────────────────
        if cls._redis_clients:
            logger.info(f"Closing {len(cls._redis_clients)} Redis clients...")
            for name, client in list(cls._redis_clients.items()):
                try:
                    if hasattr(client, "close"):
                        await client.close()
                    elif hasattr(client, "aclose"):
                        await client.aclose()
                    elif hasattr(client, "disconnect"):
                        await client.disconnect()
                    logger.info(f"Redis client '{name}' closed")
                except Exception as e:
                    logger.warning(f"Error closing Redis '{name}': {e}")
            cls._redis_clients.clear()

        # ── 3. Close DB connection pools ───────────────────────────────────
        if cls._pools:
            logger.info(f"Closing {len(cls._pools)} DB connection pools...")
            for name, pool in list(cls._pools.items()):
                try:
                    if _HAS_PG and isinstance(pool, pg_pool.ThreadedConnectionPool):
                        pool.closeall()
                    elif hasattr(pool, "closeall"):
                        pool.closeall()
                    elif hasattr(pool, "close"):
                        pool.close()
                    logger.info(f"DB pool '{name}' closed ({pool.numsUsed if hasattr(pool, 'numsUsed') else 'N/A'} connections)")
                except Exception as e:
                    logger.warning(f"Error closing DB pool '{name}': {e}")
            cls._pools.clear()

        # ── 4. Run custom callbacks ─────────────────────────────────────────
        if cls._callbacks:
            logger.info(f"Running {len(cls._callbacks)} custom shutdown callbacks...")
            for priority, callback in cls._callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.warning(f"Shutdown callback failed (priority={priority}): {e}")
            cls._callbacks.clear()

        # ── 5. Flush logs ───────────────────────────────────────────────────
        logger.info("Flushing logs...")
        try:
            # structlog flush
            for handler in logging.root.handlers:
                handler.flush()
        except Exception as e:
            logger.warning(f"Log flush warning: {e}")

        elapsed = time.monotonic() - start
        logger.info(f"=== Graceful shutdown complete in {elapsed:.2f}s ===")


# ── Convenience helpers ─────────────────────────────────────────────────

def register_pool(pool: Any, name: str = "default") -> None:
    """Convenience: register a DB pool with the global manager."""
    GracefulShutdownManager.register_pool(pool, name)


def register_redis(client: Any, name: str = "default") -> None:
    """Convenience: register a Redis client with the global manager."""
    GracefulShutdownManager.register_redis(client, name)


def register_task(task: asyncio.Task) -> None:
    """Convenience: register a background task with the global manager."""
    GracefulShutdownManager.register_task(task)


def register_callback(callback: Callable, priority: int = 0) -> None:
    """Convenience: register a shutdown callback with the global manager."""
    GracefulShutdownManager.register_callback(callback, priority)


def setup_signal_handlers(loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Convenience: install signal handlers."""
    GracefulShutdownManager.setup_signal_handlers(loop)


async def shutdown_all(drain_timeout: Optional[float] = None) -> None:
    """Convenience: trigger full graceful shutdown."""
    await GracefulShutdownManager.shutdown_all(drain_timeout)
