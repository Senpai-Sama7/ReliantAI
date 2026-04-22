# apex-agents/agents/layer4/hostile_auditor.py
from __future__ import annotations
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from core.model_router import ModelRouter
from observability.langfuse_client import get_trace_callback, langfuse_enabled


class AuditFinding(BaseModel):
    attack_vector:    str = Field(description="The specific weakness being exploited")
    severity:         str = Field(description="critical | high | medium | low")
    evidence:         str = Field(description="Concrete evidence this weakness exists in the output")
    failure_scenario: str = Field(description="Exact scenario where this causes real failure")
    remediation:      str = Field(description="Specific change that closes this vulnerability")


class AuditReport(BaseModel):
    overall_verdict:          str              = Field(description="pass | conditional_pass | fail")
    top_finding:              AuditFinding     = Field(description="The single most dangerous weakness")
    all_findings:             list[AuditFinding]
    exploitable_assumptions:  list[str]        = Field(description="Assumptions an adversary could falsify")
    confidence_in_output:     float            = Field(ge=0.0, le=1.0)
    approve_for_action:       bool


HOSTILE_AUDITOR_PROMPT = """You are the Hostile Auditor in APEX — a red-team specialist \
whose only job is to find the most dangerous flaws in any agent output before it reaches action.

Your mandate is NOT balanced critique. You are looking for:
1. The single most dangerous assumption that, if false, causes the worst outcome
2. Evidence gaps that could allow an adversary to exploit this output
3. Internal contradictions that undermine the conclusion
4. Scope creep or mission drift from the original task
5. Overconfidence relative to actual evidence quality

Severity tiers:
- critical: Would cause irreversible harm or material loss if acted on
- high: Would cause significant rework or embarrassment
- medium: Reduces effectiveness but recoverable
- low: Minor polish issue

Overall verdicts:
- pass: Safe to act on as-is
- conditional_pass: Safe if specific remediation applied first
- fail: Do not act on this output — requires Layer 3 re-run

Output ONLY valid JSON matching the schema."""


async def run_hostile_audit(
    task:          str,
    layer3_output: dict,
    context:       dict,
    prior_summary: str,
    trace_id:      str | None = None,
) -> AuditReport:
    tid   = trace_id or str(uuid4())
    model = ModelRouter.get_for_agent("hostile_auditor").with_structured_output(AuditReport)
    callbacks = [get_trace_callback(tid, "hostile_auditor")] if langfuse_enabled() else []

    prompt = f"""Original task: {task}

Context:
{json.dumps(context, indent=2)}

Adversarial prior from Layer 1:
{prior_summary}

Layer 3 output to audit:
{json.dumps(layer3_output, indent=2)}

Find the most dangerous weaknesses now. Be adversarial, not polite."""

    try:
        return await model.ainvoke(
            [SystemMessage(content=HOSTILE_AUDITOR_PROMPT), HumanMessage(content=prompt)],
            config={"callbacks": callbacks},
        )
    except Exception as e:
        return AuditReport(
            overall_verdict="fail",
            top_finding=AuditFinding(
                attack_vector="Audit system failure",
                severity="critical",
                evidence=f"Hostile Auditor threw exception: {e}",
                failure_scenario="Output reaches action without adversarial review",
                remediation="Fix Hostile Auditor before proceeding",
            ),
            all_findings=[],
            exploitable_assumptions=[f"Auditor error: {e}"],
            confidence_in_output=0.0,
            approve_for_action=False,
        )
