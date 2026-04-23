# ADR-004: API Versioning via Dual-Mount (`/` + `/v1/`)

## Status
Accepted (2024-04-22)

## Context
The ReliantAI platform APIs (Money, ComplianceOne, FinOps360, integration) were
built without version prefixes (`/health`, `/dispatch`). As the platform scales,
we need:

1. **Backward compatibility** — Existing clients must not break when `/v2/` is introduced.
2. **Gradual migration** — Clients can adopt `/v1/` at their own pace.
3. **No URL rewriting** — Nginx should not need complex rewrite rules per version.

## Decision
Use **dual-mount** strategy: every API route is registered under BOTH the
unversioned path (backward compatible) and the `/v1/` prefixed path (future-proof).

### Implementation
```python
from shared.api_versioning import include_versioned_router
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mounts both:
#   GET /health     (backward compatible)
#   GET /v1/health  (versioned)
include_versioned_router(app, router)
```

## Consequences

### Positive
- **Zero breaking changes** — Existing clients continue using `/health`.
- **Client-driven migration** — Clients opt into `/v1/` when ready; no forced deadline.
- **No nginx rewrites** — FastAPI handles routing natively; nginx config stays simple.
- **FastAPI auto-docs** — `/docs` shows both `/health` and `/v1/health` explicitly.
- **Easy deprecation** — Unversioned routes can be marked deprecated in OpenAPI schema
  while still functional.

### Negative
- **Route duplication** — Each endpoint appears twice in OpenAPI docs (can be filtered).
- **Slightly larger routing table** — negligible performance impact for FastAPI.
- **Client confusion** — "Which URL should I use?" needs documentation.
- **Testing surface doubles** — integration tests should verify both paths.

## Mitigation
- Documentation: USER_MANUAL.md specifies `/v1/` as the canonical path for new clients.
- Testing: `scripts/verify_integration.py` checks both `/health` and `/v1/health`.
- Deprecation: After 12 months, unversioned routes return `Warning: 299` header
  suggesting migration to `/v1/`.

## Alternatives Considered
- **Content negotiation (`Accept: application/vnd.reliantai.v1+json`)**: Rejected —
  non-standard for REST APIs; harder to debug via curl/browser.
- **URL rewriting in nginx (`/health → /v1/health`)**: Rejected — hides the actual
  route from FastAPI docs; harder to trace in logs.
- **Single canonical version only (`/v1/health`)**: Rejected — immediate breaking
  change for all existing clients.
- **Header-based versioning (`X-API-Version: 1`)**: Rejected — invisible in URLs,
  harder to cache, not self-documenting.
