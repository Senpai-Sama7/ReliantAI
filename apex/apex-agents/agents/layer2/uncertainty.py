# apex-agents/agents/layer2/uncertainty.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class GateDecision:
    proceed:        bool
    reason:         str
    adjusted_tier:  str | None
    aleatoric_flag: bool
    epistemic_flag: bool


def evaluate_uncertainty(
    confidence:     float,
    aleatoric:      float,
    epistemic:      float,
    routing_tier:   str,
    stakes:         str,
    min_confidence: float = 0.50,
    max_aleatoric:  float = 0.40,
    max_epistemic:  float = 0.35,
) -> GateDecision:
    """
    Layer 2 decision gate.
    Evaluates uncertainty decomposition and decides whether to proceed,
    escalate, or flag. Called after routing but before any specialist executes.
    """
    aleatoric_flag = aleatoric > max_aleatoric
    epistemic_flag = epistemic > max_epistemic

    if stakes == "irreversible" and epistemic_flag:
        return GateDecision(
            proceed=False,
            reason=(
                f"BLOCKED: irreversible stakes + epistemic uncertainty "
                f"{epistemic:.2f} > {max_epistemic}. Requires human review."
            ),
            adjusted_tier="T4Unknown",
            aleatoric_flag=aleatoric_flag,
            epistemic_flag=True,
        )

    if confidence < min_confidence and routing_tier in ("T1Reflexive", "T2Deliberative"):
        return GateDecision(
            proceed=True,
            reason=(
                f"Confidence {confidence:.2f} below {min_confidence}. "
                f"Escalating {routing_tier} → T3Contested."
            ),
            adjusted_tier="T3Contested",
            aleatoric_flag=aleatoric_flag,
            epistemic_flag=epistemic_flag,
        )

    if aleatoric_flag:
        return GateDecision(
            proceed=True,
            reason=(
                f"High aleatoric uncertainty ({aleatoric:.2f}). "
                f"Specialists should flag data quality assumptions."
            ),
            adjusted_tier=None,
            aleatoric_flag=True,
            epistemic_flag=epistemic_flag,
        )

    return GateDecision(
        proceed=True,
        reason=f"Uncertainty within bounds. Proceeding on {routing_tier}.",
        adjusted_tier=None,
        aleatoric_flag=False,
        epistemic_flag=False,
    )
