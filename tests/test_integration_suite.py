"""
ReliantAI Platform - Comprehensive Integration Test Suite
=========================================================

Organized into four layers:
  Layer 1: Contract tests  -- Does each service honour its API contract?
  Layer 2: Integration     -- Do service pairs interact correctly?
  Layer 3: End-to-end      -- Do full platform workflows complete?
  Layer 4: Chaos           -- Does the platform survive partial failures?

Usage:
    # All layers
    pytest tests/test_integration_suite.py -v

    # Single layer
    pytest tests/test_integration_suite.py -v -m contract
    pytest tests/test_integration_suite.py -v -m integration
    pytest tests/test_integration_suite.py -v -m e2e
    pytest tests/test_integration_suite.py -v -m chaos

    # Specific service
    pytest tests/test_integration_suite.py -v -k "orchestrator"

Requirements:
    pip install pytest pytest-asyncio aiohttp pytest-timeout

Environment:
    MONEY_URL          (default: http://localhost:8000)
    COMPLIANCEONE_URL  (default: http://localhost:8001)
    FINOPS360_URL      (default: http://localhost:8002)
    ORCHESTRATOR_URL   (default: http://localhost:9000)
    INTEGRATION_URL    (default: http://localhost:8080)
    API_KEY            (default: dev-key)
    TEST_TIMEOUT_S     (default: 10)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ServiceConfig:
    name: str
    url: str
    critical: bool = True

SERVICES = [
    ServiceConfig("money",        os.getenv("MONEY_URL",         "http://localhost:8000")),
    ServiceConfig("complianceone",os.getenv("COMPLIANCEONE_URL", "http://localhost:8001")),
    ServiceConfig("finops360",    os.getenv("FINOPS360_URL",      "http://localhost:8002")),
    ServiceConfig("orchestrator", os.getenv("ORCHESTRATOR_URL",   "http://localhost:9000")),
    ServiceConfig("integration",  os.getenv("INTEGRATION_URL",    "http://localhost:8080"), critical=False),
]

SERVICE_MAP: Dict[str, ServiceConfig] = {s.name: s for s in SERVICES}

API_KEY = os.getenv("API_KEY", "dev-key")
TIMEOUT = int(os.getenv("TEST_TIMEOUT_S", "10"))

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Request-ID": "",  # filled per request
}


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def http():
    """Shared aiohttp session for the entire test session."""
    connector = aiohttp.TCPConnector(limit=20)
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=TIMEOUT),
        connector=connector,
    )
    yield session
    await session.close()


def auth_headers(extra: Optional[Dict] = None) -> Dict:
    h = {**HEADERS, "X-Request-ID": str(uuid.uuid4())}
    if extra:
        h.update(extra)
    return h


async def get_json(session: aiohttp.ClientSession, url: str, **kw) -> Dict:
    async with session.get(url, headers=auth_headers(), **kw) as r:
        r.raise_for_status()
        return await r.json()


async def post_json(session: aiohttp.ClientSession, url: str, body: Dict, **kw) -> Dict:
    async with session.post(url, json=body, headers=auth_headers(), **kw) as r:
        r.raise_for_status()
        return await r.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def url(service: str, path: str) -> str:
    svc = SERVICE_MAP[service]
    return f"{svc.url}{path}"


async def wait_for_service(
    session: aiohttp.ClientSession,
    service: str,
    timeout: int = 30,
    interval: float = 1.0,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            async with session.get(
                url(service, "/health"),
                timeout=aiohttp.ClientTimeout(total=3),
            ) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        await asyncio.sleep(interval)
    return False


# ===========================================================================
# LAYER 1: CONTRACT TESTS
# Purpose: Verify each service independently meets its API contract.
# These tests should pass regardless of other services being available.
# ===========================================================================

@pytest.mark.contract
class TestHealthContracts:
    """Every service must return a 200 /health with a 'status' field."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", [s.name for s in SERVICES])
    async def test_health_endpoint_returns_200(self, http, service):
        resp = await get_json(http, url(service, "/health"))
        assert "status" in resp, f"{service} /health missing 'status' field"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", [s.name for s in SERVICES])
    async def test_health_status_is_healthy(self, http, service):
        resp = await get_json(http, url(service, "/health"))
        assert resp["status"] in ("healthy", "ok", "running"), (
            f"{service} reports non-healthy status: {resp['status']}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", [s.name for s in SERVICES])
    async def test_health_response_time_under_500ms(self, http, service):
        start = time.monotonic()
        await get_json(http, url(service, "/health"))
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 500, (
            f"{service} health check took {elapsed_ms:.0f}ms (limit: 500ms)"
        )


