from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from reliantai.main import app


@pytest.fixture
def client():
    return TestClient(app)


@patch("reliantai.api.v2.generated_sites.get_cached_site", return_value=None)
@patch("reliantai.api.v2.generated_sites.set_cached_site")
@patch("reliantai.api.v2.generated_sites.get_db_session")
def test_get_generated_site_returns_site_content(
    mock_get_db, _mock_set_cache, _mock_get_cache, client
):
    mock_site = MagicMock()
    mock_site.site_content = {
        "business": {"business_name": "Apex HVAC"},
        "hero": {"headline": "Apex HVAC"},
        "slug": "apex-hvac-houston-ab12",
    }
    mock_site.status = "preview_live"
    mock_site.slug = "apex-hvac-houston-ab12"
    mock_site.meta_title = "Apex HVAC"
    mock_site.meta_description = "Best HVAC"
    mock_site.lighthouse_score = 95
    mock_site.site_config = {"template_id": "hvac-reliable-blue"}
    mock_site.schema_org_json = {"@type": "HVACBusiness"}

    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_site
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    response = client.get("/api/v2/generated-sites/apex-hvac-houston-ab12")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "apex-hvac-houston-ab12"
    assert data["business"]["business_name"] == "Apex HVAC"


@patch("reliantai.api.v2.generated_sites.get_cached_site", return_value=None)
@patch("reliantai.api.v2.generated_sites.get_db_session")
def test_get_generated_site_not_found(mock_get_db, _mock_get_cache, client):
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    response = client.get("/api/v2/generated-sites/missing-slug")
    assert response.status_code == 404


@patch("reliantai.api.v2.generated_sites.get_cached_site", return_value=None)
@patch("reliantai.api.v2.generated_sites.get_db_session")
def test_get_generated_site_hides_non_public_status(mock_get_db, _mock_get_cache, client):
    mock_site = MagicMock()
    mock_site.status = "expired"
    mock_site.slug = "old-hvac-houston-ab12"
    mock_site.site_content = {"business": {"business_name": "Old HVAC"}}

    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_site
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    response = client.get("/api/v2/generated-sites/old-hvac-houston-ab12")
    assert response.status_code == 404


@patch("reliantai.api.v2.generated_sites.get_cached_site")
def test_get_generated_site_ignores_cached_expired_payload(mock_get_cache, client):
    mock_get_cache.return_value = {
        "slug": "old-hvac-houston-ab12",
        "status": "expired",
        "business": {"business_name": "Old HVAC"},
    }

    with patch("reliantai.api.v2.generated_sites.get_db_session") as mock_get_db:
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/api/v2/generated-sites/old-hvac-houston-ab12")
        assert response.status_code == 404


def test_get_generated_site_rejects_invalid_slug(client):
    response = client.get("/api/v2/generated-sites/../admin")
    assert response.status_code in (400, 404)
    if response.status_code == 400:
        assert response.json()["detail"] == "Invalid slug"
