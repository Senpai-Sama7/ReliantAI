"""
ETL pipeline tests backed by real dataset files and database rows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.etl.pipeline import ETLPipeline
from src.models.analytics_models import PipelineRequest
from src.models.data_models import Dataset, ETLJob, ProcessedDataset


async def _create_dataset(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
    dataset_id: str,
    file_type: str,
    content: bytes,
) -> Path:
    suffix = f".{file_type}"
    file_path = tmp_path / f"{dataset_id}{suffix}"
    file_path.write_bytes(content)

    async with session_factory() as session:
        session.add(
            Dataset(
                dataset_id=dataset_id,
                name=dataset_id,
                description="test dataset",
                file_path=str(file_path),
                file_type=file_type,
                created_by="test-user",
                status="uploaded",
                metadata_={"original_filename": file_path.name},
                row_count=0,
                column_count=0,
                file_size=len(content),
            )
        )
        await session.commit()

    return file_path


@pytest.mark.asyncio
async def test_etl_extract_stage_reads_uploaded_csv(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Extract stage reads the persisted dataset file instead of generating fake records."""
    await _create_dataset(
        test_session_factory,
        tmp_path,
        dataset_id="extract-test",
        file_type="csv",
        content=b"id,value\n1,100\n2,200\n3,300\n",
    )
    pipeline = ETLPipeline(session_factory=test_session_factory)

    raw_data = await pipeline.extract_data(
        PipelineRequest(dataset_id="extract-test"),
        user="test-user",
    )

    frame = raw_data["frame"]
    assert isinstance(frame, pl.DataFrame)
    assert frame.height == 3
    assert frame.width == 2
    assert raw_data["file_type"] == "csv"
    assert raw_data["metadata"]["record_count"] == 3


@pytest.mark.asyncio
async def test_etl_transform_stage_cleans_duplicates_and_empty_strings() -> None:
    """Transform stage removes duplicate rows and normalizes blank strings to null."""
    pipeline = ETLPipeline()
    raw_data: dict[str, Any] = {
        "dataset_id": "transform-test",
        "frame": pl.DataFrame(
            [
                {"id": 1, "value": 10, "category": " north "},
                {"id": 1, "value": 10, "category": " north "},
                {"id": 2, "value": 20, "category": ""},
            ]
        ),
        "metadata": {},
    }

    transformed = await pipeline.transform_data(raw_data)

    assert transformed["row_count"] == 2
    assert transformed["summary"]["rows_removed"] == 1
    assert transformed["summary"]["null_counts"]["category"] == 1
    assert transformed["records"][0]["category"] == "north"
    assert transformed["records"][1]["category"] is None
    assert transformed["summary"]["numeric_summary"]["value"]["mean"] == 15.0


@pytest.mark.asyncio
async def test_run_pipeline_persists_processed_dataset_and_job_status(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """A successful ETL run writes processed data and marks the job complete."""
    await _create_dataset(
        test_session_factory,
        tmp_path,
        dataset_id="orders-etl",
        file_type="csv",
        content=b"id,amount,region\n1,10,north\n2,20,south\n3,30,west\n",
    )
    pipeline = ETLPipeline(session_factory=test_session_factory)

    result = await pipeline.run(
        PipelineRequest(dataset_id="orders-etl"),
        user="etl-user",
        job_id="job-orders-etl",
    )

    assert result["dataset_id"] == "orders-etl"
    assert result["row_count"] == 3
    assert result["summary"]["column_count"] == 3

    async with test_session_factory() as session:
        dataset = (
            await session.execute(select(Dataset).where(Dataset.dataset_id == "orders-etl"))
        ).scalar_one()
        job = (
            await session.execute(select(ETLJob).where(ETLJob.job_id == "job-orders-etl"))
        ).scalar_one()
        processed = (
            await session.execute(
                select(ProcessedDataset).where(ProcessedDataset.dataset_id == "orders-etl")
            )
        ).scalar_one()

    assert dataset.status == "processed"
    assert dataset.row_count == 3
    assert job.status == "completed"
    assert job.completed_at is not None
    assert job.result["summary"]["total_records"] == 3
    assert processed.row_count == 3
    assert processed.column_count == 3
    assert processed.summary["numeric_summary"]["amount"]["max"] == 30.0
    assert len(processed.records) == 3


@pytest.mark.asyncio
async def test_run_pipeline_marks_job_failed_for_corrupt_json(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """A corrupt stored file marks the ETL job and dataset as failed."""
    await _create_dataset(
        test_session_factory,
        tmp_path,
        dataset_id="broken-json",
        file_type="json",
        content=b'{"bad": }',
    )
    pipeline = ETLPipeline(session_factory=test_session_factory)

    with pytest.raises(ValueError, match="Unable to read dataset file"):
        await pipeline.run(
            PipelineRequest(dataset_id="broken-json"),
            user="etl-user",
            job_id="job-broken-json",
        )

    async with test_session_factory() as session:
        dataset = (
            await session.execute(select(Dataset).where(Dataset.dataset_id == "broken-json"))
        ).scalar_one()
        job = (
            await session.execute(select(ETLJob).where(ETLJob.job_id == "job-broken-json"))
        ).scalar_one()
        processed = (
            await session.execute(
                select(ProcessedDataset).where(ProcessedDataset.dataset_id == "broken-json")
            )
        ).scalar_one_or_none()

    assert dataset.status == "failed"
    assert job.status == "failed"
    assert "Unable to read dataset file" in job.error_message
    assert processed is None
