from __future__ import annotations

import json

import pytest

from lead_queue import LeadQueueDB, LeadUpsertPayload


def _seed(db: LeadQueueDB, slug: str = "acme-houston-examplecom") -> None:
    db.upsert_lead(
        LeadUpsertPayload(
            lead_slug=slug,
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


def test_init_and_transitions(temp_db_path: str) -> None:
    db = LeadQueueDB(temp_db_path)
    db.init_db()
    _seed(db)

    assert db.funnel_counts()["scouted"] == 1
    db.set_status("acme-houston-examplecom", "qualified")
    db.set_status("acme-houston-examplecom", "built")
    db.set_status("acme-houston-examplecom", "approved")
    db.set_status("acme-houston-examplecom", "deployed")
    db.set_status("acme-houston-examplecom", "emailed")
    db.record_reply("acme-houston-examplecom", subject="yes", body_excerpt="send live", intent="positive")
    db.set_status("acme-houston-examplecom", "replied")

    funnel = db.funnel_counts()
    assert funnel["replied"] == 1
    timeline = db.lead_timeline("acme-houston-examplecom")
    assert any(e["event_type"] == "status_changed" and e["to_status"] == "qualified" for e in timeline)


def test_illegal_transition_rejected(temp_db_path: str) -> None:
    db = LeadQueueDB(temp_db_path)
    db.init_db()
    _seed(db)
    with pytest.raises(ValueError):
        db.set_status("acme-houston-examplecom", "deployed")


def test_webhook_idempotency_and_economics(temp_db_path: str) -> None:
    db = LeadQueueDB(temp_db_path)
    db.init_db()
    _seed(db)
    for st in ["qualified", "built", "approved", "deployed", "emailed"]:
        db.set_status("acme-houston-examplecom", st)
    oid = db.record_outreach_draft(
        "acme-houston-examplecom",
        "Subject",
        "Body " * 30,
        to_email="hello@example.com",
        body_html="<p>Body</p>",
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
    payload = {
        "event_id": "evt-1",
        "event_type": "outreach.sent",
        "lead_slug": "acme-houston-examplecom",
        "outreach_id": oid,
        "external_ref": "mail-1",
    }
    first = db.apply_webhook_event("openclaw", payload)
    second = db.apply_webhook_event("openclaw", payload)
    assert first["ok"] is True
    assert second["duplicate"] is True
    assert db.funnel_counts()["emailed"] == 1

    db.apply_webhook_event("openclaw", {
        "event_id": "evt-2",
        "event_type": "lead.replied",
        "lead_slug": "acme-houston-examplecom",
        "external_ref": "reply-1",
        "intent": "positive",
    })
    db.apply_webhook_event("openclaw", {
        "event_id": "evt-3",
        "event_type": "deal.won",
        "lead_slug": "acme-houston-examplecom",
        "deal_value_cents": 550000,
    })

    econ = db.economics_summary()
    assert econ["won_deals"] == 1
    assert econ["won_revenue_cents"] == 550000
    verticals = db.conversion_by_vertical()
    assert verticals and verticals[0]["vertical"] == "plumbing"


def test_disqualification_path(temp_db_path: str) -> None:
    db = LeadQueueDB(temp_db_path)
    db.init_db()
    _seed(db)
    db.set_status("acme-houston-examplecom", "disqualified")
    assert db.funnel_counts()["disqualified"] == 1
    with pytest.raises(ValueError):
        db.set_status("acme-houston-examplecom", "qualified")
    timeline = db.lead_timeline("acme-houston-examplecom")
    assert any(e["event_type"] == "status_changed" and e["to_status"] == "disqualified" for e in timeline)


def test_deal_lost_webhook(temp_db_path: str) -> None:
    db = LeadQueueDB(temp_db_path)
    db.init_db()
    _seed(db)
    for st in ["qualified", "built", "approved", "deployed", "emailed"]:
        db.set_status("acme-houston-examplecom", st)
    db.record_reply("acme-houston-examplecom", subject="no", body_excerpt="not interested", intent="negative")
    db.set_status("acme-houston-examplecom", "replied")
    r1 = db.apply_webhook_event("openclaw", {
        "event_id": "evt-lost-1",
        "event_type": "deal.lost",
        "lead_slug": "acme-houston-examplecom",
    })
    assert r1["ok"] is True
    econ = db.economics_summary()
    assert econ["lost_deals"] == 1
    r2 = db.apply_webhook_event("openclaw", {
        "event_id": "evt-lost-1",
        "event_type": "deal.lost",
        "lead_slug": "acme-houston-examplecom",
    })
    assert r2["duplicate"] is True


def test_deployment_failed_webhook(temp_db_path: str) -> None:
    db = LeadQueueDB(temp_db_path)
    db.init_db()
    _seed(db)
    for st in ["qualified", "built", "approved"]:
        db.set_status("acme-houston-examplecom", st)
    r = db.apply_webhook_event("openclaw", {
        "event_id": "evt-fail-1",
        "event_type": "deployment.failed",
        "lead_slug": "acme-houston-examplecom",
        "provider": "openclaw",
        "error": "timeout",
    })
    assert r["ok"] is True
    with db.tx() as con:
        dep = con.execute(
            """
            SELECT d.success, d.provider
              FROM deployments d
              JOIN leads l ON l.id = d.lead_id
             WHERE l.lead_slug = ?
             ORDER BY d.id DESC
             LIMIT 1
            """,
            ("acme-houston-examplecom",),
        ).fetchone()
    assert dep is not None
    assert int(dep["success"]) == 0
    assert dep["provider"] == "openclaw"
    lead = db.get_lead("acme-houston-examplecom")
    assert lead["pipeline_status"] == "approved"
    timeline = db.lead_timeline("acme-houston-examplecom")
    assert any(e["event_type"] == "deployment_recorded" and e["payload_json"].get("success") is False for e in timeline)
