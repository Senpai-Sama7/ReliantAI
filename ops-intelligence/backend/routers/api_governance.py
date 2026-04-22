"""
API Contract Enforcer router — API governance portal.
POST /api-governance                — register API contract
GET  /api-governance                — list all (filter by service)
GET  /api-governance/{id}           — single contract
POST /api-governance/{id}/check     — run consistency + compatibility check
GET  /api-governance/summary/stats  — health overview
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from database import (
    create_api_contract, get_api_contract,
    list_api_contracts, update_api_contract_check,
)
from models import APIContractCreate, APIContractCheck

router = APIRouter(prefix="/api-governance", tags=["api-governance"])


@router.post("", status_code=201)
def register_contract(body: APIContractCreate):
    id = str(uuid.uuid4())[:8]
    return create_api_contract(
        id, body.endpoint, body.version,
        body.method, body.service, body.notes
    )


@router.get("")
def get_contracts(service: Optional[str] = Query(None)):
    return list_api_contracts(service)


@router.get("/summary/stats")
def api_governance_summary():
    contracts = list_api_contracts()
    breaking = [c for c in contracts if c["breaking_changes"] > 0]
    undocumented = [c for c in contracts if not c["doc_complete"]]
    low_consistency = [c for c in contracts if c["consistency_score"] < 80]
    services = list({c["service"] for c in contracts})
    avg_consistency = (
        sum(c["consistency_score"] for c in contracts) / len(contracts)
        if contracts else 0
    )
    return {
        "total_contracts": len(contracts),
        "services": services,
        "breaking_changes_count": len(breaking),
        "undocumented_count": len(undocumented),
        "low_consistency_count": len(low_consistency),
        "avg_consistency_score": round(avg_consistency, 1),
        "health": "red" if breaking or low_consistency else "yellow" if undocumented else "green",
    }


@router.get("/{id}")
def get_single_contract(id: str):
    contract = get_api_contract(id)
    if not contract:
        raise HTTPException(404, f"API contract {id} not found")
    return contract


@router.post("/{id}/check")
def run_contract_check(id: str, body: APIContractCheck):
    contract = update_api_contract_check(
        id, body.breaking_changes, body.doc_complete, body.consistency_score
    )
    if not contract:
        raise HTTPException(404, f"API contract {id} not found")
    return contract
