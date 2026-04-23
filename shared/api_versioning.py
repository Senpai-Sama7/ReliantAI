# API Versioning Helper for ReliantAI Platform
# 
# Usage in any FastAPI service:
#   from shared.api_versioning import include_versioned_router
#   include_versioned_router(app, router)
#
# This mounts routes under both the original path AND /v1/ prefixed paths
# for backward-compatible versioning.

from fastapi import FastAPI, APIRouter
from typing import Optional


def include_versioned_router(
    app: FastAPI,
    router: APIRouter,
    prefix: str = "",
    version_prefix: str = "/v1",
    tags: Optional[list] = None,
    dependencies: Optional[list] = None,
    responses: Optional[dict] = None,
    **kwargs
) -> None:
    """
    Include a router in a FastAPI app with both unversioned and /v1 versioned paths.
    
    Example:
        router = APIRouter()
        @router.get("/frameworks")
        def list_frameworks(): ...
        
        include_versioned_router(app, router)
        
    Resulting endpoints:
        GET /frameworks
        GET /v1/frameworks
    """
    # Include unversioned (backward compatible)
    app.include_router(
        router,
        prefix=prefix,
        tags=tags,
        dependencies=dependencies,
        responses=responses,
        **kwargs
    )
    
    # Include versioned under /v1
    app.include_router(
        router,
        prefix=f"{version_prefix}{prefix}",
        tags=tags,
        dependencies=dependencies,
        responses=responses,
        **kwargs
    )


def create_versioned_router(*args, **kwargs) -> APIRouter:
    """Convenience wrapper to create an APIRouter."""
    return APIRouter(*args, **kwargs)
