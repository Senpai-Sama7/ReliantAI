# AGENTS.md - NexGen Web Solutions

> Essential context for AI coding agents working on this project.
> Last updated: 2026-02-07

---

## Project Overview

**NexGen Web Solutions** is a React + TypeScript + Vite marketing site for a Houston-based web design agency. It uses GSAP scroll animations and optional Three.js scenes (via `@react-three/fiber`) for premium/industrial motion design. The positioning targets small businesses in: metal fabrication, oilfield services, home services, and medical practices.

- **Live URL**: https://nexgenweb.com (intended)
- **Deployment**: Vercel (SPA rewrites + security/cache headers via `vercel.json`)
- **Package manager**: npm (`package-lock.json` is present)

---

## Technology Stack (from `package.json`)

| Category | Technology | Version |
|----------|------------|---------|
| Framework | React | 19.2.0 |
| Language | TypeScript | 5.9.3 |
| Build Tool | Vite | 7.2.4 |
| Styling | Tailwind CSS | 3.4.19 |
| UI Components | shadcn/ui (New York) + Radix UI | (multiple) |
| 3D Graphics | Three.js | 0.182.0 |
| 3D React | `@react-three/fiber` + `@react-three/drei` | 9.5.0 + 10.7.7 |
| Animations | GSAP + ScrollTrigger | 3.14.2 |
| Smooth Scroll | Lenis | 1.3.17 |
| Icons | Lucide React | 0.562.0 |
| Forms | react-hook-form + Zod | 7.70.0 + 4.3.5 |

Notes:
- Theme is implemented via a custom hook (`src/hooks/useTheme.ts`) rather than a provider-based solution.
- `next-themes` is installed (shadcn default) but is not wired up in the app layout.

---

## Repo Structure

```
./
├── public/                      # Static assets (images + SEO files)
│   ├── robots.txt
│   ├── sitemap.xml
│   ├── 404.html
│   └── _redirects               # Netlify-style SPA redirects (kept for portability)
├── src/
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components (53 TSX files)
│   │   ├── Navigation.tsx       # Sticky nav (GSAP ScrollToPlugin)
│   │   ├── SmoothScrollProvider.tsx # Lenis + ScrollTrigger sync
│   │   ├── IntroOverlay.tsx
│   │   ├── FloatingCTA.tsx
│   │   ├── ExitIntentPopup.tsx
│   │   ├── SocialProofToast.tsx
│   │   ├── ThemeToggle.tsx
│   │   └── TorusKnot3D.tsx      # Hero 3D visual (Canvas)
│   ├── sections/                # Scroll sections (some have V2 variants)
│   ├── pages/                   # Standalone pages (simple path routing in App.tsx)
│   ├── hooks/                   # Custom hooks (theme, scroll reveals, popup triggers)
│   ├── data/                    # Content data (e.g. case study chapters)
│   ├── lib/                     # Utilities (Tailwind class merge helpers)
│   ├── App.tsx                  # Root app + basic path routing
│   ├── main.tsx                 # React entry
│   ├── index.css                # Global styles + CSS variables + utility classes
│   └── App.css                  # App-specific CSS (Lenis + story utilities)
├── index.html                   # SEO-heavy HTML template (schema + analytics placeholders)
├── vite.config.ts               # Alias + manual vendor chunks
├── tailwind.config.js           # Brand color + fonts + animations
├── eslint.config.js             # Flat ESLint config
├── vercel.json                  # SPA rewrites + caching + security headers
└── package.json
```

Important repo hygiene:
- This working tree contains `dist/` and `node_modules/`. Treat both as generated artifacts and do not hand-edit them.
- `.gitignore` currently only ignores `.vercel/`. If `dist/` or `node_modules/` are not meant to be committed, update `.gitignore` separately.

---

## Path Aliases

`@/*` maps to `./src/*` via `tsconfig.json` and `vite.config.ts`.

```ts
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
```

Guideline: prefer `@/` imports when you touch a file (some older files still use relative paths—avoid mass-refactors).

---

## Build Commands

```bash
npm run dev
npm run build     # tsc -b && vite build
npm run preview
npm run lint
```

## Current Lint Status

As of 2026-02-07, `npm run lint` reports existing errors/warnings (primarily React hook rules and a few TypeScript lint rules). Treat lint as informative until these are addressed.

Hotspots flagged by ESLint:
- `src/App.tsx` (conditional hook due to early returns for path-based routing)
- `src/components/Navigation.tsx` (const used before declaration + deps warnings)
- `src/components/ParticleField.tsx` (`Math.random()` during render; purity rule)
- `src/hooks/useTheme.ts`, `src/components/CountUp.tsx` (setState-in-effect rule)
- `src/components/LogoReveal.tsx` (`any`)
- `src/sections/Testimonials.tsx` (function used before declaration)

---

## Conventions (UI + Copy)

### Styling & Tailwind
- **Brand orange**: `#ff6e00`
  - Prefer utility classes defined in `src/index.css`: `text-orange`, `bg-orange`, `border-orange`
  - Tailwind also exposes an `orange` palette via `tailwind.config.js` (e.g. `bg-orange/10`, `border-orange/30`)
- **Fonts**:
  - Headings: `font-teko` (uppercase + tracking is applied globally to `h1..h6`)
  - Body: `font-opensans`
- **Effects**:
  - Glass cards: `className="glass"`
  - Orange glow: `className="glow-orange"`

### Theme
- Light mode is default (`:root` CSS variables).
- Dark mode is enabled by toggling `<html class="dark">`.
- Use `useTheme()` from `src/hooks/useTheme.ts` and check `mounted` before rendering theme-dependent UI.

