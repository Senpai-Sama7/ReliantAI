#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Time‑Series Analytics Micro‑service
----------------------------------

This service provides endpoints for forecasting and anomaly detection
over univariate time‑series data using Facebook Prophet. Input data
should be supplied as a list of objects with `ds` (timestamp in
ISO‑format) and `y` (numeric value) keys. Forecasting returns the
predicted mean and confidence intervals for both historical and future
periods. Anomaly detection flags points where the observed value falls
outside the prediction interval.

Note: Prophet can take a few seconds to initialise on the first call
because it compiles a Stan model. In a long‑running service this cost
is amortised.

Time-Series Analytics Service (Refactored)
------------------------------------------

This service provides secure endpoints for forecasting and anomaly detection
using Facebook Prophet. It is configured via environment variables and
protected by API key authentication.
"""

import os
import logging
from typing import List

import pandas as pd
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from prophet import Prophet

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
class DataPoint(BaseModel):
    ds: str = Field(..., description="Timestamp in YYYY-MM-DD or ISO format")
    y: float = Field(..., description="Observed value at the timestamp")

class ForecastRequest(BaseModel):
    data: List[DataPoint] = Field(..., description="Historical time-series observations")
    horizon: int = Field(..., description="Number of future steps to forecast", ge=1, le=730)

# --- Service Initialization ---
app = FastAPI(
    title="Time Series Service",
    description="Provides forecasting and anomaly detection for time-series data.",
    version="2.0.0"
)

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if key == API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- Helper Function ---
def _prepare_dataframe(points: List[DataPoint]) -> pd.DataFrame:
    try:
        df = pd.DataFrame([p.dict() for p in points])
        df['ds'] = pd.to_datetime(df['ds'])
        return df
    except Exception as e:
        logger.error(f"Error preparing dataframe: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid data or datetime format: {e}")

# --- API Endpoints ---
@app.post("/forecast", summary="Forecast time series")
def forecast(req: ForecastRequest, api_key: str = Security(get_api_key)):
    if not req.data:
        raise HTTPException(status_code=400, detail="Input data cannot be empty.")
    
    df = _prepare_dataframe(req.data)
    model = Prophet(interval_width=0.95)
    
    try:
        model.fit(df)
        future = model.make_future_dataframe(periods=req.horizon)
        forecast_df = model.predict(future)
        result = forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict(orient='records')
        return {"forecast": result}
    except Exception as e:
        logger.error(f"Error during forecasting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Model fitting or prediction failed: {e}")

@app.post("/anomaly", summary="Detect anomalies")
def anomaly_detection(req: ForecastRequest, api_key: str = Security(get_api_key)):
    if not req.data:
        raise HTTPException(status_code=400, detail="Input data cannot be empty.")
        
    df = _prepare_dataframe(req.data)
    model = Prophet(interval_width=0.99) # Wider interval for anomaly detection
    
    try:
        model.fit(df)
        forecast_df = model.predict(df)
        result_df = pd.concat([df.set_index('ds')['y'], forecast_df.set_index('ds')[['yhat_lower', 'yhat_upper']]], axis=1)
        result_df['anomaly'] = (result_df['y'] < result_df['yhat_lower']) | (result_df['y'] > result_df['yhat_upper'])
        
        anomalies = result_df[result_df['anomaly']].reset_index().to_dict(orient='records')
        return {"anomalies": anomalies}
    except Exception as e:
        logger.error(f"Error during anomaly detection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Model fitting or prediction failed: {e}")

@app.get("/health", summary="Health check endpoint")
def health():
    """Provides a basic health check of the service."""
    return {"status": "ok"}
