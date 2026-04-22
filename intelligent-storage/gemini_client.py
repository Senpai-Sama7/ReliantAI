"""Gemini API client for Intelligent Storage Nexus.

Unified wrapper for Google Gemini 3.1 Flash (chat/generation)
and text-embedding-004 (embeddings). Replaces the Ollama integration.
"""

import json
import logging
from typing import AsyncGenerator, List, Optional

import httpx

from config import GEMINI_API_KEY, EMBED_MODEL, EMBED_DIM, CHAT_MODEL

logger = logging.getLogger(__name__)

# ── Gemini API URLs ──────────────────────────────────────────
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
_EMBED_URL = f"{_GEMINI_BASE}/models/{{model}}:embedContent"
_BATCH_EMBED_URL = f"{_GEMINI_BASE}/models/{{model}}:batchEmbedContents"
_GENERATE_URL = f"{_GEMINI_BASE}/models/{{model}}:generateContent"
_STREAM_URL = f"{_GEMINI_BASE}/models/{{model}}:streamGenerateContent"


async def get_embeddings(texts: list[str]) -> list[list[float] | None]:
    """Get embeddings from Gemini text-embedding-004 in batch.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (or None for failures).
    """
    if not texts:
        return []

    # Gemini batchEmbedContents supports up to 100 texts per call
    MAX_BATCH = 100
    if len(texts) > MAX_BATCH:
        results = []
        for i in range(0, len(texts), MAX_BATCH):
            batch = await get_embeddings(texts[i : i + MAX_BATCH])
            results.extend(batch)
        return results

    url = _BATCH_EMBED_URL.format(model=EMBED_MODEL)
    payload = {
        "requests": [
            {
                "model": f"models/{EMBED_MODEL}",
                "content": {"parts": [{"text": t[:2048]}]},  # Gemini limit
                "outputDimensionality": EMBED_DIM,
            }
            for t in texts
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                params={"key": GEMINI_API_KEY},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings", [])
            return [e.get("values") for e in embeddings]
    except httpx.HTTPStatusError as exc:
        logger.error(f"Gemini embedding HTTP error: {exc.response.status_code} - {exc.response.text}")
    except Exception as exc:
        logger.error(f"Gemini embedding error: {exc}")

    # On failure, try splitting in half (resilience pattern from original indexer)
    if len(texts) > 1:
        mid = len(texts) // 2
        left = await get_embeddings(texts[:mid])
        right = await get_embeddings(texts[mid:])
        return left + right

    return [None] * len(texts)


async def get_single_embedding(text: str) -> Optional[list[float]]:
    """Get a single embedding vector. Convenience wrapper."""
    results = await get_embeddings([text])
    if results and results[0]:
        return results[0]
    return [0.0] * EMBED_DIM


async def generate(prompt: str, temperature: float = 0.3) -> Optional[str]:
    """Non-streaming text generation via Gemini.

    Used for classification and structured outputs.
    """
    url = _GENERATE_URL.format(model=CHAT_MODEL)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 1024,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                params={"key": GEMINI_API_KEY},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
    except Exception as exc:
        logger.error(f"Gemini generate error: {exc}")

    return None


async def stream_chat(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream chat response from Gemini.

    Args:
        messages: List of {"role": "user"|"model"|"system", "content": "..."}
                  (system messages are prepended to the first user message)
    """
    url = _STREAM_URL.format(model=CHAT_MODEL)

    # Gemini uses "user" and "model" roles. System instructions go separately.
    system_instruction = None
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            system_instruction = content
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        else:
            contents.append({"role": "user", "parts": [{"text": content}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        },
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                url,
                params={"key": GEMINI_API_KEY, "alt": "sse"},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # Strip "data: " prefix
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        logger.error(f"Gemini stream error: {e}")
        yield f"[Error generating response: {str(e)}]"
