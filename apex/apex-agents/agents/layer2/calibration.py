# apex-agents/agents/layer2/calibration.py
from __future__ import annotations
import os
from dataclasses import dataclass
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://apex:changeme@postgres:5432/apex_db"
)

NUM_BINS = 10  # Standard ECE uses 10 equal-width confidence bins


@dataclass
class CalibrationReport:
    agent_name:    str
    ece:           float
    total_samples: int
    is_flagged:    bool
    bins:          list[dict]
    recommendation: str


async def compute_ece(agent_name: str, flag_threshold: float = 0.15) -> CalibrationReport:
    """
    Reads this agent's episodic memory rows and computes ECE.
    ECE = Σ (|bin| / n) * |accuracy(bin) - confidence(bin)|
    ECE > 0.15 triggers a flag back to the Evolver.
    """
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT confidence, outcome
            FROM episodic_memory
            WHERE agent_name = $1
              AND confidence IS NOT NULL
              AND outcome IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 500
            """,
            agent_name,
        )
    finally:
        await conn.close()

    if not rows:
        return CalibrationReport(
            agent_name=agent_name,
            ece=0.0,
            total_samples=0,
            is_flagged=False,
            bins=[],
            recommendation="Insufficient data — calibration not yet possible",
        )

    bins: list[dict] = [
        {"lower": i / NUM_BINS, "upper": (i + 1) / NUM_BINS,
         "confidences": [], "correct": 0}
        for i in range(NUM_BINS)
    ]

    for row in rows:
        conf    = float(row["confidence"])
        outcome = row["outcome"]
        approved = (
            outcome.get("approved", False)
            if isinstance(outcome, dict)
            else False
        )
        bin_idx = min(int(conf * NUM_BINS), NUM_BINS - 1)
        bins[bin_idx]["confidences"].append(conf)
        if approved:
            bins[bin_idx]["correct"] += 1

    n = len(rows)
    ece = 0.0
    bin_reports = []

    for b in bins:
        count = len(b["confidences"])
        if count == 0:
            continue
        avg_conf = sum(b["confidences"]) / count
        accuracy = b["correct"] / count
        ece += (count / n) * abs(accuracy - avg_conf)
        bin_reports.append({
            "range":    f"{b['lower']:.1f}–{b['upper']:.1f}",
            "count":    count,
            "avg_conf": round(avg_conf, 3),
            "accuracy": round(accuracy, 3),
            "gap":      round(abs(accuracy - avg_conf), 3),
        })

    is_flagged = ece > flag_threshold

    return CalibrationReport(
        agent_name=agent_name,
        ece=round(ece, 4),
        total_samples=n,
        is_flagged=is_flagged,
        bins=bin_reports,
        recommendation=(
            f"ECE={ece:.3f} exceeds threshold {flag_threshold} — "
            f"agent '{agent_name}' flagged for Evolver correction."
            if is_flagged
            else f"ECE={ece:.3f} within acceptable range."
        ),
    )
