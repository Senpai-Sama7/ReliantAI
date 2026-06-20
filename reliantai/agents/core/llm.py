"""LLM configuration for agents — Gemini 1.5 pro/flash with fallback."""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI


@lru_cache(maxsize=2)
def get_llm(model: str = "flash", temperature: float = 0.3, max_tokens: int = 2048) -> ChatGoogleGenerativeAI:
    """Get a cached LLM instance.

    Copy agent (high-quality)  -> gemini-1.5-pro
    All other agents (fast)    -> gemini-1.5-flash

    Falls back to flash if pro quota is exhausted.
    """
    api_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    model_name = "gemini-1.5-pro" if model == "pro" else "gemini-1.5-flash"

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        max_output_tokens=max_tokens,
        google_api_key=api_key,
    )


def get_copy_llm() -> ChatGoogleGenerativeAI:
    """High-quality LLM for copy writing."""
    return get_llm("pro", temperature=0.5, max_tokens=4096)


def get_research_llm() -> ChatGoogleGenerativeAI:
    """Fast LLM for research tasks."""
    return get_llm("flash", temperature=0.3, max_tokens=2048)


def get_outreach_llm() -> ChatGoogleGenerativeAI:
    """Balanced LLM for outreach messages."""
    return get_llm("flash", temperature=0.4, max_tokens=1024)
