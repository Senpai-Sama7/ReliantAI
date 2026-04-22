from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from memory import embeddings


@pytest.mark.asyncio
async def test_get_embedding_uses_gemini_with_pgvector_dim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    mock_client = MagicMock()
    mock_client.models.embed_content = AsyncMock(
        return_value=SimpleNamespace(
            embeddings=[SimpleNamespace(values=[0.5] * embeddings.EMBEDDING_DIM)]
        )
    )

    @asynccontextmanager
    async def fake_client():
        yield mock_client

    monkeypatch.setattr(embeddings, "_get_async_client", fake_client)

    result = await embeddings.get_embedding("memory payload")

    assert len(result) == embeddings.EMBEDDING_DIM
    _, kwargs = mock_client.models.embed_content.await_args
    assert kwargs["model"] == embeddings.EMBEDDING_MODEL
    assert kwargs["contents"] == "memory payload"
    assert kwargs["config"].output_dimensionality == embeddings.EMBEDDING_DIM


def test_embedding_to_pg_formats_pgvector_literal() -> None:
    assert embeddings.embedding_to_pg([0.1, 0.2]) == "[0.10000000,0.20000000]"


@pytest.mark.asyncio
async def test_get_embedding_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY not configured"):
        await embeddings.get_embedding("memory payload")