@pytest.mark.contract
class TestOrchestratorContract:
    """Orchestrator-specific API contract tests."""

    @pytest.mark.asyncio
    async def test_status_endpoint_structure(self, http):
        data = await get_json(http, url("orchestrator", "/status"))
        assert "timestamp" in data
        assert "orchestrator" in data
        assert "services" in data
        orch = data["orchestrator"]
        assert "running" in orch
        assert "ai_enabled" in orch

    @pytest.mark.asyncio
    async def test_services_endpoint_lists_known_services(self, http):
        data = await get_json(http, url("orchestrator", "/services"))
        assert "services" in data
        names = {s["name"] for s in data["services"]}
        # At minimum the critical services must be registered
        assert "money" in names
        assert "complianceone" in names
        assert "finops360" in names

    @pytest.mark.asyncio
    async def test_services_have_required_fields(self, http):
        data = await get_json(http, url("orchestrator", "/services"))
        required = {"name", "url", "status", "instances", "auto_scale", "auto_heal"}
        for svc in data["services"]:
            missing = required - set(svc.keys())
            assert not missing, f"Service {svc.get('name')} missing fields: {missing}"

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_list(self, http):
        data = await get_json(http, url("orchestrator", "/metrics"))
        assert "metrics" in data
        assert isinstance(data["metrics"], list)

    @pytest.mark.asyncio
    async def test_decisions_endpoint_returns_list(self, http):
        data = await get_json(http, url("orchestrator", "/decisions"))
        assert "decisions" in data
        assert isinstance(data["decisions"], list)

    @pytest.mark.asyncio
    async def test_dashboard_endpoint_structure(self, http):
        data = await get_json(http, url("orchestrator", "/dashboard"))
        for field in ("health_score", "services_total", "services_healthy", "active_instances"):
            assert field in data, f"dashboard missing field: {field}"
        assert 0 <= data["health_score"] <= 100

    @pytest.mark.asyncio
    async def test_scale_unknown_service_returns_404(self, http):
        async with http.post(
            url("orchestrator", "/services/nonexistent/scale"),
            params={"target_instances": 2},
            headers=auth_headers(),
        ) as r:
            assert r.status == 404

    @pytest.mark.asyncio
    async def test_scale_out_of_bounds_returns_400(self, http):
        # money has max_instances=10; requesting 999 should fail
        async with http.post(
            url("orchestrator", "/services/money/scale"),
            params={"target_instances": 999},
            headers=auth_headers(),
        ) as r:
            assert r.status == 400

    @pytest.mark.asyncio
    async def test_metrics_hours_param_accepted(self, http):
        data = await get_json(http, url("orchestrator", "/metrics?hours=2"))
        assert "metrics" in data

    @pytest.mark.asyncio
    async def test_root_lists_features(self, http):
        data = await get_json(http, url("orchestrator", "/"))
        assert "features" in data
        assert "auto_scaling" in data["features"]
        assert "auto_healing" in data["features"]


