#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the API Gateway
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Assuming the gateway's main app is accessible for import
# This might require adjusting the Python path
from notebooks.gateway.main import app

client = TestClient(app)

@pytest.mark.parametrize("service, endpoint, payload, mock_response", [
    ("vector", "search", {"query": "test"}, {"results": []}),
    ("knowledge", "query", {"query": "MATCH (n) RETURN n"}, {"result": []}),
    ("time", "forecast", {"series": [1, 2, 3]}, {"forecast": [4, 5, 6]}),
    ("causal", "infer", {"data": {}}, {"inference": "done"}),
    ("multi", "process", {"image_url": "http://a.com/b.jpg", "text": "c"}, {"processed": "data"}),
    ("hier", "classify", {"text": "some text"}, {"classification": "A/B/C"}),
    ("rule", "evaluate", {"data": {}}, {"result": "pass"}),
    ("orch", "publish", {"type": "event", "data": {}}, {"status": "published"}),
    ("web", "search", {"query": "hello"}, {"results": ["http://world.com"]}),
    ("shell", "execute", {"command": "echo 'test'"}, {"output": "test\n", "return_code": 0}),
])
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_gateway_routes_successful(mock_post, service, endpoint, payload, mock_response):
    """
    Tests that the gateway correctly routes requests to the backend services
    and returns their successful responses.
    """
    # Mock the response from the downstream service
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_response

    # Make the request to the gateway
    response = client.post(f"/{service}/{endpoint}", json=payload)

    assert response.status_code == 200
    assert response.json() == mock_response

@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_gateway_service_unavailable(mock_post):
    """
    Tests that the gateway returns a 503 Service Unavailable error
    when a downstream service cannot be reached.
    """
    # Mock a network error
    import httpx
    mock_post.side_effect = httpx.ConnectError("Connection refused")

    response = client.post("/vector/search", json={"query": "test"})

    assert response.status_code == 503
    assert "Service Unavailable" in response.json()["detail"]

@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_gateway_service_error(mock_post):
    """
    Tests that the gateway returns a 502 Bad Gateway error
    when a downstream service returns a server error (e.g., 500).
    """
    # Mock a 500 error from the downstream service
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Internal Server Error"
    mock_post.return_value.raise_for_status.side_effect = Exception("Internal Server Error")


    response = client.post("/knowledge/query", json={"query": "invalid"})

    assert response.status_code == 502
    assert "Bad Gateway" in response.json()["detail"]

def test_gateway_health_check():
    """
    Tests the gateway's own health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "gateway": "alive"}
