"""
Integration of Circuit Breaker with Money service components.
Wraps Gemini LLM calls, database operations, and external APIs.
"""

from functools import wraps

from circuit_breaker import gemini_circuit, database_circuit, CircuitBreakerOpenError


def with_gemini_circuit_breaker(func):
    """
    Decorator to apply Gemini circuit breaker to CrewAI calls.
    
    Usage:
        @with_gemini_circuit_breaker
        async def run_crew_dispatch(message: str, temp: int):
            return await crew.kickoff_async()
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await gemini_circuit._execute_async(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            # Circuit is open - return structured fallback
            return {
                "triage": "SYSTEM_UNAVAILABLE",
                "priority": 3,
                "outcome": "Circuit breaker OPEN - Gemini API unavailable",
                "fallback": True
            }
    return wrapper


def with_database_circuit(func):
    """Decorator for database operations with circuit breaker."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await database_circuit._execute_async(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            # Database unavailable - use in-memory fallback
            return None
    return wrapper


class ResilientCrewRunner:
    """
    Wrapper for CrewAI that adds circuit breaker protection.
    Falls back to local triage when Gemini is unavailable.
    """
    
    def __init__(self, crew_factory):
        self.crew_factory = crew_factory
        self.fallback_count = 0
    
    @with_gemini_circuit_breaker
    async def run(self, message: str, outdoor_temp: int = 75) -> dict:
        """Run crew with circuit breaker protection."""
        crew = self.crew_factory(message, outdoor_temp)
        result = await crew.kickoff_async()
        return result
    
    async def run_with_fallback(self, message: str, outdoor_temp: int = 75) -> dict:
        """
        Run with automatic fallback to local triage.
        
        Returns:
            CrewAI result OR local triage result if circuit open
        """
        try:
            result = await self.run(message, outdoor_temp)
            if isinstance(result, dict) and result.get("fallback"):
                # Circuit returned fallback marker
                return self._local_fallback(message, outdoor_temp)
            return result
        except Exception as e:
            # Any other error - use local triage
            return self._local_fallback(message, outdoor_temp, str(e))
    
    def _local_fallback(self, message: str, outdoor_temp: int, error: str = None) -> dict:
        """Fallback to local triage engine."""
        self.fallback_count += 1
        
        # Import here to avoid circular dependency
        from triage import triage_urgency_local
        
        triage_result = triage_urgency_local(message, outdoor_temp)
        
        return {
            "triage": triage_result["category"],
            "priority": triage_result["priority"],
            "outcome": triage_result["outcome"],
            "fallback": True,
            "error": error,
            "circuit_breaker_fallback": True
        }
    
    def get_health(self) -> dict:
        """Get circuit breaker health status."""
        return {
            "gemini_circuit": gemini_circuit.get_state(),
            "fallback_count": self.fallback_count,
            "healthy": gemini_circuit.state.value == "closed"
        }


# Health check endpoint for monitoring
def get_circuit_breaker_health() -> dict:
    """Get health status of all circuit breakers."""
    return {
        "gemini": gemini_circuit.get_state(),
        "database": database_circuit.get_state(),
        "status": "healthy" if all(
            c.state.value == "closed" 
            for c in [gemini_circuit, database_circuit]
        ) else "degraded"
    }