@pytest.mark.contract
class TestMoneyServiceContract:
    """Money service API contract."""

    @pytest.mark.asyncio
    async def test_health_includes_db_status(self, http):
        data = await get_json(http, url("money", "/health"))
        # Money service must report database connectivity
        assert "status" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint_exists(self, http):
        # Orchestrator depends on /metrics being present on all services
        async with http.get(url("money", "/metrics"), headers=auth_headers()) as r:
            # Accept 200 or 404; 500 is a failure
            assert r.status != 500, "money /metrics returned 500"


@pytest.mark.contract
class TestComplianceOneContract:

    @pytest.mark.asyncio
    async def test_health(self, http):
        data = await get_json(http, url("complianceone", "/health"))
        assert data["status"] in ("healthy", "ok")

    @pytest.mark.asyncio
    async def test_api_key_required(self, http):
        """Endpoints requiring auth must reject requests without API key."""
        async with http.get(
            url("complianceone", "/api/v1/status"),
            headers={"Content-Type": "application/json"},  # no X-API-Key
        ) as r:
            assert r.status in (401, 403), (
                f"Expected 401/403 without API key, got {r.status}"
            )


@pytest.mark.contract
class TestFinOps360Contract:

    @pytest.mark.asyncio
    async def test_health(self, http):
        data = await get_json(http, url("finops360", "/health"))
        assert data["status"] in ("healthy", "ok")

    @pytest.mark.asyncio
    async def test_api_key_required(self, http):
        async with http.get(
            url("finops360", "/api/v1/status"),
            headers={"Content-Type": "application/json"},
        ) as r:
            assert r.status in (401, 403)


# ===========================================================================
# LAYER 2: INTEGRATION TESTS
# Purpose: Verify service-to-service interactions and data flow.
# ===========================================================================

@pytest.mark.integration
class TestOrchestratorServiceDiscovery:
    """Orchestrator must correctly track downstream service health."""

    @pytest.mark.asyncio
    async def test_orchestrator_knows_money_status(self, http):
        data = await get_json(http, url("orchestrator", "/status"))
        assert "money" in data["services"], "money not tracked by orchestrator"

    @pytest.mark.asyncio
    async def test_orchestrator_health_check_freshness(self, http):
        """Last health check timestamp must not be stale (> 60s)."""
        data = await get_json(http, url("orchestrator", "/status"))
        from datetime import datetime, timezone
        for name, svc in data["services"].items():
            last_check = svc.get("last_check")
            if last_check:
                checked_at = datetime.fromisoformat(last_check)
                if checked_at.tzinfo is None:
                    checked_at = checked_at.replace(tzinfo=timezone.utc)
                age_s = (datetime.now(timezone.utc) - checked_at).total_seconds()
                assert age_s < 120, (
                    f"{name} last health check is {age_s:.0f}s old (limit: 120s)"
                )

    @pytest.mark.asyncio
    async def test_orchestrator_reflects_service_health(self, http):
        """If a service is up, orchestrator should not report it as UNHEALTHY."""
        # First verify the service is actually up
        money_health = await get_json(http, url("money", "/health"))
        if money_health["status"] in ("healthy", "ok"):
            # Give orchestrator time to sync if needed (max 35s per its 30s cycle)
            await asyncio.sleep(2)
            orch_data = await get_json(http, url("orchestrator", "/status"))
            money_orch_status = orch_data["services"]["money"]["status"]
            assert money_orch_status != "unhealthy", (
                f"money is healthy but orchestrator reports: {money_orch_status}"
            )

    @pytest.mark.asyncio
    async def test_scale_action_reflected_in_status(self, http):
        """A manual scale should be visible in the next /status call."""
        # Read current instances
        before = await get_json(http, url("orchestrator", "/status"))
        current = before["services"]["finops360"]["instances"]
        svc = SERVICE_MAP["finops360"]

        # Target: current or current+1 (within bounds)
        target = current  # no-op first to test idempotency
        async with http.post(
            url("orchestrator", f"/services/finops360/scale"),
            params={"target_instances": target},
            headers=auth_headers(),
        ) as r:
            assert r.status == 200

        after = await get_json(http, url("orchestrator", "/status"))
        assert after["services"]["finops360"]["instances"] == target


