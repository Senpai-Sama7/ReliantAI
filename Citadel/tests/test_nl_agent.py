import importlib
import json

from fastapi.testclient import TestClient


def _load_nl_agent(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

    from services.nl_agent import main as nl_agent

    return importlib.reload(nl_agent)


def test_nl_agent_health_reports_gemini_backend(monkeypatch):
    nl_agent = _load_nl_agent(monkeypatch)

    with TestClient(nl_agent.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["backend"] == "gemini"
    assert response.json()["model_status"] == "configured"


def test_nl_agent_non_stream_returns_chat_completion_shape(monkeypatch):
    nl_agent = _load_nl_agent(monkeypatch)

    async def fake_resolve(_request):
        return "Hello from Gemini."

    monkeypatch.setattr(nl_agent, "_resolve_chat_completion", fake_resolve)

    with TestClient(nl_agent.app) as client:
        response = client.post(
            "/v1/chat/completions",
            headers={"X-API-Key": "test-api-key"},
            json={
                "model": "gemini-test-model",
                "messages": [{"role": "user", "content": "Say hello."}],
                "stream": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == "gemini-test-model"
    assert body["choices"][0]["message"]["content"] == "Hello from Gemini."


def test_nl_agent_stream_returns_sse_chunks(monkeypatch):
    nl_agent = _load_nl_agent(monkeypatch)

    async def fake_resolve(_request):
        return "Hello from Gemini streaming."

    monkeypatch.setattr(nl_agent, "_resolve_chat_completion", fake_resolve)

    with TestClient(nl_agent.app) as client:
        with client.stream(
            "POST",
            "/v1/chat/completions",
            headers={"X-API-Key": "test-api-key"},
            json={
                "messages": [{"role": "user", "content": "Say hello."}],
                "stream": True,
            },
        ) as response:
            lines = [line for line in response.iter_lines() if line]

    assert response.status_code == 200
    payload_line = next(line for line in lines if line.startswith("data: {"))
    payload = json.loads(payload_line[6:])
    assert payload["object"] == "chat.completion.chunk"
    assert payload["choices"][0]["delta"]["content"]
    assert lines[-1] == "data: [DONE]"
