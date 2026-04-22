import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import os
import json
import time
import asyncio
import logging

# Import the main FastAPI app from the orchestrator service
from services.orchestrator.main import app, REDIS_STREAM, REDIS_GROUP, CONSUMER_NAME, API_KEY

# Set a test API key for the environment
TEST_API_KEY = "test_api_key"
os.environ["API_KEY"] = TEST_API_KEY

# Override Redis client for testing
@pytest.fixture(name="mock_redis_client")
def mock_redis_client_fixture():
    with patch("redis.asyncio.Redis", autospec=True) as mock_redis:
        mock_redis_instance = mock_redis.return_value
        mock_redis_instance.xadd = AsyncMock()
        mock_redis_instance.xgroup_create = AsyncMock()
        mock_redis_instance.xreadgroup = AsyncMock(return_value=[])
        mock_redis_instance.xack = AsyncMock()
        mock_redis_instance.xtrim = AsyncMock()
        mock_redis_instance.aclose = AsyncMock()
        yield mock_redis_instance

# Override Neo4j driver for testing
@pytest.fixture(name="mock_neo4j_driver")
def mock_neo4j_driver_fixture():
    with patch("neo4j.GraphDatabase.driver", autospec=True) as mock_driver:
        mock_driver_instance = mock_driver.return_value
        mock_session = MagicMock()
        mock_session.run = MagicMock()
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver_instance.session.return_value.__exit__.return_value = None
        yield mock_driver_instance

# Override psycopg2.connect for testing
@pytest.fixture(name="mock_psycopg2_connect")
def mock_psycopg2_connect_fixture():
    with patch("psycopg2.connect", autospec=True) as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_connect

# Test client fixture
@pytest.fixture(name="client")
def client_fixture(mock_redis_client, mock_neo4j_driver, mock_psycopg2_connect):
    # Ensure the app's state is reset for each test
    app.state.redis = mock_redis_client
    app.state.task = AsyncMock() # Mock the background task
    with TestClient(app) as test_client:
        yield test_client

# --- Tests ---

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_publish_event_success(client, mock_redis_client):
    event_payload = {"type": "test_event", "data": {"key": "value"}}
    headers = {"X-API-Key": TEST_API_KEY}
    mock_redis_client.xadd.return_value = b"123-0" # Mock Redis message ID

    response = client.post("/publish", json=event_payload, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"message_id": "123-0"}
    mock_redis_client.xadd.assert_called_once()
    args, kwargs = mock_redis_client.xadd.call_args
    assert args[0] == "events" # Default stream name
    assert json.loads(kwargs["mapping"]["type"]) == "test_event"
    assert json.loads(kwargs["mapping"]["data"]) == {"key": "value"}

def test_publish_event_no_api_key(client):
    event_payload = {"type": "test_event", "data": {"key": "value"}}
    response = client.post("/publish", json=event_payload) # No API key

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}

def test_publish_event_invalid_api_key(client):
    event_payload = {"type": "test_event", "data": {"key": "value"}}
    headers = {"X-API-Key": "wrong_key"}
    response = client.post("/publish", json=event_payload, headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}

@pytest.mark.asyncio
async def test_process_event_sensor_type(mock_redis_client, mock_neo4j_driver, mock_psycopg2_connect):
    # Mock httpx.AsyncClient for rule engine call
    with patch("httpx.AsyncClient", autospec=True) as mock_httpx_client:
        mock_httpx_instance = mock_httpx_client.return_value
        mock_httpx_instance.__aenter__.return_value.post = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"actions": ["action1", "action2"]}))

        from services.orchestrator.main import process_event # Import here to get patched httpx

        event_data = {
            b"type": b"sensor",
            b"data": b"{\"temperature\": 25.5, \"humidity\": 60}"
        }
        await process_event(event_data)

        # Verify rule engine call
        mock_httpx_instance.__aenter__.return_value.post.assert_called_once_with(
            f"{os.getenv('RULE_ENGINE_URL', 'http://rule_engine:8000')}/evaluate",
            json={"temperature": 25.5, "humidity": 60},
            timeout=20.0
        )

        # Verify Neo4j persistence
        mock_neo4j_driver.session.return_value.__enter__.return_value.run.assert_any_call(
            "CREATE (e:Event {type: $type, action: $action})",
            type="sensor",
            action="action1"
        )
        mock_neo4j_driver.session.return_value.__enter__.return_value.run.assert_any_call(
            "CREATE (e:Event {type: $type, action: $action})",
            type="sensor",
            action="action2"
        )

        # Verify TimescaleDB insertion
        mock_psycopg2_connect.return_value.cursor.return_value.execute.assert_any_call(
            "INSERT INTO metrics (time, measurement, value) VALUES (to_timestamp(%s), %s, %s);",
            (pytest.approx(time.time(), abs=2), "temperature", 25.5)
        )
        mock_psycopg2_connect.return_value.cursor.return_value.execute.assert_any_call(
            "INSERT INTO metrics (time, measurement, value) VALUES (to_timestamp(%s), %s, %s);",
            (pytest.approx(time.time(), abs=2), "humidity", 60.0)
        )
        mock_psycopg2_connect.return_value.commit.assert_called()

@pytest.mark.asyncio
async def test_process_event_non_sensor_type(mock_redis_client, mock_neo4j_driver, mock_psycopg2_connect):
    # Ensure httpx.AsyncClient is not called for non-sensor events
    with patch("httpx.AsyncClient", autospec=True) as mock_httpx_client:
        from services.orchestrator.main import process_event

        event_data = {
            b"type": b'"other_event"',
            b"data": b"{\"message\": \"hello\"}"
        }
        await process_event(event_data)

        mock_httpx_client.assert_not_called()
        mock_neo4j_driver.session.return_value.__enter__.return_value.run.assert_not_called()
        mock_psycopg2_connect.assert_not_called()

