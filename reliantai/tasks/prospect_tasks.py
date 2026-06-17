import os
import structlog
from celery import shared_task
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import selectinload
from ..db import get_db_session
from ..db.models import Prospect, ResearchJob, OutreachSequence, OutreachMessage, LeadEvent
from ..agents.home_services_crew import create_prospect_crew
from ..services.outreach_dispatch import send_email, send_sms
from ..services.site_registration_service import SiteRegistrationService
from ..services.sms_compliance import is_stop_request

log = structlog.get_logger()


@shared_task(bind=True, name="prospect_tasks.run_prospect_pipeline", queue="agents")
def run_prospect_pipeline(self, prospect_id: str):
    job_id = None
    try:
        with get_db_session() as db:
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            if not prospect:
                log.error("pipeline_prospect_not_found", prospect_id=prospect_id)
                return {"error": "prospect_not_found"}

            # Capture data before commit expires the instance
            prospect_data = prospect.to_dict()

            job = (
                db.query(ResearchJob)
                .filter_by(prospect_id=prospect_id, status="pending")
                .order_by(ResearchJob.created_at.desc())
                .first()
            )
            if job:
                job.status = "running"
                job.step = "starting"
            else:
                job = ResearchJob(
                    prospect_id=prospect_id,
                    status="running",
                    step="starting",
                )
                db.add(job)
            db.commit()
            job_id = job.id

        crew = create_prospect_crew(prospect_data)
        result = crew.kickoff()
        log.info("crew_result", prospect_id=prospect_id, result_summary=str(result)[:200])

        registration = SiteRegistrationService.register_from_crew_outputs(prospect_id, crew)
        if registration.get("error"):
            log.warning("site_registration_skipped", prospect_id=prospect_id, error=registration["error"])
        else:
            log.info(
                "site_registered_from_pipeline",
                prospect_id=prospect_id,
                slug=registration.get("slug"),
                preview_url=registration.get("preview_url"),
            )

        with get_db_session() as db:
            job = db.query(ResearchJob).filter_by(id=job_id).first()
            job.status = "completed"
            job.step = "done"
            job.completed_at = datetime.now(timezone.utc)

            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            if registration.get("error"):
                prospect.status = "research_completed"
            else:
                prospect.status = "site_generated"
            db.commit()

        log.info(
            "pipeline_completed",
            prospect_id=prospect_id,
            job_id=job_id,
            prospect_status=prospect.status if prospect else None,
        )
        return {
            "status": "completed",
            "prospect_id": prospect_id,
            "site_registered": not registration.get("error"),
        }

    except Exception as exc:
        log.error("pipeline_failed", prospect_id=prospect_id, error=str(exc))
        if job_id:
            with get_db_session() as db:
                db_job = db.query(ResearchJob).filter_by(id=job_id).first()
                if db_job:
                    db_job.status = "failed"
                    db_job.error_message = str(exc)[:500]
                    db.commit()
        raise self.retry(exc=exc, max_retries=3, countdown=60)


@shared_task(bind=True, name="prospect_tasks.process_inbound_response", queue="outreach")
def process_inbound_response(self, prospect_id: str, phone: str, body: str):
    is_stop = is_stop_request(body)

    try:
        with get_db_session() as db:
            event = LeadEvent(
                prospect_id=prospect_id,
                event_type="inbound_sms_stop" if is_stop else "inbound_sms",
                from_address=phone[-4:],
                message_body=body[:500],
                is_hot_lead=not is_stop and len(body) > 10,
            )
            db.add(event)

            if is_stop:
                sequences = db.query(OutreachSequence).filter_by(
                    prospect_id=prospect_id, status="active"
                ).all()
                for seq in sequences:
                    seq.status = "unsubscribed"
                    seq.next_send_at = None
                log.info("prospect_unsubscribed", prospect_id=prospect_id, phone_last4=phone[-4:])

            db.commit()

        if not is_stop and len(body) > 10:
            owner_phone = os.environ.get("OWNER_PHONE", "")
            if owner_phone:
                log.info("hot_lead_detected", prospect_id=prospect_id, phone_last4=phone[-4:])

        return {"processed": True, "is_stop": is_stop}
    except (RuntimeError, ValueError) as exc:
        log.error("inbound_response_failed", prospect_id=prospect_id, error=str(exc))
        raise self.retry(exc=exc, max_retries=3, countdown=30)


