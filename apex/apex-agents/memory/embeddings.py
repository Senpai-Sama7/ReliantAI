# apex-agents/memory/embeddings.py
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from google import genai
from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM   = 1536


def _api_key() -> str:
    """Read the Gemini API key at call time so env changes are honored in tests."""
    return os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY", "")


@asynccontextmanager
async def _get_async_client() -> AsyncIterator[object]:
    """Create a short-lived Gemini async client for embeddings calls."""
    async with genai.Client(api_key=_api_key()).aio as client:
        yield client


async def get_embedding(text: str) -> list[float]:
    """
    Returns a 1536-dim float vector for `text` using Gemini embeddings.

    Truncates input at 8000 chars to keep request sizes bounded while preserving
    the existing pgvector schema by requesting 1536 output dimensions.

    Raises ValueError if no embedding API key is configured.
    """
    key = _api_key()
    if not key:
        raise ValueError(
            "GEMINI_API_KEY not configured. "
            "Memory endpoints require embeddings. Add GEMINI_API_KEY to .env. "
            "OPENAI_API_KEY is still accepted temporarily as a compatibility alias."
        )

    async with _get_async_client() as client:
        response = await client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text[:8000],
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )

    values: list[float] | None = None
    if getattr(response, "embeddings", None):
        values = [float(value) for value in response.embeddings[0].values]
    elif getattr(response, "embedding", None):
        values = [float(value) for value in response.embedding.values]

    if not values:
        raise RuntimeError("Gemini embedding response did not contain embedding values")
    if len(values) != EMBEDDING_DIM:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIM}-dim embedding, received {len(values)} values"
        )
    return values


def embedding_to_pg(vec: list[float]) -> str:
    """
    Formats a float list as a pgvector literal string: '[0.12345678,...]'
    asyncpg requires this string format when passing to a vector column via $N::vector.
    """
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
