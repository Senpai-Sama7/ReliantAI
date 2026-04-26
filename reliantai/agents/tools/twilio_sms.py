import os
import re
import structlog
from crewai.tools import BaseTool

log = structlog.get_logger()


class TwilioSMSTool(BaseTool):
    name: str = "send_sms"
    description: str = (
        "Send an SMS message via Twilio. "
        "Pass to=phone (E.164 format) and body=message text."
    )

    def _run(self, to: str, body: str) -> str:
        if not to or not body:
            return str({"error": "to and body required"})

        if not re.match(r"^\+1\d{10}$", to):
            log.warning("sms_invalid_number", to_last4=to[-4:] if len(to) >= 4 else "???")
            return str({"error": "invalid_number"})

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        from_number = os.environ.get("TWILIO_FROM_NUMBER", "")

        if not all([account_sid, auth_token, from_number]):
            return str({"error": "twilio_not_configured"})

        try:
            import httpx
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                    auth=(account_sid, auth_token),
                    data={
                        "To": to,
                        "From": from_number,
                        "Body": body,
                    },
                )
            if resp.status_code in (200, 201):
                data = resp.json()
                log.info(
                    "sms_sent",
                    to_last4=to[-4:],
                    body_length=len(body),
                    status=data.get("status"),
                )
                return str({"sid": data.get("sid"), "status": data.get("status")})
            else:
                log.error("sms_failed", status_code=resp.status_code, to_last4=to[-4:])
                return str({"error": f"HTTP {resp.status_code}"})
        except httpx.TimeoutException:
            log.error("sms_timeout", to_last4=to[-4:] if len(to) >= 4 else "???")
            return str({"error": "timeout"})
        except httpx.HTTPStatusError as e:
            log.error("sms_http_error", status_code=e.response.status_code, to_last4=to[-4:] if len(to) >= 4 else "???")
            return str({"error": f"http_error_{e.response.status_code}"})
        except (httpx.RequestError, ValueError) as e:
            log.error("sms_exception", error=str(e), to_last4=to[-4:] if len(to) >= 4 else "???")
            return str({"error": str(e)[:100]})
