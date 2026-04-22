"""
Trigger ETL pipeline orchestration.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, cast
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import get_current_user_optional
from src.core.database import get_db
from src.etl.pipeline import run_etl_pipeline
from src.models.analytics_models import PipelineRequest, PipelineResponse
from src.models.data_models import ETLJob
from src.tasks.celery_app import celery_app
from src.tasks.pipeline_tasks import run_pipeline_task
from src.utils.logger import get_logger
from src.utils.metrics import ETL_JOBS

router = APIRouter()
logger = get_logger()


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(
    request: PipelineRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict[str, Any]] = Depends(get_current_user_optional),
) -> PipelineResponse:
    """Queue a real ETL pipeline job for a persisted dataset."""
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    started_at = datetime.now(timezone.utc)
    current_user = _get_created_by(user)
    start_time = time.time()

    try:
        db.add(
            ETLJob(
                job_id=job_id,
                dataset_id=request.dataset_id,
                status="pending",
                parameters=request.parameters or {},
                created_by=current_user,
                started_at=started_at,
            )
        )
        await db.commit()

        generate_ai = bool((request.parameters or {}).get("generate_insights", False))
        if celery_app.conf.task_always_eager:
            await run_etl_pipeline(
                request,
                current_user,
                job_id=job_id,
                generate_ai=generate_ai,
            )
        else:
            run_pipeline_task.delay(
                job_id=job_id,
                dataset_id=request.dataset_id,
                parameters=request.parameters or {},
                user=current_user,
                generate_ai=generate_ai,
            )

        ETL_JOBS.labels(status="queued").inc()
        logger.info(
            f"Queued pipeline for dataset {request.dataset_id}",
            job_id=job_id,
            queued_by=current_user,
            queued_in_seconds=time.time() - start_time,
        )
        return PipelineResponse(
            status="started",
            job_id=job_id,
            details="ETL pipeline queued via Celery",
            started_at=started_at,
        )

    except Exception as exc:
        await db.rollback()
        ETL_JOBS.labels(status="failed").inc()
        logger.error(
            f"Failed to start pipeline for dataset {request.dataset_id}: {exc}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start pipeline: {str(exc)}",
        ) from exc


@router.get("/status/{job_id}")
async def get_pipeline_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get the persisted status of a pipeline job."""
    try:
        result = await db.execute(select(ETLJob).where(ETLJob.job_id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline job {job_id} not found",
            )

        return {
            "job_id": job.job_id,
            "dataset_id": job.dataset_id,
            "status": job.status,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message,
            "result": job.result or {},
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to get status for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(exc)}",
        ) from exc


@router.get("/jobs")
async def list_pipeline_jobs(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter jobs by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    """List pipeline jobs, optionally filtered by status."""
    try:
        statement = select(ETLJob).order_by(ETLJob.started_at.desc(), ETLJob.id.desc()).limit(limit)
        if status_filter:
            statement = statement.where(ETLJob.status == status_filter)

        result = await db.execute(statement)
        jobs = result.scalars().all()
        return {
            "jobs": [
                {
                    "job_id": cast(str, job.job_id),
                    "dataset_id": cast(str, job.dataset_id),
                    "status": cast(str, job.status),
                    "started_at": cast(Optional[datetime], job.started_at),
                    "completed_at": cast(Optional[datetime], job.completed_at),
                    "error_message": cast(Optional[str], job.error_message),
                }
                for job in jobs
            ]
        }
    except Exception as exc:
        logger.error(f"Failed to list pipeline jobs: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pipeline jobs: {str(exc)}",
        ) from exc


def _get_created_by(user: Optional[dict[str, Any]]) -> str:
    if not user:
        return "system"

    for key in ("username", "sub", "user_id", "email"):
        value = user.get(key)
        if isinstance(value, str) and value:
            return value

    return "system"