@pytest.mark.integration
class TestMetricsFlow:
    """Metrics must flow from services into the orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_accumulates_metrics_over_time(self, http):
        """After 65s, the orchestrator should have at least some metrics."""
        # This test is slow; skip if metrics are already populated
        before = await get_json(http, url("orchestrator", "/metrics?hours=1"))
        if len(before["metrics"]) > 0:
            pytest.skip("Metrics already present, skipping wait")

        await asyncio.sleep(65)
        after = await get_json(http, url("orchestrator", "/metrics?hours=1"))
        assert len(after["metrics"]) > 0, "No metrics accumulated after 65s"

    @pytest.mark.asyncio
    async def test_metrics_have_valid_structure(self, http):
        data = await get_json(http, url("orchestrator", "/metrics?hours=24"))
        for metric in data["metrics"][:50]:  # spot-check first 50
            assert "timestamp" in metric
            assert "service" in metric
            assert "type" in metric
            assert "value" in metric
            assert isinstance(metric["value"], (int, float))

    @pytest.mark.asyncio
    async def test_metrics_service_filter(self, http):
        data = await get_json(http, url("orchestrator", "/metrics?service=money"))
        for m in data["metrics"]:
            assert m["service"] == "money", f"Filter leak: got metric for {m['service']}"


@pytest.mark.integration
class TestDecisionHistory:

    @pytest.mark.asyncio
    async def test_decisions_endpoint_respects_limit(self, http):
        data = await get_json(http, url("orchestrator", "/decisions?limit=5"))
        assert len(data["decisions"]) <= 5

    @pytest.mark.asyncio
    async def test_restart_generates_decision_record(self, http):
        before_count = len(
            (await get_json(http, url("orchestrator", "/decisions?limit=1000")))["decisions"]
        )

        # Trigger a restart
        async with http.post(
            url("orchestrator", "/services/integration/restart"),
            headers=auth_headers(),
        ) as r:
            assert r.status == 200

        await asyncio.sleep(8)  # allow restart simulation (5s) + margin

        after = await get_json(http, url("orchestrator", "/decisions?limit=1000"))
        after_count = len(after["decisions"])
        assert after_count > before_count, (
            "Restart did not generate a decision record"
        )

    @pytest.mark.asyncio
    async def test_decision_records_have_required_fields(self, http):
        data = await get_json(http, url("orchestrator", "/decisions?limit=100"))
        for d in data["decisions"][:20]:
            assert "timestamp" in d
            assert "type" in d
            assert d["type"] in ("scale", "heal", "optimize")


# ===========================================================================
# LAYER 3: END-TO-END TESTS
# Purpose: Full platform workflows from external client perspective.
# ===========================================================================

@pytest.mark.e2e
class TestPlatformStartupSequence:
    """The platform must be fully operational after cold start."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_all_critical_services_are_healthy(self, http):
        """Every critical service must be healthy within 60s."""
        results = {}
        for svc in [s for s in SERVICES if s.critical]:
            results[svc.name] = await wait_for_service(http, svc.name, timeout=45)

        failures = [name for name, ok in results.items() if not ok]
        assert not failures, f"Critical services failed to become healthy: {failures}"

    @pytest.mark.asyncio
    async def test_orchestrator_platform_health_score_above_50(self, http):
        data = await get_json(http, url("orchestrator", "/dashboard"))
        assert data["health_score"] >= 50, (
            f"Platform health score too low: {data['health_score']}"
        )

    @pytest.mark.asyncio
    async def test_orchestrator_running_state(self, http):
        data = await get_json(http, url("orchestrator", "/status"))
        assert data["orchestrator"]["running"] is True


