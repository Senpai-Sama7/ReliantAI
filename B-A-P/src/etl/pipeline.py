"""
ETL Pipeline for extracting, transforming, and loading uploaded datasets.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Optional, cast
import uuid

import polars as pl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.ai.insights_generator import generate_insights
from src.core.cache import CacheManager, cache_manager
from src.core.database import AsyncSessionLocal
from src.core.datasets import load_dataset_frame
from src.core.event_bus import publish_event
from src.models.analytics_models import PipelineRequest
from src.models.data_models import AIInsight, Dataset, ETLJob, ProcessedDataset
from src.utils.logger import get_logger
from src.utils.performance import AsyncPerformanceMonitor

logger = get_logger()


class ETLPipeline:
    """Real ETL pipeline backed by uploaded files and the analytics database."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        cache: CacheManager | None = None,
    ) -> None:
        self.logger = get_logger()
        self.session_factory = session_factory or AsyncSessionLocal
        self.cache = cache or cache_manager

    @asynccontextmanager
    async def _session_scope(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def extract_data(self, request: PipelineRequest, user: str) -> dict[str, Any]:
        """
        Extract dataset contents from the persisted upload artifact.
        """
        async with AsyncPerformanceMonitor(f"extract_data_{request.dataset_id}"):
            async with self._session_scope() as session:
                dataset = await self._require_dataset(session, request.dataset_id)
                file_path = Path(cast(str, dataset.file_path))
                file_type = cast(str, dataset.file_type)
                dataset_metadata = dict(cast(Optional[dict[str, Any]], dataset.metadata_) or {})

            if not file_path.exists():
                raise FileNotFoundError(f"Stored dataset file is missing: {file_path}")

            try:
                frame = await asyncio.to_thread(load_dataset_frame, file_path, file_type)
            except Exception as exc:
                raise ValueError(f"Unable to read dataset file {file_path.name}: {exc}") from exc

            extracted_at = datetime.now(timezone.utc).isoformat()
            raw_data = {
                "dataset_id": request.dataset_id,
                "file_path": str(file_path),
                "file_type": file_type,
                "frame": frame,
                "metadata": {
                    **dataset_metadata,
                    "extracted_at": extracted_at,
                    "extracted_by": user,
                    "record_count": frame.height,
                    "columns": [str(column) for column in frame.columns],
                },
            }

            self.logger.info(
                f"Extracted dataset {request.dataset_id}",
                user=user,
                record_count=frame.height,
                column_count=frame.width,
                file_type=file_type,
            )
            return raw_data

    async def transform_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Clean, normalize, and summarize extracted dataset contents.
        """
        dataset_id = cast(str, raw_data.get("dataset_id", "unknown"))

        async with AsyncPerformanceMonitor(f"transform_data_{dataset_id}"):
            frame = cast(pl.DataFrame, raw_data["frame"]).clone()
            input_row_count = frame.height

            if frame.width > 0:
                string_columns = [
                    column
                    for column, dtype in frame.schema.items()
                    if self._is_string_dtype(dtype)
                ]
                if string_columns:
                    frame = frame.with_columns(
                        [
                            pl.col(column)
                            .cast(pl.Utf8)
                            .str.strip_chars()
                            .replace("", None)
                            .alias(column)
                            for column in string_columns
                        ]
                    )

                non_null_conditions = [pl.col(column).is_not_null() for column in frame.columns]
                if non_null_conditions:
                    frame = frame.filter(pl.any_horizontal(non_null_conditions))

                frame = frame.unique(maintain_order=True)

            summary = self._build_summary(frame, input_row_count)
            transformed_data = {
                "dataset_id": dataset_id,
                "records": cast(list[dict[str, Any]], self._json_safe(frame.to_dicts())),
                "summary": summary,
                "row_count": frame.height,
                "column_count": frame.width,
                "metadata": {
                    **cast(dict[str, Any], raw_data.get("metadata", {})),
                    "transformed_at": datetime.now(timezone.utc).isoformat(),
                    "transformation_version": "2.0",
                },
            }

            self.logger.info(
                f"Transformed dataset {dataset_id}",
                input_rows=input_row_count,
                output_rows=frame.height,
                column_count=frame.width,
            )
            return transformed_data

    async def load_data(
        self,
        transformed_data: dict[str, Any],
        request: PipelineRequest,
        user: str,
        job_id: str,
    ) -> dict[str, Any]:
        """
        Persist transformed records and summary statistics to the analytics database.
        """
        dataset_id = request.dataset_id
        row_count = cast(int, transformed_data["row_count"])
        column_count = cast(int, transformed_data["column_count"])
        summary = cast(dict[str, Any], transformed_data["summary"])
        records = cast(list[dict[str, Any]], transformed_data["records"])
        metadata = cast(dict[str, Any], transformed_data["metadata"])
        processed_at = datetime.now(timezone.utc)

        async with AsyncPerformanceMonitor(f"load_data_{dataset_id}"):
            async with self._session_scope() as session:
                dataset = await self._require_dataset(session, dataset_id)
                processed_dataset = await self._get_processed_dataset(session, dataset_id)

                if processed_dataset is None:
                    processed_dataset = ProcessedDataset(
                        dataset_id=dataset_id,
                        source_job_id=job_id,
                        row_count=row_count,
                        column_count=column_count,
                        schema_=cast(dict[str, Any], summary["schema"]),
                        summary=summary,
                        records=records,
                        processed_at=processed_at,
                        created_by=user,
                    )
                    session.add(processed_dataset)
                else:
                    processed_dataset_row = cast(Any, processed_dataset)
                    processed_dataset_row.source_job_id = job_id
                    processed_dataset_row.row_count = row_count
                    processed_dataset_row.column_count = column_count
                    processed_dataset_row.schema_ = cast(dict[str, Any], summary["schema"])
                    processed_dataset_row.summary = summary
                    processed_dataset_row.records = records
                    processed_dataset_row.processed_at = processed_at
                    processed_dataset_row.created_by = user

                dataset_row = cast(Any, dataset)
                dataset_row.status = "processed"
                dataset_row.row_count = row_count
                dataset_row.column_count = column_count
                dataset_metadata = dict(cast(Optional[dict[str, Any]], dataset.metadata_) or {})
                dataset_metadata.update(
                    {
                        "etl_job_id": job_id,
                        "processed_at": metadata["transformed_at"],
                        "processed_row_count": row_count,
                        "processed_column_count": column_count,
                        "processed_schema": summary["schema"],
                    }
                )
                dataset_row.metadata_ = dataset_metadata

                await session.flush()

            result = {
                "dataset_id": dataset_id,
                "job_id": job_id,
                "row_count": row_count,
                "column_count": column_count,
                "summary": summary,
                "processed_at": metadata["transformed_at"],
            }
            await self._cache_pipeline_result(dataset_id, "completed", summary=summary)

            self.logger.info(
                f"Loaded dataset {dataset_id}",
                user=user,
                record_count=row_count,
                column_count=column_count,
            )
            return result

    async def run(
        self,
        request: PipelineRequest,
        user: str,
        job_id: str | None = None,
        generate_ai: bool = False,
    ) -> dict[str, Any]:
        """
        Orchestrate the complete ETL pipeline and persist job status.
        """
        current_user = user or "system"
        active_job_id = job_id or f"job-{uuid.uuid4().hex[:12]}"
        await self._update_job(
            active_job_id,
            request,
            current_user,
            status="running",
            error_message=None,
            result=None,
        )
        await self._update_dataset_status(request.dataset_id, "processing")

        try:
            self.logger.info(f"Starting ETL pipeline for {request.dataset_id}", user=current_user)

            raw_data = await self.extract_data(request, current_user)
            transformed_data = await self.transform_data(raw_data)
            result = await self.load_data(transformed_data, request, current_user, active_job_id)

            if generate_ai:
                result["insights"] = await self._generate_and_store_insights(
                    request.dataset_id,
                    current_user,
                )

            event_info = await publish_event(
                "analytics.recorded",
                {
                    "dataset_id": request.dataset_id,
                    "job_id": active_job_id,
                    "status": "completed",
                    "result": result,
                },
                correlation_id=active_job_id,
                source_service="bap-etl",
            )
            if event_info is not None:
                result["event_bus_event_id"] = event_info["event_id"]
                result["event_bus_channel"] = event_info["channel"]

            await self._update_job(
                active_job_id,
                request,
                current_user,
                status="completed",
                error_message=None,
                result=result,
            )
            self.logger.info(f"ETL pipeline completed for {request.dataset_id}", user=current_user)
            return result

        except Exception as exc:
            error_message = str(exc)
            await self._update_dataset_status(request.dataset_id, "failed")
            await self._update_job(
                active_job_id,
                request,
                current_user,
                status="failed",
                error_message=error_message,
                result={"dataset_id": request.dataset_id, "job_id": active_job_id},
            )
            await self._cache_pipeline_result(request.dataset_id, "failed", error_message=error_message)
            self.logger.error(
                f"ETL pipeline failed for {request.dataset_id}: {exc}",
                user=current_user,
                exc_info=True,
            )
            raise

    async def _generate_and_store_insights(self, dataset_id: str, user: str) -> dict[str, Any]:
        """
        Generate optional AI insights without blocking ETL completion if the AI layer fails.
        """
        try:
            content = await generate_insights(dataset_id, user)
        except Exception as exc:
            self.logger.error(
                f"Insight generation failed for {dataset_id}: {exc}",
                user=user,
                exc_info=True,
            )
            return {"status": "failed", "error": str(exc)}

        insight_id = f"ins-{uuid.uuid4().hex[:12]}"
        async with self._session_scope() as session:
            session.add(
                AIInsight(
                    insight_id=insight_id,
                    dataset_id=dataset_id,
                    insight_type="summary",
                    content=content,
                    confidence=1.0,
                    metadata_={"generator": "gemini"},
                    created_by=user,
                )
            )

        return {"status": "completed", "insight_id": insight_id}

    async def _update_dataset_status(self, dataset_id: str, status_value: str) -> None:
        async with self._session_scope() as session:
            dataset = await self._require_dataset(session, dataset_id)
            cast(Any, dataset).status = status_value

    async def _update_job(
        self,
        job_id: str,
        request: PipelineRequest,
        user: str,
        status: str,
        error_message: str | None,
        result: dict[str, Any] | None,
    ) -> None:
        async with self._session_scope() as session:
            etl_job = await self._get_job(session, job_id)
            if etl_job is None:
                etl_job = ETLJob(
                    job_id=job_id,
                    dataset_id=request.dataset_id,
                    status=status,
                    parameters=request.parameters or {},
                    created_by=user,
                    started_at=datetime.now(timezone.utc),
                )
                session.add(etl_job)
            else:
                etl_job_row = cast(Any, etl_job)
                etl_job_row.dataset_id = request.dataset_id
                etl_job_row.status = status
                etl_job_row.parameters = request.parameters or {}

            if status == "running":
                etl_job_row = cast(Any, etl_job)
                etl_job_row.started_at = datetime.now(timezone.utc)
                etl_job_row.completed_at = None

            if status in {"completed", "failed"}:
                cast(Any, etl_job).completed_at = datetime.now(timezone.utc)

            cast(Any, etl_job).error_message = error_message
            if result is not None:
                cast(Any, etl_job).result = result

    async def _cache_pipeline_result(
        self,
        dataset_id: str,
        status_value: str,
        summary: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        try:
            cache = await self.cache.connect()
            await cache.set(f"etl:status:{dataset_id}", status_value, ttl=3600)
            if summary is not None:
                await cache.set(f"etl:result:{dataset_id}", summary, ttl=3600)
            if error_message is not None:
                await cache.set(f"etl:error:{dataset_id}", error_message, ttl=3600)
        except Exception as exc:
            self.logger.error(
                f"Failed to update cache for dataset {dataset_id}: {exc}",
                exc_info=True,
            )

    async def _require_dataset(self, session: AsyncSession, dataset_id: str) -> Dataset:
        result = await session.execute(select(Dataset).where(Dataset.dataset_id == dataset_id))
        dataset = result.scalar_one_or_none()
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        return dataset

    async def _get_job(self, session: AsyncSession, job_id: str) -> ETLJob | None:
        result = await session.execute(select(ETLJob).where(ETLJob.job_id == job_id))
        return result.scalar_one_or_none()

    async def _get_processed_dataset(
        self,
        session: AsyncSession,
        dataset_id: str,
    ) -> ProcessedDataset | None:
        result = await session.execute(
            select(ProcessedDataset).where(ProcessedDataset.dataset_id == dataset_id)
        )
        return result.scalar_one_or_none()

    def _build_summary(self, frame: pl.DataFrame, input_row_count: int) -> dict[str, Any]:
        numeric_summary: dict[str, dict[str, float | None]] = {}
        for column, dtype in frame.schema.items():
            if not self._is_numeric_dtype(dtype):
                continue

            series = frame.get_column(column)
            numeric_summary[column] = {
                "mean": self._float_or_none(series.mean()),
                "median": self._float_or_none(series.median()),
                "min": self._float_or_none(series.min()),
                "max": self._float_or_none(series.max()),
                "std": self._float_or_none(series.std()),
            }

        null_counts: dict[str, int] = {}
        if frame.width > 0:
            for column, value in frame.null_count().to_dicts()[0].items():
                null_counts[column] = int(cast(int, value))

        summary = {
            "input_records": input_row_count,
            "total_records": frame.height,
            "rows_removed": input_row_count - frame.height,
            "column_count": frame.width,
            "columns": [str(column) for column in frame.columns],
            "schema": {
                column: str(dtype)
                for column, dtype in frame.schema.items()
            },
            "null_counts": null_counts,
            "distinct_counts": {
                column: int(frame.get_column(column).n_unique())
                for column in frame.columns
            },
            "numeric_summary": numeric_summary,
        }
        return cast(dict[str, Any], self._json_safe(summary))

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [self._json_safe(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        if hasattr(value, "isoformat") and callable(value.isoformat):
            return value.isoformat()
        return value

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _is_numeric_dtype(dtype: pl.DataType) -> bool:
        try:
            return bool(dtype.is_numeric())
        except AttributeError:
            return False

    @staticmethod
    def _is_string_dtype(dtype: pl.DataType) -> bool:
        return str(dtype) in {"String", "Utf8"}


# Global pipeline instance
pipeline = ETLPipeline()


async def run_etl_pipeline(
    request: PipelineRequest,
    user: str,
    job_id: str | None = None,
    generate_ai: bool = False,
) -> dict[str, Any]:
    """Run the ETL pipeline using the default application resources."""
    return await pipeline.run(
        request,
        user,
        job_id=job_id,
        generate_ai=generate_ai,
    )
