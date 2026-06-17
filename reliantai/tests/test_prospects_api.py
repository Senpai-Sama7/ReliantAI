import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from reliantai.main import app

API_KEY = "test_secret_key"


@pytest.fixture(autouse=True)
def api_key_env(monkeypatch):
    monkeypatch.setenv("API_SECRET_KEY", API_KEY)


@pytest.fixture
def client():
    return TestClient(app)


def _auth_headers():
    return {"Authorization": f"Bearer {API_KEY}"}


def test_create_prospect_requires_auth(client):
    response = client.post(
        "/api/v2/prospects",
        json={
            "business_name": "ACME HVAC",
            "trade": "hvac",
            "city": "Atlanta",
            "state": "GA",
        },
    )
    assert response.status_code == 401


def test_create_prospect_rejects_invalid_trade(client):
    response = client.post(
        "/api/v2/prospects",
        json={
            "business_name": "ACME HVAC",
            "trade": "invalid",
            "city": "Atlanta",
            "state": "GA",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@patch("reliantai.api.v2.prospects.get_db_session")
def test_create_prospect_returns_201(mock_get_db, client):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    created = MagicMock()
    created.to_dict.return_value = {
        "id": "prospect-1",
        "business_name": "ACME HVAC",
        "trade": "hvac",
        "city": "Atlanta",
        "state": "GA",
        "phone": None,
        "email": None,
        "address": None,
        "lat": None,
        "lng": None,
        "google_rating": None,
        "review_count": 0,
        "website_url": None,
        "status": "identified",
        "created_at": "2026-06-17T12:00:00+00:00",
    }
    mock_db.add.side_effect = lambda obj: setattr(obj, "to_dict", created.to_dict)

    response = client.post(
        "/api/v2/prospects",
        json={
            "business_name": "ACME HVAC",
            "trade": "hvac",
            "city": "Atlanta",
            "state": "GA",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["business_name"] == "ACME HVAC"
    assert data["status"] == "identified"


@patch("reliantai.api.v2.prospects.enqueue_prospect_pipeline")
@patch("reliantai.api.v2.prospects.get_db_session")
def test_trigger_research_enqueues_pipeline(mock_get_db, mock_enqueue, client):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    prospect = MagicMock()
    prospect_query = MagicMock()
    prospect_query.filter_by.return_value.first.return_value = prospect

    job_query = MagicMock()
    job_query.filter.return_value.first.return_value = None

    mock_db.query.side_effect = [prospect_query, job_query]
    mock_db.add.side_effect = lambda obj: setattr(obj, "id", "job-1")

    response = client.post(
        "/api/v2/prospects/prospect-1/research",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["message"] == "Research pipeline started"
    mock_enqueue.assert_called_once_with("prospect-1")


def test_verify_api_key_rejects_wrong_key(client):
    response = client.get(
        "/api/v2/prospects",
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 401
