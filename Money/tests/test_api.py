"""
API endpoint tests for HVAC AI Dispatch.
Tests: /health, /dispatch, /run/{id}, /dispatches, /admin, /sms
"""

import os

os.environ["SKIP_TWILIO_VALIDATION"] = "true"


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "time" in data
        assert data["api_key_configured"] is True


class TestDispatch:
    def test_dispatch_requires_auth(self, client):
        r = client.post("/dispatch", json={"customer_message": "AC broken"})
        assert r.status_code == 401

    def test_dispatch_rejects_empty_message(self, client, api_headers):
        r = client.post("/dispatch", json={"customer_message": ""}, headers=api_headers)
        assert r.status_code == 422

    def test_dispatch_rejects_extreme_temp(self, client, api_headers):
        r = client.post("/dispatch", json={"customer_message": "AC broken", "outdoor_temp_f": 999}, headers=api_headers)
        assert r.status_code == 422

    def test_dispatch_sync_success(self, client, api_headers):
        r = client.post("/dispatch", json={"customer_message": "AC not cooling", "outdoor_temp_f": 95.0}, headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "complete"
        assert "run_id" in data

    def test_dispatch_async_returns_queued(self, client, api_headers):
        r = client.post("/dispatch", json={"customer_message": "Routine checkup", "async_mode": True}, headers=api_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "queued"


class TestGetRun:
    def test_get_run_requires_auth(self, client):
        r = client.get("/run/nonexistent")
        assert r.status_code == 401

    def test_get_run_not_found(self, client, api_headers):
        r = client.get("/run/nonexistent-id", headers=api_headers)
        assert r.status_code == 404

    def test_get_run_after_dispatch(self, client, api_headers):
        # Create a dispatch first
        dr = client.post("/dispatch", json={"customer_message": "AC broken"}, headers=api_headers)
        run_id = dr.json()["run_id"]
        # Retrieve it
        r = client.get(f"/run/{run_id}", headers=api_headers)
        assert r.status_code == 200
        assert r.json()["run_id"] == run_id


class TestDispatches:
    def test_dispatches_requires_auth(self, client):
        r = client.get("/dispatches")
        assert r.status_code == 401

    def test_dispatches_returns_list(self, client, api_headers):
        r = client.get("/dispatches", headers=api_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestFrontendApp:
    def test_root_returns_html(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")


class TestSmsWebhook:
    def test_sms_returns_twiml(self, client):
        r = client.post("/sms", data={"From": "+15551234567", "Body": "AC broken", "MessageSid": "SM123", "To": "+15559876543"})
        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "")
        assert "<Response>" in r.text

    def test_sms_rate_limit_per_phone(self, client):
        data = {"From": "+15550001111", "Body": "test", "MessageSid": "SM1", "To": "+15559876543"}
        r1 = client.post("/sms", data=data)
        assert r1.status_code == 200
        # Second request within 5s from same number → should get empty TwiML
        r2 = client.post("/sms", data=data)
        assert r2.status_code == 200
        # The rate-limited response has empty body in TwiML
        assert "<Message>" not in r2.text or r2.text.count("<Message>") == 0


class TestSecurityHeaders:
    def test_hsts_header(self, client):
        r = client.get("/health")
        assert "strict-transport-security" in r.headers

    def test_x_content_type_options(self, client):
        r = client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        r = client.get("/health")
        assert r.headers.get("x-frame-options") == "DENY"
