#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Orchestrator Micro-service
-------------------------

Glues the AI platform together. Listens on a Redis stream for incoming events,
dispatches to micro-services via HTTP, and persists to Neo4j and TimescaleDB.
Exposes /publish to push events for testing.

Orchestrator Service (Refactored)
---------------------------------

This service listens for events on a Redis stream, dispatches them to other
microservices, and persists data to Neo4j and TimescaleDB. It is now
fully asynchronous and secured with API key authentication.
"""

import asyncio
import json
import os
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import httpx
import psycopg2
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from neo4j import AsyncGraphDatabase, basic_auth
from pydantic import BaseModel
from redis.exceptions import ResponseError

# --- Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
REDIS_URL = os.getenv("REDIS_URL")
NEO4J_URL = os.getenv("NEO4J_URL")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
TS_HOST = os.getenv("TS_HOST")
TS_USER = os.getenv("TS_USER")
TS_PASSWORD = os.getenv("TS_PASSWORD")
TS_DB = os.getenv("TS_DB")
RULE_ENGINE_URL = os.getenv("RULE_ENGINE_URL", "http://rule_engine:8000")
API_KEY = os.getenv("API_KEY")
REDIS_STREAM = "events"
REDIS_GROUP = "orchestrator_group"
CONSUMER_NAME = "orchestrator_consumer_1"

# --- Logging ---
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Pre-flight Checks ---
if not all([REDIS_URL, NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD, TS_HOST, TS_USER, TS_PASSWORD, TS_DB, API_KEY]):
    raise ValueError("One or more required environment variables are not set.")

# --- Globals ---
redis_client: redis.Redis
neo4j_driver: AsyncGraphDatabase
listener_task: asyncio.Task

# --- Models ---
class Event(BaseModel):
    type: str
    data: Dict[str, Any]

# --- Database Connections ---
def get_timescaledb_conn():
    """Establishes a connection to TimescaleDB."""
    try:
        return psycopg2.connect(
            host=TS_HOST, user=TS_USER, password=TS_PASSWORD, dbname=TS_DB
        )
    except psycopg2.OperationalError as e:
        logger.error(f"Failed to connect to TimescaleDB: {e}", exc_info=True)
        return None

# --- Event Processing ---
async def process_event(event: Dict[bytes, bytes]):
    """Processes a single event from the Redis stream."""
    try:
        event_data = {k.decode('utf-8'): json.loads(v.decode('utf-8')) for k, v in event.items()}
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Failed to decode event data: {e}", exc_info=True)
        return

    event_type = event_data.get("type")
    payload = event_data.get("data", {})

    if event_type == "sensor":
        # Dispatch to rule engine
        actions = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{RULE_ENGINE_URL}/evaluate", json=payload, timeout=20.0)
                if resp.status_code == 200:
                    actions = resp.json().get("actions", [])
        except httpx.RequestError as e:
            logger.error(f"Failed to call rule engine: {e}", exc_info=True)

        # Persist actions to Neo4j
        if actions:
            try:
                async with neo4j_driver.session() as session:
                    for action in actions:
                        await session.run(
                            "CREATE (e:Event {type: $type, action: $action, timestamp: datetime()})",
                            type=event_type, action=action
                        )
            except Exception as e:
                logger.error(f"Failed to persist to Neo4j: {e}", exc_info=True)

        # Persist numeric values to TimescaleDB
        conn = get_timescaledb_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    for key, value in payload.items():
                        if isinstance(value, (int, float)):
                            cur.execute(
                                "INSERT INTO metrics (time, measurement, value) VALUES (NOW(), %s, %s);",
                                (key, float(value))
                            )
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to insert into TimescaleDB: {e}", exc_info=True)
            finally:
                conn.close()

# --- Redis Listener ---
async def event_listener():
    """Listens for events on the Redis stream and processes them."""
    try:
        await redis_client.xgroup_create(REDIS_STREAM, REDIS_GROUP, id="$", mkstream=True)
    except ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    while True:
        try:
            results = await redis_client.xreadgroup(
                REDIS_GROUP, CONSUMER_NAME, {REDIS_STREAM: ">"}, count=10, block=5000
            )
            for _, messages in results:
                for msg_id, fields in messages:
                    await process_event(fields)
                    await redis_client.xack(REDIS_STREAM, REDIS_GROUP, msg_id)
        except Exception as e:
            logger.error(f"Error in event listener loop: {e}", exc_info=True)
            await asyncio.sleep(5) # Backoff before retrying

# --- FastAPI Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, neo4j_driver, listener_task
    redis_client = redis.from_url(REDIS_URL, decode_responses=False)
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    listener_task = asyncio.create_task(event_listener())
    
    conn = get_timescaledb_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS metrics (time TIMESTAMPTZ, measurement TEXT, value DOUBLE PRECISION);")
        conn.commit()
        conn.close()

    yield
    
    listener_task.cancel()
    await redis_client.aclose()
    await neo4j_driver.close()

# --- Service Initialization ---
app = FastAPI(
    title="Orchestrator Service",
    description="Listens for and processes events from a Redis stream.",
    version="2.0.0",
    lifespan=lifespan
)

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if key == API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- API Endpoints ---
@app.post("/publish", summary="Publish an event to the stream")
async def publish_event(event: Event, api_key: str = Security(get_api_key)):
    try:
        encoded_data = {k: json.dumps(v) for k, v in event.dict().items()}
        msg_id = await redis_client.xadd(REDIS_STREAM, encoded_data)
        return {"message_id": msg_id.decode('utf-8')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", summary="Health check endpoint")
async def health():
    return {"status": "ok"}
