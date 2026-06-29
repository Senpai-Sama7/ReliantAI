"""API v2 webhooks router."""

from fastapi import APIRouter, Request, HTTPException
import hmac
import os

router = APIRouter(prefix="/api/v2/webhooks", tags=["webhooks"])


def _verify_webhook_signature(signature: str, payload: bytes) -> bool:
    """Verify webhook signature from Twilio/Stripe."""
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not secret:
        return False
    
    expected = hmac.new(
        secret.encode(),
        payload,
        "sha256"
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


@router.post("/twilio/sms")
async def handle_twilio_webhook(request: Request):
    """Handle incoming Twilio SMS webhooks."""
    body = await request.body()
    signature = request.headers.get("X-Twilio-Signature", "")
    
    if not _verify_webhook_signature(signature, body):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Placeholder for Phase 4 Twilio integration
    return {"ok": True}


@router.post("/stripe/webhook")
async def handle_stripe_webhook(request: Request):
    """Handle incoming Stripe webhooks."""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    if not _verify_webhook_signature(signature, body):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Placeholder for Phase 4 Stripe integration
    return {"ok": True}
