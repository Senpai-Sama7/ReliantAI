"""Backward-compatible wrapper around the Gemini client module."""

from src.ai.llm_client import generate_text

__all__ = ["generate_text"]