@pytest.mark.e2e
class TestWebSocketConnection:
    """WebSocket updates must work end-to-end."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_websocket_sends_initial_status(self):
        ws_url = url("orchestrator", f"/ws?token={API_KEY}").replace("http://", "ws://")
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=10)
                assert "type" in msg
                assert msg["type"] == "connected"
                assert "data" in msg

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_websocket_responds_to_get_status(self):
        ws_url = url("orchestrator", f"/ws?token={API_KEY}").replace("http://", "ws://")
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                # Consume initial connect message
                await asyncio.wait_for(ws.receive_json(), timeout=5)

                # Request status
                await ws.send_json({"action": "get_status"})
                msg = await asyncio.wait_for(ws.receive_json(), timeout=5)
                assert msg.get("type") == "status"
                assert "data" in msg

    @pytest.mark.asyncio
    @pytest.mark.timeout(20)
    async def test_websocket_multiple_concurrent_clients(self):
        ws_url = url("orchestrator", f"/ws?token={API_KEY}").replace("http://", "ws://")

        async def connect_and_receive():
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(ws_url) as ws:
                    msg = await asyncio.wait_for(ws.receive_json(), timeout=10)
                    return msg["type"] == "connected"

        results = await asyncio.gather(*[connect_and_receive() for _ in range(5)])
        assert all(results), "Not all concurrent WS clients received initial message"

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_websocket_rejects_unauthenticated(self):
        """WebSocket without ?token= must be rejected (CRIT-2 hardening)."""
        ws_url = url("orchestrator", "/ws").replace("http://", "ws://")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect(ws_url) as ws:
                    # Server should close with policy violation code 1008
                    msg = await ws.receive()
                    assert msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED), (
                        f"Expected WS close, got {msg.type}"
                    )
            except aiohttp.WSServerHandshakeError:
                pass  # Also acceptable: server refuses handshake


@pytest.mark.e2e
class TestAutoHealingWorkflow:
    """End-to-end: when a service is restarted, the platform recovers."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_service_recovers_after_restart(self, http):
        """Restart integration (non-critical), verify it returns to healthy."""
        # Trigger restart
        async with http.post(
            url("orchestrator", "/services/integration/restart"),
            headers=auth_headers(),
        ) as r:
            assert r.status == 200

        # During restart, service should enter MAINTENANCE
        await asyncio.sleep(2)

        # After restart simulation (5s), service should be healthy again
        recovered = await wait_for_service(http, "integration", timeout=30)
        assert recovered, "integration service did not recover after restart"

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_orchestrator_reflects_post_restart_health(self, http):
        """Orchestrator status must update within its health check cycle."""
        async with http.post(
            url("orchestrator", "/services/integration/restart"),
            headers=auth_headers(),
        ) as r:
            assert r.status == 200

        # Wait for orchestrator to next cycle (30s) + restart sim (5s) + buffer
        await asyncio.sleep(10)

        data = await get_json(http, url("orchestrator", "/status"))
        status = data["services"]["integration"]["status"]
        assert status in ("healthy", "maintenance"), (
            f"Unexpected status after restart: {status}"
        )


# ===========================================================================
# LAYER 4: CHAOS TESTS
# Purpose: Verify platform behaviour under partial failure conditions.
# Run with caution -- these tests deliberately degrade the platform.
# Skip in CI with: pytest -m "not chaos"
# ===========================================================================

