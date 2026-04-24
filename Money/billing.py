"""
Stripe Billing Router for HVAC AI Dispatch
Handles checkout, webhooks, customer provisioning, and API key validation
"""

import os
from datetime import datetime, timezone
from typing import Optional

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False

from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import (
    create_customer,
    get_customer_by_api_key,
    get_customer_by_stripe_id,
    update_customer,
    log_customer_event,
)
from config import setup_logging

logger = setup_logging("billing")

# Initialize Stripe
if STRIPE_AVAILABLE:
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


# FIX 6: lazy accessor avoids module-level env-var capture so tests can monkeypatch reliably
def _get_webhook_secret() -> str:
    return os.getenv("STRIPE_WEBHOOK_SECRET", "")

router = APIRouter(prefix="/billing", tags=["billing"])

# Pricing configuration
PRICING = {
    "free": {
        "name": "Free",
        "price": 0,
        "dispatches_per_month": 10,
        "features": ["10 dispatches/month", "Basic analytics", "Email support"],
    },
    "digital_presence": {
        "name": "Digital Presence",
        "price": 149,
        "price_id": os.environ.get("STRIPE_DIGITAL_PRESENCE_PRICE_ID", ""),
        "dispatches_per_month": 0,
        "features": ["ReliantAI.org Auto-Generated Website (AEO/GEO/SEO optimized)", "Managed Google Business Profile Sync", "Automated review collection"],
    },
    "growth_automation": {
        "name": "Growth & Automation",
        "price": 499,
        "price_id": os.environ.get("STRIPE_GROWTH_AUTOMATION_PRICE_ID", ""),
        "dispatches_per_month": 100,
        "features": ["Everything in Digital Presence", "Smart SMS triage & automated dispatching", "Ops-Intelligence basic dashboarding", "Missed call text-back"],
    },
    "enterprise_os": {
        "name": "Enterprise OS",
        "price": 1499,
        "price_id": os.environ.get("STRIPE_ENTERPRISE_OS_PRICE_ID", ""),
        "dispatches_per_month": -1,  # Unlimited
        "features": ["Everything in Growth & Automation", "FinOps360 cloud/fleet cost optimization", "ComplianceOne certification tracking", "Dedicated 24/7 AI agents (CrewAI)"],
    },
}


# ── Pydantic Models ────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    email: str
    name: str
    company: str = ""
    phone: str = ""
    plan: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    customer_id: int
    api_key: str


class CustomerResponse(BaseModel):
    id: int
    email: str
    name: str
    company: str
    plan: str
    status: str
    billing_status: str
    trial_ends_at: Optional[str]
    api_key: str


class PricingResponse(BaseModel):
    plans: dict


# ── API Routes ─────────────────────────────────────────────────

