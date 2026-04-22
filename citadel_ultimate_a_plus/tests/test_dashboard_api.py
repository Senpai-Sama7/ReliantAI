from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from lead_queue import LeadQueueDB, LeadUpsertPayload

API_HEADERS = {"X-API-Key": "secret-123"}


def _setup(monkeypatch, tmp_path: Path):
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.setenv("CITADEL_RATE_LIMIT_API_RPM", "0")
    monkeypatch.setenv("CITADEL_DASHBOARD_API_KEY", API_HEADERS["X-API-Key"])
    monkeypatch.delenv("OPENCLAW_WEBHOOK_SECRET", raising=False)
    db = LeadQueueDB(db_path)
    db.init_db()
    db.upsert_lead(
        LeadUpsertPayload(
            lead_slug="acme-houston-examplecom",
            business_name="Acme Plumbing",
            vertical="plumbing",
            city="Houston",
            state="TX",
            has_website=True,
            website_url="https://example.com",
            phone="713-555-0101",
            email="hello@example.com",
            opportunity_score=8,
            target="https://example.com",
            source_payload_json=json.dumps({"src": "test"}),
        )
    )
    for st in ["qualified", "built"]:
        db.set_status("acme-houston-examplecom", st)
    db.record_outreach_draft(
        "acme-houston-examplecom",
        "Subject",
        "Body " * 30,
        to_email="hello@example.com",
        body_html="<p>Body</p>",
        compliance_footer="Footer text for compliance.",
        beat_audit={
            "pattern_break": "x" * 12,
            "cost_of_inaction": "x" * 12,
            "belief_shift": "x" * 12,
            "mechanism": "x" * 12,
            "proof_unit": "x" * 12,
            "offer": "x" * 12,
            "action": "x" * 8,
        },
    )
    import dashboard_app
    importlib.reload(dashboard_app)
    return TestClient(dashboard_app.app)


def _setup_rate_limited(monkeypatch, tmp_path: Path, *, api_rpm: str = "60", webhook_rpm: str = "30") -> TestClient:
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.setenv("CITADEL_RATE_LIMIT_API_RPM", api_rpm)
    monkeypatch.setenv("CITADEL_RATE_LIMIT_WEBHOOK_RPM", webhook_rpm)
    monkeypatch.setenv("OPENCLAW_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("CITADEL_DASHBOARD_API_KEY", API_HEADERS["X-API-Key"])
    LeadQueueDB(db_path).init_db()
    import dashboard_app
    importlib.reload(dashboard_app)
    return TestClient(dashboard_app.app)


def test_funnel(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/funnel", headers=API_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {
        "scouted",
        "qualified",
        "built",
        "approved",
        "deployed",
        "emailed",
        "replied",
        "disqualified",
    }
    assert all(isinstance(v, int) for v in data.values())


def test_verticals(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/verticals", headers=API_HEADERS)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert any(row.get("vertical") == "plumbing" for row in rows)


def test_leads(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/leads", headers=API_HEADERS)
    assert r.status_code == 200
    leads = r.json()
    assert len(leads) >= 1
    assert any(lead.get("lead_slug") == "acme-houston-examplecom" for lead in leads)
    r2 = c.get("/api/leads?limit=1", headers=API_HEADERS)
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_economics(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/economics", headers=API_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert {
        "total_leads",
        "won_deals",
        "lost_deals",
        "won_revenue_cents",
        "avg_won_deal_cents",
        "reply_to_close_rate",
    } <= set(data.keys())


def test_beat_compliance(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/beat-compliance", headers=API_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "total_outreach_drafts" in data
    assert "field_presence_rate" in data


def test_timeline(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/lead/acme-houston-examplecom/timeline", headers=API_HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_timeline_not_found(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/lead/nonexistent-slug-here/timeline", headers=API_HEADERS)
    assert r.status_code == 404


def test_timeline_invalid_slug_segment_returns_422(monkeypatch, tmp_path: Path) -> None:
    c = _setup(monkeypatch, tmp_path)
    r = c.get("/api/lead/ab/timeline", headers=API_HEADERS)
    assert r.status_code == 422


def test_read_endpoints_fail_closed_when_dashboard_key_missing(monkeypatch, tmp_path: Path) -> None:
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.setenv("CITADEL_RATE_LIMIT_API_RPM", "0")
    monkeypatch.delenv("CITADEL_DASHBOARD_API_KEY", raising=False)
    monkeypatch.delenv("OPENCLAW_WEBHOOK_SECRET", raising=False)
    LeadQueueDB(db_path).init_db()
    import dashboard_app
    importlib.reload(dashboard_app)
    c = TestClient(dashboard_app.app)

    response = c.get("/api/funnel")
    assert response.status_code == 503
    assert response.json()["detail"] == "CITADEL_DASHBOARD_API_KEY is not configured"


def test_api_key_protection(monkeypatch, tmp_path: Path) -> None:
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.setenv("CITADEL_DASHBOARD_API_KEY", "secret-123")
    monkeypatch.setenv("CITADEL_RATE_LIMIT_API_RPM", "0")
    monkeypatch.delenv("OPENCLAW_WEBHOOK_SECRET", raising=False)
    LeadQueueDB(db_path).init_db()
    import dashboard_app
    importlib.reload(dashboard_app)
    c = TestClient(dashboard_app.app)
    assert c.get("/api/funnel").status_code == 401
    assert c.get("/api/funnel", headers={"X-API-Key": "secret-123"}).status_code == 200


def test_rate_limit_read_endpoint_blocks_61st_request(monkeypatch, tmp_path: Path) -> None:
    c = _setup_rate_limited(monkeypatch, tmp_path, api_rpm="60", webhook_rpm="30")
    for _ in range(60):
        assert c.get("/api/funnel", headers=API_HEADERS).status_code == 200
    r = c.get("/api/funnel", headers=API_HEADERS)
    assert r.status_code == 429
    assert r.json()["detail"] == "Rate limit exceeded"


def test_rate_limit_webhook_blocks_31st_request(monkeypatch, tmp_path: Path) -> None:
    c = _setup_rate_limited(monkeypatch, tmp_path, api_rpm="60", webhook_rpm="30")
    # API traffic should not consume webhook quota.
    for _ in range(30):
        assert c.get("/api/funnel", headers=API_HEADERS).status_code == 200
    for _ in range(30):
        r = c.post("/api/webhooks/openclaw", data=b"{}", headers={"Content-Type": "application/json"})
        assert r.status_code == 400
    r = c.post("/api/webhooks/openclaw", data=b"{}", headers={"Content-Type": "application/json"})
    assert r.status_code == 429
    assert r.json()["detail"] == "Rate limit exceeded"
