#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Rule Engine Micro‑service
-------------------------

This service wraps a simple rule engine based on the Experta library.
Clients send event data (arbitrary key/value pairs) and receive a list
of actions produced by the rule engine. The example rules provided here
illustrate how to encode business logic with thresholds. You can extend
the rules by modifying the `RuleEngine` class.

Rule Engine Service (Refactored)
--------------------------------

This service wraps a simple rule engine based on the Experta library.
It is secured with API key authentication.
"""

import os
import logging
from typing import Dict, List, Any

from experta import Fact, Field, KnowledgeEngine, Rule, P
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# --- Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
API_KEY = os.getenv("API_KEY")

# --- Logging ---
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Pre-flight Checks ---
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set.")

# --- Models ---
class Event(BaseModel):
    __root__: Dict[str, float]

# --- Experta Rule Engine ---
class SensorReading(Fact):
    """A fact representing a sensor reading."""
    temperature = Field(float, mandatory=False)
    humidity = Field(float, mandatory=False)

class RuleEngine(KnowledgeEngine):
    """A simple rule engine for sensor data."""
    def __init__(self):
        super().__init__()
        self.actions: List[str] = []

    @Rule(SensorReading(temperature=P(lambda t: t > 30), humidity=P(lambda h: h > 70)))
    def high_heat_and_humidity(self):
        self.actions.append("alert_high_heat_and_humidity")

    @Rule(SensorReading(temperature=P(lambda t: t < 0)))
    def freezing(self):
        self.actions.append("alert_freezing")

# --- Service Initialization ---
app = FastAPI(
    title="Rule Engine Service",
    description="Evaluates events against a set of rules.",
    version="2.0.0"
)

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if key == API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- API Endpoints ---
@app.post("/evaluate", summary="Evaluate event through rules")
def evaluate(event: Event, api_key: str = Security(get_api_key)):
    """
    Evaluates an event with numeric attributes against the defined rules
    and returns a list of fired actions.
    """
    engine = RuleEngine()
    engine.reset()
    
    # Declare facts based on the event data
    facts_declared = 0
    if 'temperature' in event.__root__ and 'humidity' in event.__root__:
        engine.declare(SensorReading(
            temperature=event.__root__['temperature'],
            humidity=event.__root__['humidity']
        ))
        facts_declared += 1
    
    if facts_declared == 0:
        logger.warning(f"No valid facts to declare from event: {event.__root__}")

    engine.run()
    return {"actions": engine.actions}

@app.get("/health", summary="Health check endpoint")
def health():
    """Provides a basic health check of the service."""
    return {"status": "ok"}
