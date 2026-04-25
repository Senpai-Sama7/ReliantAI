import os
import structlog
from crewai.tools import BaseTool

log = structlog.get_logger()


class ResendEmailTool(BaseTool):
    name: str = "send_email"
    description: str = (
        "Send an email via Resend. "
        "Pass to=email, subject=subject line, body=email body (plain text)."
    )

    def _run(self, to: str, subject: str, body: str) -> str:
        if not to or not subject or not body:
            return str({"error": "to, subject, and body required"})

        api_key = os.environ.get("RESEND_API_KEY", "")
        from_email = os.environ.get("FROM_EMAIL", "noreply@reliantai.org")

        if not api_key:
            return str({"error": "RESEND_API_KEY not set"})

        try:
            import httpx
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
                log.info("email_sent", to_domain=to.split("@")[-1], subject=subject[:30])
                return str({"id": data.get("id"), "status": "sent"})
            else:
                log.error("email_failed", status_code=resp.status_code, to_domain=to.split("@")[-1])
                return str({"error": f"HTTP {resp.status_code}"})
        except Exception as e:
            log.error("email_exception", error=str(e))
            return str({"error": str(e)[:100]})
