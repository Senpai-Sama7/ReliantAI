"""
nextjs_templates — TSX/TS config string builders for Next.js ISR scaffold.

Each function returns a static template string. No Python brace interpolation
inside escaped JSX/TS blocks — f-strings use {{ }} which Python strips to {}
so embedded JSX literal braces survive correctly.
"""

from __future__ import annotations

import re
import json
from typing import Any


# ══════════════════════════════════════════════════════════════════════════════
#  Private helpers
# ══════════════════════════════════════════════════════════════════════════════

def _to_json(value: object, indent: int | None = None) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent)


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "website-forge-site"


# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════

GLOBAL_CSS = """\
:root {
  --font-display: "Instrument Serif", "Playfair Display", Georgia, serif;
  --font-body: "DM Sans", "Plus Jakarta Sans", system-ui, sans-serif;
  --color-primary: __PRIMARY__;
  --color-accent: __ACCENT__;
  --color-surface: #fafaf9;
  --color-ink: #1c1917;
  --color-muted: #78716c;
  --ease-out-expo: cubic-bezier(0.22, 1, 0.36, 1);
  --radius-sm: 0.375rem;
  --radius-md: 0.75rem;
  --radius-lg: 1.5rem;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; }

html { scroll-behavior: smooth; }

body {
  font-family: var(--font-body);
  color: var(--color-ink);
  background: var(--color-surface);
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3, h4 {
  font-family: var(--font-display);
  font-weight: 400;
  letter-spacing: -0.02em;
  line-height: 1.15;
}

a { color: inherit; text-decoration: none; }

/* Hero */
.hero {
  min-height: 85vh;
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 3rem;
  align-items: center;
  padding: 6rem 2rem;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  top: -30%;
  right: -20%;
  width: 70%;
  height: 140%;
  background: radial-gradient(ellipse at center, var(--color-accent) 0%, transparent 70%);
  opacity: 0.06;
  pointer-events: none;
}

.hero-copy { z-index: 1; }

.hero h1 {
  font-size: clamp(2.8rem, 6vw, 5rem);
  line-height: 1.05;
  margin-bottom: 1.25rem;
}

.hero .subhead {
  font-size: 1.15rem;
  color: var(--color-muted);
  max-width: 28rem;
  line-height: 1.7;
  margin-bottom: 2rem;
}

.cta-row { display: flex; gap: 0.75rem; flex-wrap: wrap; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: 0.95rem;
  transition: transform 0.2s var(--ease-out-expo), box-shadow 0.2s var(--ease-out-expo);
  cursor: pointer;
  border: none;
}

.btn:hover { transform: translateY(-2px); }
.btn-primary { background: var(--color-primary); color: #fff; }
.btn-secondary { background: #fff; color: var(--color-primary); border: 1px solid #e7e5e4; }

.trust-bar { display: flex; gap: 1rem; margin-top: 2.5rem; flex-wrap: wrap; }

.chip {
  padding: 0.35rem 0.85rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 500;
  background: #fff;
  border: 1px solid #e7e5e4;
  color: var(--color-muted);
}

/* Services */
.services { padding: 5rem 2rem; background: #fff; }

.section-header {
  text-align: center;
  margin-bottom: 3rem;
}

.section-header h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: 0.75rem;
}

.section-header .lead {
  color: var(--color-muted);
  font-size: 1.05rem;
  max-width: 45rem;
  margin: 0 auto;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
  max-width: 1100px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .service-grid { grid-template-columns: 1fr; }
  .hero { grid-template-columns: 1fr; gap: 2rem; }
  .about-inner { grid-template-columns: 1fr !important; }
  .review-grid { grid-template-columns: 1fr !important; }
}

.service-card {
  background: var(--color-surface);
  border: 1px solid #e7e5e4;
  border-radius: var(--radius-lg);
  padding: 2rem 1.75rem;
  transition: transform 0.25s var(--ease-out-expo), box-shadow 0.25s var(--ease-out-expo);
}

.service-card:nth-child(2) { transform: translateY(1.5rem); }
.service-card:nth-child(3) { transform: translateY(-0.5rem); }
.service-card:hover { transform: translateY(-4px); box-shadow: 0 20px 40px -15px rgba(0,0,0,0.08); }

.service-icon {
  width: 2.5rem; height: 2.5rem;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  display: grid; place-items: center;
  margin-bottom: 1rem;
  font-size: 1.25rem;
}

.service-card h3 { font-size: 1.3rem; margin-bottom: 0.5rem; }
.service-card p { color: var(--color-muted); font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.25rem; }
.card-cta { font-size: 0.85rem; font-weight: 600; color: var(--color-primary); letter-spacing: 0.02em; }

/* About */
.about { padding: 5rem 2rem; background: var(--color-surface); }
.about-inner {
  max-width: 1100px; margin: 0 auto;
  display: grid; grid-template-columns: 5fr 4fr; gap: 3rem; align-items: start;
}
.about h2 { font-size: clamp(1.8rem, 3.5vw, 2.5rem); margin-bottom: 1rem; }
.about .founder { font-size: 1.05rem; color: #57534e; line-height: 1.75; }

.trust-points { list-style: none; margin-top: 1.5rem; }
.trust-points li {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.5rem 0; font-size: 0.95rem; color: #57534e;
  border-bottom: 1px solid #e7e5e4;
}
.trust-points li::before { content: "\\2713"; color: var(--color-primary); font-weight: 700; }

.cert-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 1rem; }
.cert-badge {
  padding: 0.6rem 0.9rem; border-radius: var(--radius-sm);
  background: #fff; border: 1px solid #e7e5e4;
  font-size: 0.8rem; font-weight: 500; color: var(--color-muted); text-align: center;
}

/* Reviews */
.reviews { padding: 5rem 2rem; background: #fff; }
.review-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1rem; max-width: 1100px; margin: 0 auto;
}
.review-card {
  padding: 1.5rem; border-radius: var(--radius-md);
  background: var(--color-surface); border: 1px solid #e7e5e4;
}
.review-stars { color: var(--color-accent); font-size: 0.9rem; margin-bottom: 0.5rem; }
.review-text { font-size: 0.95rem; color: #57534e; line-height: 1.6; }
.review-author { font-size: 0.8rem; color: var(--color-muted); margin-top: 0.75rem; }

/* FAQ */
.faq { padding: 5rem 2rem; background: var(--color-surface); }
.faq-inner { max-width: 800px; margin: 0 auto; }
.faq-item { border-bottom: 1px solid #e7e5e4; padding: 1.25rem 0; }
.faq-item summary {
  font-weight: 600; font-size: 1rem; cursor: pointer; list-style: none;
  display: flex; justify-content: space-between; align-items: center;
}
.faq-item summary::after { content: "+"; font-size: 1.25rem; color: var(--color-muted); }
.faq-item[open] summary::after { content: "\\2212"; }
.faq-item p { color: var(--color-muted); font-size: 0.95rem; line-height: 1.65; margin-top: 0.75rem; }

/* Contact */
.contact-bar {
  padding: 4rem 2rem; background: var(--color-ink);
  color: #fff; text-align: center;
}
.contact-bar h2 { font-size: 2rem; margin-bottom: 0.5rem; }
.contact-bar a { color: var(--color-accent); font-weight: 600; }
.contact-bar .phone { font-size: 2.5rem; font-family: var(--font-display); margin: 1rem 0; }

.footer {
  padding: 2rem; text-align: center; font-size: 0.8rem;
  color: var(--color-muted); background: var(--color-surface);
}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  JSX / TS template strings
# ══════════════════════════════════════════════════════════════════════════════

def _layout_tsx(business_name: str) -> str:
    safe_name = business_name.replace('"', '\\"')
    return f'''\
import type {{ Metadata }} from "next";
import {{ Instrument_Serif, DM_Sans }} from "next/font/google";

const serif = Instrument_Serif({{ subsets: ["latin"], style: ["normal", "italic"], variable: "--font-display" }});
const sans = DM_Sans({{ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-body" }});

export const metadata: Metadata = {{
  title: {{ default: "{safe_name}", template: "%s" }},
  description: "Professional home services.",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en" className={{sans.variable + " " + serif.variable}}>
      <body className="bg-stone-50 text-stone-900 antialiased">
        {{children}}
      </body>
    </html>
  );
}}
'''


def _page_tsx() -> str:
    return '''\
import { SITE, COMPANY, PHONE } from "@/lib/site-content";
import { revalidatePath } from "next/cache";

export const runtime = "nodejs";
export const revalidate = 3600;

async function getData() {
  return SITE;
}

export async function generateStaticParams() {
  return [{ slug: SITE.slug || "home" }];
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const seo = SITE.seo;
  return {
    title: seo?.title || COMPANY,
    description: seo?.description || "",
    alternates: { canonical: `/${slug}` },
  };
}

const schema = SITE.schema_org;

export default async function SitePage() {
  const data = await getData();
  const { hero, services, about, reviews: reviewsBlock, faq } = data;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
      />

      <section className="hero">
        <div className="hero-copy">
          <h1>{hero.headline}</h1>
          <p className="subhead">{hero.subheadline}</p>
          <div className="cta-row">
            <a href={`tel:${PHONE}`} className="btn btn-primary">
              <span>{hero.cta_primary || "Call Now"}</span> <span>&rarr;</span>
            </a>
            <a href={hero.cta_secondary_url || "#contact"} className="btn btn-secondary">
              {hero.cta_secondary || "Get a Free Quote"}
            </a>
          </div>
          <div className="trust-bar">
            {(hero.trust_bar || []).map((t: string, i: number) => (
              <span className="chip" key={i}>{t}</span>
            ))}
          </div>
        </div>
        <div className="hero-visual">
          <div style={{
            width: "100%",
            aspectRatio: "1 / 1",
            maxWidth: "420px",
            background: "var(--color-primary)",
            opacity: 0.06,
            borderRadius: "var(--radius-lg)",
            marginLeft: "auto",
          }} />
        </div>
      </section>

      <section className="services" id="services">
        <div className="section-header">
          <h2>What We Do</h2>
          <p className="lead">Comprehensive services designed around how homeowners actually think and problem-solve.</p>
        </div>
        <div className="service-grid">
          {(services || []).map((s: any, i: number) => (
            <div className="service-card" key={i}>
              <div className="service-icon">{s.icon}</div>
              <h3>{s.title}</h3>
              <p>{s.description}</p>
              <span className="card-cta">{s.cta_text || "Learn More"} &rarr;</span>
            </div>
          ))}
        </div>
      </section>

      <section className="about" id="about">
        <div className="about-inner">
          <div>
            <h2>About {COMPANY}</h2>
            <p className="founder">{about?.story || ""}</p>
            <ul className="trust-points">
              {(about?.trust_points || []).map((t: string, i: number) => (
                <li key={i}>{t}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Certifications</h3>
            <div className="cert-grid">
              {(about?.certifications || []).map((c: string, i: number) => (
                <div className="cert-badge" key={i}>{c}</div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="reviews" id="reviews">
        <div className="section-header">
          <h2>What Neighbors Say</h2>
          <p className="lead">{reviewsBlock?.aggregate_line || ""}</p>
        </div>
        <div className="review-grid">
          {(reviewsBlock?.reviews || []).slice(0, 6).map((r: any, i: number) => (
            <div className="review-card" key={i}>
              <div className="review-stars">{"\\u2605".repeat(r.rating || 5)}</div>
              <p className="review-text">&ldquo;{r.text}&rdquo;</p>
              <p className="review-author">&mdash; {r.author || "Local Customer"}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="faq" id="faq">
        <div className="faq-inner">
          <div className="section-header"><h2>Common Questions</h2></div>
          {(faq || []).map((item: any, i: number) => (
            <details className="faq-item" key={i}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="contact-bar" id="contact">
        <h2>Ready to get started?</h2>
        <p>Call now for a free estimate or send us a message.</p>
        <div className="phone">
          <a href={`tel:${PHONE}`}>{PHONE}</a>
        </div>
      </section>

      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} {COMPANY}. All rights reserved. Licensed &amp; insured.</p>
      </footer>
    </>
  );
}
'''


def _loading_tsx() -> str:
    return """\
