# apex-agents/agents/layer3/creative.py
from __future__ import annotations
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from core.model_router import ModelRouter
from observability.langfuse_client import get_trace_callback, langfuse_enabled


class CreativeVariant(BaseModel):
    copy:            str = Field(description="The actual creative output text")
    lever:           str = Field(description="Primary psychological lever used")
    awareness_level: str = Field(description="Schwartz stage: unaware|problem_aware|solution_aware|product_aware|most_aware")
    tone:            str


class CreativeOutput(BaseModel):
    variants:             list[CreativeVariant] = Field(description="2-3 distinct creative variants")
    recommended:          int                   = Field(description="Index of recommended variant (0-based)")
    reasoning:            str                   = Field(description="Why this variant fits this audience")
    psychological_levers: list[str]             = Field(description="Full lever taxonomy used in analysis")
    confidence:           float                 = Field(ge=0.0, le=1.0)


CREATIVE_PROMPT = """You are the Creative Agent in APEX — a specialist in \
persuasive communication grounded in buyer psychology.

Schwartz buyer awareness levels:
1. Unaware — doesn't know they have a problem
2. Problem aware — knows the pain, not that solutions exist
3. Solution aware — knows solutions exist, not yours
4. Product aware — knows your product, not convinced
5. Most aware — ready to buy, needs the right offer

Psychological levers (use only what genuinely applies):
- Social proof, Authority, Scarcity/Urgency, Reciprocity,
  Loss aversion, Curiosity gap, Identity, Progress, Relief

Rules:
- Never invent testimonials or false scarcity
- Match tone exactly to the awareness level
- Output ONLY valid JSON matching the schema."""


async def run_creative(
    task:          str,
    context:       dict,
    prior_summary: str,
    trace_id:      str | None = None,
) -> CreativeOutput:
    tid   = trace_id or str(uuid4())
    model = ModelRouter.get_for_agent("creative").with_structured_output(CreativeOutput)
    callbacks = [get_trace_callback(tid, "creative")] if langfuse_enabled() else []

    prompt = f"""Task: {task}

Context:
{json.dumps(context, indent=2)}

Risk notes from adversarial analysis:
{prior_summary}

Produce 2–3 creative variants now."""

    try:
        return await model.ainvoke(
            [SystemMessage(content=CREATIVE_PROMPT), HumanMessage(content=prompt)],
            config={"callbacks": callbacks},
        )
    except Exception as e:
        return CreativeOutput(
            variants=[],
            recommended=0,
            reasoning=f"Creative agent failed: {e}",
            psychological_levers=[],
            confidence=0.05,
        )
