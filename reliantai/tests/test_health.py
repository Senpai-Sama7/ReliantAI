from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from reliantai.main import app


@patch("reliantai.main.get_db_session")
def test_health_endpoint(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] is True


@patch("reliantai.main.get_db_session")
def test_readiness_endpoint_ready(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True}


@patch("reliantai.main.get_db_session")
def test_readiness_endpoint_not_ready(mock_get_db):
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("db down")
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Not ready"


@patch("reliantai.api.v2.generated_sites.get_db_session")
def test_rate_limit_exceeded(mock_get_db):
    """After RATE_LIMIT_MAX requests from the same IP, the next one returns 429."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    import reliantai.main as main_module
    original_max = main_module._RATE_LIMIT_MAX
    main_module._RATE_LIMIT_MAX = 3
    main_module._rate_limit_buckets.clear()
    try:
        client = TestClient(app)
        for i in range(3):
            response = client.get("/api/v2/generated-sites/test-slug-xyz")
            # 404 is fine -- we just want to verify it is NOT 429
            assert response.status_code != 429, f"Request {i+1} was rate-limited prematurely (got {response.status_code})"
        # The 4th request should be rate-limited
        response = client.get("/api/v2/generated-sites/test-slug-xyz")
        assert response.status_code == 429, f"Expected 429, got {response.status_code}"
        assert "Retry-After" in response.headers
    finally:
        main_module._RATE_LIMIT_MAX = original_max
        main_module._rate_limit_buckets.clear()
