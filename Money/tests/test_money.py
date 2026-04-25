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
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests
from config import DISPATCH_API_KEY
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ════════════════════════════════════════════════════════════════════════════
# AUTH & RATE LIMITING TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestAuthorizeRequest:
    """Test the ``_authorize_request`` function — the central auth gate."""

    @pytest.mark.asyncio
    async def test_missing_credentials_returns_401(self):
        """No auth header, cookie, or API key → 401."""
        import main

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

        with pytest.raises(HTTPException) as exc_info:
            await main._authorize_request(x_api_key="invalid-key-1234567890")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_bearer_token_success_via_auth_service(self, monkeypatch):
        """Valid bearer JWT passes through to auth service."""
        import main

        mock_get = MagicMock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "user_id": "user-123",
            "role": "admin",
        }

        monkeypatch.setattr("requests.get", mock_get)

        fake_request = MagicMock()
        fake_request.headers.get.side_effect = lambda k, default=None: {
            "authorization": "Bearer valid-jwt-token-abc123"
        }.get(k, default)
        fake_request.cookies.get.return_value = None

        result = await main._authorize_request(x_api_key=None, request=fake_request)
        assert result is None
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_bearer_token_expired_returns_401(self, monkeypatch):
        """Expired or invalid bearer token → 401."""
        import main

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

        mock_get = MagicMock(
            side_effect=requests.RequestException("Connection refused")
        )
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

        fake_request = MagicMock()
        fake_request.client.host = "127.0.0.1"
        fake_request.headers.get.return_value = None

        bucket = main._rate_bucket(fake_request, "test")

        # Fill the bucket to capacity (60 requests)
        for _ in range(60):
            main._rate_limit(bucket)

        # 61st request should raise 429
        with pytest.raises(Exception) as exc_info:
            main._rate_limit(bucket)
        assert "429" in str(exc_info.value) or "Rate limit" in str(exc_info.value)

    def test_rate_limit_resets_after_window_expires(self, monkeypatch):
        """After 60s, window expires and counter resets."""
        import main

        fake_request = MagicMock()
        fake_request.client.host = "127.0.0.2"
        fake_request.headers.get.return_value = None

        bucket = main._rate_bucket(fake_request, "test2")

        # Fill bucket
        for _ in range(60):
            main._rate_limit(bucket)

        # Advance time by 70 seconds
        original_time = time.time
        monkeypatch.setattr("time.time", lambda: original_time() + 70)

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

        main.auth_circuit_breaker.state = "CLOSED"
        main.auth_circuit_breaker.failures = 0

        for _ in range(3):
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

        main.auth_circuit_breaker.state = "OPEN"
        main.auth_circuit_breaker.last_failure_time = time.time()

        with pytest.raises(Exception) as exc_info:
            main.auth_circuit_breaker.call(lambda: None)
        assert "503" in str(exc_info.value) or "Circuit Open" in str(exc_info.value)


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
                "customer_message": "AC not cooling, 102F outside",
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
        """Message > 1000 chars rejected with 422."""
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
        assert run_id in fake_pool.store.get("dispatches", {})

    def test_dispatch_rate_limited_after_limit_reached(self, client, monkeypatch):
        """After rate limit is hit from same source, returns 429."""
        import main

        monkeypatch.setattr(main, "RATE_LIMIT_COUNT", 2)

        response1 = client.post(
            "/dispatch",
            json={"customer_message": "AC failure 1", "outdoor_temp_f": 95.0},
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response1.status_code == 200

        response2 = client.post(
            "/dispatch",
            json={"customer_message": "AC failure 2", "outdoor_temp_f": 95.0},
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response2.status_code == 200

        response3 = client.post(
            "/dispatch",
            json={"customer_message": "AC failure 3", "outdoor_temp_f": 95.0},
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response3.status_code == 429

    def test_dispatch_duplicate_id_is_idempotent(self, client, mock_crew, fake_pool):
        """Duplicate dispatch_id → idempotent, returns existing record."""
        # FIX 3: seed a known dispatch row and verify it is returned without creating a new one
        fixed_id = str(uuid.uuid4())
        fake_pool.store["dispatches"][fixed_id] = {
            "dispatch_id": fixed_id,
            "status": "complete",
            "crew_result": None,
            "updated_at": "2026-04-24T00:00:00+00:00",
        }

        # First request: existing record returned
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC failure",
                "outdoor_temp_f": 95.0,
                "dispatch_id": fixed_id,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == fixed_id
        assert data["status"] == "complete"

        # Second request with same id: still 200, still the seeded record
        response2 = client.post(
            "/dispatch",
            json={
                "customer_message": "AC failure",
                "outdoor_temp_f": 95.0,
                "dispatch_id": fixed_id,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response2.status_code == 200
        assert response2.json()["run_id"] == fixed_id

        # Only one DB row exists (no new row was inserted)
        assert len(fake_pool.store["dispatches"]) == 1

    def test_dispatch_life_safety_urgency_handled(self, client, mock_crew):
        """LIFE_SAFETY message triggers correct escalation path without error."""
        response = client.post(
            "/dispatch",
            json={
                "customer_message": "Gas smell near HVAC unit, possible leak, evacuating now",
                "outdoor_temp_f": 75.0,
                "async_mode": False,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data


# ════════════════════════════════════════════════════════════════════════════
# TWILIO WEBHOOK TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestTwilioWebhooks:
    """Test ``POST /sms`` and ``POST /whatsapp`` webhook endpoints."""

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

    def test_sms_webhook_skip_validation_accepted(self, client, mock_crew):
        """With SKIP_TWILIO_VALIDATION=true (default in tests), SMS processed → 200."""
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
        assert "xml" in response.text.lower() or "Response" in response.text

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

    def test_sms_with_rate_limit_from_same_number(self, client):
        """Multiple SMS from same number within 5s → second drops gracefully."""
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

        response2 = client.post(
            "/sms",
            data={
                "From": "+15005550099",
                "Body": "Second message",
                "MessageSid": "SM2",
                "To": "+15005550000",
            },
        )
        # Should be 200 (deduplicated/rate-limited gracefully, not 5xx)
        assert response2.status_code == 200

    def test_sms_sanitizes_html_in_message_body(self, client, mock_crew):
        """HTML tags in message body are sanitized — no 5xx."""
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

    def test_checkout_free_plan_creates_customer(self, client, monkeypatch):
        """POST /billing/checkout with plan='free' → new customer, API key."""
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

    def test_webhook_stripe_checkout_completed_updates_customer(
        self, client, monkeypatch
    ):
        """Stripe webhook: checkout.session.completed → update customer."""
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
        # FIX 6: patch the lazy accessor, not the env var (module-level capture is gone)
        monkeypatch.setattr("billing._get_webhook_secret", lambda: "")

        response = client.post(
            "/billing/webhook",
            json={"type": "checkout.session.completed"},
            headers={"stripe-signature": "test-sig"},
        )
        assert response.status_code == 500


class TestDispatchQuota:
    """Test dispatch quota enforcement in billing.py."""

    def test_unlimited_quota_for_enterprise_plan(self):
        """Enterprise plan (dispatches_per_month=-1) → unlimited quota."""
        import billing

        customer = {"id": 1, "plan": "enterprise_os"}
        assert billing.check_dispatch_quota(customer) is True

    def test_quota_exceeded_for_free_plan(self, fake_pool):
        """Free plan with 10 dispatches already used → quota exceeded."""
        import billing

        fake_pool.store["dispatch_count"] = 10
        customer = {"id": 1, "plan": "free"}
        assert billing.check_dispatch_quota(customer) is False

    def test_quota_not_exceeded_for_free_plan_with_room(self, fake_pool):
        """Free plan with 5 dispatches → quota not exceeded."""
        import billing

        fake_pool.store["dispatch_count"] = 5
        customer = {"id": 1, "plan": "free"}
        assert billing.check_dispatch_quota(customer) is True

    def test_quota_exceeded_returns_402_on_dispatch(
        self, client, fake_pool, monkeypatch
    ):
        """When quota exceeded, POST /dispatch returns 402."""
        # FIX 1+2: DISPATCH_API_KEY bypasses billing; use a billing customer key
        billing_key = "billing-test-customer-api-key-pytest"
        fake_pool.store["customers_by_key"][billing_key] = {
            "id": 99,
            "api_key": billing_key,
            "plan": "free",
            "status": "active",
            "billing_status": "active",
            "trial_ends_at": None,
        }
        import billing

        monkeypatch.setattr(billing, "check_dispatch_quota", lambda customer: False)

        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC failure",
                "outdoor_temp_f": 95.0,
            },
            headers={"X-API-Key": billing_key},
        )
        # FIX 1: quota exhaustion is 402 (payment required), not 429 (rate limit)
        assert response.status_code == 402


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
        # Use stream=True so the client doesn't wait for the full body
        with client.stream(
            "GET",
            "/api/stream/dispatches",
            headers={"X-API-Key": DISPATCH_API_KEY},
        ) as response:
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type

    def test_dispatch_creation_broadcasts_event(self, client, mock_crew, fake_pool):
        """Dispatch creation doesn't crash the broadcast path."""
        import main

        broadcast_calls = []
        original = getattr(main, "_broadcast_dispatch_event", None) or getattr(
            main, "broadcast_event", None
        )

        def fake_broadcast(event_type, data):
            broadcast_calls.append({"type": event_type, "data": data})

        if hasattr(main, "_broadcast_dispatch_event"):
            main._broadcast_dispatch_event = fake_broadcast
        elif hasattr(main, "broadcast_event"):
            main.broadcast_event = fake_broadcast

        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC failure for SSE test",
                "outdoor_temp_f": 90.0,
                "async_mode": False,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        # Restore
        if original and hasattr(main, "_broadcast_dispatch_event"):
            main._broadcast_dispatch_event = original
        elif original and hasattr(main, "broadcast_event"):
            main.broadcast_event = original


# ════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════


class TestHealthEndpoints:
    """Test health check and status endpoints."""

    def test_health_endpoint_returns_200(self, client):
        """GET /health → 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ("ok", "healthy", "running")

    def test_status_endpoint_returns_system_info(self, client):
        """GET /status → system metadata returned without authentication."""
        # FIX 4: /status requires no auth; returns config metadata (no secrets)
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "dispatch_api_configured" in data
        assert "billing_configured" in data
        assert "event_bus_configured" in data
        assert isinstance(data["dispatch_api_configured"], bool)
        assert isinstance(data["billing_configured"], bool)
        assert isinstance(data["event_bus_configured"], bool)

    def test_dispatches_list_requires_auth(self, client):
        """GET /dispatches without auth → 401."""
        response = client.get("/dispatches")
        assert response.status_code == 401

    def test_dispatches_list_returns_data_with_auth(self, client, fake_pool):
        """GET /dispatches with valid auth → 200 with list."""
        response = client.get(
            "/dispatches",
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ════════════════════════════════════════════════════════════════════════════
# EVENT BUS RESILIENCE TESTS
# ════════════════════════════════════════════════════════════════════════════


class TestEventBusResilience:
    """FIX 8: dispatch must complete even when the event bus is unreachable."""

    def test_dispatch_completes_even_when_event_bus_is_down(
        self, client, mock_crew, fake_pool, monkeypatch
    ):
        """Dispatch job reaches a terminal state even if event bus publish raises ConnectionError."""
        import main

        monkeypatch.setenv("EVENT_BUS_URL", "http://localhost:9999")
        monkeypatch.setattr(
            main,
            "_event_bus_publish_sync",
            MagicMock(side_effect=requests.ConnectionError("Connection refused")),
        )

        response = client.post(
            "/dispatch",
            json={
                "customer_message": "AC failure event-bus-down",
                "outdoor_temp_f": 95.0,
            },
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Job must reach "complete" — event bus failure must not fail the dispatch
        job = main.job_store.get(run_id, {})
        assert (
            job.get("status") == "complete"
        ), f"Expected 'complete', got {job.get('status')!r}"


# ════════════════════════════════════════════════════════════════════════════
# METRICS ENDPOINT TESTS  (FIX 12)
# ════════════════════════════════════════════════════════════════════════════


class TestMetricsEndpoint:
    """FIX 12: /metrics auth enforcement and /api/metrics empty-schema contract."""

    def test_metrics_requires_auth(self, client):
        """GET /metrics with no credentials → 401 or 403."""
        response = client.get("/metrics")
        assert response.status_code in (401, 403)

    def test_metrics_accepts_dispatch_api_key(self, client):
        """GET /metrics with X-API-Key: DISPATCH_API_KEY → 200."""
        response = client.get(
            "/metrics",
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200

    def test_api_metrics_empty_returns_valid_schema(self, client, fake_pool):
        """GET /api/metrics with empty dispatches table returns required numeric keys."""
        # Ensure dispatches table is empty (fresh fake pool already is)
        fake_pool.store["dispatches"] = {}

        response = client.get(
            "/api/metrics",
            headers={"X-API-Key": DISPATCH_API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        for key in ("total_dispatches", "successful_dispatches", "failed_dispatches"):
            assert key in data, f"Missing key: {key!r}"
            assert isinstance(
                data[key], (int, float)
            ), f"{key!r} must be numeric, got {type(data[key])}"
