"""High-yield coverage tests for B-A-P helpers and lifecycle paths."""

from __future__ import annotations

from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
import polars as pl
import pytest
from fastapi import HTTPException
from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routes import analytics as analytics_routes
from src.core import event_bus as event_bus_module
from src.core import datasets as dataset_helpers
from src import main as main_module
from tests.test_api import _seed_processed_dataset


def _build_workbook_bytes(rows: list[list[Any]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def test_dataset_helpers_cover_json_payload_variants_and_trim() -> None:
    upload_path = dataset_helpers.build_upload_path(Path("/tmp/uploads"), "ds-123", "sales.JSON")
    assert upload_path == Path("/tmp/uploads/ds-123.json")

    list_frame = dataset_helpers._frame_from_json_payload([1, 2, 3])
    dict_frame = dataset_helpers._frame_from_json_payload({"revenue": [100, 200]})
    record_frame = dataset_helpers._frame_from_json_payload({"region": "north", "revenue": 100})
    scalar_frame = dataset_helpers._frame_from_json_payload("north")

    assert list_frame.to_dicts() == [{"value": 1}, {"value": 2}, {"value": 3}]
    assert dict_frame.to_dicts() == [{"revenue": 100}, {"revenue": 200}]
    assert record_frame.to_dicts() == [{"region": "north", "revenue": 100}]
    assert scalar_frame.to_dicts() == [{"value": "north"}]
    assert dataset_helpers._trim_trailing_empty_cells(["name", None, "", None]) == ["name"]


def test_dataset_helpers_cover_xlsx_and_load_variants(tmp_path: Path) -> None:
    xlsx_bytes = _build_workbook_bytes(
        [
            ["customer", "revenue", None],
            ["north", 1200, None],
            ["south", 900, "extra"],
            [None, None, None],
        ]
    )

    inspection = dataset_helpers.inspect_dataset("customers.xlsx", xlsx_bytes)
    assert inspection.row_count == 2
    assert inspection.column_count == 3
    assert inspection.columns == ["customer", "revenue", "column_3"]
    assert inspection.file_type == "xlsx"

    xlsx_path = tmp_path / "customers.xlsx"
    xlsx_path.write_bytes(xlsx_bytes)
    xlsx_frame = dataset_helpers.load_dataset_frame(xlsx_path, "xlsx")
    assert xlsx_frame.to_dicts() == [
        {"customer": "north", "revenue": 1200, "column_3": None},
        {"customer": "south", "revenue": 900, "column_3": "extra"},
    ]

    csv_path = tmp_path / "metrics.csv"
    csv_path.write_text("id,value\n1,10\n2,20\n", encoding="utf-8")
    assert dataset_helpers.load_dataset_frame(csv_path, "csv").height == 2

    json_path = tmp_path / "metrics.json"
    json_path.write_text('[{"region":"west","value":10}]', encoding="utf-8")
    assert dataset_helpers.load_dataset_frame(json_path, "json").to_dicts() == [
        {"region": "west", "value": 10}
    ]

    parquet_path = tmp_path / "metrics.parquet"
    pl.DataFrame([{"id": 1, "value": 10}]).write_parquet(parquet_path)
    assert dataset_helpers.load_dataset_frame(parquet_path, "parquet").to_dicts() == [
        {"id": 1, "value": 10}
    ]


def test_dataset_helpers_reject_unsupported_types(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported dataset file type"):
        dataset_helpers.inspect_dataset("notes.txt", b"hello")

    unsupported_path = tmp_path / "notes.txt"
    unsupported_path.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported dataset file type"):
        dataset_helpers.load_dataset_frame(unsupported_path, "txt")


@pytest.mark.asyncio
async def test_event_bus_publish_event_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EVENT_BUS_URL", raising=False)
    assert await event_bus_module.publish_event("document.processed", {"dataset_id": "ds-1"}) is None

    captured: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"event_id": "evt-123", "channel": "events:document"}

    class SuccessClient:
        def __init__(self, timeout: float) -> None:
            captured["timeout"] = timeout

        async def __aenter__(self) -> "SuccessClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setenv("EVENT_BUS_URL", "http://event-bus.test")
    monkeypatch.setenv("DEFAULT_TENANT_ID", "tenant-alpha")
    monkeypatch.setattr(event_bus_module.httpx, "AsyncClient", SuccessClient)

    result = await event_bus_module.publish_event(
        "document.processed",
        {"dataset_id": "ds-1"},
        source_service="bap-upload",
    )

    assert result == {"event_id": "evt-123", "channel": "events:document"}
    assert captured["timeout"] == 5.0
    assert captured["url"] == "http://event-bus.test/publish"
    assert captured["json"]["event_type"] == "document.processed"
    assert captured["json"]["tenant_id"] == "tenant-alpha"
    assert captured["json"]["source_service"] == "bap-upload"
    assert captured["json"]["correlation_id"].startswith("document.processed-")

    class ErrorClient(SuccessClient):
        async def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
            raise httpx.ConnectError("boom", request=httpx.Request("POST", url))

    monkeypatch.setattr(event_bus_module.httpx, "AsyncClient", ErrorClient)
    assert await event_bus_module.publish_event("document.processed", {"dataset_id": "ds-1"}) is None


@pytest.mark.asyncio
async def test_analytics_route_functions_cover_success_and_error_paths(
    test_db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _seed_processed_dataset(test_db, dataset_id="direct-analytics")

    summary = await analytics_routes.analytics_summary(dataset_id="direct-analytics", db=test_db)
    preview = await analytics_routes.analytics_preview(
        dataset_id="direct-analytics",
        limit=2,
        db=test_db,
    )
    profile = await analytics_routes.analytics_profile(dataset_id="direct-analytics", db=test_db)

    assert summary.dataset_id == "direct-analytics"
    assert summary.total_records == 3
    assert preview["row_count"] == 3
    assert len(preview["preview"]) == 2
    assert profile["profiles"][0]["column"] == "id"

    analytics_routes._validate_dataset_id("valid-dataset_123")
    with pytest.raises(HTTPException, match="Invalid dataset_id format"):
        analytics_routes._validate_dataset_id("bad@dataset")

    async def broken_processed(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("broken")

    monkeypatch.setattr(analytics_routes, "_get_processed_dataset", broken_processed)

    with pytest.raises(HTTPException, match="Failed to generate analytics summary"):
        await analytics_routes.analytics_summary(dataset_id="direct-analytics", db=test_db)
    with pytest.raises(HTTPException, match="Failed to build preview"):
        await analytics_routes.analytics_preview(dataset_id="direct-analytics", limit=1, db=test_db)
    with pytest.raises(HTTPException, match="Failed to build profile"):
        await analytics_routes.analytics_profile(dataset_id="direct-analytics", db=test_db)

    async def broken_forecast(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("forecast failed")

    monkeypatch.setattr(analytics_routes, "generate_forecast", broken_forecast)
    with pytest.raises(HTTPException, match="Failed to generate forecast"):
        await analytics_routes.analytics_forecast(
            analytics_routes.ForecastRequest(data=[1.0, 2.0], horizon=2)
        )


@pytest.mark.asyncio
async def test_main_lifespan_ready_and_metrics_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSession:
        async def execute(self, statement: Any) -> None:
            events.append(f"execute:{statement}")

    @asynccontextmanager
    async def fake_session() -> Any:
        events.append("session-enter")
        yield FakeSession()
        events.append("session-exit")

    async def fake_create_tables() -> None:
        events.append("create_tables")

    async def fake_connect() -> None:
        events.append("cache_connect")

    async def fake_exists(key: str) -> bool:
        events.append(f"cache_exists:{key}")
        return True

    async def fake_cache_close() -> None:
        events.append("cache_close")

    async def fake_db_close() -> None:
        events.append("db_close")

    monkeypatch.setattr(main_module.db_manager, "create_tables", fake_create_tables)
    monkeypatch.setattr(main_module.cache_manager, "connect", fake_connect)
    monkeypatch.setattr(main_module.db_manager, "session", fake_session)
    monkeypatch.setattr(main_module.cache_manager, "exists", fake_exists)
    monkeypatch.setattr(main_module.cache_manager, "close", fake_cache_close)
    monkeypatch.setattr(main_module.db_manager, "close", fake_db_close)

    async with main_module.lifespan(main_module.app):
        ready = await main_module.ready()
        metrics = await main_module.metrics()

    assert ready == {"status": "ready", "database": "connected", "cache": "connected"}
    assert metrics.media_type == "text/plain"
    assert b"python_gc_objects_collected_total" in metrics.body
    assert events == [
        "create_tables",
        "cache_connect",
        "session-enter",
        "execute:SELECT 1",
        "session-exit",
        "cache_exists:health-check",
        "cache_close",
        "db_close",
    ]


@pytest.mark.asyncio
async def test_main_ready_returns_503_on_dependency_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenSession:
        async def execute(self, statement: Any) -> None:
            raise RuntimeError("db down")

    @asynccontextmanager
    async def broken_session() -> Any:
        yield BrokenSession()

    monkeypatch.setattr(main_module.db_manager, "session", broken_session)

    with pytest.raises(HTTPException, match="Service not ready") as excinfo:
        await main_module.ready()

    assert excinfo.value.status_code == 503
