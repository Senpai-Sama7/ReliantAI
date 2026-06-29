"""Service layer for task queuing and background jobs."""

import uuid
from reliantai.models import ResearchJob
from reliantai.db import get_db_session


def enqueue_prospect_pipeline(prospect_id: str) -> str:
    """Enqueue a prospect for the full pipeline (research, site generation, outreach)."""
    job_id = str(uuid.uuid4())
    
    with get_db_session() as db:
        job = ResearchJob(
            id=job_id,
            prospect_id=prospect_id,
            job_type="prospect_pipeline",
            status="queued"
        )
        db.add(job)
        db.commit()
    
    return job_id
