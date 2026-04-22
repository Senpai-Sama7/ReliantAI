"""Event-bus integration tests for B-A-P upload and ETL flows."""

from __future__ import annotations

import os

import httpx
import pytest

from src.tasks.celery_app import celery_app


@pytest.mark.asyncio
async def test_upload_sets_event_bus_headers(
    authenticated_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Upload responses expose event-bus metadata when publication succeeds."""

    async def fake_publish_event(*args, **kwargs):
        return {"event_id": "evt-upload", "channel": "events:document"}

    from src.api.routes import data as data_routes

    monkeypatch.setattr(data_routes, "publish_event", fake_publish_event)
    response = await authenticated_client.post(
        "/api/data/upload-data",
        files={"file": ("upload.csv", b"id,value\n1,100\n2,200", "text/csv")},
    )

    assert response.status_code == 200
    assert response.headers["X-EventBus-EventId"] == "evt-upload"
    assert response.headers["X-EventBus-Channel"] == "events:document"


@pytest.mark.asyncio
async def test_pipeline_status_includes_event_bus_metadata(
    authenticated_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Completed pipeline jobs retain event-bus metadata in their persisted result."""

    async def fake_publish_event(*args, **kwargs):
        return {"event_id": "evt-analytics", "channel": "events:analytics"}

    from src.etl import pipeline as etl_pipeline

    monkeypatch.setattr(etl_pipeline, "publish_event", fake_publish_event)
    monkeypatch.setattr(celery_app.conf, "task_always_eager", True, raising=False)

    upload = await authenticated_client.post(
        "/api/data/upload-data",
        files={"file": ("pipeline.csv", b"id,revenue\n1,100\n2,200", "text/csv")},
    )
    assert upload.status_code == 200
    dataset_id = upload.json()["dataset_id"]

    pipeline_response = await authenticated_client.post(
        "/api/pipeline/run",
        json={"dataset_id": dataset_id, "parameters": {}},
    )
    assert pipeline_response.status_code == 200
    job_id = pipeline_response.json()["job_id"]

    status_response = await authenticated_client.get(f"/api/pipeline/status/{job_id}")
    assert status_response.status_code == 200
    result = status_response.json()["result"]
    assert result["event_bus_event_id"] == "evt-analytics"
    assert result["event_bus_channel"] == "events:analytics"


@pytest.mark.asyncio
async def test_live_event_bus_flow(
    authenticated_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise live document and analytics event publication when a bus URL is supplied."""
    live_event_bus_url = os.getenv("LIVE_EVENT_BUS_URL")
    if not live_event_bus_url:
        pytest.skip("Set LIVE_EVENT_BUS_URL to run the live B-A-P event-bus integration test")

    monkeypatch.setenv("EVENT_BUS_URL", live_event_bus_url)
    monkeypatch.setenv("DEFAULT_TENANT_ID", "bap-live")
    monkeypatch.setattr(celery_app.conf, "task_always_eager", True, raising=False)

    upload = await authenticated_client.post(
        "/api/data/upload-data",
        files={"file": ("live.csv", b"id,revenue\n1,100\n2,200", "text/csv")},
    )
    assert upload.status_code == 200
    document_event_id = upload.headers["X-EventBus-EventId"]
    dataset_id = upload.json()["dataset_id"]

    async with httpx.AsyncClient(base_url=live_event_bus_url, timeout=5.0) as event_client:
        document_event = await event_client.get(f"/event/{document_event_id}")
        assert document_event.status_code == 200
        document_payload = document_event.json()
        assert document_payload["metadata"]["event_type"] == "document.processed"
        assert document_payload["metadata"]["tenant_id"] == "bap-live"
        assert document_payload["payload"]["dataset_id"] == dataset_id

        pipeline_response = await authenticated_client.post(
            "/api/pipeline/run",
            json={"dataset_id": dataset_id, "parameters": {}},
        )
        assert pipeline_response.status_code == 200
        job_id = pipeline_response.json()["job_id"]

        status_response = await authenticated_client.get(f"/api/pipeline/status/{job_id}")
        assert status_response.status_code == 200
        analytics_event_id = status_response.json()["result"]["event_bus_event_id"]

        analytics_event = await event_client.get(f"/event/{analytics_event_id}")
        assert analytics_event.status_code == 200
        analytics_payload = analytics_event.json()
        assert analytics_payload["metadata"]["event_type"] == "analytics.recorded"
        assert analytics_payload["payload"]["dataset_id"] == dataset_id
        assert analytics_payload["payload"]["job_id"] == job_id
