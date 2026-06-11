"""CrewAI tools — lazy exports to avoid import-time crewai dependency."""

__all__ = [
    "GooglePlacesTool",
    "PageSpeedTool",
    "GBPScraperTool",
    "SchemaValidatorTool",
    "TwilioSMSTool",
    "ResendEmailTool",
]

_LAZY_IMPORTS = {
    "GooglePlacesTool": ".google_places",
    "PageSpeedTool": ".pagespeed",
    "GBPScraperTool": ".gbp_scraper",
    "SchemaValidatorTool": ".schema_validator",
    "TwilioSMSTool": ".twilio_sms",
    "ResendEmailTool": ".resend_email",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
