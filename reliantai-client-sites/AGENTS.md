<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# ReliantAI Client Sites — Agent Reference

**Full manual:** [`docs/CLIENT_SITES_MANUAL.md`](../docs/CLIENT_SITES_MANUAL.md)

## Routes

| Route | Type | Purpose |
|-------|------|---------|
| `/` | Static redirect → `/showcase` | Landing page |
| `/showcase` | Static | Interactive template studio (Preview/Grid/Prompt/Compare) |
| `/preview` | Static | Simplified template browser with JSON viewer |
| `/[slug]` | ISR (dynamic) | Client site page from API, revalidates every 3600s |
| `/api/revalidate` | Server POST | On-demand ISR cache purge |
| `/api/health` | Server GET | Health check |

## Commands

```bash
npm run dev        # Turbopack dev server (port 3000)
npm run build      # Production build
npm run typecheck  # next typegen && tsc --noEmit
npm run lint       # ESLint
npm run test       # Playwright E2E (mock API on :8765)
```

## Key Files

| File | Purpose |
|------|---------|
| `app/[slug]/page.tsx` | ISR route — fetch, validate, render template |
| `app/api/revalidate/route.ts` | Bearer-auth cache purge (503 if secret unset) |
| `lib/api.ts` | `getSiteContent()`, `getTemplate()`, timeout handling |
| `lib/slug.ts` | `isValidSlug()` — `^[a-z0-9]+(?:-[a-z0-9]+)*$`, max 100 |
| `lib/templates.ts` | `TEMPLATE_IDS` registry + dynamic imports |
| `lib/validate-site-content.ts` | Runtime API shape validation |
| `lib/serialize-json-ld.ts` | Escapes `<` in JSON-LD script tags |
| `lib/mock-data.ts` | Mock `SiteContent` per trade (showcase/preview) |
| `lib/template-meta.ts` | Metadata + generation prompts |
| `types/SiteContent.ts` | TypeScript interfaces |
| `tests/mocks/api-server.mjs` | Mock `GET /api/v2/generated-sites/{slug}` |
| `tests/e2e/site-rendering.spec.ts` | Render, JSON-LD, preview banner, headers |
| `tests/e2e/isr-routes.spec.ts` | Revalidate auth, 404, redirects |
| `next.config.ts` | Security headers, turbopack root |

## Hard Constraints

- **Design quality**: All templates MUST comply with `lib/design-quality-standards.ts` — no AI-slop patterns (gradients, backdrop-blur, animate-ping, generic copy) — all sites render via ISR from DB content
- **Slug**: `generate_slug(business_name, city)` on platform — never from `place_id`
- **Preview domain**: `preview.reliantai.org` — NOT `reliantai.org/preview/`
- **API**: `GET {API_BASE_URL}/api/v2/generated-sites/{slug}` — flat `SiteContent`, no auth
- **Unknown template_id** → `notFound()` (register in `lib/templates.ts`)
- **REVALIDATE_SECRET** must match platform env; server-only (not in client bundle)

## Development Notes

- `next dev` uses Turbopack; if it crashes, increase inotify limit or use `next build && next start`
- `/showcase` and `/preview` use mock data — no API required
- `/[slug]` requires API + seeded `generated_sites` row
- E2E tests auto-start mock API (`tests/mocks/api-server.mjs`) via `playwright.config.ts`

## Adding a Template

1. `templates/{trade}-{style}-{color}/` with sections
2. Register in `lib/templates.ts`
3. Mock data in `lib/mock-data.ts`, metadata in `lib/template-meta.ts`
4. Trade mapping in `reliantai/services/site_registration_service.py` `TEMPLATE_MAP`
5. Run full gate: `npm run build && npm run typecheck && npm run lint && npm run test`