@shared_task(name="prospect_tasks.process_scheduled_followups", queue="outreach")
def process_scheduled_followups():
    try:
        with get_db_session() as db:
            now = datetime.now(timezone.utc)
            due = (
                db.query(OutreachSequence)
                .options(selectinload(OutreachSequence.prospect))
                .filter(
                    OutreachSequence.next_send_at <= now,
                    OutreachSequence.status == "active",
                )
                .with_for_update(skip_locked=True)
                .all()
            )

            processed = 0
            for seq in due:
                next_step = seq.current_step + 1

                if next_step > seq.max_steps:
                    seq.status = "completed"
                    seq.next_send_at = None
                else:
                    if seq.channel == "sms":
                        from_address = os.environ.get("TWILIO_FROM_NUMBER", "")
                        to_address = seq.prospect.phone or ""
                    else:
                        from_address = os.environ.get("FROM_EMAIL", "noreply@reliantai.org")
                        to_address = seq.prospect.email or ""

                    if not to_address:
                        log.warning(
                            "followup_skipped_no_address",
                            sequence_id=seq.id,
                            channel=seq.channel,
                        )
                        seq.status = "completed"
                        seq.next_send_at = None
                        continue

                    msg = OutreachMessage(
                        sequence_id=seq.id,
                        prospect_id=seq.prospect_id,
                        step_number=next_step,
                        channel=seq.channel,
                        to_address=to_address,
                        from_address=from_address,
                        body=f"followup:{seq.sequence_template}:step{next_step}",
                        status="queued",
                    )
                    db.add(msg)
                    seq.current_step = next_step
                    seq.next_send_at = now + timedelta(days=3)
                    processed += 1

            db.commit()
            log.info("followups_processed", count=processed)
            return {"processed": processed}
    except (RuntimeError, ValueError) as exc:
        log.error("followups_failed", error=str(exc))
        return {"error": str(exc)[:200]}


@shared_task(name="prospect_tasks.dispatch_queued_outreach", queue="outreach")
def dispatch_queued_outreach():
    """Send queued outreach messages via Twilio or Resend."""
    try:
        with get_db_session() as db:
            messages = (
                db.query(OutreachMessage)
                .filter(OutreachMessage.status == "queued")
                .with_for_update(skip_locked=True)
                .limit(20)
                .all()
            )

            dispatched = 0
            for msg in messages:
                if msg.channel == "sms":
                    result = send_sms(msg.to_address, msg.body)
                else:
                    subject = msg.subject or "Message from ReliantAI"
                    result = send_email(msg.to_address, subject, msg.body)

                if result.get("error"):
                    msg.status = "failed"
                    msg.error_message = result["error"][:500]
                    log.warning(
                        "outreach_dispatch_failed",
                        message_id=msg.id,
                        channel=msg.channel,
                        error=result["error"],
                    )
                    continue

                msg.status = "sent"
                msg.sent_at = datetime.now(timezone.utc)
                msg.provider_message_id = result.get("sid") or result.get("id")
                dispatched += 1

                prospect = db.query(Prospect).filter_by(id=msg.prospect_id).first()
                if prospect and prospect.status in (
                    "identified",
                    "site_generated",
                    "research_completed",
                ):
                    prospect.status = "outreach_sent"

            log.info("outreach_dispatched", count=dispatched)
            return {"dispatched": dispatched}
    except (RuntimeError, ValueError) as exc:
        log.error("outreach_dispatch_failed", error=str(exc))
        return {"error": str(exc)[:200]}
