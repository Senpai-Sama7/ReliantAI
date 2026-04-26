import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime,
    DECIMAL, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _uuid():
    return str(uuid.uuid4())


class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(String(36), primary_key=True, default=_uuid)
    place_id = Column(String(255), unique=True, nullable=False)
    business_name = Column(String(255), nullable=False)
    trade = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(String(500))
    lat = Column(DECIMAL(10, 8))
    lng = Column(DECIMAL(11, 8))
    google_rating = Column(DECIMAL(2, 1))
    review_count = Column(Integer, default=0)
    website_url = Column(String(500))
    status = Column(String(50), default="identified")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    research_jobs = relationship(
        "ResearchJob", back_populates="prospect", cascade="all, delete-orphan"
    )
    business_intel = relationship(
        "BusinessIntelligence", back_populates="prospect",
        cascade="all, delete-orphan", uselist=False
    )
    competitors = relationship(
        "CompetitorIntelligence", back_populates="prospect",
        cascade="all, delete-orphan"
    )
    generated_site = relationship(
        "GeneratedSite", back_populates="prospect",
        cascade="all, delete-orphan", uselist=False
    )
    outreach_sequences = relationship(
        "OutreachSequence", back_populates="prospect",
        cascade="all, delete-orphan"
    )
    outreach_messages = relationship(
        "OutreachMessage", back_populates="prospect",
        cascade="all, delete-orphan"
    )
    lead_events = relationship(
        "LeadEvent", back_populates="prospect", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "place_id": self.place_id,
            "business_name": self.business_name,
            "trade": self.trade,
            "city": self.city,
            "state": self.state,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "lat": float(self.lat) if self.lat else None,
            "lng": float(self.lng) if self.lng else None,
            "google_rating": float(self.google_rating) if self.google_rating else None,
            "review_count": self.review_count,
            "website_url": self.website_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(String(36), primary_key=True, default=_uuid)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending")
    step = Column(String(50))
    error_message = Column(Text)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    prospect = relationship("Prospect", back_populates="research_jobs")

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "status": self.status,
            "step": self.step,
            "error_message": self.error_message,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BusinessIntelligence(Base):
    __tablename__ = "business_intelligence"

    id = Column(String(36), primary_key=True, default=_uuid)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    years_in_business = Column(Integer)
    service_area = Column(String(500))
    service_specialties = Column(Text)
    owner_name = Column(String(255))
    owner_title = Column(String(255))
    gbp_profile_complete = Column(Boolean, default=False)
    gbp_review_response_rate = Column(DECIMAL(5, 2))
    site_last_updated = Column(String(100))
    site_mobile_friendly = Column(Boolean)
    instagram_url = Column(String(500))
    facebook_url = Column(String(500))
    linkedin_url = Column(String(500))
    youtube_url = Column(String(500))
    yelp_url = Column(String(500))
    business_hours = Column(Text)
    payment_methods = Column(Text)
    certifications = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    prospect = relationship("Prospect", back_populates="business_intel")

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "years_in_business": self.years_in_business,
            "service_area": self.service_area,
            "owner_name": self.owner_name,
            "owner_title": self.owner_title,
            "gbp_profile_complete": self.gbp_profile_complete,
            "gbp_review_response_rate": float(self.gbp_review_response_rate) if self.gbp_review_response_rate else None,
            "site_mobile_friendly": self.site_mobile_friendly,
            "instagram_url": self.instagram_url,
        }


class CompetitorIntelligence(Base):
    __tablename__ = "competitor_intelligence"

    id = Column(String(36), primary_key=True, default=_uuid)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    competitor_name = Column(String(255), nullable=False)
    competitor_website = Column(String(500))
    top_keywords = Column(Text)
    content_themes = Column(Text)
    pricing_strategy = Column(Text)
    estimated_monthly_volume = Column(Integer)
    search_ranking_position = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    prospect = relationship("Prospect", back_populates="competitors")

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "competitor_name": self.competitor_name,
            "competitor_website": self.competitor_website,
            "top_keywords": self.top_keywords,
        }


class Client(Base):
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True, default=_uuid)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    package = Column(String(50))
    custom_domain = Column(String(255))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    prospect = relationship("Prospect")
    generated_sites = relationship("GeneratedSite", back_populates="client")

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "stripe_customer_id": self.stripe_customer_id,
            "package": self.package,
            "custom_domain": self.custom_domain,
            "status": self.status,
        }


class GeneratedSite(Base):
    __tablename__ = "generated_sites"

    id = Column(String(36), primary_key=True, default=_uuid)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    slug = Column(String(100), unique=True, nullable=False)
    template_id = Column(String(100), nullable=False)
    preview_url = Column(String(500))
    production_url = Column(String(500))
    status = Column(String(50), default="preview_live")
    site_content = Column(JSON)
    site_config = Column(JSON)
    schema_org_json = Column(JSON)
    meta_title = Column(String(255))
    meta_description = Column(String(500))
    lighthouse_score = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    prospect = relationship("Prospect", back_populates="generated_site")
    client = relationship("Client", back_populates="generated_sites")

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "slug": self.slug,
            "template_id": self.template_id,
            "preview_url": self.preview_url,
            "production_url": self.production_url,
            "status": self.status,
            "meta_title": self.meta_title,
            "lighthouse_score": self.lighthouse_score,
        }


class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"

    id = Column(String(36), primary_key=True, default=_uuid)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False)
    sequence_template = Column(String(100), default="home_services_v1")
    status = Column(String(50), default="pending")
    current_step = Column(Integer, default=0)
    max_steps = Column(Integer, default=4)
    next_send_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    prospect = relationship("Prospect", back_populates="outreach_sequences")
    messages = relationship(
        "OutreachMessage", back_populates="sequence", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "channel": self.channel,
            "sequence_template": self.sequence_template,
            "status": self.status,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "next_send_at": self.next_send_at.isoformat() if self.next_send_at else None,
        }


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    sequence_id = Column(String(36), ForeignKey("outreach_sequences.id", ondelete="CASCADE"), nullable=False)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    channel = Column(String(50), nullable=False)
    to_address = Column(String(255), nullable=False)
    from_address = Column(String(255), nullable=False)
    subject = Column(String(255))
    body = Column(Text, nullable=False)
    status = Column(String(50), default="queued")
    provider_message_id = Column(String(255))
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sequence = relationship("OutreachSequence", back_populates="messages")
    prospect = relationship("Prospect", back_populates="outreach_messages")

    def to_dict(self):
        return {
            "id": self.id,
            "sequence_id": self.sequence_id,
            "prospect_id": self.prospect_id,
            "step_number": self.step_number,
            "channel": self.channel,
            "to_address": self.to_address,
            "subject": self.subject,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


class LeadEvent(Base):
    __tablename__ = "lead_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    prospect_id = Column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    from_address = Column(String(255))
    message_body = Column(Text)
    is_hot_lead = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    prospect = relationship("Prospect", back_populates="lead_events")

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "event_type": self.event_type,
            "from_address": self.from_address,
            "is_hot_lead": self.is_hot_lead,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
