#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hierarchical Classification Micro‑service
---------------------------------------

This service trains and serves hierarchical classifiers using the
HiClass library. A model token is returned after training and must be
supplied when making predictions. The models are kept in memory for
the lifetime of the container; for persistence you would need to
implement model serialization and storage.

Hierarchical Classification Service (Refactored)
----------------------------------------------

This service trains and serves hierarchical classifiers using the HiClass library.
It now features model persistence to disk and is secured with API key
authentication.
"""

import os
import uuid
import logging
from typing import Dict, List

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier
from hiclass import Classifier

# --- Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
API_KEY = os.getenv("API_KEY")
MODELS_PATH = "/data/models"

# --- Logging ---
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Pre-flight Checks ---
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set.")

# --- Models ---
class TrainRequest(BaseModel):
    features: List[Dict[str, float]] = Field(..., description="Feature vectors")
    labels: List[Dict[str, str]] = Field(..., description="Label dictionaries; keys represent taxonomy levels")

class PredictRequest(BaseModel):
    model_id: str = Field(..., description="Identifier returned by /train")
    features: Dict[str, float] = Field(..., description="Feature vector to classify")

# --- Globals ---
_models: Dict[str, Classifier] = {}

# --- Service Initialization ---
app = FastAPI(
    title="Hierarchical Classification Service",
    description="Trains and serves hierarchical classifiers.",
    version="2.0.0"
)

@app.on_event("startup")
def startup_event():
    """Load pre-existing models from disk on startup."""
    os.makedirs(MODELS_PATH, exist_ok=True)
    for filename in os.listdir(MODELS_PATH):
        if filename.endswith(".joblib"):
            model_id = filename.split(".")[0]
            try:
                _models[model_id] = joblib.load(os.path.join(MODELS_PATH, filename))
                logger.info(f"Loaded model {model_id} from disk.")
            except Exception as e:
                logger.error(f"Failed to load model {model_id}: {e}", exc_info=True)

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if key == API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- API Endpoints ---
@app.post("/train", summary="Train a hierarchical classifier")
def train_model(req: TrainRequest, api_key: str = Security(get_api_key)):
    if not req.features or not req.labels:
        raise HTTPException(status_code=400, detail="Features and labels must be provided.")
    try:
        X = pd.DataFrame(req.features)
        y = pd.DataFrame(req.labels)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data format: {e}")

    base_estimator = RandomForestClassifier(n_estimators=50, random_state=42)
    clf = Classifier(classifier=base_estimator)
    
    try:
        clf.fit(X, y)
    except Exception as e:
        logger.error(f"Model training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

    model_id = uuid.uuid4().hex
    _models[model_id] = clf
    
    try:
        joblib.dump(clf, os.path.join(MODELS_PATH, f"{model_id}.joblib"))
        logger.info(f"Trained and saved new model: {model_id}")
    except Exception as e:
        logger.error(f"Failed to save model {model_id}: {e}", exc_info=True)
        # Still return the model_id, but log the persistence error
        
    return {"model_id": model_id}

@app.post("/predict", summary="Predict hierarchical labels")
def predict(req: PredictRequest, api_key: str = Security(get_api_key)):
    clf = _models.get(req.model_id)
    if not clf:
        raise HTTPException(status_code=404, detail="Model not found.")
    try:
        X = pd.DataFrame([req.features])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid features format: {e}")
    
    try:
        preds = clf.predict(X)
        path = preds[0].tolist()
        return {"path": path}
    except Exception as e:
        logger.error(f"Prediction failed for model {req.model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

@app.get("/health", summary="Health check endpoint")
def health():
    """Provides a basic health check of the service."""
    return {"status": "ok"}
