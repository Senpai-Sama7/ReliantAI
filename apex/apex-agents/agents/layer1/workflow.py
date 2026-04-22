# apex-agents/agents/layer1/workflow.py
"""
APEX Layer 1 - Intake and Triage Agent

Responsible for initial request classification and routing.
"""
from __future__ import annotations
from typing import Dict, Any, TypedDict
from uuid import uuid4


class Layer1State(TypedDict):
    trace_id: str
    task: str
    context: Dict[str, Any]
    classification: str
    priority: str
    routed_to: str
    error: str | None


async def run_layer1(
    task: str,
    context: Dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> Dict[str, Any]:
    """
    Layer 1 intake and triage.
    
    Args:
        task: The user task/request
        context: Additional context
        trace_id: Optional trace ID
        
    Returns:
        Classification and routing decision
    """
    trace_id = trace_id or str(uuid4())
    context = context or {}
    
    # Simple classification logic (placeholder for actual AI classification)
    task_lower = task.lower()
    
    if any(kw in task_lower for kw in ["urgent", "emergency", "critical", "asap"]):
        priority = "high"
        classification = "urgent_request"
    elif any(kw in task_lower for kw in ["analyze", "diagnose", "evaluate", "assess"]):
        priority = "normal"
        classification = "analysis_request"
    elif any(kw in task_lower for kw in ["create", "generate", "build", "make"]):
        priority = "normal"
        classification = "creation_request"
    elif any(kw in task_lower for kw in ["question", "what", "how", "why"]):
        priority = "low"
        classification = "inquiry"
    else:
        priority = "normal"
        classification = "general_request"
    
    # Routing decision
    if classification == "urgent_request":
        routed_to = "layer3"
    elif classification == "analysis_request":
        routed_to = "layer2"
    elif classification == "creation_request":
        routed_to = "layer3"
    else:
        routed_to = "layer4"
    
    return {
        "trace_id": trace_id,
        "classification": classification,
        "priority": priority,
        "routed_to": routed_to,
        "task_summary": task[:200] if len(task) > 200 else task,
        "next_step": f"route_to_{routed_to}",
        "error": None,
    }
