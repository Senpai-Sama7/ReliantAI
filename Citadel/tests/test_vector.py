import json

from fastapi.testclient import TestClient

from services.vector_search.main import app as vector_app


def test_index_and_search():
    client = TestClient(vector_app)
    # Index two simple documents
    docs = [
        {"id": "1", "text": "hello world"},
        {"id": "2", "text": "machine learning is fun"},
    ]
    resp = client.post("/index", json=docs)
    assert resp.status_code == 200
    assert resp.json()["indexed"] == 2
    # Search for 'machine'
    resp = client.post("/search", json={"query": "machine", "top_k": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert body["results"][0]["id"] in {"1", "2"}