#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Multi‑Modal Embedding Service
----------------------------

This service demonstrates how to work with multiple data modalities
using a unified embedding space. For the sake of offline deployment and
lightweight dependencies, the embedding functions here are deterministic
and based on hashing the input rather than neural networks. However,
the same API can be used with real models (e.g., CLIP) by replacing
`_text_to_vec` and `_image_to_vec` with calls to those models.

Multi-Modal Embedding Service (Refactored)
------------------------------------------

This service provides a secure interface for working with multiple data
modalities. For demonstration purposes, it uses deterministic hashing
to generate embeddings, but it can be extended to use real multi-modal
models like CLIP.
"""

import os
import base64
import hashlib
import io
import logging
from typing import List, Dict

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from PIL import Image

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
class TextPayload(BaseModel):
    text: str

class SearchItem(BaseModel):
    id: str
    vector: List[float]

class SearchRequest(BaseModel):
    query_type: str = Field(..., description="Type of query: 'text' or 'image'", pattern="^(text|image)$")
    query: str = Field(..., description="The text string or base64-encoded image")
    dataset: List[SearchItem] = Field(..., description="List of items with precomputed vectors")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)

# --- Service Initialization ---
app = FastAPI(
    title="Multi-Modal Service",
    description="Generates embeddings for text and images and performs multi-modal search.",
    version="2.0.0"
)

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if key == API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- Core Logic ---
def _deterministic_vector(seed: bytes, dim: int = 512) -> np.ndarray:
    """Generate a deterministic pseudo-random vector from a seed."""
    digest = hashlib.md5(seed).digest()
    seed_int = int.from_bytes(digest[:8], byteorder='big')
    rng = np.random.default_rng(seed_int)
    vec = rng.standard_normal(dim)
    vec /= np.linalg.norm(vec) + 1e-9
    return vec

def _text_to_vec(text: str) -> np.ndarray:
    return _deterministic_vector(text.encode('utf-8'))

def _image_to_vec(image_bytes: bytes) -> np.ndarray:
    return _deterministic_vector(image_bytes)

# --- API Endpoints ---
@app.post("/embed/text", summary="Embed text")
def embed_text(payload: TextPayload, api_key: str = Security(get_api_key)):
    vec = _text_to_vec(payload.text)
    return {"vector": vec.tolist()}

@app.post("/embed/image", summary="Embed image")
async def embed_image(file: UploadFile = File(...), api_key: str = Security(get_api_key)):
    contents = await file.read()
    try:
        Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    vec = _image_to_vec(contents)
    return {"vector": vec.tolist()}

@app.post("/search", summary="Search dataset")
def search(req: SearchRequest, api_key: str = Security(get_api_key)):
    try:
        if req.query_type == 'text':
            query_vec = _text_to_vec(req.query)
        else:
            img_bytes = base64.b64decode(req.query)
            query_vec = _image_to_vec(img_bytes)
    except (base64.binascii.Error, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64-encoded image query: {e}")

    if not req.dataset:
        raise HTTPException(status_code=400, detail="Dataset cannot be empty.")
    
    ids = [item.id for item in req.dataset]
    data_matrix = np.array([item.vector for item in req.dataset], dtype=np.float32)
    
    # Normalize dataset vectors
    norms = np.linalg.norm(data_matrix, axis=1, keepdims=True)
    data_matrix /= (norms + 1e-9)
    
    sims = data_matrix @ query_vec
    top_indices = sims.argsort()[-req.top_k:][::-1]
    
    results = [{"id": ids[i], "score": float(sims[i])} for i in top_indices]
    return {"results": results}

@app.get("/health", summary="Health check endpoint")
def health():
    """Provides a basic health check of the service."""
    return {"status": "ok"}
