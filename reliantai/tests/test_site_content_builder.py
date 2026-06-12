from types import SimpleNamespace

from reliantai.services.site_content_builder import build_site_content


def test_build_site_content_normalizes_copy_package():
    prospect = SimpleNamespace(
        trade="hvac",
        business_name="Apex HVAC",
        city="Houston",
        state="TX",
        phone="+18325551234",
        email="owner@apexhvac.com",
        address="123 Main St",
        google_rating=4.8,
        review_count=127,
        website_url="https://apexhvac.com",
    )
    copy_package = {
        "hero": {
            "headline": "Apex HVAC — Houston's Trusted Choice",
            "subheadline": "Same-day service",
            "trust_bar": ["Licensed", "Insured", "EPA Certified"],
        },
        "services": [
            {
                "icon": "thermometer",
                "title": "AC Repair",
                "description": "Fast repairs",
                "cta_text": "Call",
            }
        ],
        "about": {
            "owner_story": "Family owned since 2005.",
            "trust_points": ["15 years", "4.8 stars"],
        },
        "reviews": {
            "aggregate_line": "4.8 stars across 127 reviews",
            "reviews": [{"author": "Jane", "rating": 5, "text": "Great", "time": "1w"}],
        },
        "faq": [{"question": "Do you offer emergency service?", "answer": "Yes, 24/7."}],
        "seo": {
            "title": "Apex HVAC Houston",
            "description": "Top HVAC in Houston",
            "keywords": ["hvac", "houston"],
        },
    }
    research_data = {
        "name": "Apex HVAC",
        "phone": "+18325551234",
        "rating": 4.8,
        "review_count": 127,
        "city": "Houston",
        "state": "TX",
        "address": "123 Main St, Houston, TX",
        "pagespeed_score": 92,
    }
    schema = {"@context": "https://schema.org", "@type": "HVACBusiness", "name": "Apex HVAC"}

    content = build_site_content(
        copy_package=copy_package,
        research_data=research_data,
        prospect=prospect,
        slug="apex-hvac-houston-ab12",
        template_id="hvac-reliable-blue",
        theme={"primary": "#1d4ed8", "accent": "#93c5fd", "font_display": "Outfit", "font_body": "Inter"},
        schema_org=schema,
    )

    assert content["slug"] == "apex-hvac-houston-ab12"
    assert content["business"]["business_name"] == "Apex HVAC"
    assert content["hero"]["headline"].startswith("Apex HVAC")
    assert content["about"]["story"] == "Family owned since 2005."
    assert content["site_config"]["template_id"] == "hvac-reliable-blue"
    assert content["lighthouse_score"] == 92
    assert content["seo"]["title"] == "Apex HVAC Houston"


def test_build_site_content_coerces_string_lighthouse_score():
    prospect = SimpleNamespace(
        trade="hvac",
        business_name="Apex HVAC",
        city="Houston",
        state="TX",
        phone="+18325551234",
        email=None,
        address="123 Main St",
        google_rating=None,
        review_count=None,
        website_url=None,
    )
    content = build_site_content(
        copy_package={"seo": {"title": "Apex", "description": "Best"}},
        research_data={"city": "Houston", "state": "TX"},
        prospect=prospect,
        slug="apex-hvac-houston-ab12",
        template_id="hvac-reliable-blue",
        theme={"primary": "#1d4ed8", "accent": "#93c5fd", "font_display": "Outfit", "font_body": "Inter"},
        schema_org={"@context": "https://schema.org", "@type": "HVACBusiness"},
        lighthouse_score="87.0",
    )
    assert content["lighthouse_score"] == 87
    assert isinstance(content["lighthouse_score"], int)


def test_build_site_content_safe_numeric_coercion():
    prospect = SimpleNamespace(
        trade="hvac",
        business_name="Apex HVAC",
        city="Houston",
        state="TX",
        phone="+18325551234",
        email=None,
        address="123 Main St",
        google_rating=None,
        review_count=None,
        website_url=None,
    )
    content = build_site_content(
        copy_package={"seo": {"title": "Apex", "description": "Best"}},
        research_data={
            "city": "Houston",
            "state": "TX",
            "rating": "4.8",
            "review_count": "127.0",
        },
        prospect=prospect,
        slug="apex-hvac-houston-ab12",
        template_id="hvac-reliable-blue",
        theme={"primary": "#1d4ed8", "accent": "#93c5fd", "font_display": "Outfit", "font_body": "Inter"},
        schema_org={"@context": "https://schema.org", "@type": "HVACBusiness"},
    )
    assert content["business"]["google_rating"] == 4.8
    assert content["business"]["review_count"] == 127


def test_build_site_content_strips_unsafe_website_url():
    prospect = SimpleNamespace(
        trade="plumbing",
        business_name="Apex Plumbing",
        city="Houston",
        state="TX",
        phone="+18325551234",
        email=None,
        address="123 Main St",
        google_rating=None,
        review_count=None,
        website_url="javascript:alert(1)",
    )
    content = build_site_content(
        copy_package={"seo": {"title": "Apex", "description": "Best"}},
        research_data={"city": "Houston", "state": "TX"},
        prospect=prospect,
        slug="apex-plumbing-houston-ab12",
        template_id="plumbing-trustworthy-navy",
        theme={"primary": "#1e3a5f", "accent": "#60a5fa", "font_display": "Sora", "font_body": "Inter"},
        schema_org={"@context": "https://schema.org", "@type": "Plumber"},
    )
    assert content["business"]["website_url"] is None
