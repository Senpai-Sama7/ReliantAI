"""
Performance Surgeon router — bottleneck registry.
POST /performance            — record performance issue
GET  /performance            — list (filter by status)
GET  /performance/{id}       — single item
POST /performance/{id}/resolve
GET  /performance/summary    — open vs resolved, worst offenders
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from database import (
    create_performance_item, get_performance_item,
    list_performance_items, resolve_performance_item,
)
from models import PerformanceItemCreate, PerformanceResolve

router = APIRouter(prefix="/performance", tags=["performance"])


@router.post("", status_code=201)
def add_performance_issue(body: PerformanceItemCreate):
    id = str(uuid.uuid4())[:8]
    return create_performance_item(
        id, body.service, body.metric,
        body.current_value, body.baseline_value,
        body.unit, body.bottleneck
    )


@router.get("")
def get_performance_items(
    status: Optional[str] = Query(None, pattern="^(open|resolved)$")
):
    return list_performance_items(status)


@router.get("/summary/stats")
def performance_summary():
    all_items = list_performance_items()
    open_items = [i for i in all_items if i["status"] == "open"]

    # Worst degradation = highest (current - baseline) / baseline
    def degradation_pct(item):
        if item["baseline_value"] == 0:
            return 0
        return (item["current_value"] - item["baseline_value"]) / item["baseline_value"] * 100

    worst = sorted(open_items, key=degradation_pct, reverse=True)[:5]

    return {
        "open": len(open_items),
        "resolved": len(all_items) - len(open_items),
        "worst_offenders": worst,
        "services_affected": list({i["service"] for i in open_items}),
    }


@router.get("/{id}")
def get_single_perf(id: str):
    item = get_performance_item(id)
    if not item:
        raise HTTPException(404, f"Performance item {id} not found")
    return item


@router.post("/{id}/resolve")
def close_performance_item(id: str, body: PerformanceResolve):
    item = resolve_performance_item(id, body.root_cause)
    if not item:
        raise HTTPException(404, f"Performance item {id} not found")
    return item
