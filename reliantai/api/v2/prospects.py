"""API v2 prospects router."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from reliantai.auth import verify_api_key
from reliantai.db import get_db_session
from reliantai.models import Prospect, ResearchJob
from reliantai.services.task_queue import enqueue_prospect_pipeline
from .schemas import (
    ProspectCreate,
    ProspectListResponse,
    ProspectResponse,
    ResearchJobResponse,
)

router = APIRouter(prefix="/api/v2/prospects", tags=["prospects"])


def _prospect_response(prospect: Prospect) -> ProspectResponse:
    data = prospect.to_dict()
    return ProspectResponse(
        id=data["id"],
        business_name=data["business_name"],
        trade=data["trade"],
        city=data["city"],
        state=data["state"],
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
        lat=data.get("lat"),
        lng=data.get("lng"),
        google_rating=data.get("google_rating"),
        review_count=data.get("review_count"),
        website_url=data.get("website_url"),
        status=data["status"],
        created_at=data.get("created_at"),
    )


@router.get("", response_model=ProspectListResponse)
def list_prospects(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    trade: str | None = None,
    _: bool = Depends(verify_api_key),
):
    """List all prospects with optional filtering."""
    with get_db_session() as db:
        query = db.query(Prospect)
        if status_filter:
            query = query.filter(Prospect.status == status_filter)
        if trade:
            query = query.filter(Prospect.trade == trade.lower().strip())

        total = query.count()
        prospects = (
            query.order_by(Prospect.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        items = [_prospect_response(prospect) for prospect in prospects]

    return ProspectListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ProspectResponse, status_code=status.HTTP_201_CREATED)
def create_prospect(
    payload: ProspectCreate,
    _: bool = Depends(verify_api_key),
):
    """Create a new prospect."""
    prospect_id = str(uuid.uuid4())
    place_id = payload.place_id or f"manual-{prospect_id}"

    with get_db_session() as db:
        duplicate = (
            db.query(Prospect)
            .filter(
                (Prospect.place_id == place_id)
                | (
                    (Prospect.business_name == payload.business_name)
                    & (Prospect.city == payload.city)
                )
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Prospect already exists",
            )

        prospect = Prospect(
            id=prospect_id,
            place_id=place_id,
            business_name=payload.business_name.strip(),
            trade=payload.trade,
            city=payload.city.strip(),
            state=payload.state,
            phone=payload.phone,
            email=payload.email,
            address=payload.address,
            lat=payload.lat,
            lng=payload.lng,
            google_rating=payload.google_rating,
            review_count=payload.review_count or 0,
            website_url=payload.website_url,
            status="identified",
        )
        db.add(prospect)
        try:
            db.commit()
            response = _prospect_response(prospect)
            
            # Enqueue pipeline job
            enqueue_prospect_pipeline(prospect_id)
            
            return response
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Prospect already exists",
            )


@router.get("/{prospect_id}", response_model=ProspectResponse)
def get_prospect(
    prospect_id: str,
    _: bool = Depends(verify_api_key),
):
    """Get a specific prospect by ID."""
    with get_db_session() as db:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            raise HTTPException(status_code=404, detail="Prospect not found")
        return _prospect_response(prospect)