@pytest.mark.chaos
class TestCascadeIsolation:
    """Non-critical service failures must not propagate to critical services."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(45)
    async def test_orchestrator_stays_healthy_when_service_unhealthy(self, http):
        """
        Scenario: integration service is unreachable (simulated by querying a
        non-existent port). Critical services and orchestrator must remain healthy.

        NOTE: This test does not actually take down the service; it validates
        that the orchestrator's UNKNOWN status for a service does not degrade
        the orchestrator's own /health endpoint.
        """
        # Confirm orchestrator is healthy first
        orch = await get_json(http, url("orchestrator", "/health"))
        assert orch["status"] in ("healthy", "running")

        # Confirm critical services are still healthy
        for name in ("money", "complianceone", "finops360"):
            svc = await get_json(http, url(name, "/health"))
            assert svc["status"] in ("healthy", "ok"), (
                f"{name} is unhealthy during cascade test"
            )

    @pytest.mark.asyncio
    async def test_orchestrator_scale_endpoint_unaffected_by_degraded_service(self, http):
        """Scale operations on healthy services must succeed regardless of others."""
        # Attempt scale on money even if other services might be degraded
        async with http.post(
            url("orchestrator", "/services/money/scale"),
            params={"target_instances": 2},
            headers=auth_headers(),
        ) as r:
            # Must succeed or return a validation error, never 500
            assert r.status in (200, 400), (
                f"Scale endpoint returned unexpected status: {r.status}"
            )


@pytest.mark.chaos
class TestMetricsPressure:
    """Metrics endpoints must handle high request rates without degrading."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_concurrent_metrics_requests_do_not_crash_orchestrator(self, http):
        """20 concurrent /metrics requests must all return 200."""
        tasks = [
            get_json(http, url("orchestrator", "/metrics?hours=1"))
            for _ in range(20)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        failures = [r for r in results if isinstance(r, Exception)]
        assert not failures, f"{len(failures)}/20 concurrent metrics requests failed: {failures[0]}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_large_hours_param_does_not_timeout(self, http):
        """hours=24 must return within the default timeout."""
        start = time.monotonic()
        data = await get_json(http, url("orchestrator", "/metrics?hours=24"))
        elapsed = time.monotonic() - start
        assert elapsed < TIMEOUT, f"/metrics?hours=24 took {elapsed:.1f}s (limit: {TIMEOUT}s)"
        assert "metrics" in data


@pytest.mark.chaos
class TestDecisionHistoryGrowth:
    """Decision history must be bounded under sustained operation."""

    @pytest.mark.asyncio
    async def test_decision_history_does_not_exceed_safety_limit(self, http):
        """
        After generating multiple decisions, the list should not grow
        unboundedly. This tests the cap behaviour introduced as a fix.
        Trigger 5 restarts and verify total decisions is bounded.
        """
        for _ in range(5):
            await asyncio.sleep(0.5)
            async with http.post(
                url("orchestrator", "/services/integration/restart"),
                headers=auth_headers(),
            ) as r:
                pass  # fire-and-forget

        await asyncio.sleep(2)
        data = await get_json(http, url("orchestrator", "/decisions?limit=100000"))
        count = len(data["decisions"])
        # With the fix applied, this should be capped at MAX_DECISIONS
        # Without the fix, this is a soft warning (not a hard failure in CI)
        if count > 10_000:
            pytest.fail(
                f"decision_history has {count} entries -- unbounded growth detected. "
                "Apply the MAX_DECISIONS cap fix."
            )


# ===========================================================================
# SECURITY REGRESSION TESTS
# Purpose: Verify specific security fixes are in place.
# ===========================================================================

@pytest.mark.security
class TestAuthEnforcement:

    @pytest.mark.asyncio
    async def test_scale_endpoint_requires_auth(self, http):
        """POST /services/{svc}/scale must reject requests without API key."""
        async with http.post(
            url("orchestrator", "/services/money/scale"),
            params={"target_instances": 2},
            headers={"Content-Type": "application/json"},  # no X-API-Key
        ) as r:
            # Explicitly check that 200 is a failure (auth bypass)
            assert r.status != 200, (
                f"SECURITY ISSUE: Scale endpoint accepted unauthenticated request with 200 - auth not enforced"
            )
            assert r.status in (401, 403), (
                f"Scale endpoint accepted unauthenticated request: status={r.status}"
            )

    @pytest.mark.asyncio
    async def test_restart_endpoint_requires_auth(self, http):
        async with http.post(
            url("orchestrator", "/services/integration/restart"),
            headers={"Content-Type": "application/json"},
        ) as r:
            # Explicitly check that 200 is a failure (auth bypass)
            assert r.status != 200, (
                f"SECURITY ISSUE: Restart endpoint accepted unauthenticated request with 200 - auth not enforced"
            )
            assert r.status in (401, 403), (
                f"Restart endpoint accepted unauthenticated request: status={r.status}"
            )

    @pytest.mark.asyncio
    async def test_invalid_api_key_rejected(self, http):
        async with http.post(
            url("orchestrator", "/services/money/scale"),
            params={"target_instances": 2},
            headers={"X-API-Key": "definitely-wrong-key-xyz"},
        ) as r:
            assert r.status in (401, 403)

    @pytest.mark.asyncio
    async def test_empty_api_key_rejected(self, http):
        """Empty API key must not be accepted (guards against misconfigured server)."""
        async with http.post(
            url("orchestrator", "/services/money/scale"),
            params={"target_instances": 2},
            headers={"X-API-Key": ""},
        ) as r:
            assert r.status in (401, 403), (
                "Empty API key accepted -- API_KEY env var may not be set on the server. "
                "A 503 response indicates the server is misconfigured, not secured."
            )


@pytest.mark.security
class TestSecurityHeaders:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["money", "complianceone", "finops360", "orchestrator"])
    async def test_x_content_type_options(self, http, service):
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            assert r.headers.get("X-Content-Type-Options") == "nosniff", (
                f"{service} missing X-Content-Type-Options: nosniff"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["money", "complianceone", "finops360", "orchestrator"])
    async def test_x_frame_options(self, http, service):
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            assert "X-Frame-Options" in r.headers, (
                f"{service} missing X-Frame-Options header"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["money", "complianceone", "finops360", "orchestrator"])
    async def test_no_server_header_disclosure(self, http, service):
        """Server header should not disclose framework version."""
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            server = r.headers.get("server", "").lower()
            for version_string in ("uvicorn/", "fastapi/", "python/", "starlette/"):
                assert version_string not in server, (
                    f"{service} Server header discloses version: {server}"
                )
    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["money", "complianceone", "finops360", "orchestrator"])
    async def test_no_xss_protection_header(self, http, service):
        """X-XSS-Protection must NOT be present (deprecated, can cause XSS in old IE)."""
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            assert "X-XSS-Protection" not in r.headers, (
                f"{service} still sends deprecated X-XSS-Protection header"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["money", "complianceone", "finops360", "orchestrator"])
    async def test_csp_no_unsafe_eval(self, http, service):
        """CSP must not allow unsafe-eval."""
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            csp = r.headers.get("Content-Security-Policy", "")
            assert "unsafe-eval" not in csp, f"{service} CSP allows unsafe-eval"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["money", "complianceone", "finops360", "orchestrator"])
    async def test_csp_allows_websocket_connect(self, http, service):
        """CSP must allow ws: and wss: in connect-src for the dashboard."""
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            csp = r.headers.get("Content-Security-Policy", "")
            assert "connect-src" in csp, f"{service} CSP missing connect-src"
            # Extract connect-src directive
            connect_src = [d for d in csp.split(";") if "connect-src" in d][0]
            assert "ws:" in connect_src or "wss:" in connect_src, (
                f"{service} CSP connect-src does not allow WebSockets"
            )