@pytest.mark.asyncio
async def test_ensure_consumer_group(mock_redis_client):
    from services.orchestrator.main import ensure_consumer_group
    await ensure_consumer_group(mock_redis_client, REDIS_STREAM, REDIS_GROUP)
    mock_redis_client.xgroup_create.assert_called_once_with(REDIS_STREAM, REDIS_GROUP, id="$", mkstream=True)

@pytest.mark.asyncio
async def test_event_listener_processes_events(mock_redis_client, mock_neo4j_driver, mock_psycopg2_connect):
    # Mock a single event to be read
    mock_redis_client.xreadgroup.return_value = [
        [b"events", [[b"123-0", {b"type": b"sensor", b"data": b"{\"temp\": 20}"}]]]
    ]

    # Mock httpx.AsyncClient for rule engine call within process_event
    with patch("httpx.AsyncClient", autospec=True) as mock_httpx_client:
        mock_httpx_instance = mock_httpx_client.return_value
        mock_httpx_instance.__aenter__.return_value.post = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"actions": []}))

        from services.orchestrator.main import event_listener # Import here to get patched httpx

        # Run the listener for a short period
        task = asyncio.create_task(event_listener(mock_redis_client))
        await asyncio.sleep(0.1) # Give it a moment to run
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        mock_redis_client.xreadgroup.assert_called_once()
        mock_redis_client.xack.assert_called_once_with(REDIS_STREAM, REDIS_GROUP, b"123-0")
        mock_redis_client.xtrim.assert_called_once()

# Test error handling and logging
@pytest.mark.asyncio
async def test_insert_timeseries_error_logging(mock_psycopg2_connect, caplog):
    from services.orchestrator.main import insert_timeseries
    mock_psycopg2_connect.side_effect = Exception("DB connection error")

    with caplog.at_level(logging.ERROR):
        insert_timeseries("test_measurement", 10.0, time.time())
        assert "Failed to insert timeseries data: DB connection error" in caplog.text

@pytest.mark.asyncio
async def test_process_event_data_decode_error_logging(caplog):
    from services.orchestrator.main import process_event
    event_data = {b"type": b"invalid_json", b"data": b"{"} # Malformed JSON

    with caplog.at_level(logging.ERROR):
        await process_event(event_data)
        assert "Failed to decode event data:" in caplog.text

@pytest.mark.asyncio
async def test_process_event_rule_engine_error_logging(mock_neo4j_driver, mock_psycopg2_connect, caplog):
    with patch("httpx.AsyncClient", autospec=True) as mock_httpx_client:
        mock_httpx_instance = mock_httpx_client.return_value
        mock_httpx_instance.__aenter__.return_value.post = AsyncMock(side_effect=httpx.RequestError("Network error", request=MagicMock()))

        from services.orchestrator.main import process_event

        event_data = {
            b"type": b"sensor",
            b"data": b"{\"temperature\": 25.5}"
        }
        with caplog.at_level(logging.ERROR):
            await process_event(event_data)
            assert "Failed to call rule engine: Network error" in caplog.text

@pytest.mark.asyncio
async def test_process_event_neo4j_error_logging(mock_redis_client, mock_psycopg2_connect, caplog):
    with patch("httpx.AsyncClient", autospec=True) as mock_httpx_client:
        mock_httpx_instance = mock_httpx_client.return_value
        mock_httpx_instance.__aenter__.return_value.post = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"actions": ["action1"]}))

        mock_neo4j_driver.session.return_value.__enter__.return_value.run.side_effect = Exception("Neo4j error")

        from services.orchestrator.main import process_event

        event_data = {
            b"type": b"sensor",
            b"data": b"{\"temperature\": 25.5}"
        }
        with caplog.at_level(logging.ERROR):
            await process_event(event_data)
            assert "Failed to persist to Neo4j: Neo4j error" in caplog.text

@pytest.mark.asyncio
async def test_event_listener_processing_error_logging(mock_redis_client, caplog):
    mock_redis_client.xreadgroup.return_value = [
        [b"events", [[b"123-0", {b"type": b"sensor", b"data": b"{\"temp\": 20}"}]]]
    ]
    mock_redis_client.xack = AsyncMock() # Ensure xack is still mocked


    from services.orchestrator.main import event_listener

    task = asyncio.create_task(event_listener(mock_redis_client))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
        except asyncio.CancelledError:
            pass

    with caplog.at_level(logging.ERROR):
        assert "Error processing event or acknowledging:" in caplog.text
        mock_redis_client.xack.assert_called_once() # Should still attempt to ack even if process_event fails

@pytest.mark.asyncio
async def test_event_listener_trim_error_logging(mock_redis_client, caplog):
    mock_redis_client.xreadgroup.return_value = [] # No events to process
    mock_redis_client.xtrim.side_effect = Exception("Redis trim error")

    from services.orchestrator.main import event_listener

    task = asyncio.create_task(event_listener(mock_redis_client))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
            pass

    with caplog.at_level(logging.WARNING):
        assert "Error trimming Redis stream: Redis trim error" in caplog.text

@pytest.mark.asyncio
async def test_event_listener_unhandled_error_logging(mock_redis_client, caplog):
    mock_redis_client.xreadgroup.side_effect = Exception("Unhandled Redis error")

    from services.orchestrator.main import event_listener

    task = asyncio.create_task(event_listener(mock_redis_client))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
            pass

    with caplog.at_level(logging.ERROR):
        assert "Unhandled exception in event listener loop: Unhandled Redis error" in caplog.text