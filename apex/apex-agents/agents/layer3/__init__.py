# Layer 3 - Specialist Dispatch
from typing import Dict, Any

from .dispatcher import dispatch as l3_dispatch
from .cross_system_dispatch import CrossSystemDispatcher

# Create a compatibility wrapper for cross_system_dispatch function
cross_system_dispatcher = CrossSystemDispatcher()

async def cross_system_dispatch(
    task: str,
    context: Dict[str, Any] | None = None,
    agents: list[str] | None = None,
    trace_id: str | None = None,
) -> Dict[str, Any]:
    """
    Cross-system dispatch wrapper for API compatibility.
    
    Args:
        task: The task to dispatch
        context: Additional context
        agents: List of agents to involve
        trace_id: Optional trace ID
        
    Returns:
        Dispatch result
    """
    from uuid import uuid4
    trace_id = trace_id or str(uuid4())
    
    # Use the CrossSystemDispatcher
    result = await cross_system_dispatcher.dispatch(
        task=task,
        system_type="general",
        parameters=context or {}
    )
    
    return {
        "trace_id": trace_id,
        "status": "dispatched",
        "result": result,
        "agents_involved": agents or [],
    }


class EnhancedDispatchResult:
    """Enhanced result wrapper for cross-system dispatch."""
    
    def __init__(self, trace_id: str, status: str, result: Any):
        self.trace_id = trace_id
        self.status = status
        self.result = result
    
    def dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "status": self.status,
            "result": self.result,
        }


__all__ = [
    "l3_dispatch",
    "CrossSystemDispatcher",
    "cross_system_dispatch",
    "EnhancedDispatchResult",
]
