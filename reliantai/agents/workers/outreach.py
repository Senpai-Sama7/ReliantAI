"""
Outreach agent — sends personalized first-contact messages to prospects
whose sites are live. Uses SMS first, email as fallback.
"""

from __future__ import annotations

import os
import re
from typing import Any

import httpx
import structlog

from ..core.base import AgentConfig, BaseAgent
from ..core.memory import AgentMemory

logger = structlog.get_logger("agents.outreach")

OWNER_PHONE = os.environ.get("OWNER_PHONE", "")
STOP_WORDS = {"stop", "unsubscribe", "quit", "cancel", "end"}


class OutreachAgent(BaseAgent):
    """
    Sends personalized outreach to prospects with live sites.

    On each iteration:
    1. Finds prospects with status 'site_live' who haven't been contacted
    2. Crafts a personalized SMS referencing their business
    3. Sends via Twilio SMS (primary) or Resend email (fallback)
    4. Logs the outreach event
    5. Updates prospect status to 'outreach_sent'
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(
            name="outreach",
            poll_interval_seconds=float(os.environ.get("OUTREACH_POLL_SECONDS", "60")),
        ))
        self.memory = AgentMemory()
        self.twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.twilio_from = os.environ.get("TWILIO_FROM_NUMBER", "")
        self.resend_key = os.environ.get("RESEND_API_KEY", "")
        self.from_email = os.environ.get("FROM_EMAIL", "hello@reliantai.org")

    def _operation_name(self) -> str:
        return "outreach"

    async def _check_for_work(self) -> bool:
        from ...db import get_db_session
        from ...db.models import Prospect

        with get_db_session() as db:
            count = db.query(Prospect).filter_by(status="site_live").count()
        return count > 0

    async def _execute(self) -> dict[str, Any]:
        from ...db import get_db_session
        from ...db.models import Prospect, OutreachSequence, OutreachMessage

        with get_db_session() as db:
            prospects = db.query(Prospect).filter_by(status="site_live").limit(10).all()

        sent = 0
        errors = 0

        for prospect in prospects:
            try:
                phone = (prospect.phone or "").strip()
                email = (prospect.email or "").strip()
                preview_url = f"https://preview.reliantai.org/{getattr(prospect, 'slug', '')}"

                # Craft personalized message
                msg_body = self._craft_message(prospect, preview_url)
                sms_sid = None

                # Send SMS if we have a phone
                if phone and self.twilio_sid:
                    sms_sid = await self._send_sms(phone, msg_body)

                # Fallback to email
                email_sent = False
                if not sms_sid and email and self.resend_key:
                    email_sent = await self._send_email(email, prospect.business_name, msg_body)

                # Record the outreach
                with get_db_session() as db:
                    seq = OutreachSequence(
                        prospect_id=prospect.id,
                        channel="sms" if sms_sid else "email",
                        status="active",
                        current_step=1,
                        max_steps=4,
                    )
                    db.add(seq)
                    db.flush()

                    msg = OutreachMessage(
                        sequence_id=seq.id,
                        prospect_id=prospect.id,
                        step_number=1,
                        channel="sms" if sms_sid else "email",
                        to_address=phone if sms_sid else email,
                        from_address=self.twilio_from if sms_sid else self.from_email,
                        body=msg_body,
                        status="sent" if (sms_sid or email_sent) else "failed",
                        provider_message_id=sms_sid or "",
                    )
                    db.add(msg)

                    prospect.status = "outreach_sent"

                sent += 1
                self.logger.info(
                    "outreach_sent",
                    prospect_id=prospect.id,
                    business=prospect.business_name,
                    channel="sms" if sms_sid else "email",
                )

            except Exception as e:
                errors += 1
                self.logger.error("outreach_failed", prospect_id=prospect.id, error=str(e))

        return {"sent": sent, "errors": errors, "processed": len(prospects)}

    def _craft_message(self, prospect: Any, preview_url: str) -> str:
        """Craft a personalized outreach message under 160 chars."""
        name = prospect.business_name or "there"
        trade = prospect.trade or "services"
        city = prospect.city or "your area"

        templates = [
            f"Hi {name}! We built a free {trade} site for {city}. See it: {preview_url}",
            f"Hey {name} — your new {trade} website is ready. Free preview: {preview_url}",
            f"{name}, your {trade} site is live! Check your free preview: {preview_url}",
        ]
        # Use rating-based personalization
        rating = getattr(prospect, "google_rating", None)
        if rating and rating >= 4.5:
            templates.insert(0, f"Hi {name}! Loved your {rating}-star reviews. Built you a free site: {preview_url}")

        for t in templates:
            if len(t) <= 160:
                return t
        # Fallback: truncate
        return templates[-1][:157] + "..."

    async def _send_sms(self, phone: str, body: str) -> str | None:
        """Send SMS via Twilio. Returns message SID or None."""
        if not re.match(r"^\+1\d{10}$", phone):
            self.logger.warning("invalid_phone", last4=phone[-4:] if len(phone) >= 4 else "")
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json",
                    auth=(self.twilio_sid, self.twilio_token),
                    data={"To": phone, "From": self.twilio_from, "Body": body},
                )
            if resp.status_code in (200, 201):
                data = resp.json()
                self.logger.info("sms_sent", last4=phone[-4:], sid=data.get("sid"))
                return data.get("sid")
            self.logger.error("sms_failed", status=resp.status_code, last4=phone[-4:])
        except Exception as e:
            self.logger.error("sms_error", error=str(e), last4=phone[-4:])
        return None

    async def _send_email(self, email: str, business_name: str, body: str) -> bool:
        """Send email via Resend. Returns True on success."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {self.resend_key}"},
                    json={
                        "from": f"ReliantAI <{self.from_email}>",
                        "to": [email],
                        "subject": f"{business_name} — Your free website is ready",
                        "text": body,
                    },
                )
            ok = resp.status_code in (200, 201)
            self.logger.info("email_sent" if ok else "email_failed", email_last4=email[-4:], status=resp.status_code)
            return ok
        except Exception as e:
            self.logger.error("email_error", error=str(e))
            return False