export default function Loading() {
  return (
    <div className="space-y-8 p-8">
      <div className="h-96 bg-stone-200 rounded-2xl animate-pulse" />
      <div className="grid grid-cols-3 gap-4">
        <div className="h-48 bg-stone-200 rounded-xl animate-pulse" />
        <div className="h-48 bg-stone-200 rounded-xl animate-pulse" />
        <div className="h-48 bg-stone-200 rounded-xl animate-pulse" />
      </div>
    </div>
  );
}
"""


def _error_tsx() -> str:
    return """\
"use client";

export default function Error({ reset }: { reset: () => void }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="text-center">
        <h2 className="text-3xl" style={{ fontFamily: "var(--font-display)" }}>
          Something went wrong
        </h2>
        <button
          onClick={() => reset()}
          className="mt-4 rounded-full bg-stone-900 px-4 py-2 text-sm text-white"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
"""


def _revalidate_route() -> str:
    return """\
import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

const SECRET = process.env.REVALIDATE_SECRET;

export async function POST(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("secret");
  if (token !== SECRET) {
    return NextResponse.json(
      { message: "Invalid token", ok: false },
      { status: 401 }
    );
  }
  try {
    const body = await request.json();
    const slugs: string[] = Array.isArray(body?.slugs) ? body.slugs : [];
    await Promise.allSettled(
      slugs.map((slug) => revalidatePath(`/${slug}`))
    );
    return NextResponse.json({ revalidated: true, slugs }, { status: 200 });
  } catch {
    return NextResponse.json(
      { message: "Error revalidating", ok: false },
      { status: 500 }
    );
  }
}
"""


def _site_content_ts(site_content: dict[str, Any]) -> str:
    bus = site_content.get("business", {})
    cfg = site_content.get("site_config", {})

    company = _to_json(bus.get("business_name", ""))
    address = _to_json(bus.get("address", ""))
    phone = _to_json(bus.get("phone", ""))
    trade = _to_json(bus.get("trade", ""))
    rating = _to_json(bus.get("google_rating"))
    review_count = _to_json(bus.get("review_count", 0))
    slug_val = _to_json(bus.get("slug", ""))
    template_id = _to_json(cfg.get("template_id", ""))
    site_json = _to_json(site_content, indent=2)

    return f"""\
export const COMPANY = {company};
export const ADDRESS = {address};
export const PHONE = {phone};
export const TRADE = {trade};
export const RATING = {rating};
export const REVIEW_COUNT = {review_count};
export const SLUG = {slug_val};
export const TEMPLATE_ID = {template_id};

export interface SiteContent {{
  business: {{
    business_name: string;
    trade: string;
    city: string;
    state: string;
    phone: string;
    email?: string;
    address: string;
    google_rating?: number;
    review_count?: number;
    website_url?: string;
    owner_name?: string;
    owner_title?: string;
    years_in_business?: number;
    service_area?: string;
  }};
  hero: {{
    headline: string;
    subheadline: string;
    trust_bar: string[];
    cta_primary: string;
    cta_primary_url: string;
    cta_secondary: string;
    cta_secondary_url: string;
  }};
  services: Array<{{
    icon: string;
    title: string;
    description: string;
    cta_text: string;
  }}>;
  about: {{
    story: string;
    trust_points: string[];
    certifications: string[];
  }};
  reviews: {{
    reviews: Array<{{
      author?: string;
      rating?: number;
      text: string;
    }}>;
    aggregate_line: string;
  }};
  faq: Array<{{
    question: string;
    answer: string;
  }}>;
  seo: {{
    title: string;
    description: string;
    keywords: string[];
  }};
  aeo_signals: {{
    local_business_type?: string;
    primary_category?: string;
    secondary_categories?: string[];
    area_served?: string[];
  }};
  schema_org: Record<string, any> | null;
  site_config: {{
    template_id: string;
    trade: string;
    theme: {{
      primary: string;
      accent: string;
      font_display?: string;
      font_body?: string;
    }};
  }};
  status: string;
  slug: string;
  meta_title: string;
  meta_description: string;
  lighthouse_score: number;
}}

export const SITE: SiteContent = {site_json};
"""


def _slug_ts() -> str:
    return r'''\
export function isValidSlug(slug: string): boolean {
  if (!slug || typeof slug !== "string" || slug.length > 100) return false;
  if (slug.startsWith("-") || slug.endsWith("-")) return false;
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug);
}

export function generateSlug(businessName: string, city: string): string {
  const clean = (s: string) =>
    s.toLowerCase()
     .replace(/[^a-z0-9\s-]/g, "")
     .trim()
     .replace(/\s+/g, "-");
  return `${clean(businessName)}-${clean(city)}`;
}
'''


def _next_config() -> str:
    return """\
import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  output: "standalone",
  experimental: { scrollRestoration: true },
};

