import structlog
from celery import shared_task
from datetime import datetime, timedelta
from ..db import get_db_session
from ..db.models import Prospect, ResearchJob, OutreachSequence, OutreachMessage, LeadEvent
from ..agents.home_services_crew import create_prospect_crew
from ..services.site_registration_service import SiteRegistrationService

log = structlog.get_logger()

STOP_WORDS = {"stop", "unsubscribe", "quit", "cancel", "end", "no more", "opt out", "remove me"}


@shared_task(bind=True, name="prospect_tasks.run_prospect_pipeline", queue="agents")
def run_prospect_pipeline(self, prospect_id: str):
    job = None
    try:
        with get_db_session() as db:
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            if not prospect:
                log.error("pipeline_prospect_not_found", prospect_id=prospect_id)
                return {"error": "prospect_not_found"}

            job = ResearchJob(
                prospect_id=prospect_id,
                status="running",
                step="starting",
            )
            db.add(job)
            db.commit()
            job_id = job.id

        prospect_data = prospect.to_dict()

        crew = create_prospect_crew(prospect_data)
        result = crew.kickoff()

        with get_db_session() as db:
            job = db.query(ResearchJob).filter_by(id=job_id).first()
            job.status = "completed"
            job.step = "done"
            job.completed_at = datetime.utcnow()

            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            prospect.status = "outreach_sent"
            db.commit()

        log.info("pipeline_completed", prospect_id=prospect_id, job_id=job_id)
        return {"status": "completed", "prospect_id": prospect_id}

    except Exception as exc:
        log.error("pipeline_failed", prospect_id=prospect_id, error=str(exc))
        if job:
            with get_db_session() as db:
                db_job = db.query(ResearchJob).filter_by(id=job.id).first()
                if db_job:
                    db_job.status = "failed"
                    db_job.error_message = str(exc)[:500]
                    db.commit()
        raise self.retry(exc=exc, max_retries=3, countdown=60)


@shared_task(bind=True, name="prospect_tasks.process_inbound_response", queue="outreach")
def process_inbound_response(self, prospect_id: str, phone: str, body: str):
    body_lower = body.strip().lower()
    is_stop = any(word in body_lower for word in STOP_WORDS)

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
            owner_phone = __import__("os").environ.get("OWNER_PHONE", "")
            if owner_phone:
                log.info("hot_lead_detected", prospect_id=prospect_id, phone_last4=phone[-4:])

        return {"processed": True, "is_stop": is_stop}
    except Exception as exc:
        log.error("inbound_response_failed", prospect_id=prospect_id, error=str(exc))
        raise self.retry(exc=exc, max_retries=3, countdown=30)


@shared_task(name="prospect_tasks.process_scheduled_followups", queue="outreach")
def process_scheduled_followups():
    try:
        with get_db_session() as db:
            now = datetime.utcnow()
            due = db.query(OutreachSequence).filter(
                OutreachSequence.next_send_at <= now,
                OutreachSequence.status == "active",
            ).with_for_update(skip_locked=True).all()

            processed = 0
            for seq in due:
                next_step = seq.current_step + 1

                if next_step > seq.max_steps:
                    seq.status = "completed"
                    seq.next_send_at = None
                else:
                    msg = OutreachMessage(
                        sequence_id=seq.id,
                        prospect_id=seq.prospect_id,
                        step_number=next_step,
                        channel=seq.channel,
                        to_address=seq.prospect.phone if seq.channel == "sms" else seq.prospect.email,
                        from_address=__import__("os").environ.get("TWILIO_FROM_NUMBER", ""),
                        body="Follow-up message placeholder — replace with template",
                        status="queued",
                    )
                    db.add(msg)
                    seq.current_step = next_step
                    seq.next_send_at = now + timedelta(days=3)
                    processed += 1

            db.commit()
            log.info("followups_processed", count=processed)
            return {"processed": processed}
    except Exception as exc:
        log.error("followups_failed", error=str(exc))
        return {"error": str(exc)[:200]}
