"""Coverage-focused tests for Money runtime helpers and uncovered routes."""

from __future__ import annotations

import re
import hashlib
import hmac
import json
import sys
from collections import deque
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import main
from database import save_dispatch


def _build_request(
    *,
    path: str = "/",
    method: str = "GET",
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
) -> Request:
    raw_headers: list[tuple[bytes, bytes]] = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode(), value.encode()))
    if cookies:
        cookie_value = "; ".join(f"{key}={value}" for key, value in cookies.items())
        raw_headers.append((b"cookie", cookie_value.encode()))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": raw_headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "root_path": "",
    }
    return Request(scope)


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def test_get_session_user_rejects_bad_cookie() -> None:
    request = _build_request(cookies={main._SESSION_COOKIE: "not-a-valid-cookie"})
    assert main._get_session_user(request) is None


def test_validate_login_csrf_rejects_invalid_signed_token() -> None:
    token = main._create_login_csrf_token()
    tampered = f"{token[:-1]}x" if token[-1] != "x" else f"{token[:-1]}y"
    assert main._validate_login_csrf_token(tampered, tampered) is False


def test_prune_stores_removes_old_entries_and_stale_counters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "MAX_STORE_SIZE", 2)
    main.job_store.clear()
    main.rate_limit_store.clear()
    main._rate_counters.clear()

    main.job_store.update({"a": {}, "b": {}, "c": {}})
    main.rate_limit_store.update({"a": 1.0, "b": 2.0, "c": 3.0})
    main._rate_counters["fresh"] = deque([190.0])
    main._rate_counters["stale"] = deque([1.0])
    main._rate_counters["empty"] = deque()

    monkeypatch.setattr(main.time, "time", lambda: 200.0)

    main._prune_stores()

    assert len(main.job_store) == 2
    assert len(main.rate_limit_store) == 2
    assert "fresh" in main._rate_counters
    assert "stale" not in main._rate_counters
    assert "empty" not in main._rate_counters


def test_rate_limit_raises_after_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "RATE_LIMIT_COUNT", 2)
    main._rate_counters.clear()

    main._rate_limit("dispatch:test")
    main._rate_limit("dispatch:test")

    with pytest.raises(HTTPException) as exc_info:
        main._rate_limit("dispatch:test")

    assert exc_info.value.status_code == 429


def test_authorize_request_accepts_session_cookie(session_cookies: dict[str, str]) -> None:
    request = _build_request(cookies=session_cookies)
    assert main._authorize_request(None, request) is None


def test_authorize_request_returns_503_when_api_key_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "DISPATCH_API_KEY", "change-me-in-env")
    request = _build_request()

    with pytest.raises(HTTPException) as exc_info:
        main._authorize_request("supplied-key", request)

    assert exc_info.value.status_code == 503


def test_publish_dispatch_completed_event_returns_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            captured["raised"] = True

        def json(self) -> dict[str, str]:
            return {"event_id": "evt-123", "channel": "dispatch-events"}

    def fake_post(url: str, json: dict[str, object], timeout: int) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("EVENT_BUS_URL", "http://event-bus.local")
    monkeypatch.setenv("DEFAULT_TENANT_ID", "tenant-zeta")
    monkeypatch.setenv("MONEY_SERVICE_NAME", "money-api")
    monkeypatch.setattr(main.requests, "post", fake_post)

    result = main._publish_dispatch_completed_event("dispatch-1", {"status": "ok"})

    assert result == {"event_id": "evt-123", "channel": "dispatch-events"}
    assert captured["url"] == "http://event-bus.local/publish"
    assert captured["timeout"] == 5
    assert captured["raised"] is True
    assert captured["json"] == {
        "event_type": "dispatch.completed",
        "payload": {
            "dispatch_id": "dispatch-1",
            "status": "complete",
            "result": {"status": "ok"},
        },
        "correlation_id": "dispatch-1",
        "tenant_id": "tenant-zeta",
        "source_service": "money-api",
    }


def test_twilio_skip_disallowed_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_TWILIO_VALIDATION", "true")
    monkeypatch.setattr(main, "ENV", "production")

    with pytest.raises(HTTPException) as exc_info:
        main._twilio_skip_allowed()

    assert exc_info.value.status_code == 403


