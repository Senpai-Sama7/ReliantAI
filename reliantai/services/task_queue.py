def enqueue_prospect_pipeline(prospect_id: str) -> None:
    """Enqueue the research pipeline without importing Celery at module import time."""
    from ..tasks.prospect_tasks import run_prospect_pipeline

    run_prospect_pipeline.delay(prospect_id)
