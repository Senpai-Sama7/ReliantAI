"""
Revenue Intelligence router — autonomous income tracking and optimization.

POST /revenue/leads/import      — bulk import scored leads (from CSV tool)
POST /revenue/leads             — add single lead
GET  /revenue/leads             — list (sorted by score)
POST /revenue/leads/{id}/stage  — advance funnel stage
GET  /revenue/funnel            — conversion funnel stats

POST /revenue/events            — record billable event (dispatch, subscription, etc.)
GET  /revenue/events            — list events (filter by product)
GET  /revenue/summary           — revenue totals by period + product

POST /revenue/invoices          — create invoice
GET  /revenue/invoices          — list invoices
POST /revenue/invoices/{id}/send
POST /revenue/invoices/{id}/pay

GET  /revenue/health            — autonomous income health check
"""

import math
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database import (
    upsert_revenue_lead, get_revenue_lead, list_revenue_leads,
    advance_lead_stage, lead_funnel_stats,
    record_revenue_event, list_revenue_events, revenue_summary,
    create_billing_record, get_billing_record, list_billing_records,
    mark_invoice_sent, mark_invoice_paid,
)

router = APIRouter(prefix="/revenue", tags=["revenue"])

PRODUCT_LINES = ["hvac", "enterprise", "dj", "other"]
LEAD_STAGES = ["new", "contacted", "interested", "demo", "negotiating", "won", "lost"]

# ── Pricing config (override via env) ────────────────────────────────────────
import os
HVAC_DISPATCH_RATE = float(os.getenv("HVAC_DISPATCH_RATE", "15.00"))   # $/dispatch
ENTERPRISE_MONTHLY  = float(os.getenv("ENTERPRISE_MONTHLY", "500.00")) # $/month
DJ_BOOKING_FEE      = float(os.getenv("DJ_BOOKING_FEE", "50.00"))      # $/booking


# ── Models ────────────────────────────────────────────────────────────────────

