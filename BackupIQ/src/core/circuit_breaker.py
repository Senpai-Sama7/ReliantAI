#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation
FAANG-grade reliability pattern to prevent cascade failures
"""

import time
import asyncio
import logging
from enum import Enum
from typing import Callable, Any, Optional, TypeVar, Dict
from dataclasses import dataclass, field
from functools import wraps
import threading

from .exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Rejecting requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    state_change_time: float = field(default_factory=time.time)
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0

    def reset_window_counts(self):
        """Reset counts for new window"""
        self.failure_count = 0
        self.success_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "state_change_time": self.state_change_time,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes
        }


class CircuitBreaker:
    """
    Circuit Breaker implementation for protecting against cascade failures

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing if service recovered, allow limited requests

    Example:
        circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            half_open_max_calls=3
        )

        @circuit_breaker.protect
        async def call_external_service():
            # Your code here
            pass
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_max_calls: int = 3,
        excluded_exceptions: Optional[tuple] = None,
        name: Optional[str] = None
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting half-open
            half_open_max_calls: Max calls allowed in half-open state
            excluded_exceptions: Exceptions that don't count as failures
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.excluded_exceptions = excluded_exceptions or ()
        self.name = name or "unnamed"

        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics"""
        with self._lock:
            return self._stats

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self._state
        self._state = new_state
        self._stats.state_change_time = time.time()

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._stats.reset_window_counts()

        logger.info(
            f"Circuit breaker '{self.name}' state transition: {old_state.value} -> {new_state.value}",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "stats": self._stats.to_dict()
            }
        )

    def _record_success(self):
        """Record successful call"""
        with self._lock:
            self._stats.success_count += 1
            self._stats.total_successes += 1
            self._stats.total_calls += 1
            self._stats.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Successful calls in half-open state
                if self._stats.success_count >= self.half_open_max_calls:
                    # Service recovered, close circuit
                    self._transition_to(CircuitState.CLOSED)
                    logger.info(
                        f"Circuit breaker '{self.name}' recovered, closing circuit"
                    )

    def _record_failure(self, exception: Exception):
        """Record failed call"""
        with self._lock:
            self._stats.failure_count += 1
            self._stats.total_failures += 1
            self._stats.total_calls += 1
            self._stats.last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open state, back to open
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"Circuit breaker '{self.name}' failed in half-open, reopening circuit",
                    extra={"exception": str(exception)}
                )

            elif self._state == CircuitState.CLOSED:
                # Check if we should open circuit
                if self._stats.failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.error(
                        f"Circuit breaker '{self.name}' opened due to failures",
                        extra={
                            "failure_count": self._stats.failure_count,
                            "threshold": self.failure_threshold
                        }
                    )

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if timeout has passed
                time_since_open = time.time() - self._stats.state_change_time
                if time_since_open >= self.timeout:
                    # Try half-open state
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
                return False

            if self._state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

        return False

    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute async function with circuit breaker protection

        Args:
            func: Async function to protect
            *args, **kwargs: Arguments to pass to function

        Returns:
            Result of function call

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if not self._should_allow_request():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN",
                details={
                    "circuit_breaker": self.name,
                    "state": self._state.value,
                    "failure_count": self._stats.failure_count,
                    "last_failure_time": self._stats.last_failure_time
                }
            )

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result

        except Exception as e:
            # Check if exception should be excluded
            if isinstance(e, self.excluded_exceptions):
                raise

            self._record_failure(e)
            raise

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute sync function with circuit breaker protection

        Args:
            func: Function to protect
            *args, **kwargs: Arguments to pass to function

        Returns:
            Result of function call

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if not self._should_allow_request():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN",
                details={
                    "circuit_breaker": self.name,
                    "state": self._state.value,
                    "failure_count": self._stats.failure_count,
                    "last_failure_time": self._stats.last_failure_time
                }
            )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result

        except Exception as e:
            # Check if exception should be excluded
            if isinstance(e, self.excluded_exceptions):
                raise

            self._record_failure(e)
            raise

    def protect(self, func: Callable) -> Callable:
        """
        Decorator to protect a function with circuit breaker

        Example:
            @circuit_breaker.protect
            async def my_function():
                pass
        """
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self.call(func, *args, **kwargs)
            return sync_wrapper

    def reset(self):
        """Reset circuit breaker to closed state"""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._stats.reset_window_counts()
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state as dictionary"""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_threshold": self.failure_threshold,
                "timeout": self.timeout,
                "half_open_max_calls": self.half_open_max_calls,
                "stats": self._stats.to_dict()
            }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def register(self, name: str, circuit_breaker: CircuitBreaker):
        """Register a circuit breaker"""
        with self._lock:
            self._breakers[name] = circuit_breaker
            logger.info(f"Registered circuit breaker: {name}")

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        with self._lock:
            return self._breakers.get(name)

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        with self._lock:
            return {
                name: breaker.get_state()
                for name, breaker in self._breakers.items()
            }

    def reset_all(self):
        """Reset all circuit breakers"""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
            logger.info("Reset all circuit breakers")


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()
