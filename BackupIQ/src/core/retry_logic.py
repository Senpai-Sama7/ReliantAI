#!/usr/bin/env python3
"""
Retry Logic with Exponential Backoff
FAANG-grade reliability pattern for handling transient failures
"""

import time
import random
import asyncio
import logging
from typing import Callable, TypeVar, Optional, Type, Tuple, Any, Dict
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RetryStats:
    """Statistics for retry attempts"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_retry_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "failed_attempts": self.failed_attempts,
            "total_retry_time": self.total_retry_time
        }


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.1,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        on_retry: Optional[Callable] = None
    ):
        """
        Initialize retry configuration

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Exponential backoff multiplier
            jitter: Whether to add random jitter to delays
            jitter_range: Jitter range (0.1 = ±10%)
            retryable_exceptions: Tuple of exceptions that should trigger retry
            non_retryable_exceptions: Tuple of exceptions that should NOT trigger retry
            on_retry: Callback function called on each retry
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.jitter_range = jitter_range
        self.retryable_exceptions = retryable_exceptions or (Exception,)
        self.non_retryable_exceptions = non_retryable_exceptions or ()
        self.on_retry = on_retry

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(
            self.base_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )

        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_amount = delay * self.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)  # Ensure non-negative

    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if exception should trigger retry

        Args:
            exception: Exception that was raised

        Returns:
            True if should retry, False otherwise
        """
        # Check non-retryable exceptions first
        if isinstance(exception, self.non_retryable_exceptions):
            return False

        # Check retryable exceptions
        return isinstance(exception, self.retryable_exceptions)


async def retry_async(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """
    Execute async function with retry logic

    Args:
        func: Async function to execute
        config: Retry configuration
        *args, **kwargs: Arguments to pass to function

    Returns:
        Result of function call

    Raises:
        Last exception if all retries exhausted

    Example:
        result = await retry_async(
            my_async_function,
            config=RetryConfig(max_attempts=5),
            arg1, arg2
        )
    """
    config = config or RetryConfig()
    stats = RetryStats()
    last_exception = None

    for attempt in range(config.max_attempts):
        stats.total_attempts += 1

        try:
            result = await func(*args, **kwargs)
            stats.successful_attempts += 1

            if attempt > 0:
                logger.info(
                    f"Function {func.__name__} succeeded after {attempt + 1} attempts",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "stats": stats.to_dict()
                    }
                )

            return result

        except Exception as e:
            last_exception = e
            stats.failed_attempts += 1

            # Check if we should retry this exception
            if not config.should_retry(e):
                logger.warning(
                    f"Non-retryable exception in {func.__name__}: {type(e).__name__}",
                    extra={
                        "function": func.__name__,
                        "exception": str(e),
                        "attempt": attempt + 1
                    }
                )
                raise

            # Check if we have more attempts
            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)
                stats.total_retry_time += delay

                logger.warning(
                    f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__} "
                    f"after {delay:.2f}s due to {type(e).__name__}: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "delay": delay,
                        "exception": type(e).__name__,
                        "error_message": str(e),
                        "stats": stats.to_dict()
                    }
                )

                # Call retry callback if provided
                if config.on_retry:
                    try:
                        await config.on_retry(attempt, e, delay)
                    except Exception as callback_error:
                        logger.error(
                            f"Error in retry callback: {callback_error}",
                            extra={"callback_error": str(callback_error)}
                        )

                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed for {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "stats": stats.to_dict(),
                        "last_exception": type(e).__name__
                    }
                )

    # All retries exhausted
    raise last_exception


def retry_sync(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """
    Execute sync function with retry logic

    Args:
        func: Function to execute
        config: Retry configuration
        *args, **kwargs: Arguments to pass to function

    Returns:
        Result of function call

    Raises:
        Last exception if all retries exhausted

    Example:
        result = retry_sync(
            my_function,
            config=RetryConfig(max_attempts=5),
            arg1, arg2
        )
    """
    config = config or RetryConfig()
    stats = RetryStats()
    last_exception = None

    for attempt in range(config.max_attempts):
        stats.total_attempts += 1

        try:
            result = func(*args, **kwargs)
            stats.successful_attempts += 1

            if attempt > 0:
                logger.info(
                    f"Function {func.__name__} succeeded after {attempt + 1} attempts",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "stats": stats.to_dict()
                    }
                )

            return result

        except Exception as e:
            last_exception = e
            stats.failed_attempts += 1

            # Check if we should retry this exception
            if not config.should_retry(e):
                logger.warning(
                    f"Non-retryable exception in {func.__name__}: {type(e).__name__}",
                    extra={
                        "function": func.__name__,
                        "exception": str(e),
                        "attempt": attempt + 1
                    }
                )
                raise

            # Check if we have more attempts
            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)
                stats.total_retry_time += delay

                logger.warning(
                    f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__} "
                    f"after {delay:.2f}s due to {type(e).__name__}: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "delay": delay,
                        "exception": type(e).__name__,
                        "error_message": str(e),
                        "stats": stats.to_dict()
                    }
                )

                # Call retry callback if provided
                if config.on_retry:
                    try:
                        config.on_retry(attempt, e, delay)
                    except Exception as callback_error:
                        logger.error(
                            f"Error in retry callback: {callback_error}",
                            extra={"callback_error": str(callback_error)}
                        )

                time.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed for {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "stats": stats.to_dict(),
                        "last_exception": type(e).__name__
                    }
                )

    # All retries exhausted
    raise last_exception


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry logic to a function

    Args:
        config: Retry configuration

    Example:
        @with_retry(RetryConfig(max_attempts=5, base_delay=2.0))
        async def my_function():
            pass

        @with_retry()
        def sync_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_async(func, config, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return retry_sync(func, config, *args, **kwargs)
            return sync_wrapper

    return decorator


# Predefined retry configurations for common scenarios

# Quick retry for transient network issues
QUICK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=5.0,
    backoff_factor=2.0,
    jitter=True
)

# Standard retry for general operations
STANDARD_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True
)

# Aggressive retry for critical operations
AGGRESSIVE_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0,
    backoff_factor=2.0,
    jitter=True
)

# Patient retry for eventual consistency operations
PATIENT_RETRY_CONFIG = RetryConfig(
    max_attempts=10,
    base_delay=5.0,
    max_delay=120.0,
    backoff_factor=1.5,
    jitter=True
)