export default config;
"""


def _tailwind_config() -> str:
    return """\
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
        serif: ["var(--font-display)", "Georgia", "serif"],
      },
      borderRadius: { sm: "0.375rem", md: "0.75rem", lg: "1.5rem" },
      colors: {
        stone: {
          50: "#fafaf9", 100: "#f5f5f4", 200: "#e7e5e4",
          500: "#78716c", 800: "#292524", 900: "#1c1917",
        },
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
"""


def _postcss_config() -> str:
    return """\
module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
"""


def _tsconfig() -> str:
    return """\
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""


def _package_json(name: str, description: str = "") -> str:
    desc = description or f"ISR site for {name}"
    pkg_name = _slugify(name)
    safe_desc = desc.replace('"', '\\"')
    return json.dumps(
        {
            "name": pkg_name,
            "version": "1.0.0",
            "private": True,
            "description": safe_desc,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
            },
            "dependencies": {
                "next": "^16",
                "react": "^19",
                "react-dom": "^19",
                "@types/node": "^20",
                "@types/react": "^19",
                "@types/react-dom": "^19",
                "typescript": "^5",
            },
        },
        indent=2,
    )


def _gitignore() -> str:
    return """\
# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env
.env*.local
.env

# typescript
*.tsbuildinfo
next-env.d.ts
"""


def _readme(name: str) -> str:
    safe = name.replace("<", "&lt;").replace(">", "&gt;")
    return f"# {safe}\n\nGenerated by WebsiteForge.\n\n```bash\nnpm install\nnpm run dev\n```\n"
