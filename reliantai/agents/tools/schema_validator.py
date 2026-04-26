import os
import structlog
from crewai.tools import BaseTool

log = structlog.get_logger()

_REQUIRED_FIELDS = ["@context", "@type", "name", "address", "telephone"]


class SchemaValidatorTool(BaseTool):
    name: str = "schema_validator"
    description: str = (
        "Validate schema.org structured data for local businesses. "
        "Returns a dict with 'valid' (bool) and any missing fields."
    )

    def _run(self, schema: dict) -> str:
        if not schema:
            return str({"valid": False, "error": "no_schema"})
        return str(self._local_validation(schema))

    def _local_validation(self, schema: dict) -> dict:
        missing = [f for f in _REQUIRED_FIELDS if f not in schema]
        if missing:
            for field in missing:
                log.warning("schema_missing_field", field=field)
            return {"valid": False, "missing_fields": missing, "source": "local"}

        if schema.get("@context") != "https://schema.org":
            return {"valid": False, "error": "invalid_context", "source": "local"}

        schema_type = schema.get("@type")
        if not schema_type:
            return {"valid": False, "error": "missing_type", "source": "local"}

        address = schema.get("address", {})
        if not isinstance(address, dict) or "@type" not in address:
            return {"valid": False, "error": "invalid_address", "source": "local"}

        return {"valid": True, "source": "local"}
