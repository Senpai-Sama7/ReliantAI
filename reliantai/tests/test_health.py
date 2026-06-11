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
