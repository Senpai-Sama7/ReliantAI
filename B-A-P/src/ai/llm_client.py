"""
Gemini client for AI-powered features.
"""
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from google import genai
from google.genai import types

from src.config import get_settings

settings = get_settings()


@asynccontextmanager
async def _get_async_client() -> AsyncIterator[Any]:
    """Create a short-lived Gemini async client to avoid leaking transports."""
    async with genai.Client(api_key=settings.GEMINI_API_KEY).aio as client:
        yield client


async def generate_text(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    """Generate text using Google's Gemini models asynchronously."""
    selected_model = model or settings.GEMINI_MODEL
    selected_max_tokens = max_tokens if max_tokens is not None else settings.MAX_TOKENS
    selected_temperature = temperature if temperature is not None else settings.TEMPERATURE

    async with _get_async_client() as client:
        response = await client.models.generate_content(
            model=selected_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=selected_max_tokens,
                temperature=selected_temperature,
            ),
        )

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text
