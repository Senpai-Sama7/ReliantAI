"""
FinOps Auditor router — cloud cost optimization tracking.
POST /costs                  — record service cost snapshot
GET  /costs                  — list all snapshots
GET  /costs/summary          — totals, savings, by category
DELETE /costs/{id}           — remove snapshot
"""

import uuid
from fastapi import APIRouter, HTTPException

from database import (
    create_cost_snapshot, get_cost_snapshot,
    list_cost_snapshots, cost_summary,
)
from models import CostSnapshotCreate

router = APIRouter(prefix="/costs", tags=["costs"])


@router.post("", status_code=201)
def add_cost_snapshot(body: CostSnapshotCreate):
    id = str(uuid.uuid4())[:8]
    return create_cost_snapshot(
        id, body.service_name, body.monthly_cost,
        body.savings_opportunity, body.category, body.notes
    )


@router.get("")
def get_cost_snapshots():
    return list_cost_snapshots()


@router.get("/summary/stats")
def get_cost_summary():
    snapshots = list_cost_snapshots()
    summary = cost_summary()

    # Group by category
    by_category: dict = {}
    for s in snapshots:
        cat = s["category"]
        by_category.setdefault(cat, {"cost": 0, "savings": 0, "count": 0})
        by_category[cat]["cost"] += s["monthly_cost"]
        by_category[cat]["savings"] += s["savings_opportunity"]
        by_category[cat]["count"] += 1

    # Top savings opportunities
    top_savings = sorted(snapshots, key=lambda x: x["savings_opportunity"], reverse=True)[:5]

    return {
        **summary,
        "by_category": by_category,
        "top_savings_opportunities": top_savings,
        "savings_pct": round(
            summary["total_savings_opportunity"] / summary["total_monthly_cost"] * 100, 1
        ) if summary["total_monthly_cost"] > 0 else 0,
    }


@router.get("/{id}")
def get_single_cost(id: str):
    snap = get_cost_snapshot(id)
    if not snap:
        raise HTTPException(404, f"Cost snapshot {id} not found")
    return snap
