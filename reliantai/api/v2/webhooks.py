"""API v2 webhooks router.

Provider signature schemes differ — do not invent a shared HMAC.
Endpoints fail closed until Twilio RequestValidator / Stripe construct_event
are wired with real secrets.
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/v2/webhooks", tags=["webhooks"])


@router.post("/twilio/sms")
async def handle_twilio_webhook(request: Request):
    """Twilio SMS inbound — not implemented (requires RequestValidator)."""
    # Consume body so clients cannot hang; reject until real verification exists.
    await request.body()
    raise HTTPException(
        status_code=501,
        detail="Twilio webhook verification not configured",
    )


@router.post("/stripe/webhook")
async def handle_stripe_webhook(request: Request):
    """Stripe webhook — not implemented (requires stripe.Webhook.construct_event)."""
    await request.body()
    raise HTTPException(
        status_code=501,
        detail="Stripe webhook verification not configured",
    )
