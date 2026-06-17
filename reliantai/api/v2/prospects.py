import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from ..auth import verify_api_key
from ...db import get_db_session
from ...db.models import Prospect, ResearchJob
from ...services.task_queue import enqueue_prospect_pipeline
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

    return ProspectListResponse(
        items=[_prospect_response(prospect) for prospect in prospects],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ProspectResponse, status_code=status.HTTP_201_CREATED)
def create_prospect(
    payload: ProspectCreate,
    _: bool = Depends(verify_api_key),
):
    place_id = payload.place_id or f"manual-{uuid.uuid4()}"

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
            db.flush()
            response = _prospect_response(prospect)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Prospect already exists",
            ) from None

    return response


@router.get("/{prospect_id}", response_model=ProspectResponse)
def get_prospect(
    prospect_id: str,
    _: bool = Depends(verify_api_key),
):
    with get_db_session() as db:
        prospect = db.query(Prospect).filter_by(id=prospect_id).first()
        if not prospect:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found")
        return _prospect_response(prospect)


@router.post("/{prospect_id}/research", response_model=ResearchJobResponse)
def trigger_research(
    prospect_id: str,
    _: bool = Depends(verify_api_key),
):
    with get_db_session() as db:
        prospect = db.query(Prospect).filter_by(id=prospect_id).first()
        if not prospect:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found")

        active_job = (
            db.query(ResearchJob)
            .filter(
                ResearchJob.prospect_id == prospect_id,
                ResearchJob.status.in_(("pending", "running")),
            )
            .first()
        )
        if active_job:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Research pipeline already in progress",
            )

        job = ResearchJob(
            prospect_id=prospect_id,
            status="pending",
            step="queued",
        )
        db.add(job)
        db.flush()
        job_id = job.id

    enqueue_prospect_pipeline(prospect_id)

    return ResearchJobResponse(
        job_id=job_id,
        status="queued",
        message="Research pipeline started",
    )