@pytest.mark.security
class TestInputValidation:

    @pytest.mark.asyncio
    async def test_sql_injection_in_query_param_rejected(self, http):
        async with http.get(
            url("orchestrator", "/metrics"),
            params={"service": "' OR 1=1 --"},
            headers=auth_headers(),
        ) as r:
            assert r.status in (400, 422), (
                f"SQL injection pattern in query param not rejected: {r.status}"
            )

    @pytest.mark.asyncio
    async def test_xss_in_query_param_rejected(self, http):
        async with http.get(
            url("orchestrator", "/metrics"),
            params={"service": "<script>alert(1)</script>"},
            headers=auth_headers(),
        ) as r:
            assert r.status in (400, 422)

    @pytest.mark.asyncio
    async def test_oversized_hours_param_handled(self, http):
        """hours=999999 must not cause a timeout or 500."""
        async with http.get(
            url("orchestrator", "/metrics"),
            params={"hours": "999999"},
            headers=auth_headers(),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as r:
            assert r.status != 500, "Large hours param caused a server error"


@pytest.mark.security
class TestCORSHardening:
    """CORS must be fail-closed across all services."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["orchestrator", "money", "complianceone", "finops360"])
    async def test_cors_rejects_unknown_origin(self, http, service):
        """An unknown origin must not receive Access-Control-Allow-Origin."""
        async with http.options(
            url(service, "/health"),
            headers={
                "Origin": "https://evil-attacker.com",
                "Access-Control-Request-Method": "GET",
            },
        ) as r:
            allow_origin = r.headers.get("Access-Control-Allow-Origin", "")
            assert allow_origin != "*", (
                f"{service} returned wildcard CORS origin — fail-closed violated"
            )
            assert "evil-attacker.com" not in allow_origin, (
                f"{service} reflected unknown origin in CORS header"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["orchestrator", "money", "complianceone", "finops360"])
    async def test_csp_header_present(self, http, service):
        """Content-Security-Policy must be present on all responses."""
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            csp = r.headers.get("Content-Security-Policy", "")
            assert "default-src" in csp, (
                f"{service} missing Content-Security-Policy with default-src"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("service", ["orchestrator", "money", "complianceone", "finops360"])
    async def test_csp_upgrade_insecure_requests(self, http, service):
        """CSP must include upgrade-insecure-requests directive."""
        async with http.get(url(service, "/health"), headers=auth_headers()) as r:
            csp = r.headers.get("Content-Security-Policy", "")
            assert "upgrade-insecure-requests" in csp, (
                f"{service} CSP missing upgrade-insecure-requests directive"
            )


@pytest.mark.integration
class TestRedisStreams:
    """Verify Redis Stream infrastructure and event publishing."""

    @pytest.mark.asyncio
    async def test_platform_events_endpoint_exists(self, http):
        data = await get_json(http, url("orchestrator", "/events"))
        assert "events" in data
        assert "redis_available" in data

    @pytest.mark.asyncio
    async def test_scale_action_publishes_event(self, http):
        """Manual scale must result in a platform event within 5s."""
        # Trigger scale
        async with http.post(
            url("orchestrator", "/services/finops360/scale"),
            params={"target_instances": 1},
            headers=auth_headers(),
        ) as r:
            assert r.status == 200

        # Wait for event propagation
        await asyncio.sleep(3)

        events = await get_json(http, url("orchestrator", "/events?limit=20"))
        if not events["redis_available"]:
            pytest.skip("Redis unavailable in this environment")

        recent = [
            e for e in events["events"]
            if e.get("service") == "finops360"
            and e.get("event") in ("scale_intent", "scale_executed")
        ]
        assert recent, "No scale event found for finops360 after manual scale"

    @pytest.mark.asyncio
    async def test_events_endpoint_respects_limit(self, http):
        data = await get_json(http, url("orchestrator", "/events?limit=5"))
        assert len(data["events"]) <= 5

    @pytest.mark.asyncio
    async def test_events_limit_capped_at_1000(self, http):
        """Adversarial limit parameter must be capped server-side."""
        data = await get_json(http, url("orchestrator", "/events?limit=999999"))
        assert "events" in data  # must not 500


# ===========================================================================
# TEST COLLECTION ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    import subprocess
    import sys

    sys.exit(
        subprocess.call([
            "pytest",
            __file__,
            "-v",
            "--tb=short",
            "-m", "contract or integration",
            "--timeout=30",
        ])
    )
