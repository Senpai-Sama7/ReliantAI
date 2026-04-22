"""
API endpoint tests.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routes import data as data_routes
from src.api.routes import pipeline as pipeline_routes
from src.models.data_models import Dataset, ETLJob, ProcessedDataset
from src.tasks.celery_app import celery_app


async def _upload_csv_dataset(
    authenticated_client: AsyncClient,
    filename: str,
    body: bytes,
) -> dict[str, Any]:
    """Upload a CSV dataset and return the response payload."""
    files = {"file": (filename, body, "text/csv")}
    response = await authenticated_client.post("/api/data/upload-data", files=files)
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


async def _seed_processed_dataset(
    test_db: AsyncSession,
    dataset_id: str = "test123",
) -> None:
    """Insert a processed dataset row for analytics endpoint tests."""
    test_db.add(
        ProcessedDataset(
            dataset_id=dataset_id,
            source_job_id=f"job-{dataset_id}",
            row_count=3,
            column_count=3,
            schema_={"id": "Int64", "revenue": "Int64", "region": "String"},
            summary={
                "input_records": 3,
                "total_records": 3,
                "rows_removed": 0,
                "column_count": 3,
                "columns": ["id", "revenue", "region"],
                "schema": {"id": "Int64", "revenue": "Int64", "region": "String"},
                "null_counts": {"id": 0, "revenue": 0, "region": 0},
                "distinct_counts": {"id": 3, "revenue": 3, "region": 3},
                "numeric_summary": {
                    "id": {"mean": 2.0, "median": 2.0, "min": 1.0, "max": 3.0, "std": 1.0},
                    "revenue": {
                        "mean": 1325.0,
                        "median": 1350.0,
                        "min": 1200.0,
                        "max": 1425.0,
                        "std": 114.564392373896,
                    },
                },
            },
            records=[
                {"id": 1, "revenue": 1200, "region": "north"},
                {"id": 2, "revenue": 1350, "region": "south"},
                {"id": 3, "revenue": 1425, "region": "west"},
            ],
            created_by="test-user",
        )
    )
    await test_db.commit()


async def _seed_pipeline_job(
    test_db: AsyncSession,
    job_id: str,
    dataset_id: str,
    status_value: str,
) -> None:
    """Insert a pipeline job row for job-tracking endpoint tests."""
    test_db.add(
        ETLJob(
            job_id=job_id,
            dataset_id=dataset_id,
            status=status_value,
            parameters={},
            result={"dataset_id": dataset_id, "status": status_value},
            created_by="test-user",
        )
    )
    await test_db.commit()


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert isinstance(datetime.fromisoformat(data["timestamp"]), datetime)

@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Test root endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data

@pytest.mark.asyncio
async def test_analytics_summary(authenticated_client: AsyncClient, test_db: AsyncSession) -> None:
    """Test analytics summary endpoint."""
    await _seed_processed_dataset(test_db, dataset_id="test123")
    response = await authenticated_client.get("/api/analytics/summary?dataset_id=test123")
    assert response.status_code == 200
    data = response.json()
    assert "dataset_id" in data
    assert data["dataset_id"] == "test123"
    assert data["total_records"] == 3
    assert data["summary_statistics"]["revenue"]["median"] == 1350.0


@pytest.mark.asyncio
async def test_analytics_summary_missing_dataset(
    authenticated_client: AsyncClient,
) -> None:
    """Summary endpoint returns 404 for a valid but unknown processed dataset."""
    response = await authenticated_client.get("/api/analytics/summary?dataset_id=unknown123")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_analytics_summary_invalid_id(authenticated_client: AsyncClient) -> None:
    """Test analytics summary with invalid dataset ID."""
    response = await authenticated_client.get("/api/analytics/summary?dataset_id=test@123")
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_analytics_forecast(authenticated_client: AsyncClient) -> None:
    """Test analytics forecast endpoint."""
    payload = {"data": [1.0, 2.0, 3.0], "horizon": 2}
    response = await authenticated_client.post("/api/analytics/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "forecast" in data

@pytest.mark.asyncio
async def test_analytics_forecast_invalid_data(authenticated_client: AsyncClient) -> None:
    """Test forecast with invalid data."""
    payload = {"data": [], "horizon": 2}
    response = await authenticated_client.post("/api/analytics/forecast", json=payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analytics_preview(authenticated_client: AsyncClient, test_db: AsyncSession) -> None:
    """Preview endpoint returns the first N processed rows."""
    await _seed_processed_dataset(test_db, dataset_id="preview123")
    response = await authenticated_client.get("/api/analytics/preview?dataset_id=preview123&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "preview123"
    assert len(data["preview"]) == 2
    assert data["preview"][0]["region"] == "north"


@pytest.mark.asyncio
async def test_analytics_profile(authenticated_client: AsyncClient, test_db: AsyncSession) -> None:
    """Profile endpoint returns schema, nulls, and distinct counts per column."""
    await _seed_processed_dataset(test_db, dataset_id="profile123")
    response = await authenticated_client.get("/api/analytics/profile?dataset_id=profile123")
    assert response.status_code == 200
    data = response.json()
    profiles = {profile["column"]: profile for profile in data["profiles"]}
    assert profiles["revenue"]["type"] == "Int64"
    assert profiles["revenue"]["unique_count"] == 3
    assert profiles["revenue"]["statistics"]["mean"] == 1325.0


@pytest.mark.asyncio
async def test_pipeline_run_creates_job(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pipeline run endpoint creates a persisted job row."""
    async def fake_run_etl_pipeline(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"status": "completed"}

    monkeypatch.setattr(pipeline_routes, "run_etl_pipeline", fake_run_etl_pipeline)
    monkeypatch.setattr(
        celery_app.conf,
        "task_always_eager",
        True,
        raising=False,
    )

    response = await authenticated_client.post(
        "/api/pipeline/run",
        json={"dataset_id": "pipe123", "parameters": {}},
    )
    assert response.status_code == 200
    payload = response.json()

    result = await test_db.execute(select(ETLJob).where(ETLJob.job_id == payload["job_id"]))
    job = result.scalar_one()
    assert job.dataset_id == "pipe123"
    assert job.status == "pending"


