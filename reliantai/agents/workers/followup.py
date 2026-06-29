"""
Followup agent — manages the outreach follow-up sequence.
Sends follow-up messages to prospects who haven't responded,
with increasing urgency and value propositions.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from ..core.base import AgentConfig, BaseAgent
from ..core.memory import AgentMemory

logger = structlog.get_logger("agents.followup")

FOLLOWUP_TEMPLATES = {
    2: "Hey {name} — just checking if you got a chance to see your free site: {preview_url}. Happy to make any changes!",
    3: "{name}, your free preview site is still live: {preview_url}. Want me to add anything or take it down?",
    4: "Last follow-up, {name}. Your site is ready whenever you are: {preview_url}. No pressure — just let me know!",
}


class FollowupAgent(BaseAgent):
    """
    Manages follow-up sequences for prospects who haven't responded.

    On each iteration:
    1. Finds active outreach sequences where next_send_at <= now
    2. Sends the next follow-up message in the sequence
    3. Updates sequence step and schedules next follow-up
    4. Marks sequence as completed after max_steps
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(
            name="followup",
            poll_interval_seconds=float(os.environ.get("FOLLOWUP_POLL_SECONDS", "300")),
        ))
        self.memory = AgentMemory()

    def _operation_name(self) -> str:
        return "followup"

    async def _check_for_work(self) -> bool:
        from ...db import get_db_session
        from ...db.models import OutreachSequence

        with get_db_session() as db:
            now = datetime.now(timezone.utc)
            count = db.query(OutreachSequence).filter(
                OutreachSequence.next_send_at <= now,
                OutreachSequence.status == "active",
            ).count()
        return count > 0

    async def _execute(self) -> dict[str, Any]:
        from ...db import get_db_session
        from ...db.models import OutreachSequence, OutreachMessage, Prospect

        now = datetime.now(timezone.utc)

        with get_db_session() as db:
            due_sequences = db.query(OutreachSequence).filter(
                OutreachSequence.next_send_at <= now,
                OutreachSequence.status == "active",
            ).limit(20).all()

        sent = 0
        completed = 0
        errors = 0

        for seq in due_sequences:
            try:
                next_step = seq.current_step + 1

                if next_step > seq.max_steps:
                    with get_db_session() as db:
                        s = db.query(OutreachSequence).filter_by(id=seq.id).first()
                        if s:
                            s.status = "completed"
                            s.next_send_at = None
                    completed += 1
                    continue

                # Get prospect info
                with get_db_session() as db:
                    prospect = db.query(Prospect).filter_by(id=seq.prospect_id).first()
                    if not prospect:
                        continue

                    name = prospect.business_name or "there"
                    preview_url = f"https://preview.reliantai.org/{getattr(prospect, 'slug', '')}"
                    channel = seq.channel
                    to_addr = prospect.phone if channel == "sms" else prospect.email

                if not to_addr:
                    self.logger.warning("no_address", seq_id=seq.id, channel=channel)
                    with get_db_session() as db:
                        s = db.query(OutreachSequence).filter_by(id=seq.id).first()
                        if s:
                            s.status = "completed"
                            s.next_send_at = None
                    continue

                # Build message
                template = FOLLOWUP_TEMPLATES.get(
                    next_step,
                    f"Hey {name} — following up on your free site: {preview_url}",
                )
                body = template.format(name=name, preview_url=preview_url)
                # Enforce SMS length limit
                if channel == "sms" and len(body) > 160:
                    body = body[:157] + "..."

                # Send via appropriate channel
                if channel == "sms":
                    sms_sent = await self._send_sms(to_addr, body)
                    status = "sent" if sms_sent else "failed"
                else:
                    email_sent = await self._send_email(to_addr, name, body)
                    status = "sent" if email_sent else "failed"

                # Record message and update sequence
                with get_db_session() as db:
                    msg = OutreachMessage(
                        sequence_id=seq.id,
                        prospect_id=seq.prospect_id,
                        step_number=next_step,
                        channel=channel,
                        to_address=to_addr,
                        from_address=os.environ.get("TWILIO_FROM_NUMBER", "") if channel == "sms" else os.environ.get("FROM_EMAIL", "hello@reliantai.org"),
                        body=body,
                        status=status,
                    )
                    db.add(msg)

                    s = db.query(OutreachSequence).filter_by(id=seq.id).first()
                    if s:
                        s.current_step = next_step
                        s.next_send_at = now + timedelta(days=3)

                sent += 1
                self.logger.info(
                    "followup_sent",
                    seq_id=seq.id,
                    step=next_step,
                    channel=channel,
                )

            except Exception as e:
                errors += 1
                self.logger.error("followup_failed", seq_id=seq.id, error=str(e))

        return {"sent": sent, "completed": completed, "errors": errors, "processed": len(due_sequences)}

    async def _send_sms(self, phone: str, body: str) -> bool:
        """Send SMS via Twilio."""
        import httpx
        import re

        sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        from_num = os.environ.get("TWILIO_FROM_NUMBER", "")

        if not all([sid, token, from_num]):
            return False
        if not re.match(r"^\+1\d{10}$", phone):
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                    auth=(sid, token),
                    data={"To": phone, "From": from_num, "Body": body},
                )
            return resp.status_code in (200, 201)
        except Exception as e:
            self.logger.error("followup_sms_error", error=str(e))
            return False

    async def _send_email(self, email: str, name: str, body: str) -> bool:
        """Send email via Resend."""
        import httpx

        key = os.environ.get("RESEND_API_KEY", "")
        from_email = os.environ.get("FROM_EMAIL", "hello@reliantai.org")
        if not key:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "from": f"ReliantAI <{from_email}>",
                        "to": [email],
                        "subject": f"{name} — following up on your free website",
                        "text": body,
                    },
                )
            return resp.status_code in (200, 201)
        except Exception as e:
            self.logger.error("followup_email_error", error=str(e))
            return False
