from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from lead_queue import LeadQueueDB, LeadUpsertPayload
from tests.conftest import sign_webhook


def _seed(db_path: str) -> None:
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
    for st in ["qualified", "built", "approved"]:
        db.set_status("acme-houston-examplecom", st)
    db.record_outreach_draft(
        "acme-houston-examplecom",
        "Subject line",
        "Body " * 30,
        to_email="hello@example.com",
        body_html="<p>Body html content long enough for test</p>",
        compliance_footer="Sent by Test. Mailing address: Humble, TX. Reply stop to opt out.",
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


def _load_app(monkeypatch, tmp_path: Path):
    db_path = str(tmp_path / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.setenv("OPENCLAW_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("OPENCLAW_WEBHOOK_MAX_SKEW_SECONDS", "300")
    monkeypatch.delenv("CITADEL_DASHBOARD_API_KEY", raising=False)
    _seed(db_path)
    import dashboard_app
    importlib.reload(dashboard_app)
    return dashboard_app


def test_webhook_signature_success_and_duplicate(monkeypatch, tmp_path: Path) -> None:
    dashboard_app = _load_app(monkeypatch, tmp_path)
    client = TestClient(dashboard_app.app)

    payload = {
        "event_id": "evt-123",
        "event_type": "deployment.succeeded",
        "lead_slug": "acme-houston-examplecom",
        "provider": "openclaw",
        "live_url": "https://example-deploy.test",
        "preview_url": "file:///tmp/preview.html",
    }
    raw, headers = sign_webhook("test-secret", payload)
    r1 = client.post("/api/webhooks/openclaw", data=raw, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["ok"] is True

    r2 = client.post("/api/webhooks/openclaw", data=raw, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["duplicate"] is True


def test_webhook_signature_rejects_bad_sig(monkeypatch, tmp_path: Path) -> None:
    dashboard_app = _load_app(monkeypatch, tmp_path)
    client = TestClient(dashboard_app.app)

    payload = {"event_id": "evt-1", "event_type": "deal.lost", "lead_slug": "acme-houston-examplecom"}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Citadel-Timestamp": "1",
        "X-Citadel-Signature": "sha256=deadbeef",
    }
    r = client.post("/api/webhooks/openclaw", data=raw, headers=headers)
    assert r.status_code in (400, 401)  # skew and signature are both acceptable reject paths


def test_webhook_rejects_oversized_body(monkeypatch, tmp_path: Path) -> None:
    dashboard_app = _load_app(monkeypatch, tmp_path)
    client = TestClient(dashboard_app.app)
    raw = b"x" * 65537
    r = client.post("/api/webhooks/openclaw", data=raw, headers={"Content-Type": "application/json"})
    assert r.status_code == 413
