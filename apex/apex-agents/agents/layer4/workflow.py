# apex-agents/agents/layer4/workflow.py
from __future__ import annotations
from typing import TypedDict, Literal
from uuid import uuid4

from langgraph.graph import StateGraph, END

from agents.layer4.hostile_auditor import run_hostile_audit, AuditReport
from agents.layer4.debate_agent    import run_debate,        DebateResult
from agents.layer4.evolver         import run_evolver,       EvolverOutput, MAX_ITERATIONS


class Layer4State(TypedDict):
    trace_id:         str
    task:             str
    context:          dict
    prior_summary:    str
    layer3_output:    dict
    routing_tier:     str
    prior_confidence: float
    iteration:        int
    audit_report:     AuditReport   | None
    debate_result:    DebateResult  | None
    evolver_output:   EvolverOutput | None
    final_approved:   bool
    error:            str | None


async def audit_node(state: Layer4State) -> dict:
    try:
        report = await run_hostile_audit(
            task=state["task"],
            layer3_output=state["layer3_output"],
            context=state["context"],
            prior_summary=state["prior_summary"],
            trace_id=state["trace_id"],
        )
        return {"audit_report": report, "error": None}
    except Exception as e:
        return {"audit_report": None, "error": f"Audit node failed: {e}"}


async def debate_node(state: Layer4State) -> dict:
    audit    = state.get("audit_report")
    findings = [f.model_dump() for f in audit.all_findings] if audit else []
    try:
        result = await run_debate(
            task=state["task"],
            layer3_output=state["layer3_output"],
            audit_findings=findings,
            context=state["context"],
            trace_id=state["trace_id"],
        )
        return {"debate_result": result}
    except Exception as e:
        return {"debate_result": None, "error": f"Debate node failed: {e}"}


async def evolver_node(state: Layer4State) -> dict:
    audit      = state.get("audit_report")
    audit_dict = audit.model_dump() if audit else {}
    try:
        result = await run_evolver(
            task=state["task"],
            audit_report=audit_dict,
            layer3_output=state["layer3_output"],
            context=state["context"],
            prior_confidence=state["prior_confidence"],
            iteration=state["iteration"],
            trace_id=state["trace_id"],
        )
        approved = (
            not result.requires_hitl
            and not result.requires_layer3_rerun
            and result.revised_confidence >= 0.65
        )
        return {
            "evolver_output":   result,
            "final_approved":   approved,
            "prior_confidence": result.revised_confidence,
            "iteration":        state["iteration"] + 1,
        }
    except Exception as e:
        return {
            "evolver_output": None,
            "final_approved": False,
            "error": f"Evolver node failed: {e}",
        }


def route_after_audit(state: Layer4State) -> Literal["debate", "evolve"]:
    """Debate only for T3 Contested and T4 Unknown."""
    tier = state.get("routing_tier", "")
    return "debate" if tier in ("T3Contested", "T4Unknown") else "evolve"


def route_after_evolver(state: Layer4State) -> Literal["evolve", "__end__"]:
    """Loop back only if not converged and under max iterations."""
    ev = state.get("evolver_output")
    if ev is None:
        return "__end__"
    converged = "converged" in (ev.convergence_note or "").lower()
    if not converged and state["iteration"] <= MAX_ITERATIONS:
        return "evolve"
    return "__end__"


def build_layer4_workflow():
    graph = StateGraph(Layer4State)
    graph.add_node("audit",  audit_node)
    graph.add_node("debate", debate_node)
    graph.add_node("evolve", evolver_node)
    graph.set_entry_point("audit")
    graph.add_conditional_edges("audit",  route_after_audit,   {"debate": "debate", "evolve": "evolve"})
    graph.add_edge("debate", "evolve")
    graph.add_conditional_edges("evolve", route_after_evolver, {"evolve": "evolve", "__end__": END})
    return graph.compile()


_l4_graph = None

def get_layer4_graph():
    global _l4_graph
    if _l4_graph is None:
        _l4_graph = build_layer4_workflow()
    return _l4_graph


async def run_layer4(
    task:             str,
    layer3_output:    dict,
    context:          dict,
    prior_summary:    str,
    routing_tier:     str,
    prior_confidence: float,
    trace_id:         str | None = None,
) -> Layer4State:
    graph  = get_layer4_graph()
    result = await graph.ainvoke({
        "trace_id":         trace_id or str(uuid4()),
        "task":             task,
        "context":          context,
        "prior_summary":    prior_summary,
        "layer3_output":    layer3_output,
        "routing_tier":     routing_tier,
        "prior_confidence": prior_confidence,
        "iteration":        1,
        "audit_report":     None,
        "debate_result":    None,
        "evolver_output":   None,
        "final_approved":   False,
        "error":            None,
    })
    return result
