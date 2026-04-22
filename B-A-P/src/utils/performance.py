"""
Performance monitoring utilities.
"""
import time
from functools import wraps
from typing import Any, Callable, TypeVar, Literal
from src.utils.logger import get_logger

logger = get_logger()

F = TypeVar("F", bound=Callable[..., Any])


def timed(func: F) -> Callable[..., Any]:
    """Decorator to time synchronous function execution."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper


def async_timed(func: F) -> Callable[..., Any]:
    """Decorator to time asynchronous function execution."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper


class PerformanceMonitor:
    """Context manager for monitoring performance of code blocks."""

    def __init__(self, operation_name: str) -> None:
        self.operation_name = operation_name
        self.start_time = 0.0

    def __enter__(self) -> "PerformanceMonitor":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        duration = time.time() - self.start_time
        logger.info(f"{self.operation_name} completed in {duration:.4f} seconds")
        return False


class AsyncPerformanceMonitor:
    """Async context manager for monitoring performance of async code blocks."""

    def __init__(self, operation_name: str) -> None:
        self.operation_name = operation_name
        self.start_time = 0.0

    async def __aenter__(self) -> "AsyncPerformanceMonitor":
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        duration = time.time() - self.start_time
        logger.info(f"{self.operation_name} completed in {duration:.4f} seconds")
        return False
