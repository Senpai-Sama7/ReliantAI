import json
from unittest.mock import MagicMock, patch

from reliantai.services import cache as cache_module


def test_get_cached_site_handles_missing_redis_package(monkeypatch):
    monkeypatch.setattr(cache_module, "_redis_client", None)
    assert cache_module.get_cached_site("test-slug") is None


def test_get_cached_site_uses_module_level_redis_error():
    mock_client = MagicMock()
    mock_client.get.side_effect = cache_module.RedisError("down")
    with patch.object(cache_module, "_redis_client", mock_client):
        assert cache_module.get_cached_site("test-slug") is None


def test_set_cached_site_stores_json():
    mock_client = MagicMock()
    payload = {"slug": "test-slug", "status": "preview_live"}
    with patch.object(cache_module, "_redis_client", mock_client):
        cache_module.set_cached_site("test-slug", payload)
    mock_client.setex.assert_called_once_with(
        "site:test-slug",
        cache_module.SITE_CACHE_TTL,
        json.dumps(payload),
    )
