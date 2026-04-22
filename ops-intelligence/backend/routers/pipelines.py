"""
Data Pipeline Architect router — pipeline health + quality tracking.
POST /pipelines          — register or update pipeline
GET  /pipelines          — list all pipelines
GET  /pipelines/{id}     — single pipeline
GET  /pipelines/summary  — health overview
"""

import uuid
from fastapi import APIRouter, HTTPException

from database import upsert_pipeline, get_pipeline, list_pipelines
from models import PipelineUpsert

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("", status_code=201)
def register_pipeline(body: PipelineUpsert):
    id = str(uuid.uuid4())[:8]
    return upsert_pipeline(
        id, body.name, body.status, body.quality_score,
        body.cost_per_record, body.records_per_day,
        body.sla_minutes, body.phase
    )


@router.put("/{id}")
def update_pipeline(id: str, body: PipelineUpsert):
    existing = get_pipeline(id)
    if not existing:
        raise HTTPException(404, f"Pipeline {id} not found")
    return upsert_pipeline(
        id, body.name, body.status, body.quality_score,
        body.cost_per_record, body.records_per_day,
        body.sla_minutes, body.phase
    )


@router.get("")
def get_pipelines():
    return list_pipelines()


@router.get("/summary/stats")
def pipeline_summary():
    pipelines = list_pipelines()
    healthy = [p for p in pipelines if p["status"] == "healthy"]
    degraded = [p for p in pipelines if p["status"] == "degraded"]
    failed = [p for p in pipelines if p["status"] == "failed"]
    avg_quality = (
        sum(p["quality_score"] for p in pipelines) / len(pipelines)
        if pipelines else 0
    )
    return {
        "total": len(pipelines),
        "healthy": len(healthy),
        "degraded": len(degraded),
        "failed": len(failed),
        "avg_quality_score": round(avg_quality, 1),
        "sla_breaches": [p for p in pipelines if p["quality_score"] < 95],
    }


@router.get("/{id}")
def get_single_pipeline(id: str):
    pipe = get_pipeline(id)
    if not pipe:
        raise HTTPException(404, f"Pipeline {id} not found")
    return pipe
