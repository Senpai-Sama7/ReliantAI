"""SQLAlchemy ORM models for ReliantAI."""

import json
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Prospect(Base):
    """Lead prospect record."""

    __tablename__ = "prospects"

    id = Column(String(36), primary_key=True)
    place_id = Column(String(255), unique=True, nullable=False, index=True)
    business_name = Column(String(255), nullable=False)
    trade = Column(String(50), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(2), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    google_rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True, default=0)
    website_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="identified", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    generated_site = relationship("GeneratedSite", back_populates="prospect", uselist=False)

    __table_args__ = (
        Index("ix_prospects_city_state", "city", "state"),
        Index("ix_prospects_trade", "trade"),
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
            "lat": self.lat,
            "lng": self.lng,
            "google_rating": self.google_rating,
            "review_count": self.review_count,
            "website_url": self.website_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GeneratedSite(Base):
    """Generated website record."""

    __tablename__ = "generated_sites"

    id = Column(String(36), primary_key=True)
    prospect_id = Column(String(36), ForeignKey("prospects.id"), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    site_content = Column(JSON, nullable=True)
    site_config = Column(JSON, nullable=True)
    schema_org_json = Column(JSON, nullable=True)
    lighthouse_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    prospect = relationship("Prospect", back_populates="generated_site")

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "slug": self.slug,
            "status": self.status,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "lighthouse_score": self.lighthouse_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ResearchJob(Base):
    """Background research job tracking."""

    __tablename__ = "research_jobs"

    id = Column(String(36), primary_key=True)
    prospect_id = Column(String(36), ForeignKey("prospects.id"), nullable=True, index=True)
    job_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="queued", index=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "job_type": self.job_type,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
