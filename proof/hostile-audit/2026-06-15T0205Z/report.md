# Hostile Audit Report — 2026-06-15T03:05Z

**Scope:** Tier-1 sprint path — `reliantai-client-sites/`, `reliantai/`, `mock-platform-api/`, `scripts/`  
**Method:** DevOps/Quality Architect plan + frontend/backend/security parallel review + hostile execution (Sections 0–6)

---

## Verdict: **SHIP WITH CONDITIONS**

Production ISR path is functional and hardened. Two non-ISR backend stubs and one DNS item remain.

---

## Fixes applied this audit

| ID | Severity | Finding | Fix | Proof |
|----|----------|---------|-----|-------|
| F1 | HIGH | `vercel.json` blanket `Cache-Control: max-age=0` overrode ISR edge semantics | Removed catch-all Cache-Control; let Next.js manage HTML caching | 2nd request `x-vercel-cache: HIT` |
| F2 | HIGH | Production `X-Frame-Options: DENY` vs local/e2e `SAMEORIGIN` | Aligned `vercel.json` to `SAMEORIGIN`; redeployed | `curl -sI ... \| rg x-frame` → `SAMEORIGIN` |
| F3 | MEDIUM | Backend `generated_sites` accepted any slug string (DB probe) | Added `reliantai/lib/slug.py` + 400 on invalid slug | `pytest test_generated_sites_api` 3 passed |
| F4 | MEDIUM | Revalidate endpoint no body size limit | 413 when body > 4096 bytes | `app/api/revalidate/route.ts` |
| F5 | LOW | Mock API lacked slug validation | `mock-platform-api/lib/slug.js`; redeployed | live probe |

---

## Section 0 — Initial sweep

```
grep TODO/FIXME/NotImplemented in reliantai/*.py (prod): 
  reliantai/main.py:86 — comment only (routers wired)
  reliantai/api/v2/prospects.py:5 — STUB "Phase 2"
  reliantai/api/v2/webhooks.py:5 — STUB "Phase 4"
```

**Acceptable in tests/mocks.** **NON-FUNCTIONAL** for prospects/webhooks APIs (not ISR critical path).

---

## Section 1–2 — Dependencies & gates

| Gate | Command | Result |
|------|---------|--------|
| Client build | `npm run build` | exit 0 |
| Typecheck | `npm run typecheck` | exit 0 |
| Lint | `npm run lint` | exit 0 |
| E2E | `npm run test` | **13 passed** (33.1s) |
| Platform | `PYTHONPATH=. pytest reliantai/tests/ -q` | **22 passed** (0.95s) |

---

## Section 5 — Security attacks (production)

| Attack | Target | Result |
|--------|--------|--------|
| Revalidate no auth | POST `/api/revalidate` | **401** |
| Revalidate wrong secret | POST `/api/revalidate` | **401** |
| Revalidate traversal slug | `{"slug":"../admin"}` | **401** (auth first) |
| GET path traversal | `/%2e%2e%2fadmin` | **400** |
| JSON-LD XSS breakout | `test-hvac-austin` | **PASS** (e2e: no `</script` in serialized output) |
| Slug fetch injection | `lib/api.ts` + `isValidSlug` | **PASS** (rejected before fetch) |
| Hardcoded secrets grep | `reliantai/` | **none** in prod paths |

---

## Section 6 — End-to-end ISR

```
curl https://reliantai-client-sites.vercel.app/test-hvac-austin → 200
curl https://reliantai-mock-platform-api.vercel.app/api/v2/generated-sites/test-hvac-austin → 200
POST /api/revalidate (valid Bearer) → 200 {"revalidated":true}
Platform _revalidate_preview_cache() → revalidate_ok status=200 (prior session)
```

---

## Passing components (verified)

- [x] ISR `app/[slug]/page.tsx` — fetch → validate → template → JSON-LD
- [x] `serializeJsonLd()` — `\u003c` escape prevents script breakout
- [x] `POST /api/revalidate` — timing-safe secret compare (`crypto.timingSafeEqual`)
- [x] `site_registration_service` — sync httpx revalidation loop
- [x] Mock platform API — public stand-in until `api.reliantai.org` hosted
- [x] Playwright mock API + 13 e2e tests

---

## Open conditions (blocks full SHIP)

1. **`preview.reliantai.org` DNS** — NXDOMAIN. Run `CLOUDFLARE_API_TOKEN=... node scripts/configure-preview-dns.mjs`
2. **`api.reliantai.org`** — not hosted. Replace mock `API_BASE_URL` when real API + DB seeds exist
3. **`prospects.py` / `webhooks.py`** — stub routers (Phase 2/4). Non-blocking for ISR-only deploy

---

## Untracked / out of scope

- `dollar-dank/`, `faang-2026/` demo routes — build clean, not ISR pipeline
- `reGenesis/`, `vibe-coding-platform/` — not audited in depth this pass
- Legacy subprojects (`Money/`, `integration/`, etc.) — not in Phase 5 sprint gate

---

*Proof captured by orchestrator @ 2026-06-15T03:05Z*
