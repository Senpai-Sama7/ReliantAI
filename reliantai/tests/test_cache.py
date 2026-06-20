import json
from unittest.mock import MagicMock, patch

import pytest

from reliantai.services import cache as cache_module


def _reset_redis_client():
    """Reset the lazy client cache between tests."""
    cache_module._redis_client = None


def test_get_cached_site_handles_missing_redis_package(monkeypatch):
    _reset_redis_client()
    monkeypatch.setattr(cache_module, "redis", None)
    assert cache_module.get_cached_site("test-slug") is None


def test_get_cached_site_handles_missing_env_var(monkeypatch):
    """When REDIS_URL is not set, get_cached_site returns None."""
    _reset_redis_client()
    monkeypatch.delenv("REDIS_URL", raising=False)
    client = cache_module._get_redis_client()
    assert client is None
    assert cache_module.get_cached_site("test-slug") is None


def test_get_cached_site_uses_module_level_redis_error():
    _reset_redis_client()
    mock_client = MagicMock()
    mock_client.get.side_effect = cache_module.RedisError("down")
    with patch.object(cache_module, "_redis_client", mock_client):
        assert cache_module.get_cached_site("test-slug") is None


def test_set_cached_site_stores_json():
    _reset_redis_client()
    mock_client = MagicMock()
    payload = {"slug": "test-slug", "status": "preview_live"}
    with patch.object(cache_module, "_redis_client", mock_client):
        cache_module.set_cached_site("test-slug", payload)
    mock_client.setex.assert_called_once_with(
        "site:test-slug",
        cache_module.SITE_CACHE_TTL,
        json.dumps(payload),
    )


def test_set_cached_site_skips_when_ttl_zero():
    _reset_redis_client()
    original_ttl = cache_module.SITE_CACHE_TTL
    try:
        cache_module.SITE_CACHE_TTL = 0
        mock_client = MagicMock()
        with patch.object(cache_module, "_redis_client", mock_client):
            cache_module.set_cached_site("test-slug", {"slug": "test-slug"})
        mock_client.setex.assert_not_called()
    finally:
        cache_module.SITE_CACHE_TTL = original_ttl


def test_invalidate_site_cache_deletes_key():
    _reset_redis_client()
    mock_client = MagicMock()
    with patch.object(cache_module, "_redis_client", mock_client):
        cache_module.invalidate_site_cache("test-slug")
    mock_client.delete.assert_called_once_with("site:test-slug")
