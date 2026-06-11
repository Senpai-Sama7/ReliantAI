"""Schema.org validation without CrewAI dependency."""

import structlog

log = structlog.get_logger()

_REQUIRED_FIELDS = ["@context", "@type", "name", "address", "telephone"]


def validate_local_business_schema(schema: dict) -> dict:
    """Validate schema.org LocalBusiness JSON-LD."""
    if not schema:
        return {"valid": False, "error": "no_schema", "source": "local"}

    missing = [field for field in _REQUIRED_FIELDS if field not in schema]
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
