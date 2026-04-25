# ReliantAI Client Sites

ISR-powered landing page generator for home service businesses. Serves branded, trade-specific pages from a single Next.js app — no per-site builds.

## Architecture

```
API (FastAPI + Celery)
  └── Prospected businesses → template_id + content → ISR cache
                                                              ← On-demand revalidation
Next.js App Router (revalidate=3600) ← ISR cache ← /[slug] → Branded page
```

Content flows: **Prospect created** → Celery task generates content → stored in DB → fetched at build time by Next.js → served as ISR page.

## Quick Start

```bash
cd reliantai-client-sites
npm install
cp .env.example .env  # fill in API_BASE_URL
npm run dev
```

Open [http://localhost:3000/hvac-reliable-cooling-austin](http://localhost:3000/hvac-reliable-cooling-austin) (sample slug).

## Development

```bash
npm run dev        # dev server
npm run build      # production build
npx tsc --noEmit  # typecheck
npm run test:e2e   # Playwright E2E tests
```

## Slug Format

`generate_slug(business_name, city)` — lowercase, hyphenated.

Example: "Reliable Cooling & Heating" in "Austin, TX" → `reliable-cooling-heating-austin`

## Templates

| ID | Trade | Accent | Theme |
|----|-------|--------|-------|
| `hvac` | HVAC | Blue | Dark, professional |
| `plumbing` | Plumbing | Blue | Dark, emergency-focused |
| `electrical` | Electrical | Amber | Dark, safety-first |
| `roofing` | Roofing | Orange | Dark, bold |
| `painting` | Painting | Violet | **Light**, minimal |
| `landscaping` | Landscaping | Emerald | Dark, organic |

## ISR & Revalidation

- Pages revalidate every **3600 seconds** automatically.
- On-demand revalidation: `POST /api/revalidate` with `Authorization: Bearer <token>`.
- Revalidation secret must match `REVALIDATE_SECRET` env var.

## API Integration

Templates receive a `SiteContent` object from `GET {API_BASE_URL}/v2/generated-sites/{slug}` — no hardcoded business data.

## Environment Variables

```
API_BASE_URL=https://api.reliantai.com      # ReliantAI API base
REVALIDATE_SECRET=<secret>                 # Bearer token for /api/revalidate
NEXT_PUBLIC_PREVIEW_DOMAIN=preview.reliantai.org
```

## Project Structure

```
app/
├── [slug]/page.tsx      # Dynamic ISR route
├── api/revalidate/      # On-demand revalidation endpoint
└── globals.css         # Shared styles + font-display

components/
├── PreviewBanner.tsx   # Preview-mode branded banner
└── shared/
    ├── StatsBar.tsx
    ├── CTASection.tsx
    ├── TrustBanner.tsx
    └── SectionDivider.tsx

templates/
└── [trade]/           # One subdirectory per template
    ├── index.tsx
    └── sections/
        ├── Hero.tsx
        ├── Services.tsx
        ├── About.tsx
        ├── Reviews.tsx
        ├── FAQ.tsx
        ├── Footer.tsx
        └── ContactBar.tsx

lib/
├── api.ts              # getSiteContent() + getTemplate()
└── trade-copy.ts       # TRADE_COPY per-trade section headers
```