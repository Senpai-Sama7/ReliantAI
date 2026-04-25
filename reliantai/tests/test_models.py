"""
Phase 1 gate: create all core models, read back with relationships loaded.
Uses SQLite in-memory for CI — no Postgres required.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from reliantai.db.models import (
    Base, Prospect, ResearchJob, BusinessIntelligence,
    CompetitorIntelligence, GeneratedSite, OutreachSequence,
    OutreachMessage, LeadEvent, Client
)


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # SQLite doesn't enforce FK constraints by default — enable them
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_full_prospect_lifecycle(db_session):
    # Create Prospect
    prospect = Prospect(
        place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
        business_name="Apex HVAC",
        trade="hvac",
        city="Houston",
        state="TX",
        phone="+17135551234",
        email="owner@apexhvac.com",
        google_rating=4.8,
        review_count=127,
        status="identified",
    )
    db_session.add(prospect)
    db_session.flush()

    # Create ResearchJob
    job = ResearchJob(prospect_id=prospect.id, status="running", step="business_researcher")
    db_session.add(job)

    # Create BusinessIntelligence
    intel = BusinessIntelligence(
        prospect_id=prospect.id,
        years_in_business=12,
        owner_name="John Smith",
        owner_title="Owner",
        gbp_profile_complete=True,
        gbp_review_response_rate=85.5,
        site_mobile_friendly=False,
        instagram_url="https://instagram.com/apexhvac",
    )
    db_session.add(intel)

    # Create CompetitorIntelligence
    competitor = CompetitorIntelligence(
        prospect_id=prospect.id,
        competitor_name="Houston HVAC Pro",
        competitor_website="https://houstonhvacpro.com",
        top_keywords="hvac repair houston,ac repair near me",
    )
    db_session.add(competitor)

    # Create GeneratedSite
    site = GeneratedSite(
        prospect_id=prospect.id,
        slug="apex-hvac-houston-a3f1",
        template_id="hvac-reliable-blue",
        preview_url="https://preview.reliantai.org/apex-hvac-houston-a3f1",
        status="preview_live",
        meta_title="Apex HVAC — Trusted Houston HVAC Service",
    )
    db_session.add(site)

    # Create OutreachSequence
    sequence = OutreachSequence(
        prospect_id=prospect.id,
        channel="sms",
        sequence_template="home_services_v1",
        status="active",
        current_step=0,
        max_steps=4,
    )
    db_session.add(sequence)
    db_session.flush()

    # Create OutreachMessage
    message = OutreachMessage(
        sequence_id=sequence.id,
        prospect_id=prospect.id,
        step_number=0,
        channel="sms",
        to_address="+17135551234",
        from_address="+18885550000",
        body="Hey John, we built a free preview site for Apex HVAC. Check it out: https://preview.reliantai.org/apex-hvac-houston-a3f1",
        status="sent",
    )
    db_session.add(message)

    db_session.commit()

    # ─── READ BACK WITH RELATIONSHIPS ────────────────────────────────
    loaded = db_session.query(Prospect).filter_by(id=prospect.id).first()

    assert loaded is not None
    assert loaded.business_intel is not None
    assert loaded.business_intel.owner_name == "John Smith"
    assert loaded.business_intel.instagram_url == "https://instagram.com/apexhvac"
    assert loaded.generated_site is not None
    assert loaded.generated_site.slug == "apex-hvac-houston-a3f1"
    assert loaded.generated_site.status == "preview_live"
    assert len(loaded.research_jobs) == 1
    assert loaded.research_jobs[0].step == "business_researcher"
    assert len(loaded.competitors) == 1
    assert loaded.competitors[0].competitor_name == "Houston HVAC Pro"
    assert len(loaded.outreach_sequences) == 1
    assert loaded.outreach_sequences[0].channel == "sms"
    assert len(loaded.outreach_sequences[0].messages) == 1


def test_to_dict_serializable(db_session):
    prospect = db_session.query(Prospect).first()
    d = prospect.to_dict()
    assert d["business_name"] == "Apex HVAC"
    assert d["trade"] == "hvac"
    assert isinstance(d["google_rating"], float)

    site = prospect.generated_site
    sd = site.to_dict()
    assert sd["slug"] == "apex-hvac-houston-a3f1"
    assert sd["status"] == "preview_live"

    seq = prospect.outreach_sequences[0]
    seqd = seq.to_dict()
    assert seqd["channel"] == "sms"
    assert seqd["max_steps"] == 4
