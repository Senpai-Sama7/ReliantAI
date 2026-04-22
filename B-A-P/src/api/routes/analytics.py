"""
Analytics endpoints backed by processed dataset artifacts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, cast
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.forecast_engine import generate_forecast
from src.core.database import get_db
from src.models.analytics_models import AnalyticsSummary, ForecastRequest, ForecastResponse
from src.models.data_models import ProcessedDataset
from src.utils.logger import get_logger
from src.utils.metrics import AI_LATENCY, AI_REQUESTS

router = APIRouter()
logger = get_logger()


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    dataset_id: str = Query(..., min_length=1, max_length=128, description="Dataset ID to get summary for"),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummary:
    """Return persisted summary statistics for a processed dataset."""
    start_time = time.time()

    try:
        _validate_dataset_id(dataset_id)
        processed = await _get_processed_dataset(db, dataset_id)
        summary = cast(dict[str, Any], processed.summary or {})
        numeric_summary = cast(dict[str, Any], summary.get("numeric_summary", {}))
        created_at = cast(Optional[datetime], processed.processed_at) or datetime.now(timezone.utc)

        response = AnalyticsSummary(
            dataset_id=dataset_id,
            total_records=cast(int, processed.row_count),
            summary_statistics=numeric_summary,
            insights=_build_summary_insights(dataset_id, processed, summary),
            created_at=created_at,
        )

        AI_REQUESTS.labels(operation="summary", status="success").inc()
        AI_LATENCY.labels(operation="summary").observe(time.time() - start_time)
        logger.info(f"Generated analytics summary for dataset {dataset_id}")
        return response

    except HTTPException:
        AI_REQUESTS.labels(operation="summary", status="error").inc()
        raise
    except Exception as exc:
        AI_REQUESTS.labels(operation="summary", status="error").inc()
        logger.error(f"Failed to generate summary for {dataset_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics summary: {str(exc)}",
        ) from exc


@router.get("/preview")
async def analytics_preview(
    dataset_id: str = Query(..., min_length=1, max_length=128, description="Dataset ID to preview"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of preview rows to return"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the first N processed rows for a dataset."""
    try:
        _validate_dataset_id(dataset_id)
        processed = await _get_processed_dataset(db, dataset_id)
        records = cast(list[dict[str, Any]], processed.records or [])
        return {
            "dataset_id": dataset_id,
            "row_count": cast(int, processed.row_count),
            "preview": records[:limit],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to build preview for {dataset_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build preview: {str(exc)}",
        ) from exc


@router.get("/profile")
async def analytics_profile(
    dataset_id: str = Query(..., min_length=1, max_length=128, description="Dataset ID to profile"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return column profile metadata for a processed dataset."""
    try:
        _validate_dataset_id(dataset_id)
        processed = await _get_processed_dataset(db, dataset_id)
        summary = cast(dict[str, Any], processed.summary or {})
        schema = cast(dict[str, str], summary.get("schema", {}))
        null_counts = cast(dict[str, int], summary.get("null_counts", {}))
        distinct_counts = cast(dict[str, int], summary.get("distinct_counts", {}))
        numeric_summary = cast(dict[str, Any], summary.get("numeric_summary", {}))

        profiles = [
            {
                "column": column,
                "type": schema.get(column, "unknown"),
                "null_count": int(null_counts.get(column, 0)),
                "unique_count": int(distinct_counts.get(column, 0)),
                "statistics": numeric_summary.get(column),
            }
            for column in schema
        ]
        return {"dataset_id": dataset_id, "profiles": profiles}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to build profile for {dataset_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build profile: {str(exc)}",
        ) from exc


@router.post("/forecast", response_model=ForecastResponse)
async def analytics_forecast(request: ForecastRequest) -> ForecastResponse:
    """Return a forecast for the provided data and horizon."""
    start_time = time.time()

    try:
        if not request.data or request.horizon < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid forecast request. Data must not be empty and horizon must be positive.",
            )

        forecast = await generate_forecast(request)

        AI_REQUESTS.labels(operation="forecast", status="success").inc()
        AI_LATENCY.labels(operation="forecast").observe(time.time() - start_time)

        logger.info(
            f"Generated forecast for {len(request.data)} data points with horizon {request.horizon}"
        )
        return forecast

    except HTTPException:
        AI_REQUESTS.labels(operation="forecast", status="error").inc()
        raise
    except Exception as exc:
        AI_REQUESTS.labels(operation="forecast", status="error").inc()
        logger.error(f"Failed to generate forecast: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(exc)}",
        ) from exc


async def _get_processed_dataset(db: AsyncSession, dataset_id: str) -> ProcessedDataset:
    result = await db.execute(
        select(ProcessedDataset).where(ProcessedDataset.dataset_id == dataset_id)
    )
    processed = result.scalar_one_or_none()
    if processed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processed dataset {dataset_id} not found",
        )
    return processed


def _validate_dataset_id(dataset_id: str) -> None:
    if not dataset_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset_id format. Must contain only alphanumeric characters, hyphens, and underscores.",
        )


def _build_summary_insights(
    dataset_id: str,
    processed: ProcessedDataset,
    summary: dict[str, Any],
) -> list[str]:
    numeric_summary = cast(dict[str, dict[str, float | None]], summary.get("numeric_summary", {}))
    schema = cast(dict[str, str], summary.get("schema", {}))
    distinct_counts = cast(dict[str, int], summary.get("distinct_counts", {}))

    insights = [
        f"Processed dataset {dataset_id} contains {processed.row_count} rows across {processed.column_count} columns.",
        f"Numeric columns profiled: {', '.join(numeric_summary) if numeric_summary else 'none'}.",
    ]

    highest_cardinality_column = max(
        distinct_counts.items(),
        key=lambda item: item[1],
        default=("n/a", 0),
    )
    insights.append(
        f"Highest-cardinality column: {highest_cardinality_column[0]} ({highest_cardinality_column[1]} unique values)."
    )

    if schema:
        insights.append(f"Schema captured for columns: {', '.join(schema)}.")

    return insights
