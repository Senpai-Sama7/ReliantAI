import os

import httpx
import structlog

from .phone import normalize_us_e164

log = structlog.get_logger()


def send_sms(to: str, body: str) -> dict:
    if not to or not body:
        return {"error": "to and body required"}

    normalized_to = normalize_us_e164(to)
    if not normalized_to:
        log.warning("sms_invalid_number", to_last4=to[-4:] if len(to) >= 4 else "???")
        return {"error": "invalid_number"}

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    from_number = os.environ.get("TWILIO_FROM_NUMBER", "")

    if not all([account_sid, auth_token, from_number]):
        return {"error": "twilio_not_configured"}

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                auth=(account_sid, auth_token),
                data={"To": normalized_to, "From": from_number, "Body": body},
            )
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"sid": data.get("sid"), "status": data.get("status")}
        return {"error": f"HTTP {resp.status_code}"}
    except httpx.RequestError as exc:
        return {"error": str(exc)[:100]}


def send_email(to: str, subject: str, body: str) -> dict:
    if not to or not subject or not body:
        return {"error": "to, subject, and body required"}

    api_key = os.environ.get("RESEND_API_KEY", "")
    from_email = os.environ.get("FROM_EMAIL", "noreply@reliantai.org")

    if not api_key:
        return {"error": "RESEND_API_KEY not set"}

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_email,
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"id": data.get("id"), "status": "sent"}
        return {"error": f"HTTP {resp.status_code}"}
    except httpx.RequestError as exc:
        return {"error": str(exc)[:100]}