### Sections & Navigation
- Each section should have a stable `id` for anchor navigation.
- Navigation is implemented in `src/components/Navigation.tsx` via GSAP ScrollToPlugin (offset `80px`).
- `src/sections/*V2.tsx` are the currently used variants in `src/App.tsx` (Hero/Services/Testimonials).

### Routing (no router)
There is no React Router. `src/App.tsx` does simple path checks:
- `/privacy-policy` → `src/pages/PrivacyPolicy.tsx`
- `/terms-of-service` → `src/pages/TermsOfService.tsx`

If you add a new route, mirror this pattern or introduce a router intentionally (larger change).

---

## Animation Patterns (GSAP)

### ScrollTrigger hygiene
- Register plugins once per module (`gsap.registerPlugin(ScrollTrigger)`).
- Prefer `gsap.context(() => { … }, scopeRef)` and cleanup with `ctx.revert()`.
- If you create ScrollTriggers manually, track them and `kill()` on unmount.

Reference cleanup pattern:

```ts
const triggersRef = useRef<ScrollTrigger[]>([]);

useEffect(() => {
  const ctx = gsap.context(() => {
    const st = ScrollTrigger.create({ /* ... */ });
    triggersRef.current.push(st);
  }, sectionRef);

  return () => {
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];
    ctx.revert();
  };
}, []);
```

### Smooth scroll (Lenis)
`src/components/SmoothScrollProvider.tsx` wires Lenis to ScrollTrigger and skips smoothing if the user prefers reduced motion.

When adding GSAP ticker callbacks, keep a stable function reference so cleanup removes the same handler.

---

## 3D / Canvas Guidelines

Current pattern: hero 3D visual is in `src/components/TorusKnot3D.tsx` and is lazy-loaded by `src/sections/HeroV2.tsx`.

Guidelines:
- Wrap fiber scenes in `Suspense` with a lightweight fallback (often `null`).
- Prefer conservative render settings: `dpr={[1, 1.5]}`, `powerPreference: 'low-power'`, disable antialias when acceptable.
- Keep 3D visuals desktop-first (`hidden lg:block`) unless there’s a clear mobile value.

If you add a global background canvas later, reuse `.canvas-container` in `src/index.css`.

---

## SEO Notes

`index.html` contains extensive SEO markup:
- Schema.org JSON-LD (Organization, WebSite, Service, FAQPage)
- Open Graph + Twitter meta tags
- Hidden semantic anchors for AI/LLM retrieval
- Analytics placeholders (GA4, Meta Pixel, Clarity)

Before deployment, replace placeholder tracking IDs in `index.html`:
- `G-XXXXXXXXXX` (GA4)
- `XXXXXXXXXXXXXXX` (Meta Pixel)
- `XXXXXXXXXX` (Microsoft Clarity)

Public SEO files:
- `public/robots.txt`
- `public/sitemap.xml` (currently does **not** list `/privacy-policy` or `/terms-of-service`; update when publishing those routes)

---

## Performance Optimizations

1. **Manual chunks** in `vite.config.ts`:
   - `vendor-react`, `vendor-three`, `vendor-gsap`, `vendor-ui`
2. **Lazy loading**:
   - Hero 3D scene is lazy-loaded (`HeroV2` → `TorusKnot3D`)
3. **Images**:
   - WebP + JPG variants live in `public/`

---

## Deployment (Vercel)

`vercel.json` includes:
- SPA rewrite: all paths → `index.html`
- Cache headers for images/assets
- Security headers (e.g. `X-Frame-Options: DENY`, `Referrer-Policy`, etc.)

Build output:
- Static files in `dist/`
- Vite base path is `'./'` for relative asset paths

---

## Common Tasks

### Add a New Section
1. Create `src/sections/NewSection.tsx` and give it an `id`.
2. Import and render it in `src/App.tsx`.
3. Add an entry in `src/components/Navigation.tsx` (`navItems`).
4. If it’s indexable, update `public/sitemap.xml` and (optionally) breadcrumbs/schema in `index.html`.

### Add a Standalone Page Route (no router)
1. Create `src/pages/NewPage.tsx`.
2. Add a `window.location.pathname` check in `src/App.tsx`.
3. Update `public/sitemap.xml` if it should be indexed.

### Add a shadcn/ui Component
```bash
npx shadcn add <component-name>
```

Note: `components.json` is configured with `style: "new-york"` and `@/` aliases. If the shadcn CLI complains about Tailwind config paths, verify `components.json` points at the correct Tailwind config file for this repo.

---

## Security Considerations

- Static SPA only (no server-side code in this repo).
- Contact form in `src/sections/Contact.tsx` is currently simulated; needs an external form backend (Formspree, Netlify Forms, etc.).
- External links should include `rel="noopener noreferrer"` when using `target="_blank"`.

---

## Troubleshooting

### Theme flash on load
`useTheme()` uses a `mounted` flag to avoid mismatches. If flashing persists, consider pre-applying the theme class before React mounts.

### GSAP animations not working
Ensure plugins are registered and ScrollTriggers are cleaned up properly (`ctx.revert()` + `kill()`).

### TypeScript errors on build
Run `tsc -b` separately for detailed output before `vite build`.

---

## External Dependencies to Know

| Package | Purpose |
|---------|---------|
| `lenis` | Smooth scroll (used in `SmoothScrollProvider`) |
| `gsap/ScrollToPlugin` | Navigation anchor scrolling |
| `sonner` | Toast system (installed; not currently mounted) |
| `next-themes` | Installed (shadcn default); not wired up in app layout |
| `sharp` | Installed as a dev dependency (useful for image optimization scripts) |

---

## Contact & Positioning

- **Project Type**: Marketing landing page
- **Target Industries**: Metal fabrication, oilfield services, home services, medical practices
- **Geographic Focus**: Houston, Texas
- **Design Style**: Industrial/premium with orange accent (`#ff6e00`)
