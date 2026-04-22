#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Knowledge Graph Micro-service.

This service exposes a minimal API around a Neo4j graph database.  For the
unit tests in this repository we do not always have Neo4j or the associated
Python driver available.  To allow the tests to import the module and exercise
the health endpoint we provide a lightweight *stub* mode.  When the driver or
required environment configuration is missing the service falls back to this
stub which simply reports that the database is unavailable.
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# The Neo4j driver is optional for the test environment.  If it or the required
# environment variables are missing we run in a stub mode.
try:  # pragma: no cover - import depends on environment
    from neo4j import AsyncGraphDatabase, exceptions
except Exception as exc:  # pragma: no cover - optional dependency
    AsyncGraphDatabase = None  # type: ignore
    exceptions = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


# --- Configuration ---------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
NEO4J_URL = os.getenv("NEO4J_URL")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
API_KEY = os.getenv("API_KEY")


# --- Logging ---------------------------------------------------------------------------
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# --- Mode Selection --------------------------------------------------------------------
# If any configuration or imports are missing we fall back to a stub
# implementation so that the service can still be imported in tests.
STUB_MODE = bool(
    _IMPORT_ERROR or not all([NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD, API_KEY])
)
if STUB_MODE:
    logger.warning(
        "Knowledge graph running in stub mode: %s",
        _IMPORT_ERROR or "missing configuration",
    )


driver: AsyncGraphDatabase | None = None

if STUB_MODE:
    # ------------------------------------------------------------------ Stubbed Service
    app = FastAPI(
        title="Knowledge Graph Service (stub)",
        description="Stub implementation used when Neo4j is unavailable.",
        version="0.0.0",
    )

    @app.get("/health", summary="Health check endpoint")
    async def health_check_stub() -> Dict[str, str]:
        return {"status": "ok", "neo4j_connection": "unavailable"}

else:
    # ------------------------------------------------------------------ Full Service
    # --- Neo4j Driver Management --------------------------------------------------
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage the Neo4j driver lifecycle."""
        global driver
        logger.info("Initializing Neo4j driver for %s", NEO4J_URL)
        try:
            driver = AsyncGraphDatabase.driver(
                NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            await driver.verify_connectivity()
            logger.info("Neo4j driver initialized successfully.")
        except exceptions.AuthError as e:  # type: ignore[union-attr]
            logger.critical("Neo4j authentication failed: %s", e)
            raise RuntimeError("Neo4j authentication failed.")
        except Exception as e:  # pragma: no cover - defensive
            logger.critical("Failed to initialize Neo4j driver: %s", e, exc_info=True)
            raise RuntimeError(f"Neo4j driver initialization failed: {e}")

        yield

        if driver:
            logger.info("Closing Neo4j driver.")
            await driver.close()

    # --- Models -------------------------------------------------------------------
    class CypherQuery(BaseModel):
        query: str
        parameters: Dict[str, Any] = {}

    # --- Service Initialization ----------------------------------------------------
    app = FastAPI(
        title="Knowledge Graph Service",
        description="Provides an interface for querying a Neo4j graph database.",
        version="2.0.0",
        lifespan=lifespan,
    )

    # --- Security -----------------------------------------------------------------
    api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

    async def get_api_key(key: str = Security(api_key_header)) -> str:
        if key == API_KEY:
            return key
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # --- API Endpoints -------------------------------------------------------------
    @app.post("/query", summary="Execute a Cypher query")
    async def execute_query(
        request: CypherQuery, api_key: str = Security(get_api_key)
    ):
        """Execute a read-only Cypher query against the Neo4j database."""

        query = request.query.strip()
        if not query.lower().startswith("match"):
            raise HTTPException(
                status_code=400,
                detail="Query is not read-only. Only queries beginning with 'MATCH' are allowed.",
            )

        try:
            async with driver.session() as session:  # type: ignore[union-attr]
                result = await session.run(query, request.parameters)
                records = [record.data() async for record in result]
                logger.info(
                    "Query executed successfully, returned %d records.",
                    len(records),
                )
                return {"result": records}
        except exceptions.CypherSyntaxError as e:  # type: ignore[union-attr]
            logger.error("Cypher syntax error in query '%s': %s", query, e)
            raise HTTPException(status_code=400, detail=f"Cypher Syntax Error: {e.message}")
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Error executing Cypher query: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health", summary="Health check endpoint")
    async def health_check() -> Dict[str, str]:
        if not driver:
            return {"status": "error", "neo4j_connection": "uninitialized"}
        try:
            await driver.verify_connectivity()
            return {"status": "ok", "neo4j_connection": "ok"}
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Health check failed: %s", e)
            return {"status": "error", "neo4j_connection": "failed"}

