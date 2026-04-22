"""Coverage-focused tests for event-bus DLQ behavior."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

EVENT_BUS_DIR = Path(__file__).resolve().parents[1] / "event-bus"
sys.path.insert(0, str(EVENT_BUS_DIR))

import event_bus  # noqa: E402


class FakeRedis:
    """Minimal async Redis replacement for event-bus route testing."""

    def __init__(self, *, publish_error: Exception | None = None) -> None:
        self.publish_error = publish_error
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.lists: defaultdict[str, list[str]] = defaultdict(list)
        self.published: list[tuple[str, str]] = []

    async def ping(self) -> bool:
        return True

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self.values[key] = value
        self.ttls[key] = seconds

    async def publish(self, channel: str, value: str) -> int:
        if self.publish_error is not None:
            raise self.publish_error
        self.published.append((channel, value))
        return 1

    async def lpush(self, key: str, value: str) -> int:
        self.lists[key].insert(0, value)
        return len(self.lists[key])

    async def lindex(self, key: str, index: int) -> str | None:
        try:
            return self.lists[key][index]
        except IndexError:
            return None

    async def get(self, key: str) -> str | None:
        return self.values.get(key)


class FakePubSub:
    """Async pubsub stream that yields a fixed message list."""

    def __init__(self, messages: list[dict[str, object]]) -> None:
        self.messages = messages
        self.patterns: list[str] = []

    async def psubscribe(self, pattern: str) -> None:
        self.patterns.append(pattern)

    async def listen(self):
        for message in self.messages:
            yield message


@pytest.mark.asyncio
async def test_publish_failure_writes_event_to_dlq() -> None:
    fake_redis = FakeRedis(publish_error=RuntimeError("publish failed"))
    event_bus.app.state.redis = fake_redis

    async with AsyncClient(transport=ASGITransport(app=event_bus.app), base_url="http://testserver") as client:
        response = await client.post(
            "/publish",
            json={
                "event_type": "lead.created",
                "payload": {"lead_id": "lead-1"},
                "correlation_id": "corr-1",
                "tenant_id": "tenant-1",
                "source_service": "money",
            },
        )

        assert response.status_code == 500

        dlq_response = await client.get("/dlq")
        assert dlq_response.status_code == 200
        dlq_payload = dlq_response.json()
        assert dlq_payload["dlq_size"] == 1
        assert dlq_payload["events"][0]["error"] == "publish failed"
        assert dlq_payload["events"][0]["request"]["tenant_id"] == "tenant-1"


@pytest.mark.asyncio
async def test_process_subscriptions_writes_handler_errors_to_dlq() -> None:
    fake_redis = FakeRedis()
    event_payload = {
        "metadata": {
            "event_id": "evt-1",
            "event_type": "lead.created",
            "timestamp": "2026-03-06T00:00:00+00:00",
            "correlation_id": "corr-1",
            "tenant_id": "tenant-1",
            "source_service": "bap",
            "version": "1.0",
        },
        "payload": {"lead_id": "lead-1"},
    }

    fake_pubsub = FakePubSub(
        [
            {
                "type": "pmessage",
                "channel": b"events:lead",
                "data": json.dumps(event_payload),
            }
        ]
    )

    event_bus.app.state.redis = fake_redis
    event_bus.app.state.pubsub = fake_pubsub
    event_bus.handlers.clear()

    def failing_handler(event: event_bus.Event) -> None:
        raise RuntimeError(f"handler failed for {event.metadata.event_id}")

    event_bus.handlers[event_bus.EventType.LEAD_CREATED.value] = [failing_handler]

    await event_bus.process_subscriptions(event_bus.app)

    assert fake_pubsub.patterns == ["events:*"]
    assert fake_redis.lists["dlq:handler_errors"]
    dlq_entry = json.loads(fake_redis.lists["dlq:handler_errors"][0])
    assert dlq_entry["error"] == "handler failed for evt-1"
    assert dlq_entry["event"]["metadata"]["event_id"] == "evt-1"

    event_bus.handlers.clear()
