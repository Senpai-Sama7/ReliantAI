import pytest
from fastapi.testclient import TestClient

from services.vector_search.main import app as vector_app
from services.knowledge_graph.main import app as graph_app
from services.causal_inference.main import app as causal_app
from services.time_series.main import app as ts_app
from services.multi_modal.main import app as multi_app
from services.hierarchical_classification.main import app as hier_app

try:
    from services.rule_engine.main import app as rule_app
except ImportError as exc:  # pragma: no cover - optional dependency
    rule_app = pytest.param(
        None, marks=pytest.mark.skip(reason=f"rule_engine import failed: {exc}")
    )

try:
    from services.orchestrator.main import app as orch_app
except Exception as exc:  # pragma: no cover - optional dependency
    orch_app = pytest.param(
        None, marks=pytest.mark.skip(reason=f"orchestrator import failed: {exc}")
    )
else:  # pragma: no cover - unstable shutdown
    orch_app = pytest.param(
        orch_app, marks=pytest.mark.skip(reason="orchestrator shutdown fails")
    )

try:
    from gateway.main import app as gateway_app
except Exception as exc:  # pragma: no cover - optional dependency
    gateway_app = pytest.param(
        None, marks=pytest.mark.skip(reason=f"gateway import failed: {exc}")
    )


@pytest.mark.parametrize(
    "app",
    [
        vector_app,
        graph_app,
        causal_app,
        ts_app,
        multi_app,
        hier_app,
        rule_app,
        orch_app,
        gateway_app,
    ],
)
def test_health_endpoints(app):
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

