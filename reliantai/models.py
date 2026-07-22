"""Canonical ORM models — re-export from db.models (Alembic source of truth).

Do not define parallel schemas here. All API/services must use these exports
so runtime columns match migrated tables.
"""

from reliantai.db.models import (  # noqa: F401
    Base,
    BusinessIntelligence,
    CompetitorIntelligence,
    GeneratedSite,
    LeadEvent,
    OutreachMessage,
    OutreachSequence,
    Prospect,
    ResearchJob,
)

__all__ = [
    "Base",
    "BusinessIntelligence",
    "CompetitorIntelligence",
    "GeneratedSite",
    "LeadEvent",
    "OutreachMessage",
    "OutreachSequence",
    "Prospect",
    "ResearchJob",
]
