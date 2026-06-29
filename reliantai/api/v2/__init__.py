"""API v2 router initialization."""

from .prospects import router as prospects_router
from .generated_sites import router as generated_sites_router
from .webhooks import router as webhooks_router

__all__ = ["prospects_router", "generated_sites_router", "webhooks_router"]
