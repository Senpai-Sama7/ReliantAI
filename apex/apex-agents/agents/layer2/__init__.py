# Layer 2 - Calibration and Gate
from typing import Dict, Any
from uuid import uuid4

from .workflow import run_layer2 as _original_run_layer2
from .calibration import compute_ece
from .uncertainty import evaluate_uncertainty


async def run_layer2(
    task: str,
    context: Dict[str, Any] | None = None,
    agents: list[str] | None = None,
    trace_id: str | None = None,
) -> Dict[str, Any]:
    """
    Layer 2 calibration gate API wrapper.
    
    This wraps the original run_layer2 to provide a compatible API signature
    for the /agents/layer2/calibration-gate endpoint.
    
    Args:
        task: The task description
        context: Additional context (used for routing_tier, stakes, confidence values)
        agents: List of agent names to evaluate
        trace_id: Optional trace ID
        
    Returns:
        Calibration and gate decision results
    """
    trace_id = trace_id or str(uuid4())
    context = context or {}
    agents = agents or ["default_agent"]
    
    # Extract calibration parameters from context
    confidence = context.get("confidence", 0.8)
    aleatoric = context.get("aleatoric", 0.1)
    epistemic = context.get("epistemic", 0.1)
    routing_tier = context.get("routing_tier", "standard")
    stakes = context.get("stakes", "medium")
    
    agent_name = agents[0] if agents else "default_agent"
    
    # Call the original run_layer2
    calibration, gate = await _original_run_layer2(
        agent_name=agent_name,
        confidence=confidence,
        aleatoric=aleatoric,
        epistemic=epistemic,
        routing_tier=routing_tier,
        stakes=stakes,
        trace_id=trace_id,
    )
    
    return {
        "trace_id": trace_id,
        "agent": agent_name,
        "calibration": calibration,
        "gate_decision": gate,
        "task": task,
        "status": "completed",
    }


__all__ = ["run_layer2", "compute_ece", "evaluate_uncertainty"]
