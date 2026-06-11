from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from reliantai.services.site_registration_service import SiteRegistrationService


@patch("reliantai.services.site_registration_service.SiteRegistrationService._revalidate_preview_cache")
@patch("reliantai.services.site_registration_service.invalidate_site_cache")
@patch("reliantai.services.site_registration_service.get_db_session")
def test_register_preserves_existing_slug(mock_get_db, _mock_cache, _mock_revalidate):
    mock_prospect = MagicMock()
    mock_prospect.id = "prospect-1"
    mock_prospect.business_name = "Apex HVAC"
    mock_prospect.city = "Houston"
    mock_prospect.trade = "hvac"
    mock_prospect.phone = "+18325551234"
    mock_prospect.email = None
    mock_prospect.address = "123 Main St"
    mock_prospect.google_rating = 4.8
    mock_prospect.review_count = 10
    mock_prospect.website_url = None

    mock_existing = MagicMock()
    mock_existing.slug = "apex-hvac-houston-ab12"
    mock_existing.lighthouse_score = None

    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_prospect,
        mock_existing,
    ]
    mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

    copy_package = {
        "hero": {"headline": "Updated headline", "trust_bar": ["A", "B", "C"]},
        "seo": {"title": "Updated", "description": "Updated desc"},
        "reviews": {"reviews": []},
    }
    research_data = {
        "name": "Apex HVAC",
        "phone": "+18325551234",
        "address": "123 Main St, Houston, TX",
        "city": "Houston",
        "state": "TX",
        "rating": 4.8,
        "review_count": 10,
    }

    result = SiteRegistrationService.register(
        prospect_id="prospect-1",
        copy_package=copy_package,
        research_data=research_data,
        competitor_data=[],
    )

    assert result["slug"] == "apex-hvac-houston-ab12"
    assert mock_existing.slug == "apex-hvac-houston-ab12"


def test_register_from_crew_outputs_parses_tasks():
    task_research = SimpleNamespace(
        description="Research the business",
        output='{"name": "Apex HVAC", "phone": "+18325551234", "city": "Houston", "state": "TX", "rating": 4.8, "review_count": 10, "address": "123 Main"}',
    )
    task_copy = SimpleNamespace(
        description="Write website copy and copy_package",
        output='{"hero": {"headline": "Apex HVAC"}, "seo": {"title": "Apex", "description": "Best"}, "reviews": {"reviews": []}}',
    )
    crew = SimpleNamespace(tasks=[task_research, task_copy])

    with patch.object(SiteRegistrationService, "register", return_value={"slug": "apex-hvac-houston-ab12"}) as mock_register:
        result = SiteRegistrationService.register_from_crew_outputs("prospect-1", crew)

    assert result["slug"] == "apex-hvac-houston-ab12"
    mock_register.assert_called_once()
    kwargs = mock_register.call_args.kwargs
    assert kwargs["prospect_id"] == "prospect-1"
    assert kwargs["copy_package"]["hero"]["headline"] == "Apex HVAC"
    assert kwargs["research_data"]["name"] == "Apex HVAC"


def test_register_from_crew_outputs_research_with_reviews_not_misclassified_as_copy():
    """Research output includes reviews (list); must not be routed to copy_package."""
    task_research = SimpleNamespace(
        description="Research the business in Houston",
        output=(
            '{"name": "Apex HVAC", "phone": "+18325551234", "city": "Houston", '
            '"state": "TX", "rating": 4.8, "review_count": 42, "address": "123 Main", '
            '"pagespeed_score": 88, "profile_completeness": 75, '
            '"reviews": [{"author": "Jane", "rating": 5, "text": "Great", "time": "1 week ago"}]}'
        ),
    )
    task_copy = SimpleNamespace(
        description="Write website copy and copy_package",
        output='{"hero": {"headline": "Apex HVAC"}, "seo": {"title": "Apex", "description": "Best"}, "reviews": {"reviews": []}}',
    )
    crew = SimpleNamespace(tasks=[task_research, task_copy])

    with patch.object(
        SiteRegistrationService, "register", return_value={"slug": "apex-hvac-houston-ab12"}
    ) as mock_register:
        SiteRegistrationService.register_from_crew_outputs("prospect-1", crew)

    kwargs = mock_register.call_args.kwargs
    assert kwargs["research_data"]["pagespeed_score"] == 88
    assert kwargs["research_data"]["profile_completeness"] == 75
    assert kwargs["research_data"]["reviews"][0]["author"] == "Jane"
    assert kwargs["copy_package"]["hero"]["headline"] == "Apex HVAC"


def test_register_from_crew_outputs_ignores_site_build_registration_echo():
    task_copy = SimpleNamespace(
        description="Write website copy and produce a copy_package dict",
        output='{"hero": {"headline": "Apex HVAC"}, "seo": {"title": "Apex", "description": "Best"}, "reviews": {"reviews": []}}',
    )
    task_site_build = SimpleNamespace(
        description=(
            "Register the preview site using copy_package from the copy agent's output. "
            "Return slug, preview_url, schema_valid."
        ),
        output='{"slug": "apex-hvac-houston-ab12", "preview_url": "https://preview.reliantai.org/apex-hvac-houston-ab12", "schema_valid": true}',
    )
    crew = SimpleNamespace(tasks=[task_copy, task_site_build])

    with patch.object(SiteRegistrationService, "register", return_value={"slug": "apex-hvac-houston-ab12"}) as mock_register:
        SiteRegistrationService.register_from_crew_outputs("prospect-1", crew)

    kwargs = mock_register.call_args.kwargs
    assert kwargs["copy_package"]["hero"]["headline"] == "Apex HVAC"
    assert "slug" not in kwargs["copy_package"]
