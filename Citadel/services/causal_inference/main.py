#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Causal Inference Micro‑service
-----------------------------

This service exposes a simple interface for estimating causal effects
using the DoWhy and EconML libraries. Given a dataset, a treatment
variable and an outcome variable, it identifies a causal model,
estimates the effect of the treatment on the outcome using backdoor
adjustment and returns the point estimate.

The API accepts data as a list of dictionaries (each row), but you can
also upload CSV files via the API gateway. The implementation is
intentionally basic to keep the service lightweight; more advanced
estimators (e.g. Double Machine Learning) can be plugged in with
minimal modifications.

Causal Inference Service (Refactored)
-------------------------------------

This service exposes a secure interface for estimating causal effects using
the DoWhy library. It is configured via environment variables and protected
by API key authentication.
"""

import os
import logging
from typing import List, Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dowhy import CausalModel

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
class EffectRequest(BaseModel):
    data: List[Dict[str, float]] = Field(..., description="Rows of the dataset.")
    treatment: str = Field(..., description="Name of the treatment column.")
    outcome: str = Field(..., description="Name of the outcome column.")
    confounders: Optional[List[str]] = Field(None, description="Optional list of confounder column names.")

# --- Service Initialization ---
app = FastAPI(
    title="Causal Inference Service",
    description="Estimates causal effects from observational data.",
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
@app.post("/effect", summary="Estimate treatment effect")
def estimate_effect(req: EffectRequest, api_key: str = Security(get_api_key)):
    """
    Estimate the causal effect of a treatment on an outcome using the backdoor
    criterion and propensity score matching.
    """
    if not req.data:
        raise HTTPException(status_code=400, detail="Dataset cannot be empty.")

    try:
        df = pd.DataFrame(req.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data format: {e}")

    if req.treatment not in df.columns or req.outcome not in df.columns:
        raise HTTPException(status_code=400, detail="Treatment or outcome column not found in data.")

    confounders = req.confounders
    if not confounders:
        confounders = [c for c in df.columns if c not in {req.treatment, req.outcome}]
        logger.info(f"No confounders provided. Using all other columns as confounders: {confounders}")

    try:
        model = CausalModel(
            data=df,
            treatment=req.treatment,
            outcome=req.outcome,
            common_causes=confounders,
        )
        identified_effect = model.identify_effect(proceed_when_unidentifiable=True)
        estimate = model.estimate_effect(
            identified_effect,
            method_name="backdoor.propensity_score_matching"
        )
        effect_value = float(estimate.value)
        return {"estimated_effect": effect_value}
    except Exception as e:
        logger.error(f"Error during causal inference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during causal inference: {str(e)}")

@app.get("/health", summary="Health check endpoint")
def health():
    """Provides a basic health check of the service."""
    return {"status": "ok"}
