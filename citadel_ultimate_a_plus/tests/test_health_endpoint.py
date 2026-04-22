from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from lead_queue import LeadQueueDB


def test_health_returns_ok(monkeypatch, tmp_path: Path) -> None:
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.delenv("CITADEL_DASHBOARD_API_KEY", raising=False)
    monkeypatch.delenv("OPENCLAW_WEBHOOK_SECRET", raising=False)
    LeadQueueDB(db_path).init_db()
    import dashboard_app
    importlib.reload(dashboard_app)
    client = TestClient(dashboard_app.app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_no_api_key_required(monkeypatch, tmp_path: Path) -> None:
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.setenv("CITADEL_DASHBOARD_API_KEY", "secret-key-123")
    monkeypatch.delenv("OPENCLAW_WEBHOOK_SECRET", raising=False)
    LeadQueueDB(db_path).init_db()
    import dashboard_app
    importlib.reload(dashboard_app)
    client = TestClient(dashboard_app.app)
    # No X-API-Key header — should still return 200
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_default_no_cors_headers_when_origins_unset(monkeypatch, tmp_path: Path) -> None:
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.delenv("CITADEL_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("CITADEL_DASHBOARD_API_KEY", "secret-key-123")
    monkeypatch.delenv("OPENCLAW_WEBHOOK_SECRET", raising=False)
    LeadQueueDB(db_path).init_db()
    import dashboard_app
    importlib.reload(dashboard_app)
    client = TestClient(dashboard_app.app)

    r = client.get("/api/funnel", headers={"Origin": "https://example.com", "X-API-Key": "secret-key-123"})
    assert r.status_code == 200
    assert "access-control-allow-origin" not in r.headers
