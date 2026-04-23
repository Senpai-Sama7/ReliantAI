"""
ReliantAI Platform — Load Testing Suite (Locust)

Targets:
  - Money dispatch endpoint (POST /dispatch)
  - ComplianceOne frameworks list (GET /frameworks)
  - FinOps360 dashboard (GET /dashboard)
  - Orchestrator status (GET /status)
  - Integration health (GET /health)

Usage:
    cd tests/load
    pip install -r requirements.txt
    locust -f locustfile.py --host=http://localhost:8000

    # Headless mode (CI/CD)
    locust -f locustfile.py --headless -u 100 -r 10 --run-time 5m --host=http://localhost:8000

Baselines:
  - 100 concurrent users: p95 < 500ms
  - 500 concurrent users: p95 < 1000ms (auto-scale trigger)
  - 1000 concurrent users: p95 < 2000ms (degraded but functional)
  - Error rate: < 1% at all levels
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

# ── Shared Metrics ─────────────────────────────────────────────────────────
API_KEY = "test-api-key"  # Override via --host or env


class MoneyUser(HttpUser):
    """Simulates HVAC dispatch customers."""
    host = "http://localhost:8000"
    wait_time = between(1, 5)
    weight = 5

    def on_start(self):
        self.client.headers.update({"X-API-Key": API_KEY})

    @task(10)
    def health_check(self):
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()

    @task(5)
    def create_dispatch(self):
        payload = {
            "customer_name": f"LoadTest-{random.randint(1, 999999)}",
            "phone": f"+1{random.randint(2000000000, 9999999999)}",
            "address": f"{random.randint(1, 9999)} Test St, Houston, TX",
            "issue_type": random.choice(["AC Repair", "Heating", "Ventilation", "Thermostat"]),
            "urgency": random.choice(["low", "medium", "high"]),
            "description": "Load test dispatch request",
        }
        with self.client.post("/dispatch", json=payload, catch_response=True) as resp:
            if resp.status_code in (200, 201):
                resp.success()
            elif resp.status_code == 429:
                resp.success()  # Rate limiting is expected behavior

    @task(3)
    def list_dispatches(self):
        self.client.get("/dispatches")

    @task(2)
    def get_metrics(self):
        self.client.get("/api/metrics")

    @task(1)
    def search_dispatches(self):
        self.client.get("/api/dispatches/search?q=AC")


class ComplianceUser(HttpUser):
    """Simulates compliance auditors."""
    host = "http://localhost:8001"
    wait_time = between(2, 10)
    weight = 2

    def on_start(self):
        self.client.headers.update({"X-API-Key": API_KEY})

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(5)
    def list_frameworks(self):
        self.client.get("/frameworks")

    @task(3)
    def list_controls(self):
        self.client.get("/frameworks/1/controls")

    @task(3)
    def dashboard(self):
        self.client.get("/dashboard")

    @task(1)
    def list_violations(self):
        self.client.get("/violations")


class FinOpsUser(HttpUser):
    """Simulates cloud cost analysts."""
    host = "http://localhost:8002"
    wait_time = between(2, 10)
    weight = 2

    def on_start(self):
        self.client.headers.update({"X-API-Key": API_KEY})

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(5)
    def dashboard(self):
        self.client.get("/dashboard")

    @task(3)
    def list_accounts(self):
        self.client.get("/accounts")

    @task(2)
    def get_budget_status(self):
        self.client.get("/budgets/1/status")

    @task(1)
    def generate_recommendations(self):
        self.client.post("/recommendations/generate?account_id=1")


class OrchestratorUser(HttpUser):
    """Simulates dashboard users polling platform status."""
    host = "http://localhost:9000"
    wait_time = between(1, 3)
    weight = 1

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(5)
    def platform_status(self):
        self.client.get("/status")

    @task(3)
    def dashboard_data(self):
        self.client.get("/dashboard")

    @task(1)
    def list_services(self):
        self.client.get("/services")

    @task(1)
    def get_decisions(self):
        self.client.get("/decisions?limit=50")


class IntegrationUser(HttpUser):
    """Simulates internal service-to-service calls."""
    host = "http://localhost:8080"
    wait_time = between(1, 5)
    weight = 1

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(5)
    def auth_health(self):
        self.client.get("/auth/health")

    @task(3)
    def event_bus_publish(self):
        payload = {
            "event_type": "analytics.recorded",
            "payload": {"metric": "test", "value": random.randint(1, 100)},
        }
        self.client.post("/event-bus/publish", json=payload)


# ── Event Hooks ────────────────────────────────────────────────────────────

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    if isinstance(environment.runner, MasterRunner):
        print("=" * 60)
        print("ReliantAI Platform Load Test Started")
        print("=" * 60)


@events.quitting.add_listener
def on_locust_quitting(environment, **kwargs):
    stats = environment.runner.stats
    print("\n" + "=" * 60)
    print("ReliantAI Platform Load Test Summary")
    print("=" * 60)
    for key in sorted(stats.entries.keys()):
        entry = stats.entries[key]
        print(
            f"  {key.method} {key.name}: "
            f"reqs={entry.num_requests} "
            f"failures={entry.num_failures} "
            f"p50={entry.get_response_time_percentile(0.50):.0f}ms "
            f"p95={entry.get_response_time_percentile(0.95):.0f}ms "
            f"p99={entry.get_response_time_percentile(0.99):.0f}ms"
        )
