# apex-agents/agents/layer3/analytics.py
from __future__ import annotations
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from core.model_router import ModelRouter
from observability.langfuse_client import get_trace_callback, langfuse_enabled


class AnalyticsInsight(BaseModel):
    insight:        str = Field(description="The finding in one sentence")
    evidence_level: str = Field(description="validated_data | inference | speculation")
    data_source:    str = Field(description="Where this insight comes from")
    implication:    str = Field(description="What this means for the decision")


class AnalyticsReport(BaseModel):
    headline:            str                    = Field(description="Single most important finding")
    insights:            list[AnalyticsInsight]
    flagged_assumptions: list[str]              = Field(description="Load-bearing assumptions in this analysis")
    recommended_action:  str
    data_gaps:           list[str]              = Field(description="Data that would change these conclusions")
    confidence:          float                  = Field(ge=0.0, le=1.0)


ANALYTICS_PROMPT = """You are the Analytics Agent in APEX — a specialist in \
evidence-based analysis and decision support.

Evidence hierarchy you MUST enforce:
1. Validated data — confirmed, measured facts
2. Inference — logical deductions from validated data
3. Speculation — hypotheses without direct data support

Rules:
- Every insight must declare its evidence level
- Flagged assumptions are ones that, if wrong, would flip the recommendation
- Data gaps must be actionable — name exactly what data would close each gap
- Output ONLY valid JSON matching the schema."""


async def run_analytics(
    task:          str,
    context:       dict,
    prior_summary: str,
    trace_id:      str | None = None,
) -> AnalyticsReport:
    tid   = trace_id or str(uuid4())
    model = ModelRouter.get_for_agent("analytics").with_structured_output(AnalyticsReport)
    callbacks = [get_trace_callback(tid, "analytics")] if langfuse_enabled() else []

    prompt = f"""Task: {task}

Context:
{json.dumps(context, indent=2)}

Risk context:
{prior_summary}

Produce your analytics report now."""

    try:
        return await model.ainvoke(
            [SystemMessage(content=ANALYTICS_PROMPT), HumanMessage(content=prompt)],
            config={"callbacks": callbacks},
        )
    except Exception as e:
        return AnalyticsReport(
            headline=f"Analytics failed: {e}",
            insights=[],
            flagged_assumptions=[f"Analytics error: {e}"],
            recommended_action="Escalate to human review",
            data_gaps=["Full analysis required"],
            confidence=0.05,
        )
