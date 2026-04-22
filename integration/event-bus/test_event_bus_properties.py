"""
Property-based tests for Event Bus
NO MOCKING - Real Redis, real event publishing/consuming
"""
import pytest
import asyncio
import json
from datetime import datetime
from hypothesis import given, settings, strategies as st, HealthCheck
from httpx import AsyncClient, ASGITransport
from event_bus import app, Event, EventMetadata, EventType, lifespan


@pytest.fixture
async def client():
    """Async client that manually triggers lifespan for Redis initialization"""
    async with lifespan(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c

@pytest.fixture(autouse=True)
async def cleanup_redis():
    """Flush Redis before each test"""
    # Lifespan will initialize app.state.redis
    async with lifespan(app):
        if hasattr(app.state, "redis") and app.state.redis:
            await app.state.redis.flushdb()
    yield




@pytest.mark.asyncio
@settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])

@given(
    event_type=st.sampled_from([e.value for e in EventType]),
    tenant_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    source_service=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    correlation_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    payload=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.booleans())
    )
)
async def test_event_publish_and_retrieve(client, event_type, tenant_id, source_service, correlation_id, payload):
    """Property 1: Published events can be retrieved by ID"""
    # Publish event
    response = await client.post("/publish", json={
        "event_type": event_type,
        "payload": payload,
        "correlation_id": correlation_id,
        "tenant_id": tenant_id,
        "source_service": source_service
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "published"
    assert "event_id" in data
    assert "channel" in data
    
    event_id = data["event_id"]
    # Retrieve event
    get_response = await client.get(f"/event/{event_id}")
    assert get_response.status_code == 200
    
    event_data = get_response.json()
    assert event_data["metadata"]["event_id"] == event_id
    assert event_data["metadata"]["event_type"] == event_type
    assert event_data["metadata"]["tenant_id"] == tenant_id
    assert event_data["metadata"]["source_service"] == source_service
    assert event_data["metadata"]["correlation_id"] == correlation_id
    assert event_data["payload"] == payload


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Property 2: Health endpoint returns healthy status"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["redis"] == "connected"
    assert data["service"] == "event-bus"


@pytest.mark.asyncio
async def test_event_not_found(client):
    """Property 3: Non-existent event returns 404"""
    response = await client.get("/event/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_event_type(client):
    """Property 4: Invalid event type returns 422"""
    response = await client.post("/publish", json={
        "event_type": "invalid.event.type",
        "payload": {"test": "data"},
        "correlation_id": "test-123",
        "tenant_id": "test-tenant",
        "source_service": "test-service"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_dlq_empty(client):
    """Property 5: DLQ is empty initially"""
    response = await client.get("/dlq")
    assert response.status_code == 200
    data = response.json()
    assert data["dlq_size"] == 0
    assert data["events"] == []


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """Property 6: Metrics endpoint returns Prometheus format"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    # Should contain event bus metrics
    assert b"events_published_total" in response.content


@pytest.mark.asyncio
async def test_event_ttl(client):
    """Property 7: Events expire after TTL"""
    # Publish event
    response = await client.post("/publish", json={
        "event_type": "lead.created",
        "payload": {"test": "ttl"},
        "correlation_id": "ttl-test",
        "tenant_id": "test-tenant",
        "source_service": "test-service"
    })
    
    assert response.status_code == 200
    event_id = response.json()["event_id"]
    
    # Verify event exists
    get_response = await client.get(f"/event/{event_id}")
    assert get_response.status_code == 200
    
    # Check TTL is set (should be close to 86400 seconds)
    ttl = await app.state.redis.ttl(f"event:{event_id}")
    assert ttl > 0

    assert ttl <= 86400


@pytest.mark.asyncio
async def test_multiple_events_same_channel(client):
    """Property 8: Multiple events can be published to same channel"""
    event_ids = []
    
    # Publish 5 events
    for i in range(5):
        response = await client.post("/publish", json={
            "event_type": "lead.created",
            "payload": {"index": i},
            "correlation_id": f"batch-{i}",
            "tenant_id": "test-tenant",
            "source_service": "test-service"
        })
        assert response.status_code == 200
        event_ids.append(response.json()["event_id"])
    
    # Verify all events exist
    for event_id in event_ids:
        get_response = await client.get(f"/event/{event_id}")
        assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_event_schema_validation(client):
    """Property 9: Event schema is validated correctly"""
    # Missing required field
    response = await client.post("/publish", json={
        "event_type": "lead.created",
        "payload": {"test": "data"}
        # Missing correlation_id, tenant_id, source_service
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_concurrent_event_publishing(client):
    """Property 10: Concurrent event publishing works correctly"""
    async def publish_event(i):
        return await client.post("/publish", json={
            "event_type": "lead.created",
            "payload": {"concurrent": True, "index": i},
            "correlation_id": f"concurrent-{i}",
            "tenant_id": "test-tenant",
            "source_service": "test-service"
        })
    
    # Publish 10 events concurrently
    tasks = [publish_event(i) for i in range(10)]
    responses = await asyncio.gather(*tasks)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200
        assert response.json()["status"] == "published"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
