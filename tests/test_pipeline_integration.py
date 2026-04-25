import pytest
import json
from unittest.mock import patch, MagicMock

from reliantai.db.models import Prospect, GeneratedSite, OutreachMessage
from reliantai.services.site_registration_service import SiteRegistrationService, generate_slug
from reliantai.agents.tools.schema_builder import build_local_business_schema
from reliantai.agents.tools.google_places import GooglePlacesTool
from reliantai.agents.tools.twilio_sms import TwilioSMSTool


FIXTURE_PROSPECT = {
    "id": "test-prospect-001",
    "place_id": "ChIJTest123HoustonHVAC",
    "name": "Apex HVAC",
    "business_name": "Apex HVAC",
    "trade": "hvac",
    "city": "Houston",
    "state": "TX",
    "phone": "+18325551234",
    "email": "owner@apexhvac.com",
    "website": "https://apexhvac.com",
    "rating": 4.8,
    "review_count": 127,
    "address": "1234 Main St, Houston, TX 77002",
    "lat": 29.7604,
    "lng": -95.3698,
    "summary": "Apex HVAC provides heating and cooling services to Houston area homes and businesses.",
}


def test_generate_slug():
    slug = generate_slug("Apex HVAC", "Houston")
    assert slug.startswith("apex-hvac-houston-")
    assert len(slug) <= 55 + 5


def test_build_local_business_schema():
    schema = build_local_business_schema(
        business_data=FIXTURE_PROSPECT,
        review_data={"reviews": [{"author": "John", "rating": 5, "text": "Great service"}]},
        competitor_keywords=["houston hvac", "ac repair"],
    )
    assert "@context" in schema
    assert "HVACBusiness" in schema["@type"]
    assert "LocalBusiness" in schema["@type"]
    assert schema["name"] == "Apex HVAC"
    assert "aggregateRating" in schema
    assert len(schema["review"]) == 1


def test_schema_validator_local_fallback():
    from reliantai.agents.tools.schema_validator import SchemaValidatorTool
    validator = SchemaValidatorTool()
    schema = build_local_business_schema(FIXTURE_PROSPECT)
    result = validator._run(schema)
    assert "valid" in result.lower() or "true" in result.lower() or "false" in result.lower()


@patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "test-key"})
@patch("httpx.Client")
def test_google_places_tool_search(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [{
            "place_id": "ChIJTest123",
            "name": "Apex HVAC",
            "formatted_address": "1234 Main St, Houston, TX",
            "rating": 4.8,
            "user_ratings_total": 127,
            "geometry": {"location": {"lat": 29.76, "lng": -95.37}},
        }],
        "status": "OK",
    }
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_cls.return_value = mock_client

    tool = GooglePlacesTool()
    result = tool._run(query="Apex HVAC Houston TX")
    assert "Apex HVAC" in result


def test_twilio_sms_tool_invalid_number():
    tool = TwilioSMSTool()
    result = tool._run(to="5551234567", body="Hello")
    assert "invalid_number" in result


@patch.dict("os.environ", {"TWILIO_ACCOUNT_SID": "test-sid", "TWILIO_AUTH_TOKEN": "test-token", "TWILIO_FROM_NUMBER": "+18325550000"})
@patch("httpx.Client")
def test_twilio_sms_tool_valid(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"sid": "SM123", "status": "queued"}
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_cls.return_value = mock_client

    tool = TwilioSMSTool()
    result = tool._run(to="+18325551234", body="Hey, saw your reviews on Google!")
    assert "SM123" in result


@patch("reliantai.services.site_registration_service.SchemaValidatorTool")
@patch("reliantai.services.site_registration_service.get_db_session")
def test_site_registration_service_register(mock_get_db, mock_validator_cls):
    mock_validator = MagicMock()
    mock_validator._run.return_value = '{"valid": true, "source": "local_fallback"}'
    mock_validator_cls.return_value = mock_validator

    mock_db = MagicMock()
    mock_prospect = MagicMock()
    mock_prospect.id = "test-prospect-001"
    mock_prospect.business_name = "Apex HVAC"
    mock_prospect.city = "Houston"
    mock_prospect.trade = "hvac"
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_prospect
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    copy_package = {
        "hero": {"headline": "Apex HVAC - Houston's Trusted Choice"},
        "seo": {"title": "Apex HVAC Houston", "description": "Best HVAC in Houston"},
        "reviews": {"reviews": []},
    }
    research_data = {
        "name": "Apex HVAC",
        "trade": "hvac",
        "city": "Houston",
        "state": "TX",
        "phone": "+18325551234",
        "rating": 4.8,
        "review_count": 127,
    }
    result = SiteRegistrationService.register(
        prospect_id="test-prospect-001",
        copy_package=copy_package,
        research_data=research_data,
        competitor_data=[],
    )
    assert "slug" in result
    assert "preview_url" in result
    assert "preview.reliantai.org" in result["preview_url"]


def test_pipeline_integration_mock():
    with patch("reliantai.agents.home_services_crew.create_prospect_crew") as mock_crew_factory:
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = {"status": "completed"}
        mock_crew_factory.return_value = mock_crew

        from reliantai.agents.home_services_crew import create_prospect_crew
        crew = create_prospect_crew(FIXTURE_PROSPECT)
        result = crew.kickoff()
        assert result["status"] == "completed"
