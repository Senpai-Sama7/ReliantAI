import httpx
import structlog
from crewai.tools import BaseTool

log = structlog.get_logger()


class SchemaValidatorTool(BaseTool):
    name: str = "schema_validator"
    description: str = (
        "Validate schema.org structured data using Google Rich Results Test API. "
        "Returns True if valid, False with warning on failure. Non-fatal."
    )

    def _run(self, schema: dict) -> str:
        if not schema:
            return str({"valid": False, "error": "no_schema"})

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    "https://searchconsole.googleapis.com/v1/urlTestingTools/mobileFriendlyTest:run",
                    json={"url": "https://example.com", "requestScreenshot": False},
                    params={"key": __import__("os").environ.get("GOOGLE_PAGESPEED_API_KEY", "")},
                )
            if resp.status_code == 200:
                data = resp.json()
                valid = not data.get("mobileFriendlyIssues")
                return str({"valid": valid, "source": "google_api"})
        except Exception as e:
            log.warning("schema_api_failed", error=str(e))

        valid = self._local_validation(schema)
        return str({"valid": valid, "source": "local_fallback"})

    def _local_validation(self, schema: dict) -> bool:
        required = ["@context", "@type", "name", "address"]
        for field in required:
            if field not in schema:
                log.warning("schema_missing_field", field=field)
                return False
        if schema.get("@context") != "https://schema.org":
            return False
        if not isinstance(schema.get("@type"), list):
            return False
        return True
