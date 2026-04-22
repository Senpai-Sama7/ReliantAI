"""
Migration Strategist router — zero-downtime migration tracker.
POST /migrations              — create migration plan
GET  /migrations              — list all
GET  /migrations/{id}         — single migration
POST /migrations/{id}/phase   — advance phase gate
"""

import uuid
from fastapi import APIRouter, HTTPException

from database import (
    create_migration, get_migration,
    list_migrations, advance_migration_phase,
)
from models import MigrationCreate, MigrationPhaseAdvance

router = APIRouter(prefix="/migrations", tags=["migrations"])

PHASE_ORDER = ["scope", "risk", "architecture", "rollback", "validation", "execution", "completed"]


@router.post("", status_code=201)
def start_migration(body: MigrationCreate):
    id = str(uuid.uuid4())[:8]
    return create_migration(id, body.name, body.risk_level)


@router.get("")
def get_migrations():
    return list_migrations()


@router.get("/summary/stats")
def migration_summary():
    migrations = list_migrations()
    active = [m for m in migrations if m["phase"] != "completed"]
    completed = [m for m in migrations if m["phase"] == "completed"]
    high_risk = [m for m in active if m["risk_level"] in ("high", "critical")]
    no_rollback = [m for m in active if not m["rollback_ready"]]
    return {
        "active": len(active),
        "completed": len(completed),
        "high_risk_active": len(high_risk),
        "missing_rollback_plan": len(no_rollback),
        "phase_distribution": {
            phase: len([m for m in migrations if m["phase"] == phase])
            for phase in PHASE_ORDER
        },
    }


@router.get("/{id}")
def get_single_migration(id: str):
    mig = get_migration(id)
    if not mig:
        raise HTTPException(404, f"Migration {id} not found")
    return mig


@router.post("/{id}/phase")
def advance_phase(id: str, body: MigrationPhaseAdvance):
    mig = advance_migration_phase(
        id, body.phase, body.rollback_ready,
        body.kill_switch, body.validation_pct
    )
    if not mig:
        raise HTTPException(404, f"Migration {id} not found")
    return mig