def test_validate_twilio_signature_uses_forwarded_proto(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeValidator:
        def __init__(self, token: str) -> None:
            captured["token"] = token

        def validate(self, url: str, params: dict[str, str], signature: str) -> bool:
            captured["url"] = url
            captured["params"] = params
            captured["signature"] = signature
            return True

    monkeypatch.setattr(main, "RequestValidator", FakeValidator)
    request = _build_request(
        path="/sms",
        headers={
            "X-Twilio-Signature": "sig-123",
            "X-Forwarded-Proto": "https",
        },
    )

    assert main._validate_twilio_signature(request, {"From": "+15550001111"}) is True
    assert captured["token"] == main.TWILIO_TOKEN
    assert captured["url"] == "https://testserver/sms"
    assert captured["signature"] == "sig-123"


def test_execute_job_records_error(monkeypatch: pytest.MonkeyPatch, isolated_runtime: str) -> None:
    import state_machine

    class FakeStateMachine:
        def __init__(self) -> None:
            self.recorded: list[tuple[str, str, str, str | None, dict[str, object]]] = []

        def record_event(
            self,
            dispatch_id: str,
            event_type: str,
            actor: str,
            run_id: str | None = None,
            payload: dict[str, object] | None = None,
        ) -> None:
            self.recorded.append((dispatch_id, event_type, actor, run_id, payload or {}))

    fake_sm = FakeStateMachine()
    status_updates: list[tuple[str, str, dict[str, object]]] = []

    monkeypatch.setattr(main, "_advance_dispatch_workflow", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(main, "update_dispatch_status", lambda dispatch_id, status, result=None: status_updates.append((dispatch_id, status, result or {})))
    monkeypatch.setattr(state_machine, "get_state_machine", lambda: fake_sm)

    main.job_store.clear()
    main.job_store["job-error"] = {"status": "queued", "result": None}

    main._execute_job("job-error", "AC broken", 95.0)

    assert main.job_store["job-error"]["status"] == "error"
    assert status_updates == [("job-error", "error", {"error": "boom"})]
    assert fake_sm.recorded == [
        ("job-error", "error", "system", "job-error", {"error": "boom"}),
    ]


def test_on_startup_handles_warmup_failure(monkeypatch: pytest.MonkeyPatch, isolated_runtime: str) -> None:
    fake_module = ModuleType("hvac_dispatch_crew")

    def warmup_node() -> None:
        raise RuntimeError("warmup boom")

    fake_module.warmup_node = warmup_node
    monkeypatch.setitem(sys.modules, "hvac_dispatch_crew", fake_module)

    main.on_startup()


def test_run_uses_database_fallback(client, api_headers: dict[str, str]) -> None:
    main.job_store.clear()
    save_dispatch(dispatch_id="db-only", issue_summary="Persisted", status="complete")

    response = client.get("/run/db-only", headers=api_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "db-only"
    assert payload["status"] == "complete"


def test_timeline_and_funnel_endpoints(client, api_headers: dict[str, str]) -> None:
    dispatch_response = client.post(
        "/dispatch",
        json={"customer_message": "AC not cooling", "outdoor_temp_f": 100.0},
        headers=api_headers,
    )
    run_id = dispatch_response.json()["run_id"]

    timeline_response = client.get(f"/api/dispatch/{run_id}/timeline", headers=api_headers)
    funnel_response = client.get("/api/dispatch/funnel", headers=api_headers)

    assert timeline_response.status_code == 200
    timeline_payload = timeline_response.json()
    assert timeline_payload["dispatch_id"] == run_id
    assert timeline_payload["event_count"] >= 1
    assert timeline_payload["current_state"] == "dispatched"

    assert funnel_response.status_code == 200
    funnel_payload = funnel_response.json()
    assert funnel_payload["total_dispatches"] >= 1
    assert funnel_payload["state_counts"]["dispatched"] >= 1


def test_sms_invalid_signature_returns_403(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeValidator:
        def __init__(self, token: str) -> None:
            self.token = token

        def validate(self, url: str, params: dict[str, str], signature: str) -> bool:
            return False

    monkeypatch.setenv("SKIP_TWILIO_VALIDATION", "false")
    monkeypatch.setattr(main, "RequestValidator", FakeValidator)

    response = client.post(
        "/sms",
        data={"From": "+15550000001", "Body": "Need AC help", "MessageSid": "SM-invalid", "To": "+15559876543"},
        headers={"X-Twilio-Signature": "bad-signature"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid signature"


def test_whatsapp_success_and_rate_limit(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeValidator:
        def __init__(self, token: str) -> None:
            self.token = token

        def validate(self, url: str, params: dict[str, str], signature: str) -> bool:
            return True

    monkeypatch.setenv("SKIP_TWILIO_VALIDATION", "false")
    monkeypatch.setattr(main, "RequestValidator", FakeValidator)

    data = {"From": "whatsapp:+15550000002", "Body": "Need service", "MessageSid": "WA-1", "To": "whatsapp:+15559876543"}
    headers = {"X-Twilio-Signature": "good-signature"}

    first = client.post("/whatsapp", data=data, headers=headers)
    second = client.post("/whatsapp", data=data, headers=headers)

    assert first.status_code == 200
    assert "<Message>" in first.text
    assert second.status_code == 200
    assert "<Message>" not in second.text


def test_login_redirects_when_session_is_present(client, session_cookies: dict[str, str]) -> None:
    for key, value in session_cookies.items():
        client.cookies.set(key, value)

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/admin"


def test_login_rejects_invalid_credentials(client) -> None:
    login_page = client.get("/login")
    csrf_token = _extract_csrf_token(login_page.text)

    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong-password", "csrf_token": csrf_token},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert "Invalid username or password" in response.text


def test_logout_clears_auth_cookies(client) -> None:
    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(main._SESSION_COOKIE in header for header in set_cookie_headers)
    assert any(main._LOGIN_CSRF_COOKIE in header for header in set_cookie_headers)


def test_legacy_admin_renders_metrics(client, session_cookies: dict[str, str]) -> None:
    for key, value in session_cookies.items():
        client.cookies.set(key, value)

    save_dispatch(dispatch_id="admin-1", customer_phone="+15551110000", issue_summary="Emergency repair", urgency="EMERGENCY", status="complete")
    save_dispatch(dispatch_id="admin-2", customer_phone="", issue_summary="Routine maintenance", urgency="ROUTINE", status="queued")

    response = client.get("/legacy-admin")

    assert response.status_code == 200
    assert "Emergency repair" in response.text
    assert "+15551110000" in response.text
    assert "Routine maintenance" in response.text


def test_integrations_status_uses_connector_status(
    client,
    api_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_integrations = ModuleType("integrations")

    class FakeConnector:
        def check_connection(self) -> dict[str, object]:
            return {"connected": True, "provider": "fake"}

    fake_integrations.SalesIntelligenceConnector = FakeConnector
    monkeypatch.setitem(sys.modules, "integrations", fake_integrations)
    monkeypatch.setenv("HUBSPOT_API_KEY", "hubspot-key")
    monkeypatch.setenv("GOOGLE_SHEETS_ID", "sheet-id")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://slack.example")

    response = client.get("/integrations/status", headers=api_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["sales_intelligence"] == {"connected": True, "provider": "fake"}
    assert payload["hubspot"] == {"connected": True}
    assert payload["google_sheets"] == {"connected": True}
    assert payload["slack"] == {"connected": True}


def test_make_webhook_success_with_signature(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notified: list[dict[str, object]] = []
    fake_integrations = ModuleType("integrations")

    class FakeVerifier:
        def __init__(self, secret: str) -> None:
            self.secret = secret

        def verify(self, raw_body: bytes, timestamp: str, signature: str) -> SimpleNamespace:
            return SimpleNamespace(valid=True, error="", skew_seconds=2)

    class FakeReceiver:
        @staticmethod
        def parse_make_payload(payload: dict[str, object]) -> dict[str, object]:
            return {"sender_email": payload["sender_email"], "lead_score": {"score": 91}}

        @staticmethod
        def validate_webhook(payload: dict[str, object], secret: str) -> bool:
            return True

    class FakeNotificationRouter:
        def route_lead_notification(self, lead_data: dict[str, object]) -> None:
            notified.append(lead_data)

    fake_integrations.WebhookVerifier = FakeVerifier
    fake_integrations.MakeWebhookReceiver = FakeReceiver
    fake_integrations.NotificationRouter = FakeNotificationRouter
    fake_integrations.create_dispatch_from_sales_lead = lambda lead_data: "dispatch-lead-1"
    monkeypatch.setitem(sys.modules, "integrations", fake_integrations)
    monkeypatch.setenv("MAKE_WEBHOOK_SECRET", "super-secret-value")

    response = client.post(
        "/webhooks/make/sales-lead",
        json={"sender_email": "lead@example.com"},
        headers={"x-webhook-timestamp": "1700000000", "x-webhook-signature": "sig"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "received",
        "dispatch_id": "dispatch-lead-1",
        "lead_score": 91,
    }
    assert notified and notified[0]["dispatch_id"] == "dispatch-lead-1"


def test_make_webhook_rejects_invalid_signature(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_integrations = ModuleType("integrations")

    class FakeVerifier:
        def __init__(self, secret: str) -> None:
            self.secret = secret

        def verify(self, raw_body: bytes, timestamp: str, signature: str) -> SimpleNamespace:
            return SimpleNamespace(valid=False, error="bad signature", skew_seconds=0)

    class FakeReceiver:
        @staticmethod
        def parse_make_payload(payload: dict[str, object]) -> dict[str, object]:
            return payload

        @staticmethod
        def validate_webhook(payload: dict[str, object], secret: str) -> bool:
            return True

    class FakeNotificationRouter:
        def route_lead_notification(self, lead_data: dict[str, object]) -> None:
            return None

    fake_integrations.WebhookVerifier = FakeVerifier
    fake_integrations.MakeWebhookReceiver = FakeReceiver
    fake_integrations.NotificationRouter = FakeNotificationRouter
    fake_integrations.create_dispatch_from_sales_lead = lambda lead_data: "unused"
    monkeypatch.setitem(sys.modules, "integrations", fake_integrations)
    monkeypatch.setenv("MAKE_WEBHOOK_SECRET", "super-secret-value")

    response = client.post(
        "/webhooks/make/sales-lead",
        json={"sender_email": "lead@example.com"},
        headers={"x-webhook-timestamp": "1700000000", "x-webhook-signature": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook: bad signature"


def test_make_webhook_rejects_when_secret_missing(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_integrations = ModuleType("integrations")

    class FakeReceiver:
        @staticmethod
        def parse_make_payload(payload: dict[str, object]) -> dict[str, object]:
            return payload

        @staticmethod
        def validate_webhook(payload: dict[str, object], secret: str) -> bool:
            return False

    class FakeVerifier:
        def __init__(self, secret: str) -> None:
            self.secret = secret

        def verify(self, raw_body: bytes, timestamp: str, signature: str) -> SimpleNamespace:
            return SimpleNamespace(valid=True, error="", skew_seconds=0)

    class FakeNotificationRouter:
        def route_lead_notification(self, lead_data: dict[str, object]) -> None:
            return None

    fake_integrations.MakeWebhookReceiver = FakeReceiver
    fake_integrations.WebhookVerifier = FakeVerifier
    fake_integrations.NotificationRouter = FakeNotificationRouter
    fake_integrations.create_dispatch_from_sales_lead = lambda lead_data: "unused"
    monkeypatch.setitem(sys.modules, "integrations", fake_integrations)
    monkeypatch.delenv("MAKE_WEBHOOK_SECRET", raising=False)

    response = client.post("/webhooks/make/sales-lead", json={"sender_email": "lead@example.com"})

    assert response.status_code == 503
    assert response.json()["detail"] == "MAKE_WEBHOOK_SECRET is not configured"


def test_hubspot_webhook_acknowledges(client) -> None:
    response = client.post("/webhooks/hubspot/contact-updated", json={"eventId": "evt-1"})

    assert response.status_code == 503
    assert response.json()["detail"] == "HUBSPOT_WEBHOOK_SECRET is not configured"


def test_hubspot_webhook_requires_valid_signature(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "super-secret-hubspot-key"
    payload = {"eventId": "evt-1"}
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    monkeypatch.setenv("HUBSPOT_WEBHOOK_SECRET", secret)

    response = client.post(
        "/webhooks/hubspot/contact-updated",
        content=body,
        headers={
            "content-type": "application/json",
            "x-hubspot-signature": signature,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "acknowledged"}


def test_root_serves_built_index_when_present(
    client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    (tmp_path / "index.html").write_text("<html><body>built frontend</body></html>", encoding="utf-8")
    monkeypatch.setattr(main, "frontend_dist", str(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "built frontend" in response.text
