"""
ReliantAI Platform - Graceful Shutdown Handler
Handles graceful shutdown of FastAPI applications
"""

import asyncio
import signal
import sys
from typing import Callable, List
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class GracefulShutdownManager:
    """Manages graceful shutdown of services"""
    
    def __init__(self):
        self.shutdown_hooks: List[Callable] = []
        self.is_shutting_down = False
    
    def add_shutdown_hook(self, hook: Callable):
        """Add a function to be called during shutdown"""
        self.shutdown_hooks.append(hook)
    
    async def shutdown(self):
        """Execute all shutdown hooks"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logger.info("Starting graceful shutdown...")
        
        # Execute all shutdown hooks
        for hook in self.shutdown_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                logger.error(f"Error during shutdown hook: {e}")
        
        logger.info("Graceful shutdown complete")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            try:
                # Try to get running loop first (Python 3.7+)
                asyncio.get_running_loop()
                # Schedule shutdown in the running loop
                asyncio.create_task(self.shutdown())
            except RuntimeError:
                # No loop running, create new one for sync context
                asyncio.run(self.shutdown())
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Windows doesn't support SIGUSR1/SIGUSR2
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, signal_handler)
        if hasattr(signal, 'SIGUSR2'):
            signal.signal(signal.SIGUSR2, signal_handler)


def create_lifespan_manager(shutdown_manager: GracefulShutdownManager):
    """Create a lifespan manager for FastAPI"""
    
    @asynccontextmanager
    async def lifespan(app):
        # Startup
        logger.info("Application starting up...")
        
        # Setup signal handlers
        shutdown_manager.setup_signal_handlers()
        
        yield
        
        # Shutdown
        await shutdown_manager.shutdown()
    
    return lifespan


# Database shutdown hook example
async def close_database_connections():
    """Example: Close database connections"""
    logger.info("Closing database connections...")
    # Add your database cleanup code here
    await asyncio.sleep(1)
    logger.info("Database connections closed")


# Redis shutdown hook example
async def close_redis_connections():
    """Example: Close Redis connections"""
    logger.info("Closing Redis connections...")
    # Add your Redis cleanup code here
    await asyncio.sleep(0.5)
    logger.info("Redis connections closed")


# HTTP client shutdown hook example
async def close_http_clients():
    """Example: Close HTTP clients"""
    logger.info("Closing HTTP clients...")
    # Add your HTTP client cleanup code here
    await asyncio.sleep(0.5)
    logger.info("HTTP clients closed")


# Background task shutdown hook example
def stop_background_tasks():
    """Example: Stop background tasks"""
    logger.info("Stopping background tasks...")
    # Add your background task cleanup code here
    logger.info("Background tasks stopped")


# Default shutdown manager instance
shutdown_manager = GracefulShutdownManager()

# Register default hooks
shutdown_manager.add_shutdown_hook(close_database_connections)
shutdown_manager.add_shutdown_hook(close_redis_connections)
shutdown_manager.add_shutdown_hook(close_http_clients)
shutdown_manager.add_shutdown_hook(stop_background_tasks)
