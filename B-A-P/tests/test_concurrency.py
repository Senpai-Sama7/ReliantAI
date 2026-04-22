"""
Concurrency tests for the real ETL pipeline and cache layer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import asyncio

import polars as pl
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.cache import cache_manager
from src.etl.pipeline import ETLPipeline
from src.models.analytics_models import PipelineRequest
from src.models.data_models import Dataset, ProcessedDataset


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
                description="concurrency dataset",
                file_path=str(file_path),
                file_type="csv",
                created_by="test-user",
                status="uploaded",
                metadata_={"original_filename": file_path.name},
                row_count=0,
                column_count=0,
                file_size=len(content),
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_parallel_etl_runs(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Multiple extraction and transformation stages should run in parallel."""
    pipeline = ETLPipeline(session_factory=test_session_factory)

    for index in range(5):
        await _create_dataset(
            test_session_factory,
            tmp_path,
            dataset_id=f"ds-{index}",
            content=f"id,value\n{index},10\n{index + 1},20\n".encode("utf-8"),
        )

    async def worker(dataset_id: str) -> None:
        request = PipelineRequest(dataset_id=dataset_id)
        raw_data = await pipeline.extract_data(request, user="test-user")
        transformed = await pipeline.transform_data(raw_data)
        assert transformed["summary"]["total_records"] == 2

    await asyncio.gather(*(worker(f"ds-{index}") for index in range(5)))


@pytest.mark.asyncio
async def test_concurrent_cache_operations() -> None:
    """Cache reads and writes should behave consistently under concurrency."""
    cache = await cache_manager.connect()

    async def write_and_read(key: str, value: str) -> None:
        await cache.set(key, value)
        result = await cache.get(key)
        assert result == value

    tasks = [write_and_read(f"key-{index}", f"value-{index}") for index in range(10)]
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_sequential_jobs_for_single_dataset_update_processed_result(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Repeated ETL runs for one dataset should update the same processed artifact."""
    await _create_dataset(
        test_session_factory,
        tmp_path,
        dataset_id="race-test",
        content=b"id,value\n1,10\n2,20\n",
    )
    pipeline = ETLPipeline(session_factory=test_session_factory)

    await pipeline.run(
        PipelineRequest(dataset_id="race-test"),
        user="test-user",
        job_id="job-race-1",
    )
    await pipeline.run(
        PipelineRequest(dataset_id="race-test"),
        user="test-user",
        job_id="job-race-2",
    )

    async with test_session_factory() as session:
        processed_records = (
            await session.execute(
                select(ProcessedDataset).where(ProcessedDataset.dataset_id == "race-test")
            )
        ).scalars().all()

    assert len(processed_records) == 1
    assert processed_records[0].row_count == 2


@pytest.mark.asyncio
async def test_concurrent_data_transformations() -> None:
    """Concurrent transformations should produce correct summaries for each frame."""
    pipeline = ETLPipeline()

    async def transform_frame(index: int) -> None:
        raw_data: dict[str, Any] = {
            "dataset_id": f"transform-{index}",
            "frame": pl.DataFrame(
                {
                    "id": list(range(100)),
                    "value": [value * 10 for value in range(100)],
                    "category": ["test"] * 100,
                }
            ),
            "metadata": {},
        }
        result = await pipeline.transform_data(raw_data)
        assert result["summary"]["total_records"] == 100

    await asyncio.gather(*[transform_frame(index) for index in range(5)])


@pytest.mark.asyncio
async def test_asyncio_semaphore_limiting() -> None:
    """A semaphore can cap application-level concurrent work."""
    semaphore = asyncio.Semaphore(3)
    counter = {"current": 0, "max": 0}

    async def limited_operation(_: int) -> None:
        async with semaphore:
            counter["current"] += 1
            counter["max"] = max(counter["max"], counter["current"])
            await asyncio.sleep(0.1)
            counter["current"] -= 1

    await asyncio.gather(*[limited_operation(index) for index in range(10)])
    assert counter["max"] <= 3
