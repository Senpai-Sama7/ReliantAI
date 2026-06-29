"""
test_quality_gate — validates the quality gate detects AI-slop patterns,
passes on clean content, and rejects banned fonts/colors/patterns.
"""

from __future__ import annotations

import pytest

from reliantai.agents.websiteforge.quality_gate import quality_gate_check


BASE_CONTENT = {
    "business": {
        "business_name": "Austin Pro HVAC",
        "trade": "hvac",
        "city": "Austin",
        "state": "TX",
        "phone": "(512) 555-1234",
        "address": "123 Main St, Austin, TX 78701",
        "google_rating": 4.8,
        "review_count": 127,
        "years_in_business": 15,
    },
    "hero": {
        "headline": "Austin Pro HVAC — Same-Day AC Repair in Austin, TX",
        "subheadline": "EPA 608 certified technicians. 15 years serving Austin homeowners with honest pricing and 5-star reviews.",
        "trust_bar": ["EPA 608 Certified", "TX License #TACLB12345", "15 Years in Austin"],
        "cta_primary": "Call Now",
        "cta_primary_url": "tel:+15125551234",
        "cta_secondary": "Get a Free Quote",
        "cta_secondary_url": "#contact",
    },
    "services": [
        {
            "icon": "snowflake",
            "title": "AC Repair & Maintenance",
            "description": "Same-day service for all major brands. Our EPA 608 certified techs fix it right the first time.",
            "cta_text": "Schedule Service",
        },
        {
            "icon": "bolt",
            "title": "Emergency Furnace Repair",
            "description": "24/7 emergency service when your heat goes out. We answer after hours — not voicemail.",
            "cta_text": "Call Emergency Line",
        },
        {
            "icon": "gauge",
            "title": "Duct Cleaning & Indoor Air Quality",
            "description": "Improve airflow and reduce allergens with our NADCA-certified duct cleaning service.",
            "cta_text": "Get a Quote",
        },
    ],
    "about": {
        "story": "Founded in 2010 by master technician Marcus Rivera, Austin Pro HVAC was built on a simple premise: homeowners deserve technicians who show up on time, explain the problem, and charge what they said they'd charge.",
        "trust_points": [
            "Family-owned and operated since 2010",
            "EPA 608 certified technicians (Type I, II, III)",
            "Upfront pricing — no hidden fees",
            "Same-day service for most calls",
        ],
        "certifications": ["EPA 608 Certified", "NATE Certified", "BBB A+ Rated"],
    },
    "reviews": {
        "reviews": [
            {
                "author": "Sarah M.",
                "rating": 5,
                "text": "Marcus came out on a Saturday morning when our AC died. Had us cooling same day. Very knowledgeable and honest.",
            },
            {
                "author": "James K.",
                "rating": 5,
                "text": "Best HVAC experience I've had in 20 years in Austin. No pressure, fair price, quality work.",
            },
            {
                "author": "Linda R.",
                "rating": 5,
                "text": "They replaced our system and the installation was flawless. Clean, professional, on schedule.",
            },
        ],
        "aggregate_line": "4.9/5 stars from 127+ verified Austin homeowners",
    },
    "faq": [
        {
            "question": "How quickly can you respond to an emergency AC call in Austin?",
            "answer": "Most emergency calls are serviced within 4 hours. We prioritize calls during Austin's summer months (June–September) when temperatures exceed 100°F.",
        },
        {
            "question": "Do you charge for diagnostic visits?",
            "answer": "No. If we perform the repair, the diagnostic fee is waived. Standalone diagnostics are $89, credited toward any repair we perform.",
        },
        {
            "question": "What brands of HVAC equipment do you service?",
            "answer": "We service all major brands including Carrier, Trane, Lennox, Rheem, Goodman, and York. Our technicians are factory-trained on each.",
        },
        {
            "question": "Are your technicians licensed and insured in Texas?",
            "answer": "Yes. All technicians hold Texas HVAC licenses and carry liability insurance. Our license number is TACLB12345.",
        },
        {
            "question": "Do you offer maintenance plans for Austin homeowners?",
            "answer": "Yes. Our Comfort Club includes two annual tune-ups, priority scheduling, 15% off repairs, and no after-hours diagnostic fees.",
        },
    ],
    "seo": {
        "title": "Austin Pro HVAC — Same-Day AC Repair in Austin, TX",
        "description": "EPA-certified HVAC technicians serving Austin, TX since 2010. Same-day AC repair, emergency furnace service, duct cleaning. BBB A+ rated.",
        "keywords": ["hvac Austin TX", "AC repair Austin", "emergency HVAC Austin", "duct cleaning Austin", "furnace repair Austin"],
    },
    "aeo_signals": {
        "local_business_type": "HomeService",
        "primary_category": "HVAC Contractor",
        "secondary_categories": ["AC Repair", "Furnace Repair", "Duct Cleaning"],
        "area_served": ["Austin", "Round Rock", "Cedar Park", "Georgetown"],
    },
    "schema_org": {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "LocalBusiness",
                "name": "Austin Pro HVAC",
                "telephone": "+15125551234",
                "address": "123 Main St, Austin, TX 78701",
                "aggregateRating": {"@type": "AggregateRating", "ratingValue": 4.8, "reviewCount": 127},
            }
        ],
    },
    "site_config": {
        "template_id": "hvac-reliable-blue",
        "trade": "hvac",
        "theme": {
            "primary": "#1e3a5f",
            "accent": "#0ea5e9",
            "font_display": "Instrument Serif",
            "font_body": "DM Sans",
        },
    },
    "status": "draft",
    "slug": "austin-pro-hvac-austin-tx",
    "meta_title": "Austin Pro HVAC — Same-Day AC Repair in Austin, TX",
    "meta_description": "EPA 608 certified HVAC technicians serving Austin since 2010. Same-day service, BBB A+ rated.",
    "lighthouse_score": 92,
}