class LeadImportItem(BaseModel):
    external_id: str = Field(default="", max_length=64)
    company: str = Field(..., max_length=200)
    contact_name: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=200)
    city: str = Field(default="", max_length=100)
    rating: float = Field(default=0, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    has_website: bool = Field(default=False)
    product_line: str = Field(default="hvac")
    deal_value: float = Field(default=0, ge=0)
    source: str = Field(default="csv", max_length=50)
    notes: str = Field(default="", max_length=500)


class BulkImport(BaseModel):
    leads: list[LeadImportItem] = Field(..., max_length=10000)


class LeadStageUpdate(BaseModel):
    stage: str = Field(..., pattern="^(new|contacted|interested|demo|negotiating|won|lost)$")
    notes: str = Field(default="", max_length=500)


class RevenueEventCreate(BaseModel):
    lead_id: str = Field(default="", max_length=32)
    event_type: str = Field(..., max_length=50,
                            description="dispatch, subscription, booking, renewal, refund")
    product_line: str = Field(default="hvac", max_length=20)
    amount: float = Field(..., ge=0)
    description: str = Field(default="", max_length=500)
    reference_id: str = Field(default="", max_length=100)


class InvoiceCreate(BaseModel):
    lead_id: str = Field(..., max_length=32)
    company: str = Field(..., max_length=200)
    line_items: list[dict] = Field(...,
        description="[{description, quantity, unit_price}]")


# ── Lead scoring ──────────────────────────────────────────────────────────────

def _score_lead(rating: float, review_count: int, has_website: bool,
                deal_value: float, product_line: str) -> float:
    """
    Composite lead score 0–100.
    Higher = contact first.

    HVAC:       rating (0-5) + log(reviews) + website bonus
    Enterprise: deal_value + probability signal
    """
    if product_line == "enterprise":
        # Enterprise: prioritize by deal value and review/rating proxy
        return min(100, deal_value / 100 + rating * 5)

    # HVAC/default
    rating_score    = rating * 15          # max 75
    review_score    = math.log1p(review_count) * 4  # log scale, max ~30
    website_score   = 10 if has_website else 0
    return round(min(100, rating_score + review_score + website_score), 2)


# ── Lead endpoints ────────────────────────────────────────────────────────────

@router.post("/leads/import", status_code=201)
def bulk_import_leads(body: BulkImport):
    imported = 0
    skipped = 0
    for item in body.leads:
        score = _score_lead(item.rating, item.review_count, item.has_website,
                            item.deal_value, item.product_line)
        id = str(uuid.uuid5(uuid.NAMESPACE_DNS,
                            f"{item.product_line}:{item.company}:{item.external_id}"))[:16]
        upsert_revenue_lead(
            id=id, external_id=item.external_id, company=item.company,
            contact_name=item.contact_name, phone=item.phone, email=item.email,
            city=item.city, rating=item.rating, review_count=item.review_count,
            has_website=item.has_website, lead_score=score,
            product_line=item.product_line, deal_value=item.deal_value,
            source=item.source, notes=item.notes,
        )
        imported += 1
    return {"imported": imported, "skipped": skipped}


@router.post("/leads", status_code=201)
def add_lead(body: LeadImportItem):
    score = _score_lead(body.rating, body.review_count, body.has_website,
                        body.deal_value, body.product_line)
    id = str(uuid.uuid5(uuid.NAMESPACE_DNS,
                        f"{body.product_line}:{body.company}:{body.external_id}"))[:16]
    return upsert_revenue_lead(
        id=id, external_id=body.external_id, company=body.company,
        contact_name=body.contact_name, phone=body.phone, email=body.email,
        city=body.city, rating=body.rating, review_count=body.review_count,
        has_website=body.has_website, lead_score=score,
        product_line=body.product_line, deal_value=body.deal_value,
        source=body.source, notes=body.notes,
    )


@router.get("/leads")
def get_leads(
    stage: Optional[str] = Query(None),
    product_line: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
):
    return list_revenue_leads(stage, product_line, limit)


@router.post("/leads/{id}/stage")
def update_lead_stage(id: str, body: LeadStageUpdate):
    lead = advance_lead_stage(id, body.stage, body.notes)
    if not lead:
        raise HTTPException(404, f"Lead {id} not found")
    return lead


@router.get("/funnel")
def get_funnel():
    return lead_funnel_stats()


# ── Revenue events ────────────────────────────────────────────────────────────

@router.post("/events", status_code=201)
def add_revenue_event(body: RevenueEventCreate):
    id = str(uuid.uuid4())[:12]
    return record_revenue_event(
        id=id, lead_id=body.lead_id, event_type=body.event_type,
        product_line=body.product_line, amount=body.amount,
        description=body.description, reference_id=body.reference_id,
    )


@router.post("/events/dispatch")
def record_dispatch_event(
    lead_id: str = Query(default=""),
    reference_id: str = Query(default=""),
    notes: str = Query(default=""),
):
    """Called by Money/dispatch service on job completion."""
    id = str(uuid.uuid4())[:12]
    return record_revenue_event(
        id=id, lead_id=lead_id, event_type="dispatch",
        product_line="hvac", amount=HVAC_DISPATCH_RATE,
        description=f"HVAC dispatch completed. {notes}",
        reference_id=reference_id,
    )


@router.get("/events")
def get_revenue_events(
    product_line: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
):
    return list_revenue_events(product_line, days)


@router.get("/summary")
def get_revenue_summary(days: int = Query(30, ge=1, le=365)):
    summary = revenue_summary(days)
    funnel = lead_funnel_stats()
    return {
        **summary,
        "pipeline_value": funnel["pipeline_value"],
        "pricing": {
            "hvac_per_dispatch": HVAC_DISPATCH_RATE,
            "enterprise_monthly": ENTERPRISE_MONTHLY,
            "dj_per_booking": DJ_BOOKING_FEE,
        },
    }


# ── Invoices ──────────────────────────────────────────────────────────────────

@router.post("/invoices", status_code=201)
def create_invoice(body: InvoiceCreate):
    subtotal = sum(
        item.get("quantity", 1) * item.get("unit_price", 0)
        for item in body.line_items
    )
    id = str(uuid.uuid4())[:12]
    return create_billing_record(id, body.lead_id, body.company,
                                 body.line_items, subtotal)


@router.get("/invoices")
def get_invoices(status: Optional[str] = Query(None)):
    return list_billing_records(status)


@router.get("/invoices/{id}")
def get_invoice(id: str):
    inv = get_billing_record(id)
    if not inv:
        raise HTTPException(404, f"Invoice {id} not found")
    return inv


@router.post("/invoices/{id}/send")
def send_invoice(id: str):
    inv = mark_invoice_sent(id)
    if not inv:
        raise HTTPException(404, f"Invoice {id} not found")
    return inv


@router.post("/invoices/{id}/pay")
def pay_invoice(id: str):
    inv = mark_invoice_paid(id)
    if not inv:
        raise HTTPException(404, f"Invoice {id} not found")
    # Record as revenue event
    rev_id = str(uuid.uuid4())[:12]
    record_revenue_event(
        id=rev_id, lead_id=inv["lead_id"], event_type="payment",
        product_line="hvac", amount=inv["subtotal"],
        description=f"Invoice {id} paid — {inv['company']}",
        reference_id=id,
    )
    return inv


# ── Income health check ───────────────────────────────────────────────────────

@router.get("/health")
def income_health():
    """
    Autonomous income health check.
    Returns risk signals that indicate revenue is at risk.
    """
    summary_30 = revenue_summary(30)
    summary_7 = revenue_summary(7)
    funnel = lead_funnel_stats()

    # Warning: no revenue in last 7 days
    no_recent_revenue = summary_7["total_revenue"] == 0

    # Warning: no new leads this week
    new_leads = len(list_revenue_leads(stage="new", limit=1000))
    no_new_leads = new_leads == 0

    # Warning: invoices overdue (sent but not paid, >30d old)
    unpaid = list_billing_records("sent")
    from datetime import timedelta, datetime, timezone
    now = datetime.now(timezone.utc)
    overdue = [
        i for i in unpaid
        if i.get("due_date") and datetime.fromisoformat(i["due_date"]) < now
    ]

    # Warning: pipeline value is low
    low_pipeline = funnel["pipeline_value"] < ENTERPRISE_MONTHLY * 3

    signals = []
    if no_recent_revenue:
        signals.append({"severity": "HIGH", "message": "No revenue recorded in last 7 days"})
    if no_new_leads:
        signals.append({"severity": "MEDIUM", "message": "Lead pipeline is empty — import new leads"})
    if overdue:
        signals.append({"severity": "HIGH",
                        "message": f"{len(overdue)} invoice(s) overdue — follow up immediately"})
    if low_pipeline:
        signals.append({"severity": "MEDIUM",
                        "message": f"Pipeline value ${funnel['pipeline_value']:.0f} is below 3-month target"})

    return {
        "status": "at_risk" if any(s["severity"] == "HIGH" for s in signals) else
                  "warning" if signals else "healthy",
        "signals": signals,
        "revenue_30d": summary_30["total_revenue"],
        "revenue_7d": summary_7["total_revenue"],
        "pipeline_value": funnel["pipeline_value"],
        "overdue_invoices": len(overdue),
    }
