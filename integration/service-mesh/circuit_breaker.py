"""
Circuit Breaker Implementation for Linkerd
Monitors error rates and manages circuit state
"""
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict
import structlog

logger = structlog.get_logger()

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """
    Circuit breaker implementation
    - Opens after 50% error rate over 10s window
    - Stays open for 30s
    - Half-open allows 1 test request
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None
        self.window_start = datetime.utcnow()
        
        # Configuration
        self.failure_threshold = 0.5  # 50%
        self.window_duration = timedelta(seconds=10)
        self.open_duration = timedelta(seconds=30)
    
    def record_success(self):
        """Record successful request"""
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Success in half-open state closes circuit
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            logger.info("circuit_closed", service=self.service_name)
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        # Check if should open circuit
        if self.state == CircuitState.CLOSED:
            total_requests = self.failure_count + self.success_count
            if total_requests > 0:
                error_rate = self.failure_count / total_requests
                
                if error_rate >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.opened_at = datetime.utcnow()
                    logger.warning("circuit_opened", 
                                 service=self.service_name,
                                 error_rate=error_rate)
        
        elif self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state reopens circuit
            self.state = CircuitState.OPEN
            self.opened_at = datetime.utcnow()
            logger.warning("circuit_reopened", service=self.service_name)
    
    def can_attempt(self) -> bool:
        """Check if request should be attempted"""
        now = datetime.utcnow()
        
        # Reset window if expired
        if now - self.window_start > self.window_duration:
            self.window_start = now
            self.failure_count = 0
            self.success_count = 0
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if should enter half-open
            if now - self.opened_at > self.open_duration:
                self.state = CircuitState.HALF_OPEN
                logger.info("circuit_half_open", service=self.service_name)
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow one test request
            return True
        
        return False
    
    def get_state(self) -> Dict:
        """Get current circuit state"""
        return {
            "service": self.service_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "error_rate": self.failure_count / (self.failure_count + self.success_count) if (self.failure_count + self.success_count) > 0 else 0
        }

# Global circuit breakers for all services
circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get or create circuit breaker for service"""
    if service_name not in circuit_breakers:
        circuit_breakers[service_name] = CircuitBreaker(service_name)
    return circuit_breakers[service_name]
