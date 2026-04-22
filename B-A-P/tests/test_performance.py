"""
Performance tests for the real ETL pipeline.
"""
from __future__ import annotations

from pathlib import Path
import asyncio
import time

import polars as pl
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.etl.pipeline import ETLPipeline
from src.models.analytics_models import PipelineRequest
from src.models.data_models import Dataset


async def _create_dataset(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
    dataset_id: str,
    content: bytes,
) -> None:
    file_path = tmp_path / f"{dataset_id}.csv"
    file_path.write_bytes(content)

    async with session_factory() as session:
        session.add(
            Dataset(
                dataset_id=dataset_id,
                name=dataset_id,
                description="performance dataset",
                file_path=str(file_path),
                file_type="csv",
                created_by="perf-user",
                status="uploaded",
                metadata_={"original_filename": file_path.name},
                row_count=0,
                column_count=0,
                file_size=len(content),
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_etl_performance(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """A single ETL run should complete within a reasonable bound."""
    await _create_dataset(
        test_session_factory,
        tmp_path,
        dataset_id="perf-dataset",
        content=b"id,value\n1,10\n2,20\n3,30\n",
    )
    pipeline = ETLPipeline(session_factory=test_session_factory)
    request = PipelineRequest(dataset_id="perf-dataset")

    start = time.time()
    await pipeline.run(request, user="perf-user", job_id="job-perf-dataset")
    elapsed = time.time() - start

    assert elapsed < 2.0, f"ETL took too long: {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_concurrent_etl_runs(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Extraction and transformation should scale across multiple datasets."""
    pipeline = ETLPipeline(session_factory=test_session_factory)

    for index in range(10):
        await _create_dataset(
            test_session_factory,
            tmp_path,
            dataset_id=f"concurrent-{index}",
            content=f"id,value\n{index},10\n{index + 1},20\n".encode("utf-8"),
        )

    async def run_job(index: int) -> None:
        request = PipelineRequest(dataset_id=f"concurrent-{index}")
        raw_data = await pipeline.extract_data(request, user="test-user")
        transformed = await pipeline.transform_data(raw_data)
        assert transformed["summary"]["total_records"] == 2

    start = time.time()
    await asyncio.gather(*[run_job(index) for index in range(10)])
    elapsed = time.time() - start

    assert elapsed < 5.0, f"Concurrent ETL took too long: {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_etl_throughput(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """The full ETL pipeline should sustain multiple small jobs per second."""
    pipeline = ETLPipeline(session_factory=test_session_factory)
    num_jobs = 10

    for index in range(num_jobs):
        await _create_dataset(
            test_session_factory,
            tmp_path,
            dataset_id=f"throughput-{index}",
            content=f"id,value\n{index},10\n{index + 1},20\n".encode("utf-8"),
        )

    start = time.time()
    for index in range(num_jobs):
        request = PipelineRequest(dataset_id=f"throughput-{index}")
        await pipeline.run(request, user="test-user", job_id=f"job-throughput-{index}")

    elapsed = time.time() - start
    throughput = num_jobs / elapsed

    assert throughput > 1.0, f"Low throughput: {throughput:.2f} jobs/s"


@pytest.mark.asyncio
async def test_data_transformation_performance() -> None:
    """Transformations over a moderately sized frame should remain fast."""
    pipeline = ETLPipeline()
    raw_data = {
        "dataset_id": "large-dataset",
        "frame": pl.DataFrame(
            {
                "id": list(range(500)),
                "value": [index * 10 for index in range(500)],
                "category": ["performance"] * 500,
            }
        ),
        "metadata": {},
    }

    start = time.time()
    transformed = await pipeline.transform_data(raw_data)
    transform_time = time.time() - start

    assert transform_time < 1.0, f"Transformation too slow: {transform_time:.2f}s"
    assert transformed["summary"]["total_records"] == 500
