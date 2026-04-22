from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient


def _install_fake_modules() -> None:
    auth_module = types.ModuleType("auth_integration")
    security = HTTPBearer(auto_error=False)

    async def require_authenticated_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ) -> dict[str, object]:
        if credentials is None or credentials.credentials != "valid-token":
            raise HTTPException(status_code=401, detail="Missing authentication credentials")
        return {"username": "tester", "roles": ["admin"]}

    auth_module.require_authenticated_user = require_authenticated_user
    auth_module.get_current_user = require_authenticated_user
    auth_module.AUTH_ENABLED = True

    class AuthIntegration:
        def __init__(self) -> None:
            self.enabled = True

    auth_module.AuthIntegration = AuthIntegration
    sys.modules["auth_integration"] = auth_module

    layer1 = types.ModuleType("agents.layer1.workflow")
    async def run_layer1(**_: object) -> dict[str, object]:
        return {"routing_tier": "T2Deliberative", "confidence": 0.8, "prior_summary": "ok"}
    layer1.run_layer1 = run_layer1
    sys.modules["agents.layer1.workflow"] = layer1

    layer2 = types.ModuleType("agents.layer2.workflow")
    async def run_layer2(**_: object) -> dict[str, object]:
        return {"gate_decision": {"block": False}}
    layer2.run_layer2 = run_layer2
    sys.modules["agents.layer2.workflow"] = layer2

    layer3 = types.ModuleType("agents.layer3.dispatcher")
    async def dispatch(**_: object) -> dict[str, object]:
        return {"specialists_used": ["alpha"], "aggregated_confidence": 0.9}
    layer3.dispatch = dispatch
    sys.modules["agents.layer3.dispatcher"] = layer3

    layer4 = types.ModuleType("agents.layer4.workflow")
    async def run_layer4(**_: object) -> dict[str, object]:
        return {"final_approved": True, "iteration": 1, "audit_report": {"overall_verdict": "pass"}}
    layer4.run_layer4 = run_layer4
    sys.modules["agents.layer4.workflow"] = layer4

    memory = types.ModuleType("memory.search")
    async def search_memory(**_: object) -> list[dict[str, object]]:
        return [{"id": "mem-1"}]
    async def save_memory(**_: object) -> str:
        return "mem-1"
    memory.search_memory = search_memory
    memory.save_memory = save_memory
    sys.modules["memory.search"] = memory


def _load_main_module():
    _install_fake_modules()
    main_path = Path(__file__).resolve().parent / "main.py"
    spec = importlib.util.spec_from_file_location("isolated_apex_main", main_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protected_route_rejects_missing_auth() -> None:
    module = _load_main_module()
    client = TestClient(module.app)

    response = client.post("/agents/layer1/analyze", json={"task": "test"})

    assert response.status_code == 401


def test_protected_route_accepts_valid_auth() -> None:
    module = _load_main_module()
    client = TestClient(module.app)

    response = client.post(
        "/memory/search",
        json={"query": "audit"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
