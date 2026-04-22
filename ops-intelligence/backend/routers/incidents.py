"""
Incident Commander router — 6-phase production incident protocol.
POST /incidents            — open new incident
GET  /incidents            — list all (filter by status)
GET  /incidents/{id}       — single incident
POST /incidents/{id}/phase — advance phase
POST /incidents/{id}/resolve
"""

import os
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

import requests

from database import (
    create_incident, get_incident, list_incidents,
    advance_incident_phase, resolve_incident,
)
from models import IncidentCreate, IncidentPhaseAdvance, IncidentResolve

logger = logging.getLogger("ops.incidents")
EVENT_BUS_URL = os.getenv("EVENT_BUS_URL", "http://localhost:8081")


def _event_bus_headers() -> dict[str, str]:
    h: dict[str, str] = {"Content-Type": "application/json"}
    key = (os.getenv("EVENT_BUS_API_KEY") or "").strip()
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _publish_event(event_type: str, payload: dict) -> None:
    """Fire-and-forget event bus publish. Failure is non-fatal."""
    try:
        requests.post(
            f"{EVENT_BUS_URL}/publish",
            json={
                "event_type": event_type,
                "payload": payload,
                "correlation_id": str(uuid.uuid4()),
                "tenant_id": "reliantai",
                "source_service": "ops-intelligence",
            },
            headers=_event_bus_headers(),
            timeout=2,
        )
    except Exception as exc:
        logger.warning("Event bus publish failed (non-fatal): %s", exc)

router = APIRouter(prefix="/incidents", tags=["incidents"])

PHASES = ["triage", "evidence", "containment", "investigation", "mitigation", "stabilization"]


@router.post("", status_code=201)
def open_incident(body: IncidentCreate):
    id = str(uuid.uuid4())[:8]
    inc = create_incident(id, body.title, body.severity, body.blast_radius)
    _publish_event("agent.task.created", {
        "incident_id": id, "title": body.title,
        "severity": body.severity, "source": "ops-intelligence",
    })
    return inc


@router.get("")
def get_incidents(status: Optional[str] = Query(None, pattern="^(active|resolved)$")):
    return list_incidents(status)


@router.get("/{id}")
def get_single_incident(id: str):
    inc = get_incident(id)
    if not inc:
        raise HTTPException(404, f"Incident {id} not found")
    return inc


@router.post("/{id}/phase")
def advance_phase(id: str, body: IncidentPhaseAdvance):
    inc = advance_incident_phase(id, body.phase, body.note)
    if not inc:
        raise HTTPException(404, f"Incident {id} not found")
    return inc


@router.post("/{id}/resolve")
def close_incident(id: str, body: IncidentResolve):
    inc = resolve_incident(id, body.root_cause)
    if not inc:
        raise HTTPException(404, f"Incident {id} not found")
    _publish_event("agent.task.completed", {
        "incident_id": id, "root_cause": body.root_cause,
        "source": "ops-intelligence",
    })
    return inc


@router.get("/summary/stats")
def incident_stats():
    active = list_incidents("active")
    resolved = list_incidents("resolved")
    sev1 = [i for i in active if i["severity"] == "SEV-1"]
    return {
        "active_count": len(active),
        "resolved_count": len(resolved),
        "sev1_active": len(sev1),
        "phases": PHASES,
    }
