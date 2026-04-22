# apex-agents/agents/layer3/sales.py
from __future__ import annotations
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from core.model_router import ModelRouter
from observability.langfuse_client import get_trace_callback, langfuse_enabled


class FrictionPoint(BaseModel):
    stage:      str = Field(description="awareness|consideration|decision|retention")
    friction:   str = Field(description="Specific friction at this stage")
    resolution: str = Field(description="How to address this friction")
    priority:   str = Field(description="high | medium | low")


class SalesStrategy(BaseModel):
    decision_stage:    str                = Field(description="Current buyer stage")
    friction_points:   list[FrictionPoint]
    recommended_moves: list[str]          = Field(description="Prioritized next actions")
    objections:        dict[str, str]     = Field(description="Objection → specific response")
    success_metric:    str                = Field(description="Measurable success definition")
    confidence:        float              = Field(ge=0.0, le=1.0)


SALES_PROMPT = """You are the Sales Agent in APEX — a specialist in B2B decision \
facilitation and friction removal.

Decision journey stages:
1. Awareness — buyer doesn't know you exist
2. Consideration — evaluating options
3. Decision — choosing between finalists
4. Retention — driving renewal / expansion

Rules:
- Map friction to a SPECIFIC stage — never generic
- Objection responses must be specific and non-defensive
- Recommended moves must be sequenced
- Success metric must be measurable, not aspirational
- Output ONLY valid JSON matching the schema."""


async def run_sales(
    task:          str,
    context:       dict,
    prior_summary: str,
    trace_id:      str | None = None,
) -> SalesStrategy:
    tid   = trace_id or str(uuid4())
    model = ModelRouter.get_for_agent("sales").with_structured_output(SalesStrategy)
    callbacks = [get_trace_callback(tid, "sales")] if langfuse_enabled() else []

    prompt = f"""Task: {task}

Context:
{json.dumps(context, indent=2)}

Risk context:
{prior_summary}

Produce the sales strategy now."""

    try:
        return await model.ainvoke(
            [SystemMessage(content=SALES_PROMPT), HumanMessage(content=prompt)],
            config={"callbacks": callbacks},
        )
    except Exception as e:
        return SalesStrategy(
            decision_stage="unknown",
            friction_points=[],
            recommended_moves=[f"Sales agent failed: {e}"],
            objections={},
            success_metric="N/A — analysis failed",
            confidence=0.05,
        )
