"""API v2 schemas for request/response validation."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator

VALID_TRADES = frozenset(
    {"hvac", "plumbing", "electrical", "roofing", "painting", "landscaping"}
)


class ProspectCreate(BaseModel):
    """Schema for creating a new prospect."""
    
    business_name: str = Field(..., min_length=1, max_length=255)
    trade: str
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    place_id: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    lat: float | None = None
    lng: float | None = None
    google_rating: float | None = None
    review_count: int | None = None
    website_url: str | None = Field(default=None, max_length=500)

    @field_validator("trade")
    @classmethod
    def validate_trade(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in VALID_TRADES:
            allowed = ", ".join(sorted(VALID_TRADES))
            raise ValueError(f"trade must be one of: {allowed}")
        return normalized

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        normalized = value.upper().strip()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("state must be a 2-letter code")
        return normalized


class ProspectResponse(BaseModel):
    """Schema for prospect responses."""
    
    id: str
    business_name: str
    trade: str
    city: str
    state: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    google_rating: float | None = None
    review_count: int | None = None
    website_url: str | None = None
    status: str
    created_at: str | None = None

    model_config = {"from_attributes": True}


class ProspectListResponse(BaseModel):
    """Schema for list of prospects."""
    
    items: list[ProspectResponse]
    total: int
    limit: int
    offset: int


class ResearchJobResponse(BaseModel):
    """Schema for research job responses."""
    
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    message: str