@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """Get all pricing plans."""
    return {"plans": PRICING}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(request: CheckoutRequest):
    """Create a Stripe checkout session and provision customer."""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Billing service not available")
    if request.plan not in PRICING:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan}")
    
    plan_config = PRICING[request.plan]
    
    # For free plan, no Stripe checkout needed
    if request.plan == "free":
        customer = create_customer(
            email=request.email,
            name=request.name,
            company=request.company,
            phone=request.phone,
            plan="free",
            lead_source="checkout_free",
        )
        log_customer_event(
            customer_id=customer["id"],
            event_type="customer_created",
            event_data={"plan": "free", "source": "checkout"},
        )
        return CheckoutResponse(
            checkout_url=f"{request.success_url}?customer_id={customer['id']}",
            customer_id=customer["id"],
            api_key=customer["api_key"],
        )
    
    # Check if Stripe is configured
    if not stripe or not stripe.api_key or not plan_config.get("price_id"):
        raise HTTPException(status_code=503, detail="Billing not configured")
    
    try:
        # Create Stripe customer
        stripe_customer = stripe.Customer.create(
            email=request.email,
            name=request.name,
            phone=request.phone,
            metadata={
                "company": request.company,
                "plan": request.plan,
            },
        )
        
        # Create local customer record
        customer = create_customer(
            email=request.email,
            name=request.name,
            company=request.company,
            phone=request.phone,
            stripe_customer_id=stripe_customer.id,
            plan=request.plan,
            lead_source="checkout_stripe",
        )
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer.id,
            payment_method_types=["card"],
            line_items=[{
                "price": plan_config["price_id"],
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{request.success_url}?session_id={{CHECKOUT_SESSION_ID}}&customer_id={customer['id']}",
            cancel_url=request.cancel_url,
            metadata={
                "customer_id": str(customer["id"]),
                "plan": request.plan,
            },
        )
        
        log_customer_event(
            customer_id=customer["id"],
            event_type="checkout_created",
            event_data={"plan": request.plan, "stripe_session_id": checkout_session.id},
        )
        
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            customer_id=customer["id"],
            api_key=customer["api_key"],
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customer")
async def get_customer(x_api_key: str = Header(..., alias="X-API-Key")):
    """Get customer details by API key."""
    customer = get_customer_by_api_key(x_api_key)
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Don't return full API key, only masked version
    masked_key = f"{customer['api_key'][:8]}...{customer['api_key'][-4:]}"
    
    return {
        "id": customer["id"],
        "email": customer["email"],
        "name": customer["name"],
        "company": customer["company"],
        "plan": customer["plan"],
        "status": customer["status"],
        "billing_status": customer["billing_status"],
        "trial_ends_at": customer["trial_ends_at"].isoformat() if customer["trial_ends_at"] else None,
        "api_key_masked": masked_key,
        "dispatches_allowed": PRICING.get(customer["plan"], {}).get("dispatches_per_month", 0),
    }


@router.get("/customers")
async def list_customers(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    limit: int = 100,
):
    """List all customers (admin only)."""
    from database import list_customers as db_list_customers
    
    customers = db_list_customers(status=status, plan=plan, limit=limit)
    
    # Mask API keys for security
    for customer in customers:
        if customer.get("api_key"):
            customer["api_key"] = f"{customer['api_key'][:8]}...{customer['api_key'][-4:]}"
    
    return {"customers": customers, "count": len(customers)}


# ── Webhook Handlers ────────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for subscription events."""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Billing service not available")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # FIX 6: read secret lazily so tests can monkeypatch _get_webhook_secret
    _secret = _get_webhook_secret()
    if not _secret:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, _secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_type = event["type"]
    data = event["data"]["object"]
    
    logger.info(f"Stripe webhook received: {event_type}")
    
    # Handle different event types
    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data)
    elif event_type == "invoice.payment_succeeded":
        await _handle_payment_succeeded(data)
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_cancelled(data)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data)
    
    return JSONResponse({"status": "success"})


async def _handle_checkout_completed(data: dict):
    """Handle successful checkout completion."""
    stripe_customer_id = data.get("customer")
    metadata = data.get("metadata", {})
    try:
        customer_id = int(metadata.get("customer_id", 0))
    except (ValueError, TypeError):
        logger.warning(f"Invalid customer_id in metadata: {metadata.get('customer_id')}")
        customer_id = 0
    plan = metadata.get("plan", "starter")
    
    if customer_id:
        # Update customer with subscription info
        update_customer(
            customer_id=customer_id,
            billing_status="active",
            status="active",
            plan=plan,
            subscription_starts_at=datetime.now(),
        )
        
        # Log revenue event
        price = PRICING.get(plan, {}).get("price", 0)
        log_customer_event(
            customer_id=customer_id,
            event_type="subscription_started",
            event_data={"plan": plan, "stripe_customer_id": stripe_customer_id},
            revenue_impact=price,
        )
        
        logger.info(f"Customer {customer_id} subscribed to {plan}")


async def _handle_payment_succeeded(data: dict):
    """Handle successful subscription payment."""
    stripe_customer_id = data.get("customer")
    amount_paid = data.get("amount_paid", 0) / 100  # Convert from cents
    
    customer = get_customer_by_stripe_id(stripe_customer_id)
    if customer:
        log_customer_event(
            customer_id=customer["id"],
            event_type="payment_succeeded",
            event_data={"amount": amount_paid, "invoice_id": data.get("id")},
            revenue_impact=amount_paid,
        )
        
        # Update monthly revenue
        update_customer(
            customer_id=customer["id"],
            monthly_revenue=amount_paid,
            billing_status="active",
        )


