# apex-agents/agents/layer3/research.py
from __future__ import annotations
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from core.model_router import ModelRouter
from observability.langfuse_client import get_trace_callback, langfuse_enabled


class ResearchReport(BaseModel):
    summary:                   str        = Field(description="Concise findings answer")
    key_findings:              list[str]  = Field(description="Numbered factual findings, each independently verifiable")
    sources_used:              list[str]  = Field(description="Named sources or systems consulted")
    evidence_quality:          str        = Field(description="validated_data | inference | speculation")
    load_bearing_assumptions:  list[str]  = Field(description="Assumptions this report depends on")
    gaps:                      list[str]  = Field(description="What additional data would improve this report")
    confidence:                float      = Field(ge=0.0, le=1.0)


RESEARCH_PROMPT = """You are the Research Agent in APEX — a specialist in finding, \
verifying, and structuring factual information.

Evidence hierarchy you must enforce:
1. Validated data (confirmed facts) — highest weight
2. Inference (logical deductions from confirmed data) — medium weight
3. Speculation (unverified hypotheses) — lowest weight; must be explicitly labelled

Rules:
- Every key finding must be independently verifiable
- Never mix evidence levels without explicit labelling
- Load-bearing assumptions are ones that, if false, would invalidate your findings
- Output ONLY valid JSON matching the schema."""


async def run_research(
    task:          str,
    context:       dict,
    prior_summary: str,
    trace_id:      str | None = None,
) -> ResearchReport:
    tid   = trace_id or str(uuid4())
    model = ModelRouter.get_for_agent("research").with_structured_output(ResearchReport)
    callbacks = [get_trace_callback(tid, "research")] if langfuse_enabled() else []

    prompt = f"""Task: {task}

Context:
{json.dumps(context, indent=2)}

Adversarial prior notes:
{prior_summary}

Conduct your research and produce the report now."""

    try:
        return await model.ainvoke(
            [SystemMessage(content=RESEARCH_PROMPT), HumanMessage(content=prompt)],
            config={"callbacks": callbacks},
        )
    except Exception as e:
        return ResearchReport(
            summary=f"Research failed: {e}",
            key_findings=[],
            sources_used=[],
            evidence_quality="speculation",
            load_bearing_assumptions=[f"Research agent error: {e}"],
            gaps=["Full research required before proceeding"],
            confidence=0.05,
        )