@pytest.mark.asyncio
async def test_pipeline_status_endpoint(authenticated_client: AsyncClient, test_db: AsyncSession) -> None:
    """Pipeline status endpoint returns persisted job details."""
    await _seed_pipeline_job(test_db, job_id="job-status", dataset_id="ds-status", status_value="completed")
    response = await authenticated_client.get("/api/pipeline/status/job-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == "job-status"
    assert payload["status"] == "completed"
    assert payload["result"]["dataset_id"] == "ds-status"


@pytest.mark.asyncio
async def test_pipeline_jobs_endpoint_filters_by_status(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    """Pipeline jobs endpoint filters persisted jobs by status."""
    await _seed_pipeline_job(test_db, job_id="job-complete", dataset_id="ds-complete", status_value="completed")
    await _seed_pipeline_job(test_db, job_id="job-failed", dataset_id="ds-failed", status_value="failed")

    response = await authenticated_client.get("/api/pipeline/jobs?status=completed")
    assert response.status_code == 200
    payload = response.json()
    assert [job["job_id"] for job in payload["jobs"]] == ["job-complete"]

@pytest.mark.asyncio
async def test_data_upload_endpoint(authenticated_client: AsyncClient) -> None:
    """Test data upload endpoint."""
    files = {"file": ("test.csv", b"id,value\n1,100\n2,200", "text/csv")}
    response = await authenticated_client.post("/api/data/upload-data", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "dataset_id" in data
    assert data["status"] == "uploaded"
    assert data["row_count"] == 2
    assert data["column_count"] == 2

@pytest.mark.asyncio
async def test_data_upload_json_endpoint(authenticated_client: AsyncClient) -> None:
    """Test JSON upload metadata extraction."""
    files = {
        "file": (
            "test.json",
            b'[{"region":"west","revenue":1000},{"region":"east","revenue":900}]',
            "application/json",
        )
    }
    response = await authenticated_client.post("/api/data/upload-data", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 2
    assert data["column_count"] == 2

@pytest.mark.asyncio
async def test_data_upload_invalid_extension(authenticated_client: AsyncClient) -> None:
    """Test upload with invalid file extension."""
    files = {"file": ("test.txt", b"some text", "text/plain")}
    response = await authenticated_client.post("/api/data/upload-data", files=files)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_data_upload_empty_file(authenticated_client: AsyncClient) -> None:
    """Reject empty uploads."""
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = await authenticated_client.post("/api/data/upload-data", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty"

@pytest.mark.asyncio
async def test_data_upload_oversized_file(
    authenticated_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject uploads that exceed the configured size limit."""
    monkeypatch.setattr(data_routes, "MAX_FILE_SIZE", 8)
    files = {"file": ("big.csv", b"id,value\n1,100\n", "text/csv")}
    response = await authenticated_client.post("/api/data/upload-data", files=files)
    assert response.status_code == 413

@pytest.mark.asyncio
async def test_data_upload_persists_dataset(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    """Persist dataset metadata and the stored file path."""
    files = {"file": ("orders.csv", b"id,amount\n1,10\n2,20\n3,30", "text/csv")}
    response = await authenticated_client.post(
        "/api/data/upload-data?name=orders&description=quarterly",
        files=files,
    )

    assert response.status_code == 200
    payload = response.json()

    result = await test_db.execute(
        select(Dataset).where(Dataset.dataset_id == payload["dataset_id"])
    )
    dataset = result.scalar_one()

    assert dataset.name == "orders"
    assert dataset.description == "quarterly"
    assert dataset.row_count == 3
    assert dataset.column_count == 2
    assert dataset.file_type == "csv"
    assert Path(dataset.file_path).exists()

@pytest.mark.asyncio
async def test_list_datasets(authenticated_client: AsyncClient) -> None:
    """List datasets returns an empty collection before uploads."""
    response = await authenticated_client.get("/api/data/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == []


@pytest.mark.asyncio
async def test_list_datasets_returns_uploaded_data(authenticated_client: AsyncClient) -> None:
    """List datasets returns uploaded records in reverse chronological order."""
    first = await _upload_csv_dataset(authenticated_client, "first.csv", b"id,value\n1,100\n2,200")
    second = await _upload_csv_dataset(authenticated_client, "second.csv", b"id,value\n3,300\n4,400")

    response = await authenticated_client.get("/api/data/datasets?skip=0&limit=10")
    assert response.status_code == 200

    data = response.json()
    assert [item["dataset_id"] for item in data] == [
        second["dataset_id"],
        first["dataset_id"],
    ]
    assert data[0]["name"] == "second"
    assert data[1]["name"] == "first"


@pytest.mark.asyncio
async def test_list_datasets_respects_pagination(authenticated_client: AsyncClient) -> None:
    """List datasets applies offset and limit against the database query."""
    first = await _upload_csv_dataset(authenticated_client, "page-one.csv", b"id,value\n1,100")
    second = await _upload_csv_dataset(authenticated_client, "page-two.csv", b"id,value\n2,200")

    response = await authenticated_client.get("/api/data/datasets?skip=1&limit=1")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["dataset_id"] == first["dataset_id"]
    assert data[0]["dataset_id"] != second["dataset_id"]


@pytest.mark.asyncio
async def test_get_dataset_returns_existing_record(authenticated_client: AsyncClient) -> None:
    """Get dataset returns the persisted dataset metadata."""
    created = await _upload_csv_dataset(authenticated_client, "customers.csv", b"id,value\n1,100\n2,200")

    response = await authenticated_client.get(f"/api/data/datasets/{created['dataset_id']}")
    assert response.status_code == 200

    data = response.json()
    assert data["dataset_id"] == created["dataset_id"]
    assert data["name"] == "customers"
    assert data["row_count"] == 2
    assert data["column_count"] == 2


@pytest.mark.asyncio
async def test_get_dataset_returns_404_for_unknown_id(authenticated_client: AsyncClient) -> None:
    """Get dataset returns 404 when the identifier does not exist."""
    response = await authenticated_client.get("/api/data/datasets/ds-missing123456")
    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset ds-missing123456 not found"


@pytest.mark.asyncio
async def test_delete_dataset_removes_record_and_file(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    """Delete dataset removes the DB row and the stored upload from disk."""
    created = await _upload_csv_dataset(authenticated_client, "archive.csv", b"id,value\n1,100\n2,200")

    result = await test_db.execute(
        select(Dataset).where(Dataset.dataset_id == created["dataset_id"])
    )
    dataset = result.scalar_one()
    stored_path = Path(dataset.file_path)
    assert stored_path.exists()

    response = await authenticated_client.delete(f"/api/data/datasets/{created['dataset_id']}")
    assert response.status_code == 204
    assert response.content == b""

    result = await test_db.execute(
        select(Dataset).where(Dataset.dataset_id == created["dataset_id"])
    )
    assert result.scalar_one_or_none() is None
    assert not stored_path.exists()


@pytest.mark.asyncio
async def test_delete_dataset_returns_404_for_unknown_id(
    authenticated_client: AsyncClient,
) -> None:
    """Delete dataset returns 404 when the identifier does not exist."""
    response = await authenticated_client.delete("/api/data/datasets/ds-missing123456")
    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset ds-missing123456 not found"

@pytest.mark.asyncio
async def test_metrics_endpoint(async_client: AsyncClient) -> None:
    """Test Prometheus metrics endpoint."""
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_openapi_docs(async_client: AsyncClient) -> None:
    """Test OpenAPI documentation endpoint."""
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