@pytest.fixture
def clean_content():
    return BASE_CONTENT.copy()


@pytest.fixture
def banned_indigo_content():
    content = BASE_CONTENT.copy()
    content["site_config"] = {
        "template_id": "bad",
        "trade": "hvac",
        "theme": {
            "primary": "#6366f1",
            "accent": "#3b82f6",
            "font_display": "Inter",
            "font_body": "Inter",
        },
    }
    return content


@pytest.fixture
def banned_generic_headline_content():
    content = BASE_CONTENT.copy()
    content["hero"]["headline"] = "Your Trusted Partner — Quality Service You Can Count On"
    return content


@pytest.fixture
def banned_animate_content():
    content = BASE_CONTENT.copy()
    content["hero"]["headline"] = "Best HVAC in Austin — We Are the #1 Choice!"
    return content


@pytest.mark.asyncio
async def test_gate_passes_clean_content(clean_content):
    result = await quality_gate_check(clean_content)
    assert result["score"] >= 0.85, f"Clean content should score >= 0.85, got {result['score']}"
    assert result["passed"] is True, "Clean content should pass"
    assert len(result["violations"]) == 0, f"Clean content should have 0 violations, got {result['violations']}"


@pytest.mark.asyncio
async def test_gate_bans_inter_font(banned_indigo_content):
    result = await quality_gate_check(banned_indigo_content)
    assert result["score"] < 1.0, "Score should be penalized for banned Inter font"
    assert any("banned" in v.lower() for v in result["violations"]), f"Expected BANNED violation, got: {result['violations']}"


@pytest.mark.asyncio
async def test_gate_bans_generic_headline(banned_generic_headline_content):
    result = await quality_gate_check(banned_generic_headline_content)
    assert result["score"] < 1.0, "Score should be penalized for generic headline"
    assert any("copy" in v.lower() or "headline" in v.lower() for v in result["violations"]), (
        f"Expected COPY violation for generic headline, got: {result['violations']}"
    )


@pytest.mark.asyncio
async def test_gate_returns_expected_keys(clean_content):
    result = await quality_gate_check(clean_content)
    for key in ["score", "violations", "passed", "details"]:
        assert key in result, f"quality_gate_check must return '{key}' key"

    assert isinstance(result["score"], float), "score must be float"
    assert isinstance(result["violations"], list), "violations must be list"
    assert isinstance(result["passed"], bool), "passed must be bool"
    assert isinstance(result["details"], dict), "details must be dict"


@pytest.mark.asyncio
async def test_gate_score_bounded():
    """Score must always be between 0.0 and 1.0."""
    terrible = {"business": {"business_name": "x"}, "hero": {"headline": "Best in town!!!"}, "services": [], "about": {}, "reviews": {"reviews": []}, "faq": [], "seo": {"title": "", "description": "", "keywords": []}, "aeo_signals": {}, "schema_org": None, "site_config": {}, "status": "", "slug": "", "meta_title": "", "meta_description": "", "lighthouse_score": 0}
    result = await quality_gate_check(terrible)
    assert 0.0 <= result["score"] <= 1.0, f"Score must be in [0,1], got {result['score']}"


@pytest.mark.asyncio
async def test_gate_no_double_counting():
    """Awwwards penalty must not double-count. Minimum score should not plummet
    from double-penalties on clean-ish content."""
    content = {
        "business": {"business_name": "Austin Pro HVAC", "trade": "hvac", "city": "Austin", "state": "TX", "phone": "(512) 555-1234", "address": "123 Main St", "google_rating": 4.8, "review_count": 127, "years_in_business": 15},
        "hero": {"headline": "Austin Pro HVAC — Same-Day AC Repair in Austin, TX", "subheadline": "Professional service.", "trust_bar": ["Licensed"], "cta_primary": "Call", "cta_primary_url": "tel:+15125551234", "cta_secondary": "Quote", "cta_secondary_url": "#"},
        "services": [{"icon": "wrench", "title": "Service", "description": "We do HVAC work in Austin with real expertise.", "cta_text": "More"}],
        "about": {"story": "Austin Pro HVAC was founded in Austin.", "trust_points": ["Local team"], "certifications": ["EPA 608"]},
        "reviews": {"reviews": [{"rating": 5, "text": "Great work by Austin Pro HVAC.", "author": "Customer"}], "aggregate_line": "Rated 5 stars"},
        "faq": [{"question": "Do you offer free estimates?", "answer": "Yes, all estimates are free."}],
        "seo": {"title": "Austin Pro HVAC | HVAC in Austin, TX", "description": "Austin Pro HVAC provides professional HVAC services in Austin, TX.", "keywords": ["hvac", "Austin"]},
        "aeo_signals": {"local_business_type": "HomeService", "primary_category": "HVAC", "secondary_categories": [], "area_served": ["Austin"]},
        "schema_org": {"@context": "https://schema.org", "@type": "LocalBusiness", "name": "Austin Pro HVAC"},
        "site_config": {"template_id": "hvac-reliable-blue", "trade": "hvac", "theme": {"primary": "#1e3a5f", "accent": "#0ea5e9", "font_display": "Instrument Serif", "font_body": "DM Sans"}},
        "status": "draft",
        "slug": "austin-pro-hvac-austin-tx",
        "meta_title": "Austin Pro HVAC | HVAC in Austin, TX",
        "meta_description": "Professional HVAC in Austin, TX.",
        "lighthouse_score": 90,
    }
    result = await quality_gate_check(content)
    assert result["score"] >= 0.50, f"Score should not be crushed by double-counting, got {result['score']}"
