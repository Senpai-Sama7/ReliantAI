"""Live event-bus integration tests for Money dispatch completion."""

import os

import pytest
import requests


@pytest.mark.skipif(
    not os.getenv("LIVE_EVENT_BUS_URL"),
    reason="Set LIVE_EVENT_BUS_URL to run the live Money event-bus integration test",
)
def test_live_dispatch_completed_event_is_published(client, api_headers, monkeypatch: pytest.MonkeyPatch):
    """Dispatch completion publishes a retrievable event to the live event bus."""
    event_bus_url = os.environ["LIVE_EVENT_BUS_URL"]
    monkeypatch.setenv("EVENT_BUS_URL", event_bus_url)
    monkeypatch.setenv("DEFAULT_TENANT_ID", "money-live")

    response = client.post(
        "/dispatch",
        json={"customer_message": "AC not cooling", "outdoor_temp_f": 95.0},
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "complete"
    event_id = payload["result"]["event_bus_event_id"]

    event_response = requests.get(f"{event_bus_url}/event/{event_id}", timeout=5)
    assert event_response.status_code == 200

    event_payload = event_response.json()
    assert event_payload["metadata"]["event_type"] == "dispatch.completed"
    assert event_payload["metadata"]["tenant_id"] == "money-live"
    assert event_payload["payload"]["dispatch_id"] == payload["run_id"]
    assert event_payload["payload"]["status"] == "complete"
    assert "raw_output" in event_payload["payload"]["result"]
