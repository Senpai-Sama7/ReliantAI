"""Tests for the Prospect Engine."""

from __future__ import annotations

import os
import tempfile

import pytest

from reliantai.agents.core.prospect_engine import Prospect, ProspectEngine, OutreachTemplate


@pytest.fixture
def engine():
    """Create a temporary ProspectEngine for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    eng = ProspectEngine(db_path=db_path)
    yield eng
    os.unlink(db_path)


class TestProspectEngine:
    def test_add_prospect(self, engine):
        p = Prospect(company_name="Test HVAC", trade="hvac", city="Houston", state="TX",
                     pain_points='["no_website","high_rating","operational"]',
                     estimated_value=25000)
        pid = engine.add_prospect(p)
        assert pid > 0

    def test_score_no_website(self, engine):
        p = Prospect(company_name="Test", trade="hvac", city="Houston", state="TX",
                     pain_points='["no_website","high_rating","operational"]')
        score = engine.score_prospect(p)
        assert score >= 65  # no_website(30) + high_rating(15) + operational(10) + ai_relevance(10) + geography(5)

    def test_score_with_website(self, engine):
        p = Prospect(company_name="Test", website="https://example.com", trade="hvac",
                     city="Houston", state="TX")
        score = engine.score_prospect(p)
        assert score < 40  # Has website = lower score

    def test_get_hot_prospects(self, engine):
        engine.seed_demo_prospects()
        hot = engine.get_hot_prospects()
        assert len(hot) > 0
        for p in hot:
            assert p.score >= 80

    def test_get_warm_prospects(self, engine):
        engine.seed_demo_prospects()
        warm = engine.get_warm_prospects()
        # Warm = score 60-79; demo prospects may score higher
        for p in warm:
            assert p.score >= 60

    def test_get_cold_prospects(self, engine):
        engine.seed_demo_prospects()
        cold = engine.get_cold_prospects()
        for p in cold:
            assert p.score >= 40

    def test_advance_stage(self, engine):
        p = Prospect(company_name="Test Co", trade="hvac", city="Houston", state="TX")
        pid = engine.add_prospect(p)
        assert pid > 0
        engine.advance_stage(pid)
        prospects = engine.get_prospects()
        found = [x for x in prospects if x.id == pid]
        assert len(found) == 1
        assert found[0].stage == "contacted"

    def test_advance_to_specific_stage(self, engine):
        p = Prospect(company_name="Test Co", trade="hvac", city="Houston", state="TX")
        pid = engine.add_prospect(p)
        engine.advance_stage(pid, "negotiation")
        prospects = engine.get_prospects()
        found = [x for x in prospects if x.id == pid]
        assert found[0].stage == "negotiation"

    def test_generate_outreach(self, engine):
        p = Prospect(company_name="Apex HVAC", trade="hvac", city="Houston", state="TX",
                     pain_points='["no_website","high_rating","operational"]')
        pid = engine.add_prospect(p)
        msg = engine.generate_outreach(pid, "first_contact")
        assert msg is not None
        assert "Apex HVAC" in msg
        assert "Houston" in msg
        assert len(msg) <= 160

    def test_generate_outreach_email(self, engine):
        p = Prospect(company_name="Test Co", trade="freight", city="Atlanta", state="GA",
                     contact_name="John")
        pid = engine.add_prospect(p)
        msg = engine.generate_outreach(pid, "first_contact")
        assert msg is not None
        assert "Test Co" in msg
        assert "John" in msg

    def test_outreach_length_limit(self, engine):
        p = Prospect(company_name="Very Long Company Name LLC", trade="hvac",
                     city="Houston", state="TX",
                     pain_points='["no_website","high_rating","operational"]')
        pid = engine.add_prospect(p)
        msg = engine.generate_outreach(pid, "first_contact")
        assert msg is not None
        assert len(msg) <= 160

    def test_get_pipeline_summary(self, engine):
        engine.seed_demo_prospects()
        summary = engine.get_pipeline_summary()
        assert summary["total_prospects"] >= 10
        assert "new" in summary["by_stage"]
        assert summary["avg_score"] > 0

    def test_get_templates(self, engine):
        templates = engine.get_templates(vertical="hvac", channel="sms")
        assert len(templates) > 0
        for t in templates:
            assert t["vertical"] == "hvac"
            assert t["channel"] == "sms"

    def test_filter_by_trade(self, engine):
        engine.seed_demo_prospects()
        hvac = engine.get_prospects(trade="hvac")
        for p in hvac:
            assert p.trade == "hvac"

    def test_estimated_value_preserved(self, engine):
        p = Prospect(company_name="Valued Co", trade="saas", city="NYC", state="NY",
                     estimated_value=50000)
        pid = engine.add_prospect(p)
        prospects = engine.get_prospects()
        found = [x for x in prospects if x.id == pid]
        assert len(found) == 1
        assert found[0].estimated_value == 50000

    def test_seed_demo_prospects(self, engine):
        ids = engine.seed_demo_prospects()
        assert len(ids) == 10
        summary = engine.get_pipeline_summary()
        assert summary["total_prospects"] == 10