async def _handle_payment_failed(data: dict):
    """Handle failed subscription payment."""
    stripe_customer_id = data.get("customer")
    
    customer = get_customer_by_stripe_id(stripe_customer_id)
    if customer:
        log_customer_event(
            customer_id=customer["id"],
            event_type="payment_failed",
            event_data={"invoice_id": data.get("id")},
        )
        
        update_customer(
            customer_id=customer["id"],
            billing_status="past_due",
        )


async def _handle_subscription_cancelled(data: dict):
    """Handle subscription cancellation."""
    stripe_customer_id = data.get("customer")
    
    customer = get_customer_by_stripe_id(stripe_customer_id)
    if customer:
        log_customer_event(
            customer_id=customer["id"],
            event_type="subscription_cancelled",
            event_data={"subscription_id": data.get("id")},
        )
        
        update_customer(
            customer_id=customer["id"],
            billing_status="cancelled",
            status="inactive",
            subscription_ends_at=datetime.now(),
        )


async def _handle_subscription_updated(data: dict):
    """Handle subscription updates (plan changes, etc.)."""
    stripe_customer_id = data.get("customer")
    status = data.get("status")
    
    customer = get_customer_by_stripe_id(stripe_customer_id)
    if customer and status:
        update_customer(
            customer_id=customer["id"],
            billing_status=status,
        )


# ── API Key Validation ─────────────────────────────────────────

async def validate_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> dict:
    """
    Validate API key and return customer.
    Raises HTTPException if invalid.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    customer = get_customer_by_api_key(x_api_key)
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check if billing is in good standing
    if customer["billing_status"] in ["past_due", "cancelled"]:
        raise HTTPException(
            status_code=403,
            detail="Billing issue. Please update payment method."
        )
    
    # FIX 7: use timezone-aware comparison; guard against mismatched types
    if customer["trial_ends_at"]:
        try:
            trial_expired = customer["trial_ends_at"] < datetime.now(timezone.utc)
        except TypeError:
            logger.warning("trial_ends_at type mismatch for customer %s", customer.get("id"))
            trial_expired = True
        if trial_expired and customer["billing_status"] == "trialing":
            raise HTTPException(
                status_code=403,
                detail="Trial expired. Please subscribe to continue."
            )
    
    return customer


def check_dispatch_quota(customer: dict) -> bool:
    """Check if customer has remaining dispatch quota for the month."""
    plan = customer.get("plan", "free")
    quota = PRICING.get(plan, {}).get("dispatches_per_month", 0)
    
    # Unlimited
    if quota == -1:
        return True
    
    # Count dispatches this month
    from database import get_pool
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT COUNT(*) FROM customer_events 
                   WHERE customer_id = %s 
                   AND event_type = 'dispatch_created'
                   AND created_at > DATE_TRUNC('month', NOW())""",
                (customer["id"],),
            )
            count = cursor.fetchone()[0]
            return count < quota
    finally:
        get_pool().putconn(conn)


# ── Revenue Tracking ───────────────────────────────────────────

@router.get("/revenue")
async def get_revenue(days: int = 30):
    """Get revenue summary."""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Billing service not available")
    from database import get_revenue_summary
    
    summary = get_revenue_summary(days)
    
    return {
        "period_days": days,
        "active_customers": summary["active_customers"],
        "total_revenue": float(summary["total_revenue"] or 0),
        "total_events": summary["total_events"],
        "mrr_estimate": float(summary["total_revenue"] or 0) / (days / 30),
    }


# ── Customer Portal ────────────────────────────────────────────

@router.post("/portal")
async def create_portal_session(x_api_key: str = Header(..., alias="X-API-Key")):
    """Create a Stripe customer portal session."""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Billing service not available")
    customer = await validate_api_key(x_api_key)
    
    if not customer.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="No Stripe subscription found")
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer["stripe_customer_id"],
            return_url=os.environ.get("PORTAL_RETURN_URL", "http://localhost:5173/billing"),
        )
        return {"portal_url": session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
