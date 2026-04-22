"""
Circuit Breaker Pattern for External API Resilience
Prevents cascade failures when Gemini API (or other services) are unavailable.
"""

import time
import functools
import asyncio
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

T = TypeVar('T')


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5        # Open after N failures
    success_threshold: int = 3        # Close after N successes in half-open
    timeout_seconds: float = 30.0     # Wait before half-open
    half_open_max_calls: int = 3      # Max calls in half-open state


class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    Usage:
        gemini_breaker = CircuitBreaker(
            "gemini-api",
            failure_threshold=5,
            timeout_seconds=60.0
        )
        
        @gemini_breaker
        async def call_gemini(prompt: str) -> str:
            # ... actual API call
            return result
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        excluded_exceptions: Optional[tuple] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.excluded = excluded_exceptions or ()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to wrap a function with circuit breaker."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await self._execute_async(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return self._execute_sync(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    def _can_execute(self) -> bool:
        """Check if call should proceed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed for half-open test
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return True
    
    def _on_success(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                # Circuit healed, close it
                self._close()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Record failed call."""
        if self.excluded and isinstance(exception, self.excluded):
            # Don't count excluded exceptions
            return
        
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed in half-open, reopen circuit
            self._open()
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                # Too many failures, open circuit
                self._open()
    
    def _open(self):
        """Open the circuit."""
        self.state = CircuitState.OPEN
        self.success_count = 0
        
    def _close(self):
        """Close the circuit."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
    
    async def _execute_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit breaker."""
        if not self._can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit '{self.name}' is OPEN. Last failure: {self.last_failure_time}"
            )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _execute_sync(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute sync function with circuit breaker."""
        if not self._can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit '{self.name}' is OPEN. Last failure: {self.last_failure_time}"
            )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            }
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Pre-configured circuit breakers for ReliantAI services
gemini_circuit = CircuitBreaker(
    "gemini-api",
    config=CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=60.0,
        half_open_max_calls=2
    ),
    excluded_exceptions=(ValueError,)  # Don't open on validation errors
)

twilio_circuit = CircuitBreaker(
    "twilio-api",
    config=CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=30.0
    )
)

database_circuit = CircuitBreaker(
    "database",
    config=CircuitBreakerConfig(
        failure_threshold=10,
        success_threshold=5,
        timeout_seconds=10.0
    ),
    excluded_exceptions=(KeyError, AttributeError)  # Logic errors, not infra
)
