# ReliantAI Client Sites — Instruction Manual

Complete operational guide for `reliantai-client-sites/`: the Next.js ISR renderer that serves branded home-service landing pages at `preview.reliantai.org/{slug}`.

**Related docs:** [`reliantai-client-sites/README.md`](../reliantai-client-sites/README.md) (developer reference) · [`API_REFERENCE.md`](./API_REFERENCE.md) · [`MICROSERVICE_MANUALS.md`](./MICROSERVICE_MANUALS.md) §2

---

## Table of Contents

1. [What This Service Does](#1-what-this-service-does)
2. [Architecture & Data Flow](#2-architecture--data-flow)
3. [Local Development](#3-local-development)
4. [Environment Variables](#4-environment-variables)
5. [API Integration](#5-api-integration)
6. [ISR & Cache Revalidation](#6-isr--cache-revalidation)
7. [Security](#7-security)
8. [Testing & Verification](#8-testing--verification)
9. [Production Deployment (Vercel)](#9-production-deployment-vercel)
10. [Troubleshooting](#10-troubleshooting)
11. [Adding a New Template](#11-adding-a-new-template)

---

## 1. What This Service Does

| Capability | Detail |
|------------|--------|
| **ISR rendering** | One Next.js app serves all client sites — no per-site builds |
| **Preview domain** | `https://preview.reliantai.org/{slug}` |
| **Template studio** | `/showcase` — browse, compare, and inspect generation prompts |
| **Template browser** | `/preview` — simpler full-page / grid views with JSON viewer |
| **On-demand revalidation** | `POST /api/revalidate` purges ISR cache when platform content changes |

**Hard constraints (never deviate):**

- Slugs come from `generate_slug(business_name, city)` on the platform — never from `place_id`
- Preview domain is `preview.reliantai.org` — not `reliantai.org/preview/`
- Checkout CTAs point to the marketing site (`NEXT_PUBLIC_CHECKOUT_BASE_URL`), not this app

---

## 2. Architecture & Data Flow

```
Prospect pipeline (reliantai/)
  CrewAI research → copy → site_registration_service.register()
       │
       ▼
  PostgreSQL generated_sites.site_content
       │
       ▼
  GET /api/v2/generated-sites/{slug}  (public, no auth)
       │
       ▼
  reliantai-client-sites app/[slug]/page.tsx
    ├── parseSiteContent()     validate API shape
    ├── loadTemplate()         dynamic import by template_id
    ├── serializeJsonLd()      safe JSON-LD in <script>
    └── PreviewBanner          when status === "preview_live"
       │
       ▼
  ISR cache (revalidate: 3600s)
```

**On content update**, `SiteRegistrationService._revalidate_preview_cache()` calls:

```http
POST https://preview.reliantai.org/api/revalidate
Authorization: Bearer {REVALIDATE_SECRET}
Content-Type: application/json

{"slug": "comfort-pro-hvac-austin-ab12"}
```

---

## 3. Local Development

### Prerequisites

- Node.js 20+
- Running ReliantAI API (or use mock data routes `/showcase`, `/preview`)

### Setup

```bash
cd reliantai-client-sites
npm install
cp .env.example .env.local   # or .env.local for Next.js
```

**`.env.local` minimum for `/[slug]` routes:**

```bash
API_BASE_URL=http://localhost:8000
REVALIDATE_SECRET=dev_revalidate_secret
```

### Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Dev server on port 3000 (Turbopack) |
| `npm run build` | Production build |
| `npm run typecheck` | `next typegen && tsc --noEmit` |
| `npm run lint` | ESLint |
| `npm run test` | Playwright E2E (starts mock API + dev server) |

### Quick verification

```bash
# Showcase works without API (mock data)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/showcase

# Health
curl -s http://localhost:3000/api/health

# ISR route (needs API + seeded generated_sites row)
curl -s http://localhost:8000/api/v2/generated-sites/<slug>
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/<slug>
```

### Turbopack file-watch errors

```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
# Or: npm run build && npm run start
```

---

## 4. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_BASE_URL` | **Yes** (prod) | `http://localhost:8000` | Platform API for ISR fetches |
| `REVALIDATE_SECRET` | **Yes** (prod) | — | Bearer token for `/api/revalidate`. Returns **503** if unset |
| `NEXT_PUBLIC_CHECKOUT_BASE_URL` | No | `https://reliantai.org` | Preview banner checkout links |
| `API_TIMEOUT_MS` | No | `10000` | Server-side fetch timeout. Invalid values fall back to 10s |
| `PLATFORM_API_URL` | No | — | Legacy alias for `API_BASE_URL` |

**Platform side (reliantai):**

| Variable | Description |
|----------|-------------|
| `REVALIDATE_SECRET` | Must match client-sites value exactly |
| `PREVIEW_SITES_BASE_URL` | Default `https://preview.reliantai.org`. Until DNS propagates, set to `https://reliantai-client-sites.vercel.app` |

---

## 5. API Integration

### Fetch site content

```http
GET {API_BASE_URL}/api/v2/generated-sites/{slug}
```

- **Auth:** None (public)
- **Response:** Flat `SiteContent` object (no `{ success, data }` wrapper)
- **404:** `{ "detail": "Site not found" }`

Implementation: `lib/api.ts` → `lib/validate-site-content.ts` → `types/SiteContent.ts`

### Slug rules

Validated client-side before any fetch (`lib/slug.ts`):

- Pattern: `^[a-z0-9]+(?:-[a-z0-9]+)*$`
- Max length: 100 characters
- Invalid slugs return `notFound()` without calling the API

### Template registry

Single source of truth: `lib/templates.ts`

```typescript
export const TEMPLATE_IDS = [
  "hvac-reliable-blue",
  "plumbing-trustworthy-navy",
  // ...
] as const;
```

Unknown `template_id` from API → `notFound()` (no silent fallback).

---

## 6. ISR & Cache Revalidation

| Mechanism | Interval / trigger |
|-----------|-------------------|
| Time-based ISR | `revalidate = 3600` in `app/[slug]/page.tsx` |
| On-demand | `POST /api/revalidate` with valid Bearer token |

### Revalidate endpoint behavior

| Condition | HTTP | Body |
|-----------|------|------|
| `REVALIDATE_SECRET` unset | 503 | `{ "revalidated": false, "error": "revalidation not configured" }` |
| Missing / wrong Bearer | 401 | `{}` |
| Missing / invalid slug | 400 | `{ "revalidated": false, "error": "..." }` |
| Success | 200 | `{ "revalidated": true, "slug": "..." }` |

### Manual revalidation

```bash
curl -X POST https://preview.reliantai.org/api/revalidate \
  -H "Authorization: Bearer $REVALIDATE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"slug":"comfort-pro-hvac-austin-ab12"}'
```

---

## 7. Security

| Control | Location |
|---------|----------|
| Slug path traversal block | `lib/slug.ts` + `encodeURIComponent` in fetch URL |
| JSON-LD XSS breakout prevention | `lib/serialize-json-ld.ts` escapes `<` as `\u003c` |
| API response validation | `lib/validate-site-content.ts` |
| Revalidate timing-safe compare | `app/api/revalidate/route.ts` |
| Security headers | `next.config.ts` — `nosniff`, `SAMEORIGIN`, `Referrer-Policy`, `Permissions-Policy` |
| Secrets not in client bundle | `REVALIDATE_SECRET` is server-only (not in `next.config env`) |

---

## 8. Testing & Verification

### Automated gates (run before merge)

```bash
cd reliantai-client-sites
npm run build       # exit 0
npm run typecheck   # exit 0
npm run lint        # exit 0
npm run test        # 13 Playwright tests, exit 0
```

### E2E test architecture

`playwright.config.ts` starts two servers:

1. **Mock API** (`tests/mocks/api-server.mjs`) — simulates `GET /api/v2/generated-sites/{slug}`
2. **Next.js dev** — with `API_BASE_URL=http://127.0.0.1:8765`

Test suites:

- `tests/e2e/isr-routes.spec.ts` — redirects, revalidate auth, 404
- `tests/e2e/site-rendering.spec.ts` — live render, JSON-LD safety, preview banner, security headers

### Production smoke (after build)

```bash
node tests/mocks/api-server.mjs &
API_BASE_URL=http://127.0.0.1:8765 REVALIDATE_SECRET=test npx next start -p 3001

curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3001/api/health          # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3001/test-hvac-austin     # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3001/no-such-site        # 404
```

### Platform tests (Python)

```bash
PYTHONPATH=. pytest reliantai/tests/test_site_registration.py -v
PYTHONPATH=. pytest reliantai/tests/test_generated_sites_api.py -v
```

---

## 9. Production Deployment (Vercel)

### Checklist

- [ ] Import `reliantai-client-sites` as Vercel project (root directory setting)
- [ ] Set `API_BASE_URL=https://api.reliantai.org` (or your API host)
- [ ] Set `REVALIDATE_SECRET` (match platform `reliantai` env)
- [ ] Set `NEXT_PUBLIC_CHECKOUT_BASE_URL=https://reliantai.org`
- [ ] Point `preview.reliantai.org` DNS to Vercel: `A preview.reliantai.org → 76.76.21.21` (Cloudflare)
- [ ] Until DNS works: set platform `PREVIEW_SITES_BASE_URL=https://reliantai-client-sites.vercel.app`
- [ ] Seed at least one `generated_sites` row and verify `GET /{slug}` returns 200
- [ ] Trigger revalidation from platform after site registration

### Post-deploy verification

```bash
curl -s https://preview.reliantai.org/api/health
curl -s -o /dev/null -w "%{http_code}\n" https://preview.reliantai.org/<slug>
curl -s -X POST https://preview.reliantai.org/api/revalidate \
  -H "Authorization: Bearer $REVALIDATE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"slug":"<slug>"}'
```

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| All slugs return 404 | API down or `API_BASE_URL` wrong | Check `curl $API_BASE_URL/health` and Vercel env |
| All slugs return 404 instantly | Invalid `API_TIMEOUT_MS` (was 0/NaN) | Remove or fix env var; defaults to 10s |
| Content stale after DB update | ISR cache not purged | Verify `REVALIDATE_SECRET` on both sides; check platform logs for `revalidate_ok` |
| Revalidate returns 503 | `REVALIDATE_SECRET` unset on Vercel | Add env var and redeploy |
| Revalidate returns 401 | Secret mismatch | Align platform + client-sites secrets |
| Preview banner missing | `status` is not `preview_live` | Check `generated_sites.status` in DB |
| Wrong template renders | Invalid `template_id` in `site_config` | Fix DB row; unknown IDs return 404 |
| `next dev` crashes | inotify limit | See §3 Turbopack note |
| `typecheck` fails locally | Stale `.next/dev/types` | Run `npm run typecheck` (runs `next typegen` first) |
| Lighthouse score always 0 | Research misclassified as copy | Fixed in `site_registration_service` — ensure latest platform code |

---

## 11. Adding a New Template

1. Create `templates/{trade}-{style}-{color}/` with `index.tsx` and `sections/`
2. Register ID in `lib/templates.ts` (`TEMPLATE_IDS` + `templateImports`)
3. Add mock data in `lib/mock-data.ts`
4. Add metadata + prompt in `lib/template-meta.ts`
5. Add trade mapping in `reliantai/services/site_registration_service.py` `TEMPLATE_MAP`
6. Add E2E fixture entry in `tests/mocks/api-server.mjs` if testing render
7. Run full gate suite (§8)

---

*Last updated: Phase 5 — post ISR hardening merge (`#17`)*
