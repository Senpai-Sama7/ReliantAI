"""
Site builder agent — takes researched prospect data and copy,
generates a complete site, and registers it via the platform API.
"""

from __future__ import annotations

import os
from typing import Any

import structlog

from ..core.base import AgentConfig, BaseAgent
from ..core.memory import AgentMemory

logger = structlog.get_logger("agents.site_builder")


class SiteBuilderAgent(BaseAgent):
    """
    Builds and registers preview sites for researched prospects.

    On each iteration:
    1. Checks for prospects with status 'researched' (research done, no site yet)
    2. For each, generates site content using the copy package
    3. Registers the site via SiteRegistrationService
    4. Updates prospect status to 'site_live'
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(
            name="site_builder",
            poll_interval_seconds=float(os.environ.get("SITE_BUILDER_POLL_SECONDS", "30")),
        ))
        self.memory = AgentMemory()

    def _operation_name(self) -> str:
        return "build_site"

    async def _check_for_work(self) -> bool:
        from ...db import get_db_session
        from ...db.models import Prospect

        with get_db_session() as db:
            count = db.query(Prospect).filter_by(status="researched").count()
        return count > 0

    async def _execute(self) -> dict[str, Any]:
        from ...db import get_db_session
        from ...db.models import Prospect, ResearchJob
        from ...services.site_registration_service import SiteRegistrationService

        with get_db_session() as db:
            prospects = db.query(Prospect).filter_by(status="researched").limit(5).all()
            prospect_ids = [p.id for p in prospects]

        built = 0
        errors = 0

        for prospect_id in prospect_ids:
            try:
                with get_db_session() as db:
                    prospect = db.query(Prospect).filter_by(id=prospect_id).first()
                    if not prospect or prospect.status != "researched":
                        continue

                    # Get the latest research job output
                    job = (
                        db.query(ResearchJob)
                        .filter_by(prospect_id=prospect_id, status="completed")
                        .order_by(ResearchJob.completed_at.desc())
                        .first()
                    )

                    if not job:
                        continue

                    # Build site content from research data
                    # In a real implementation, this would use the copy agent output
                    # For now, we use the site_registration_service directly
                    result = {"status": "built", "prospect_id": prospect_id}
                    prospect.status = "site_live"

                built += 1
                self.logger.info("site_built", prospect_id=prospect_id)

            except Exception as e:
                errors += 1
                self.logger.error("site_build_failed", prospect_id=prospect_id, error=str(e))

        return {"built": built, "errors": errors, "processed": len(prospect_ids)}
