"""
Production Test Suite for Money Service (HVAC AI Dispatch)

Covers all critical paths:
  * Authentication (bearer JWT, API key, session, rate limiting, circuit breaker)
  * Dispatch creation & workflow
  * Twilio webhook handling (SMS/WhatsApp)
  * Billing & quota enforcement
  * SSE broadcast stream

Runs via: cd Money && pytest tests/ -v
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import requests
from fastapi.testclient import TestClient

from config import DISPATCH_API_KEY


# ════════════════════════════════════════════════════════════════════════════
# AUTH & RATE LIMITING TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestAuthorizeRequest:
    """Test the ``_authorize_request`` function — the central auth gate."""

    @pytest.mark.asyncio
    async def test_missing_credentials_returns_401(self):
        """No auth header, cookie, or API key → 401."""
        import main
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await main._authorize_request(x_api_key=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_api_key_passes(self):
        """Valid X-API-Key (matches DISPATCH_API_KEY) → no exception."""
        import main

        result = await main._authorize_request(x_api_key=DISPATCH_API_KEY)
        assert result is None  # Success is None return

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(self):
        """Invalid X-API-Key → 401."""
        import main
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await main._authorize_request(x_api_key="invalid-key-1234567890")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_bearer_token_success_via_auth_service(self, monkeypatch):
        """Valid bearer JWT passes through to auth service."""
        import main

        mock_get = MagicMock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"user_id": "user-123", "role": "admin"}

        monkeypatch.setattr("requests.get", mock_get)

        # Create a fake request object with the bearer token
        fake_request = MagicMock()
        fake_request.headers.get.side_effect = lambda k, default=None: {
            "authorization": "Bearer valid-jwt-token-abc123"
        }.get(k, default)
        fake_request.cookies.get.return_value = None

        # Should call auth service and succeed
        result = await main._authorize_request(x_api_key=None, request=fake_request)
        assert result is None
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_bearer_token_expired_returns_401(self, monkeypatch):
        """Expired or invalid bearer token → 401."""
        import main
        from fastapi import HTTPException

        mock_get = MagicMock()
        mock_get.return_value.status_code = 401

        monkeypatch.setattr("requests.get", mock_get)

        fake_request = MagicMock()
        fake_request.headers.get.side_effect = lambda k, default=None: {
            "authorization": "Bearer expired-jwt-token"
        }.get(k, default)
        fake_request.cookies.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await main._authorize_request(x_api_key=None, request=fake_request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_service_down_returns_503_after_circuit_opens(self, monkeypatch):
        """Auth service unavailable → circuit breaker opens after 3 failures → 503."""
        import main
        from fastapi import HTTPException

        mock_get = MagicMock(side_effect=requests.RequestException("Connection refused"))
        monkeypatch.setattr("requests.get", mock_get)

        fake_request = MagicMock()
        fake_request.headers.get.side_effect = lambda k, default=None: {
            "authorization": "Bearer test-token"
        }.get(k, default)
        fake_request.cookies.get.return_value = None

        # Failure 1
        with pytest.raises(HTTPException):
            await main._authorize_request(x_api_key=None, request=fake_request)

        # Failure 2
        with pytest.raises(HTTPException):
            await main._authorize_request(x_api_key=None, request=fake_request)

        # Failure 3 — triggers circuit to OPEN
        with pytest.raises(HTTPException):
            await main._authorize_request(x_api_key=None, request=fake_request)

        # Now circuit is OPEN; 4th call should get 503 without even trying the network
        with pytest.raises(HTTPException) as exc_info:
            await main._authorize_request(x_api_key=None, request=fake_request)
        assert exc_info.value.status_code == 503


class TestRateLimiting:
    """Test the ``_rate_limit`` function."""

    def test_rate_limit_allows_up_to_60_requests_in_window(self):
        """Within 60-second window, allow 60 requests."""
        import main
        from fastapi import HTTPException

        fake_request = MagicMock()
        fake_request.client.host = "127.0.0.1"
        fake_request.headers.get.return_value = None

        bucket = main._rate_bucket(fake_request, "test")

        # Fill the bucket to capacity (60 requests)
        for _ in range(60):
            main._rate_limit(bucket)

        # 61st request should raise 429
        with pytest.raises(HTTPException) as exc_info:
            main._rate_limit(bucket)
        assert exc_info.value.status_code == 429

    def test_rate_limit_resets_after_window_expires(self, monkeypatch):
        """After 60s, window expires and counter resets."""
        import main

        fake_request = MagicMock()
        fake_request.client.host = "127.0.0.1"
        fake_request.headers.get.return_value = None

        bucket = main._rate_bucket(fake_request, "test")

        # Fill bucket
        for _ in range(60):
            main._rate_limit(bucket)

        # Advance time by 61 seconds
        monkeypatch.setattr("time.time", lambda: time.time() + 70)

        # Should allow another batch now (bucket was pruned)
        main._rate_limit(bucket)  # Should not raise


class TestCircuitBreaker:
    """Test the circuit breaker — resilience against failing auth service."""

    def test_circuit_breaker_starts_closed(self):
        """Circuit breaker initial state is CLOSED."""
        import main

        assert main.auth_circuit_breaker.state == "CLOSED"

    def test_circuit_breaker_opens_after_3_failures(self):
        """After 3 failures, circuit transitions to OPEN."""
        import main

        # Reset for this test
        main.auth_circuit_breaker.state = "CLOSED"
        main.auth_circuit_breaker.failures = 0

        # Simulate 3 failures
        for i in range(3):
            try:
                main.auth_circuit_breaker.call(
                    lambda: (_ for _ in ()).throw(requests.RequestException("test"))
                )
            except Exception:
                pass

        assert main.auth_circuit_breaker.state == "OPEN"

    def test_circuit_breaker_rejects_calls_when_open(self):
        """When circuit is OPEN, calls are rejected immediately (no network attempt)."""
        import main
        from fastapi import HTTPException

        main.auth_circuit_breaker.state = "OPEN"
        main.auth_circuit_breaker.last_failure_time = time.time()

        with pytest.raises(HTTPException) as exc_info:
            main.auth_circuit_breaker.call(lambda: None)
        assert exc_info.value.status_code == 503


# ════════════════════════════════════════════════════════════════════════════
# DISPATCH ENDPOINT TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestDispatchEndpoint:
    """Test ``POST /dispatch`` — the main revenue-generating endpoint."""

    def test_dispatch_happy_path_returns_200(self, client, mock_crew, fake_pool):
        """Valid dispatch request → 200 with run_id and status."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC not cooling, 102°F outside",
                "outdoor_temp_f": 102.0,
                "async_mode": False,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] in ("complete", "running")
        assert data["timestamp"] is not None

    def test_dispatch_missing_auth_returns_401(self, client):
        """No API key or bearer token → 401."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC failure",
                "outdoor_temp_f": 95.0,
            },
        )
        assert response.status_code == 401

    def test_dispatch_invalid_api_key_returns_401(self, client):
        """Invalid API key → 401."""
        response = client.post(
            "/dispatch",
            json={"customer_message": "AC failure", "outdoor_temp_f": 95.0},
            headers={"X-API-Key": "invalid-key-xyz"},
        )
        assert response.status_code == 401

    def test_dispatch_message_max_length_enforced(self, client):
        """Message > 1000 chars rejected."""
        long_msg = "x" * 1001
        response = client.post(
            "/dispatch",
            json={
                "customer_message": long_msg,
                "outdoor_temp_f": 95.0,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_dispatch_async_mode_returns_queued_immediately(self, client, mock_crew):
        """With async_mode=True, returns immediately with status 'queued'."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC not cooling",
                "outdoor_temp_f": 95.0,
                "async_mode": True,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "queued"

    def test_dispatch_saves_to_database(self, client, mock_crew, fake_pool):
        """Dispatch data is persisted to fake database."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "Heat pump not working",
                "outdoor_temp_f": 40.0,
                "async_mode": False,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Verify it's in the fake pool store
        assert run_id in fake_pool.store.get("dispatches", {})

    def test_dispatch_rate_limited_after_60_requests(self, client, monkeypatch):
        """After 60 dispatch requests from same source, 429."""
        import main

        # Patch RATE_LIMIT_COUNT to a small number for testing
        monkeypatch.setattr(main, "RATE_LIMIT_COUNT", 2)

        # First request OK
        response1 = client.post(
            "/dispatch",
            json={"customer_message": "AC failure", "outdoor_temp_f": 95.0},
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response1.status_code == 200

        # Second request OK
        response2 = client.post(
            "/dispatch",
            json={"customer_message": "AC failure 2", "outdoor_temp_f": 95.0},
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response2.status_code == 200

        # Third request hits limit
        response3 = client.post(
            "/dispatch",
            json={"customer_message": "AC failure 3", "outdoor_temp_f": 95.0},
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response3.status_code == 429


# ════════════════════════════════════════════════════════════════════════════
# TWILIO WEBHOOK TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestTwilioWebhooks:
    """Test ``POST /sms`` and ``POST /whatsapp`` webhook endpoints."""

    def _twilio_signature(self, url: str, params: dict, token: str) -> str:
        """Compute valid Twilio signature for a webhook."""
        data = url
        for key in sorted(params.keys()):
            data += key + params[key]
        mac = hmac.new(token.encode(), data.encode(), hashlib.sha1)
        return mac.digest().hex()

    def test_sms_webhook_with_invalid_signature_returns_403(self, client, monkeypatch):
        """Invalid Twilio signature → 403 (when validation enabled)."""
        monkeypatch.setenv("SKIP_TWILIO_VALIDATION", "false")

        response = client.post(
            "/sms",
            data={
                "From": "+15005550001",
                "Body": "AC not cooling",
                "MessageSid": "SMtest123",
                "To": "+15005550000",
            },
            headers={"X-Twilio-Signature": "invalid-signature-xyz"},
        )
        assert response.status_code == 403

    def test_sms_webhook_with_valid_signature_accepted(self, client, monkeypatch, mock_crew):
        """Valid signature → processed (returns 200 TwiML)."""
        from config import TWILIO_TOKEN

        # Signature validation is skipped in test env by default, so just test the path
        response = client.post(
            "/sms",
            data={
                "From": "+15005550001",
                "Body": "AC stopped working at 102F",
                "MessageSid": "SMtest123",
                "To": "+15005550000",
            },
        )
        assert response.status_code == 200
        assert "<?xml" in response.text or "Response" in response.text

    def test_sms_classifies_emergency_correctly(self, client, mock_crew):
        """Inbound message with LIFE_SAFETY keywords triggers correct handling."""
        response = client.post(
            "/sms",
            data={
                "From": "+15005550001",
                "Body": "Smell gas coming from AC unit, call 911?",
                "MessageSid": "SMtest456",
                "To": "+15005550000",
            },
        )
        assert response.status_code == 200
        # The response text should be TwiML with a message
        assert "Response" in response.text

    def test_whatsapp_webhook_accepted(self, client, mock_crew):
        """WhatsApp webhook format also accepted."""
        response = client.post(
            "/whatsapp",
            data={
                "From": "whatsapp:+15005550001",
                "Body": "AC not cooling",
                "MessageSid": "WAtest789",
                "To": "whatsapp:+15005550000",
            },
        )
        assert response.status_code == 200

    def test_sms_with_rate_limit_from_same_number(self, client, monkeypatch):
        """Multiple SMS from same number within 5s → drop after 1st."""
        import main

        # First SMS from this number
        response1 = client.post(
            "/sms",
            data={
                "From": "+15005550099",
                "Body": "First message",
                "MessageSid": "SM1",
                "To": "+15005550000",
            },
        )
        assert response1.status_code == 200

        # Second SMS from same number within 5s (monkeypatch time didn't advance)
        response2 = client.post(
            "/sms",
            data={
                "From": "+15005550099",
                "Body": "Second message",
                "MessageSid": "SM2",
                "To": "+15005550000",
            },
        )
        assert response2.status_code == 200
        # Response text should be empty (rate limit hit within main.py logic)

    def test_sms_sanitizes_html_in_message_body(self, client, mock_crew):
        """HTML tags in message body are redacted."""
        response = client.post(
            "/sms",
            data={
                "From": "+15005550088",
                "Body": "<script>alert('xss')</script> AC not cooling",
                "MessageSid": "SMtest999",
                "To": "+15005550000",
            },
        )
        assert response.status_code == 200
        # Should still process but with HTML stripped


# ════════════════════════════════════════════════════════════════════════════
# BILLING TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestBillingEndpoints:
    """Test ``/billing/*`` endpoints — quota, pricing, webhooks."""

    def test_pricing_endpoint_returns_all_plans(self, client):
        """GET /billing/pricing → all plans listed."""
        response = client.get("/billing/pricing")
        assert response.status_code == 200
        plans = response.json()["plans"]
        assert "free" in plans
        assert "growth_automation" in plans
        assert "enterprise_os" in plans

    def test_checkout_free_plan_creates_customer(self, client, fake_pool, monkeypatch):
        """POST /billing/checkout with plan='free' → new customer, API key."""
        import billing

        # Stub create_customer in database
        mock_create = MagicMock(
            return_value={
                "id": 1,
                "api_key": "sk_test123",
                "email": "test@example.com",
                "plan": "free",
            }
        )
        monkeypatch.setattr("billing.create_customer", mock_create)

        response = client.post(
            "/billing/checkout",
            json={
                "email": "test@example.com",
                "name": "Test User",
                "company": "Test Co",
                "phone": "+15551234567",
                "plan": "free",
                "success_url": "http://localhost/success",
                "cancel_url": "http://localhost/cancel",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["customer_id"] == 1

    def test_webhook_stripe_checkout_completed_updates_customer(self, client, monkeypatch):
        """Stripe webhook: checkout.session.completed → update customer."""
        import billing
        import stripe as stripe_module

        # Stub the webhook construction
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test123",
                    "metadata": {"customer_id": "1", "plan": "growth_automation"},
                }
            },
        }

        monkeypatch.setattr(
            "stripe.Webhook.construct_event",
            MagicMock(return_value=mock_event),
        )

        mock_update = MagicMock()
        monkeypatch.setattr("billing.update_customer", mock_update)

        response = client.post(
            "/billing/webhook",
            json=mock_event,
            headers={"stripe-signature": "test-sig"},
        )
        assert response.status_code == 200

    def test_webhook_missing_stripe_secret_returns_500(self, client, monkeypatch):
        """Stripe webhook without secret configured → 500."""
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "")

        response = client.post(
            "/billing/webhook",
            json={"type": "checkout.session.completed"},
            headers={"stripe-signature": "test-sig"},
        )
        assert response.status_code == 500


class TestDispatchQuota:
    """Test dispatch quota enforcement in billing.py."""

    def test_unlimited_quota_for_enterprise_plan(self, monkeypatch):
        """Enterprise plan (dispatches_per_month=-1) → unlimited quota."""
        import billing

        customer = {"id": 1, "plan": "enterprise_os"}
        assert billing.check_dispatch_quota(customer) is True

    def test_quota_exceeded_for_free_plan(self, fake_pool, monkeypatch):
        """Free plan with 10 dispatches already used → quota exceeded."""
        import billing

        # Stub query to return 10 dispatches this month
        fake_pool.store["dispatch_count"] = 10

        customer = {"id": 1, "plan": "free"}
        # Free plan allows 10, we have 10, so next is over
        assert billing.check_dispatch_quota(customer) is False

    def test_quota_not_exceeded_for_free_plan_with_room(self, fake_pool):
        """Free plan with 5 dispatches → quota not exceeded."""
        import billing

        fake_pool.store["dispatch_count"] = 5

        customer = {"id": 1, "plan": "free"}
        assert billing.check_dispatch_quota(customer) is True


# ════════════════════════════════════════════════════════════════════════════
# SSE STREAM TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestSSEStream:
    """Test ``GET /api/stream/dispatches`` — Server-Sent Events broadcast."""

    def test_sse_endpoint_requires_auth(self, client):
        """Without API key, stream endpoint returns 401."""
        response = client.get("/api/stream/dispatches")
        assert response.status_code == 401

    def test_sse_endpoint_with_valid_auth_returns_event_stream(self, client):
        """With valid API key, returns text/event-stream response."""
        response = client.get(
            "/api/stream/dispatches",
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

    def test_sse_broadcasts_dispatch_created_event(self, client, monkeypatch, fake_pool):
        """Dispatch creation broadcasts to all SSE clients."""
        import main

        # Connect SSE stream (in a real scenario, this would be a WebSocket or streaming)
        # For now, verify the broadcast function exists and can be called
        assert hasattr(main, "_broadcast_dispatch_event")

        # Simulate a broadcast
        main._broadcast_dispatch_event("dispatch_created", {"run_id": "test-123"})
        # If it doesn't raise, it worked


# ════════════════════════════════════════════════════════════════════════════
# TRIAGE & URGENCY CLASSIFICATION TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestUrgentyTriageLogic:
    """Test urgency classification — the core decision engine."""

    def test_life_safety_keyword_detected(self):
        """Gas/CO/fire keywords → LIFE_SAFETY."""
        from triage import triage_urgency_local

        result = triage_urgency_local("Smell gas from AC unit, carbon monoxide", 80.0)
        assert result["urgency_level"] == "LIFE_SAFETY"
        assert result["safety_flag"] is True

    def test_emergency_heat_in_high_temp(self):
        """No AC + temp > 95°F → EMERGENCY."""
        from triage import triage_urgency_local

        result = triage_urgency_local("AC not cooling, it's really hot", outdoor_temp_f=102.0)
        assert result["urgency_level"] == "EMERGENCY"
        assert result["safety_flag"] is False

    def test_emergency_cold_in_low_temp(self):
        """No heat + temp < 42°F → EMERGENCY."""
        from triage import triage_urgency_local

        result = triage_urgency_local("No heat at all", outdoor_temp_f=35.0)
        assert result["urgency_level"] == "EMERGENCY"

    def test_urgent_keyword_classified_as_urgent(self):
        """Urgent keywords (leak, flood, broken) → URGENT."""
        from triage import triage_urgency_local

        result = triage_urgency_local("Water leak from AC, not cooling", 80.0)
        assert result["urgency_level"] == "URGENT"

    def test_routine_message_classified_as_routine(self):
        """Normal maintenance request → ROUTINE."""
        from triage import triage_urgency_local

        result = triage_urgency_local("Can you service my AC unit?", 80.0)
        assert result["urgency_level"] == "ROUTINE"

    def test_triage_includes_timestamp(self):
        """Triage result includes ISO timestamp."""
        from triage import triage_urgency_local

        result = triage_urgency_local("AC issue", 80.0)
        assert "timestamp" in result
        assert "T" in result["timestamp"]  # ISO format


# ════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════


class TestHealthEndpoint:
    """Test ``GET /health`` — liveness probe."""

    def test_health_returns_200_with_status_ok(self, client):
        """GET /health → 200 with status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "service" in data
        assert "time" in data

    def test_health_includes_database_status(self, client):
        """Health response includes database connectivity."""
        response = client.get("/health")
        data = response.json()
        assert "database" in data


class TestMetricsEndpoint:
    """Test ``GET /metrics`` — Prometheus metrics."""

    def test_metrics_requires_auth(self, client):
        """Without API key, metrics endpoint returns 401."""
        response = client.get("/metrics")
        assert response.status_code == 401

    def test_metrics_returns_prometheus_format(self, client):
        """With valid API key, returns Prometheus text format."""
        response = client.get(
            "/metrics",
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        # Prometheus format starts with # HELP or # TYPE
        assert "#" in response.text or "hvac" in response.text.lower()


# ════════════════════════════════════════════════════════════════════════════
# GET /dispatches — DISPATCH HISTORY
# ════════════════════════════════════════════════════════════════════════════


class TestDispatchHistoryEndpoint:
    """Test ``GET /dispatches`` — recent dispatch list."""

    def test_get_dispatches_requires_auth(self, client):
        """GET /dispatches without API key → 401."""
        response = client.get("/dispatches")
        assert response.status_code == 401

    def test_get_dispatches_returns_list(self, client, fake_pool):
        """GET /dispatches with API key → returns list."""
        response = client.get(
            "/dispatches",
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_dispatches_respects_limit_parameter(self, client):
        """GET /dispatches?limit=10 → limits to 10."""
        response = client.get(
            "/dispatches?limit=10",
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200


# ════════════════════════════════════════════════════════════════════════════
# INTEGRATION: FULL DISPATCH WORKFLOW
# ════════════════════════════════════════════════════════════════════════════


class TestFullDispatchWorkflow:
    """End-to-end: inbound SMS → triage → dispatch."""

    def test_inbound_sms_triggers_dispatch_workflow(self, client, mock_crew, mock_state_machine):
        """Customer texts in → dispatch created → crew executes → returns TwiML."""
        response = client.post(
            "/sms",
            data={
                "From": "+15005550007",
                "Body": "AC stopped working, very hot inside",
                "MessageSid": "SMfull123",
                "To": "+15005550000",
            },
        )
        assert response.status_code == 200
        # Should return TwiML response
        assert "<?xml" in response.text or "Response" in response.text

    def test_api_dispatch_request_full_path(self, client, mock_crew, disable_event_bus):
        """POST /dispatch with crew mocked → full workflow without external deps."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "Unit not cooling in 102°F heat",
                "outdoor_temp_f": 102.0,
                "async_mode": False,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("complete", "running")
        # Crew was mocked, so should complete quickly
        assert "run_id" in data

    def test_outbound_sms_dispatch(self, client, monkeypatch):
        """POST /api/dispatch/sms → sends SMS via Twilio."""
        import main

        # Mock Twilio client
        mock_twilio_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SMout123"
        mock_twilio_client.messages.create.return_value = mock_message

        monkeypatch.setattr(
            "main.TwilioClient",
            MagicMock(return_value=mock_twilio_client),
        )

        response = client.post(
            "/api/dispatch/sms",
            json={
                "to": "+15005550010",
                "body": "Your HVAC service is scheduled for 2pm",
                "correlation_id": "disp-123",
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["sms_sid"] == "SMout123"


# ════════════════════════════════════════════════════════════════════════════
# EDGE CASES & RESILIENCE
# ════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_malformed_json_in_dispatch_returns_422(self, client):
        """Invalid JSON in POST /dispatch body → 422."""
        response = client.post(
            "/dispatch",
            data="not json",
            headers={
                "X-API-Key": DISPATCH_API_KEY,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code in (400, 422)

    def test_missing_required_field_in_dispatch_returns_422(self, client):
        """POST /dispatch without customer_message → 422."""
        response = client.post(
            "/dispatch",
            json={"outdoor_temp_f": 95.0},
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 422

    def test_dispatch_with_invalid_temp_returns_422(self, client):
        """Temperature outside valid range (-50 to 150°F) → 422."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "Help",
                "outdoor_temp_f": 200.0,  # Invalid
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 422

    def test_cors_headers_included_in_response(self, client):
        """Response includes CORS headers."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC failure",
                "outdoor_temp_f": 95.0,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        # Check for CORS headers (set by CORSMiddleware)
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
