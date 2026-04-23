# ReliantAI Platform — Load Testing Suite

## Quick Start

```bash
cd tests/load
pip install -r requirements.txt
```

## 1. HTTP Load Test (Locust)

### Interactive (Web UI)
```bash
locust -f locustfile.py
# Open http://localhost:8089
```

### Headless (CI/CD)
```bash
# Baseline: 100 users, ramp 10/sec, 5 minutes
locust -f locustfile.py --headless \
  -u 100 -r 10 --run-time 5m \
  --host=http://localhost:8000 \
  --html=report-100u.html

# Stress: 500 users
locust -f locustfile.py --headless \
  -u 500 -r 50 --run-time 5m \
  --host=http://localhost:8000 \
  --html=report-500u.html

# Peak: 1000 users
locust -f locustfile.py --headless \
  -u 1000 -r 100 --run-time 5m \
  --host=http://localhost:8000 \
  --html=report-1000u.html
```

## 2. SSE Load Test

```bash
# Baseline: 100 concurrent clients, 60s
python sse_load_test.py --clients 100 --duration 60

# Stress: 1000 concurrent clients
python sse_load_test.py --clients 1000 --duration 300
```

## 3. WebSocket Load Test

```bash
# Baseline: 100 concurrent clients
python websocket_load_test.py --clients 100 --duration 60

# Stress: 500 concurrent clients
python websocket_load_test.py --clients 500 --duration 300
```

## Performance Baselines

| Metric | Baseline (100u) | Target (500u) | Stress (1000u) |
|--------|----------------|---------------|----------------|
| **HTTP p95** | < 200ms | < 1000ms | < 2000ms |
| **HTTP error rate** | < 0.1% | < 0.5% | < 1% |
| **SSE connect p95** | < 100ms | < 500ms | < 1000ms |
| **SSE disconnect rate** | < 1% | < 5% | < 10% |
| **WS connect p95** | < 100ms | < 500ms | < 1000ms |
| **WS disconnect rate** | < 1% | < 5% | < 10% |

## Auto-Scale Validation

The orchestrator auto-scales when:
- Response time > 1000ms
- CPU > 75%
- Error rate > 5%

Run the 500-user test and verify in Grafana that:
1. Response time crosses 1000ms
2. Scale-up intent is published to `reliantai:scale_intents`
3. Money container count increases

## CI/CD Integration

Add to `.github/workflows/ci-cd.yml`:

```yaml
- name: Load Test
  run: |
    cd tests/load
    locust -f locustfile.py --headless -u 100 -r 10 --run-time 2m \
      --host=http://localhost:8000 --exit-code-on-error
```

## Architecture

- `locustfile.py`: Multi-user classes simulating real traffic patterns
  - `MoneyUser` (weight 5): Heavy HVAC dispatch traffic
  - `ComplianceUser` (weight 2): Audit workflows
  - `FinOpsUser` (weight 2): Cost analytics
  - `OrchestratorUser` (weight 1): Dashboard polling
  - `IntegrationUser` (weight 1): Internal service calls

- `sse_load_test.py`: Asyncio-based SSE stress test with aiohttp
- `websocket_load_test.py`: Asyncio-based WebSocket stress test
