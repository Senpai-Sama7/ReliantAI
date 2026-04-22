"""
Celery tasks for ETL and optional AI pipeline execution.
"""
from __future__ import annotations

import asyncio
from threading import Thread
from typing import Any

from src.etl.pipeline import run_etl_pipeline
from src.models.analytics_models import PipelineRequest
from src.tasks.celery_app import celery_app


@celery_app.task(name="bap.pipeline.run", bind=True, max_retries=3)  # type: ignore[misc]
def run_pipeline_task(
    self: Any,
    job_id: str,
    dataset_id: str,
    parameters: dict[str, Any] | None,
    user: str,
    generate_ai: bool = False,
) -> dict[str, Any]:
    """Execute the ETL pipeline inside a Celery worker."""
    request = PipelineRequest(dataset_id=dataset_id, parameters=parameters or {})
    return _run_pipeline_coroutine(
        run_etl_pipeline(
            request,
            user,
            job_id=job_id,
            generate_ai=generate_ai,
        )
    )


def _run_pipeline_coroutine(coroutine: Any) -> dict[str, Any]:
    """Run the ETL coroutine from sync Celery code in both eager and worker modes."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    result: dict[str, Any] = {}
    error: list[BaseException] = []

    def _runner() -> None:
        try:
            result.update(asyncio.run(coroutine))
        except BaseException as exc:  # pragma: no cover - surfaced to caller
            error.append(exc)

    thread = Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if error:
        raise error[0]
    return result
