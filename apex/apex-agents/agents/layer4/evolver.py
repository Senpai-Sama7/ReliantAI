# apex-agents/agents/layer4/evolver.py
from __future__ import annotations
import json
import os
from uuid import uuid4
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
import asyncpg

from core.model_router import ModelRouter
from observability.langfuse_client import get_trace_callback, langfuse_enabled

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://apex:changeme@postgres:5432/apex_db"
)

MAX_ITERATIONS      = 3
MIN_DELTA_THRESHOLD = 0.05


class RemediationStep(BaseModel):
    finding_ref:  str = Field(description="Which audit finding this addresses")
    action:       str = Field(description="Specific action to take")
    verification: str = Field(description="How to confirm this remediation worked")
    owner:        str = Field(description="layer1 | layer2 | layer3 | human")


class EvolverOutput(BaseModel):
    playbook:              list[RemediationStep]
    revised_confidence:    float = Field(ge=0.0, le=1.0)
    requires_layer3_rerun: bool
    requires_hitl:         bool
    convergence_note:      str
    iteration:             int


EVOLVER_PROMPT = """You are the Evolver in APEX — a continuous improvement specialist \
that turns adversarial audit findings and human corrections into concrete remediation playbooks.

Your inputs:
- Hostile Auditor findings (what's wrong)
- Human corrections from episodic memory (what humans fixed in similar past decisions)
- Current iteration number and prior confidence (for convergence tracking)

Rules:
1. Every remediation step must have a verifiable completion condition
2. Steps assigned to 'human' require explicit human sign-off before proceeding
3. If revised_confidence is not at least MIN_DELTA above prior_confidence, set convergence_note to 'converged'
4. After iteration 3, always set requires_hitl=true regardless of confidence
5. Output ONLY valid JSON matching the schema."""


async def _load_human_corrections(task_summary: str, limit: int = 5) -> list[dict]:
    """Loads recent human corrections from episodic memory as Evolver training signal."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch(
            """
            SELECT task_summary, correction, outcome, confidence, created_at
            FROM episodic_memory
            WHERE agent_name = 'human_correction'
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        await conn.close()
        return [
            {
                "task":       r["task_summary"],
                "correction": r["correction"],
                "outcome":    r["outcome"],
                "confidence": float(r["confidence"] or 0),
            }
            for r in rows
        ]
    except Exception:
        return []


async def run_evolver(
    task:             str,
    audit_report:     dict,
    layer3_output:    dict,
    context:          dict,
    prior_confidence: float,
    iteration:        int = 1,
    trace_id:         str | None = None,
) -> EvolverOutput:
    if iteration > MAX_ITERATIONS:
        return EvolverOutput(
            playbook=[
                RemediationStep(
                    finding_ref="max_iterations_exceeded",
                    action="Escalate to human review — automated convergence failed",
                    verification="Human confirms decision",
                    owner="human",
                )
            ],
            revised_confidence=prior_confidence,
            requires_layer3_rerun=False,
            requires_hitl=True,
            convergence_note=f"Max iterations ({MAX_ITERATIONS}) exceeded. Human review required.",
            iteration=iteration,
        )

    tid         = trace_id or str(uuid4())
    model       = ModelRouter.get_for_agent("evolver").with_structured_output(EvolverOutput)
    callbacks   = [get_trace_callback(tid, "evolver")] if langfuse_enabled() else []
    corrections = await _load_human_corrections(task)

    prompt = f"""Task: {task}

Hostile Auditor report:
{json.dumps(audit_report, indent=2)}

Layer 3 output being remediated:
{json.dumps(layer3_output, indent=2)}

Recent human corrections from episodic memory (learn from these):
{json.dumps(corrections, indent=2)}

Current iteration: {iteration} / {MAX_ITERATIONS}
Prior confidence:  {prior_confidence}
Min delta to continue: {MIN_DELTA_THRESHOLD}

Write the remediation playbook now."""

    try:
        result = await model.ainvoke(
            [SystemMessage(content=EVOLVER_PROMPT), HumanMessage(content=prompt)],
            config={"callbacks": callbacks},
        )
        delta = result.revised_confidence - prior_confidence
        if delta < MIN_DELTA_THRESHOLD and not result.requires_hitl:
            result = EvolverOutput(
                **{
                    **result.model_dump(),
                    "convergence_note": (
                        f"Delta {delta:.3f} below threshold {MIN_DELTA_THRESHOLD}. "
                        f"Converged at iteration {iteration}."
                    ),
                }
            )
        return result
    except Exception as e:
        return EvolverOutput(
            playbook=[
                RemediationStep(
                    finding_ref="evolver_failure",
                    action=f"Evolver threw exception: {e}",
                    verification="Fix Evolver",
                    owner="human",
                )
            ],
            revised_confidence=prior_confidence,
            requires_layer3_rerun=False,
            requires_hitl=True,
            convergence_note=f"Evolver error: {e}",
            iteration=iteration,
        )
