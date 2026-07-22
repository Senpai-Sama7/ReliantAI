"""Service layer for task queuing and background jobs."""

from __future__ import annotations

import logging
import uuid

from reliantai.db import get_db_session
from reliantai.db.models import ResearchJob

log = logging.getLogger(__name__)


def enqueue_prospect_pipeline(prospect_id: str) -> str:
    """Persist a ResearchJob and enqueue the Celery prospect pipeline."""
    job_id = str(uuid.uuid4())

    with get_db_session() as db:
        job = ResearchJob(
            id=job_id,
            prospect_id=prospect_id,
            status="pending",
            step="queued",
        )
        db.add(job)

    try:
        from reliantai.tasks.prospect_tasks import run_prospect_pipeline

        run_prospect_pipeline.delay(prospect_id)
    except Exception as exc:
        # Persist the job even if the broker is down; beat/workers can pick up pending.
        log.warning(
            "pipeline_enqueue_failed",
            extra={"prospect_id": prospect_id, "job_id": job_id, "error": str(exc)[:160]},
        )

    return job_id
