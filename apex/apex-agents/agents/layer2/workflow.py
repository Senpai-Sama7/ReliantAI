# apex-agents/agents/layer2/workflow.py
from __future__ import annotations
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import StateGraph, END

from agents.layer2.calibration import compute_ece, CalibrationReport
from agents.layer2.uncertainty  import evaluate_uncertainty, GateDecision


class Layer2State(TypedDict):
    trace_id:     str
    agent_name:   str
    confidence:   float
    aleatoric:    float
    epistemic:    float
    routing_tier: str
    stakes:       str
    calibration:  CalibrationReport | None
    gate:         GateDecision | None
    error:        str | None


async def calibration_node(state: Layer2State) -> dict:
    try:
        report = await compute_ece(state["agent_name"])
        return {"calibration": report, "error": None}
    except Exception as e:
        return {"calibration": None, "error": f"Calibration failed: {e}"}


def gate_node(state: Layer2State) -> dict:
    gate = evaluate_uncertainty(
        confidence=state["confidence"],
        aleatoric=state["aleatoric"],
        epistemic=state["epistemic"],
        routing_tier=state["routing_tier"],
        stakes=state["stakes"],
    )
    return {"gate": gate}


def build_layer2_workflow():
    graph = StateGraph(Layer2State)
    graph.add_node("calibrate", calibration_node)
    graph.add_node("gate",      gate_node)
    graph.set_entry_point("calibrate")
    graph.add_edge("calibrate", "gate")
    graph.add_edge("gate", END)
    return graph.compile()


_l2_graph = None

def get_layer2_graph():
    global _l2_graph
    if _l2_graph is None:
        _l2_graph = build_layer2_workflow()
    return _l2_graph


async def run_layer2(
    agent_name:   str,
    confidence:   float,
    aleatoric:    float,
    epistemic:    float,
    routing_tier: str,
    stakes:       str,
    trace_id:     str | None = None,
) -> tuple[CalibrationReport | None, GateDecision]:
    graph  = get_layer2_graph()
    result = await graph.ainvoke({
        "trace_id":     trace_id or str(uuid4()),
        "agent_name":   agent_name,
        "confidence":   confidence,
        "aleatoric":    aleatoric,
        "epistemic":    epistemic,
        "routing_tier": routing_tier,
        "stakes":       stakes,
        "calibration":  None,
        "gate":         None,
        "error":        None,
    })
    return result["calibration"], result["gate"]
