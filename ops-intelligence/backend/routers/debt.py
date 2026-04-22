"""
Technical Debt Quantifier router — ROI-based debt prioritization.
POST /debt            — add debt item with interest/principal
GET  /debt            — list all (sorted by ROI desc)
GET  /debt/{id}       — single item
PATCH /debt/{id}      — update status
GET  /debt/summary    — total interest, total principal, avg ROI
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from database import (
    create_debt_item, get_debt_item, list_debt_items, update_debt_status,
)
from models import DebtItemCreate, DebtStatusUpdate

router = APIRouter(prefix="/debt", tags=["debt"])


@router.post("", status_code=201)
def add_debt_item(body: DebtItemCreate):
    id = str(uuid.uuid4())[:8]
    return create_debt_item(id, body.name, body.description,
                            body.interest_per_year, body.principal_cost)


@router.get("")
def get_debt_items(status: Optional[str] = Query(None, pattern="^(open|in_progress|resolved)$")):
    return list_debt_items(status)


@router.get("/summary/stats")
def debt_summary():
    items = list_debt_items()
    open_items = [i for i in items if i["status"] != "resolved"]
    total_interest = sum(i["interest_per_year"] for i in open_items)
    total_principal = sum(i["principal_cost"] for i in open_items)
    avg_roi = (
        sum(i["roi"] for i in open_items) / len(open_items)
        if open_items else 0
    )
    return {
        "open_items": len(open_items),
        "total_annual_interest": round(total_interest, 2),
        "total_principal": round(total_principal, 2),
        "avg_roi_pct": round(avg_roi, 1),
        "payback_months": round((total_principal / total_interest * 12), 1) if total_interest > 0 else None,
    }


@router.get("/{id}")
def get_single_debt(id: str):
    item = get_debt_item(id)
    if not item:
        raise HTTPException(404, f"Debt item {id} not found")
    return item


@router.patch("/{id}")
def update_debt_item_status(id: str, body: DebtStatusUpdate):
    item = update_debt_status(id, body.status)
    if not item:
        raise HTTPException(404, f"Debt item {id} not found")
    return item
