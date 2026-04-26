<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Routes

| Route | Type | Purpose |
|-------|------|---------|
| `/` | Static redirect → `/showcase` | Landing page |
| `/showcase` | Static | Interactive template studio with 4 views (Preview/Grid/Prompt/Compare) |
| `/preview` | Static | Simplified template browser with JSON viewer |
| `/[slug]` | ISR (dynamic) | Client site page from API, revalidates every 3600s |
| `/api/revalidate` | Server POST | On-demand ISR cache purge |

## Key Files

- `app/showcase/page.tsx` — Interactive showcase (518 lines)
- `app/preview/page.tsx` — Simplified preview (181 lines)
- `components/showcase/DeviceFrame.tsx` — macOS/iOS device chrome (191 lines)
- `components/showcase/CodeBlock.tsx` — Syntax-highlighted code display (182 lines)
- `lib/template-meta.ts` — Rich metadata + generation prompts for all 6 templates (448 lines)
- `lib/mock-data.ts` — Complete SiteContent mock data per trade (352 lines)

## Development Notes

- `next dev` uses Turbopack; if it crashes, increase inotify limit or use `next build && next start`
- All template renderings happen client-side in `/showcase` and `/preview` (static prerender)
- `/[slug]` uses ISR with `revalidate=3600`
- DeviceFrame component mimics real device chrome (not just width constraints)