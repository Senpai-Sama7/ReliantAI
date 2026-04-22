"""
Gemini client tests.
"""
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ai import llm_client
from src.config import Settings


@pytest.mark.asyncio
async def test_generate_text_uses_gemini_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Gemini client should honor the configured defaults."""
    monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL", "gemini-test")
    monkeypatch.setattr(llm_client.settings, "MAX_TOKENS", 321)
    monkeypatch.setattr(llm_client.settings, "TEMPERATURE", 0.15)

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "  Gemini output  "
    mock_client.models.generate_content = AsyncMock(return_value=mock_response)

    @asynccontextmanager
    async def fake_client():
        yield mock_client

    monkeypatch.setattr(llm_client, "_get_async_client", fake_client)

    result = await llm_client.generate_text("forecast prompt")

    assert result == "Gemini output"
    mock_client.models.generate_content.assert_awaited_once()
    _, kwargs = mock_client.models.generate_content.await_args
    assert kwargs["model"] == "gemini-test"
    assert kwargs["contents"] == "forecast prompt"
    assert kwargs["config"].max_output_tokens == 321
    assert kwargs["config"].temperature == 0.15


@pytest.mark.asyncio
async def test_generate_text_rejects_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The wrapper should fail fast when Gemini returns no text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = None
    mock_client.models.generate_content = AsyncMock(return_value=mock_response)

    @asynccontextmanager
    async def fake_client():
        yield mock_client

    monkeypatch.setattr(llm_client, "_get_async_client", fake_client)

    with pytest.raises(RuntimeError, match="empty response"):
        await llm_client.generate_text("forecast prompt")


def test_settings_accept_legacy_openai_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    """Legacy env names should still hydrate the Gemini settings fields."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "legacy-openai-model")

    settings = Settings()

    assert settings.GEMINI_API_KEY == "legacy-openai-key"
    assert settings.GEMINI_MODEL == "legacy-openai-model"
