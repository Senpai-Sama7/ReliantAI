#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web Service for the Full AI Platform
------------------------------------

This service provides the AI agent with the ability to interact with the internet.

Features:
- Web Search: Uses the `duckduckgo-search` library to perform web searches.
- Web Fetching: Uses `httpx` and `BeautifulSoup` to fetch and parse the content of a URL.
- Enhanced Error Handling: More robust error handling and logging.

Web Service (Refactored)
------------------------

This service provides secure and robust web search and content fetching
capabilities for the AI agent. It is configured via environment variables
and protected by API key authentication.
"""

import os
import logging
from typing import List

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

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
class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query.")
    max_results: int = Field(5, ge=1, le=20, description="The maximum number of search results.")

class FetchRequest(BaseModel):
    url: str = Field(..., description="The URL of the web page to fetch.")

# --- Service Initialization ---
app = FastAPI(
    title="Web Service",
    description="Provides web search and content fetching capabilities.",
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
@app.post("/search", summary="Perform a web search")
def web_search(request: SearchRequest, api_key: str = Security(get_api_key)):
    """Performs a web search using DuckDuckGo."""
    logger.info(f"Performing web search for: '{request.query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(request.query, max_results=request.max_results))
        logger.info(f"Web search for '{request.query}' returned {len(results)} results.")
        return {"results": results}
    except Exception as e:
        logger.error(f"Error during web search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to perform web search: {e}")

@app.post("/fetch", summary="Fetch content from a URL")
async def fetch_url(request: FetchRequest, api_key: str = Security(get_api_key)):
    """Fetches and parses the text content of a URL."""
    logger.info(f"Fetching URL: {request.url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(request.url, timeout=30.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return {"url": request.url, "content": text}
        except httpx.RequestError as e:
            logger.error(f"Network error fetching URL {request.url}: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Network error fetching URL: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching URL {request.url}: {e}", exc_info=True)
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error fetching URL {request.url}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/health", summary="Health check endpoint")
def health():
    """Provides a basic health check of the service."""
    return {"status": "ok"}
