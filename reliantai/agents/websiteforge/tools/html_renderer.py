"""
html_renderer - produces a production-grade standalone HTML file.

Delegates section rendering to tools/sections.py and CSS assembly to this
module. Public API (compile_html, render_html_file) is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...core import get_logger
from ..constants import TRADE_TEMPLATE_MAP, DEFAULT_FALLBACK_TEMPLATE, BANNED_AI_PATTERNS
from .content_forge import _build_minimal_shell
from .sections import (
    render_schema_org,
    render_hero,
    render_services,
    render_about,
    render_reviews,
    render_faq,
    render_contact,
    render_footer,
)

log = get_logger("agents.websiteforge.html_renderer")


BASE_CSS = """*, *::before, *::after { box-sizing: border-box; margin: 0; }

:root {
  --font-display: "Instrument Serif", "Playfair Display", Georgia, serif;
  --font-body: "DM Sans", "Plus Jakarta Sans", system-ui, sans-serif;
  --color-primary: {primary};
  --color-accent: {accent};
  --color-surface: #fafaf9;
  --color-ink: #1c1917;
  --color-muted: #78716c;
  --ease-out-expo: cubic-bezier(0.22, 1, 0.36, 1);
  --radius-sm: 0.375rem;
  --radius-md: 0.75rem;
  --radius-lg: 1.5rem;
}

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

.hero {
  min-height: 85vh;
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 3rem;
  align-items: center;
  padding: 6rem 2rem;
  background: linear-gradient(160deg, {surface_1} 0%, {surface_2} 100%);
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
  color: var(--color-ink);
}

.hero .subhead {
  font-size: 1.15rem;
  color: var(--color-muted);
  max-width: 28rem;
  margin-bottom: 2rem;
  line-height: 1.7;
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

.btn-primary {
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.btn-secondary {
  background: #fff;
  color: var(--color-primary);
  border: 1px solid #e7e5e4;
}

.trust-bar {
  display: flex;
  gap: 1rem;
  margin-top: 2.5rem;
  flex-wrap: wrap;
}

.trust-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.85rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 500;
  background: #fff;
  border: 1px solid #e7e5e4;
  color: var(--color-muted);
}

.services { padding: 5rem 2rem; background: #fff; }

.section-header { text-align: center; margin-bottom: 3rem; }

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
  margin-bottom: 1rem; font-size: 1.25rem;
}

.service-card h3 { font-size: 1.3rem; margin-bottom: 0.5rem; }
.service-card p { color: var(--color-muted); font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.25rem; }
.service-card .card-cta { font-size: 0.85rem; font-weight: 600; color: var(--color-primary); letter-spacing: 0.02em; }

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
.trust-points li::before { content: "\2713"; color: var(--color-primary); font-weight: 700; }

.cert-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 1rem; }
.cert-badge {
  padding: 0.6rem 0.9rem; border-radius: var(--radius-sm);
  background: #fff; border: 1px solid #e7e5e4;
  font-size: 0.8rem; font-weight: 500; color: var(--color-muted); text-align: center;
}

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

.faq { padding: 5rem 2rem; background: var(--color-surface); }
.faq-inner { max-width: 800px; margin: 0 auto; }
.faq-item { border-bottom: 1px solid #e7e5e4; padding: 1.25rem 0; }
.faq-item summary {
  font-weight: 600; font-size: 1rem; cursor: pointer; list-style: none;
  display: flex; justify-content: space-between; align-items: center;
}
.faq-item summary::after { content: "+"; font-size: 1.25rem; color: var(--color-muted); }
.faq-item[open] summary::after { content: "\2212"; }
.faq-item p { color: var(--color-muted); font-size: 0.95rem; line-height: 1.65; margin-top: 0.75rem; }

.contact-bar {
  padding: 4rem 2rem;
  background: var(--color-ink);
  color: #fff;
  text-align: center;
}
.contact-bar h2 { font-size: 2rem; margin-bottom: 0.5rem; }
.contact-bar a { color: var(--color-accent); font-weight: 600; }
.contact-bar .phone { font-size: 2.5rem; font-family: var(--font-display); margin: 1rem 0; }

.footer {
  padding: 2rem; text-align: center; font-size: 0.8rem;
  color: var(--color-muted); background: var(--color-surface);
}"""


def _build_minimal_shell_guard(content: dict[str, Any]) -> dict[str, Any]:
    """Ensure we always have enough to render without crashing."""
    try:
        if not isinstance(content, dict):
            raise TypeError
        if not content.get("hero", {}).get("headline") or not content.get("seo", {}).get("title"):
            raise ValueError("incomplete")
        return content
    except (TypeError, ValueError):
        log.warning("html_renderer.fallback_shell")
        return _build_minimal_shell({}, {})


def compile_html(site_content: dict[str, Any]) -> str:
    """Build a single standalone HTML file string from SiteContent."""
    site_content = _build_minimal_shell_guard(site_content)
    cfg = site_content.get("site_config", {})
    primary = cfg.get("theme", {}).get("primary", "#1e3a5f")
    accent = cfg.get("theme", {}).get("accent", "#3b82f6")

    css = (
        BASE_CSS.replace("{primary}", primary)
        .replace("{accent}", accent)
        .replace("{surface_1}", primary + "08")
        .replace("{surface_2}", accent + "05")
    )

    title = site_content.get("seo", {}).get("title", "")
    description = site_content.get("seo", {}).get("description", "")

    body = "\n".join([
        render_hero(site_content),
        render_services(site_content),
        render_about(site_content),
        render_reviews(site_content),
        render_faq(site_content),
        render_contact(site_content),
        render_footer(site_content),
    ])

    return f"""\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet" />
  {render_schema_org(site_content)}
  <style>
{css}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def render_html_file(site_content: dict[str, Any], output_dir: Path) -> Path:
    """
    Compile HTML and write to output_dir/index.html.
    Returns the written Path.
    Handles bad input by falling back to a minimal shell.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "index.html"
    html = compile_html(site_content)
    path.write_text(html, encoding="utf-8")
    log.info("html_renderer.wrote", path=str(path), size=len(html))
    return path
