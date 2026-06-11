import structlog
from crewai.tools import BaseTool

from ...services.schema_validation import validate_local_business_schema

log = structlog.get_logger()


class SchemaValidatorTool(BaseTool):
    name: str = "schema_validator"
    description: str = (
        "Validate schema.org structured data for local businesses. "
        "Returns a dict with 'valid' (bool) and any missing fields."
    )

    def _run(self, schema: dict) -> str:
        return str(validate_local_business_schema(schema))
