# apex-agents/agents/layer4/debate_agent.py
from __future__ import annotations
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from core.model_router import ModelRouter
from observability.langfuse_client import get_trace_callback, langfuse_enabled


class Position(BaseModel):
    stance:     str       = Field(description="for | against | alternative")
    argument:   str       = Field(description="Core argument in 2-3 sentences")
    key_points: list[str] = Field(description="3-5 strongest supporting points")
    weaknesses: list[str] = Field(description="This position's own admitted weaknesses")


class DebateResult(BaseModel):
    positions:               list[Position]
    strongest_opposition:    str       = Field(description="Single strongest argument against proposed action")
    synthesis:               str       = Field(description="Defensible conclusion after hearing all positions")
    irresolvable_tensions:   list[str] = Field(description="Disagreements requiring more data to resolve")
    recommended_action:      str
    confidence_after_debate: float     = Field(ge=0.0, le=1.0)


DEBATE_PROMPT = """You are the Debate Agent in APEX — a dialectical reasoning specialist \
activated only for high-stakes contested decisions.

Your process:
1. Argue FOR the proposed action as strongly as possible
2. Argue AGAINST with equal force — find the strongest objection, not a straw man
3. If a clearly superior alternative exists, argue for it as a third position
4. Synthesize honestly — acknowledge tensions that cannot be resolved with current data

You are NOT trying to justify a predetermined conclusion.
If the opposition is stronger than the proposal, say so.

Output ONLY valid JSON matching the schema."""


async def run_debate(
    task:           str,
    layer3_output:  dict,
    audit_findings: list[dict],
    context:        dict,
    trace_id:       str | None = None,
) -> DebateResult:
    tid   = trace_id or str(uuid4())
    model = ModelRouter.get_for_agent("debate_agent").with_structured_output(DebateResult)
    callbacks = [get_trace_callback(tid, "debate_agent")] if langfuse_enabled() else []

    prompt = f"""Task under debate: {task}

Context:
{json.dumps(context, indent=2)}

Proposed output from Layer 3:
{json.dumps(layer3_output, indent=2)}

Hostile Auditor findings (top threats):
{json.dumps(audit_findings[:3], indent=2)}

Run the debate now."""

    try:
        return await model.ainvoke(
            [SystemMessage(content=DEBATE_PROMPT), HumanMessage(content=prompt)],
            config={"callbacks": callbacks},
        )
    except Exception as e:
        return DebateResult(
            positions=[],
            strongest_opposition=f"Debate agent failed: {e}",
            synthesis="Debate failed — escalate to human review",
            irresolvable_tensions=[f"Debate error: {e}"],
            recommended_action="Escalate to HITL",
            confidence_after_debate=0.1,
        )
