"""
test_isr_renderer — validates the Next.js ISR scaffold output.

Checks that render_isr_scaffold produces the complete file tree
with correct structure, imports, and content wiring.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reliantai.agents.websiteforge.renderers.isr_renderer import render_isr_scaffold
from reliantai.agents.websiteforge.tools.content_forge import _build_minimal_shell


@pytest.fixture
def sample_content(tmp_path: Path):
    content = _build_minimal_shell("Austin Pro HVAC", {"trade": "hvac", "city_state": "Austin, TX"})
    content["services"] = [
        {"icon": "snowflake", "title": "AC Repair", "description": "Fast AC repair.", "cta_text": "Book"},
        {"icon": "bolt", "title": "Emergency Service", "description": "24/7 emergency HVAC.", "cta_text": "Call"},
        {"icon": "gauge", "title": "Duct Cleaning", "description": "Improve air quality.", "cta_text": "Quote"},
    ]
    content["reviews"] = {
        "reviews": [{"rating": 5, "text": "Great work.", "author": "Sarah"}],
        "aggregate_line": "5/5 from homeowners",
    }
    content["faq"] = [
        {"question": "Do you offer free estimates?", "answer": "Yes, all estimates are free."},
        {"question": "How quickly can you respond?", "answer": "Most calls within 4 hours."},
        {"question": "What brands do you service?", "answer": "Carrier, Trane, Lennox, Goodman, York."},
        {"question": "Are your technicians licensed?", "answer": "Yes, all hold Texas HVAC licenses."},
        {"question": "Do you offer maintenance plans?", "answer": "Yes, our Comfort Club includes annual tune-ups."},
    ]
    content["about"]["certifications"] = ["EPA 608", "NATE"]
    content["slug"] = "austin-pro-hvac-austin-tx"
    content["schema_org"] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "Austin Pro HVAC",
        "telephone": "+15125551234",
    }
    content["site_config"]["theme"] = {
        "primary": "#1e3a5f",
        "accent": "#0ea5e9",
        "font_display": "Instrument Serif",
        "font_body": "DM Sans",
    }
    return content


@pytest.mark.asyncio
async def test_isr_creates_all_required_files(tmp_path: Path, sample_content):
    out = tmp_path / "isr_out"
    result = await render_isr_scaffold(sample_content, out)

    assert result.exists(), "Output directory must exist"
    assert result.is_dir()

    required_files = [
        "app/globals.css",
        "app/layout.tsx",
        "app/[slug]/page.tsx",
        "app/[slug]/loading.tsx",
        "app/[slug]/error.tsx",
        "app/api/revalidate/route.ts",
        "lib/site-content.ts",
        "lib/slug.ts",
        "package.json",
        "tsconfig.json",
        "tailwind.config.ts",
        "postcss.config.js",
        "next.config.ts",
        "next-env.d.ts",
    ]

    for rel in required_files:
        p = result / rel
        assert p.exists(), f"Missing required file: {rel}"
        assert p.stat().st_size > 0, f"File is empty: {rel}"


@pytest.mark.asyncio
async def test_isr_page_tsx_imports_site(tmp_path: Path, sample_content):
    """page.tsx must import SITE from @/lib/site-content (no broken runtime refs)."""
    out = tmp_path / "isr_jsx"
    await render_isr_scaffold(sample_content, out)
    page = out / "app/[slug]/page.tsx"
    text = page.read_text(encoding="utf-8")

    assert 'from "@/lib/site-content"' in text, "page.tsx must import from @/lib/site-content"
    assert "import { SITE" in text, "page.tsx must import SITE for runtime data"
    assert "SITE.slug" in text or "SITE.schema_org" in text, "SITE must be used for data"


@pytest.mark.asyncio
async def test_isr_layout_has_fonts(tmp_path: Path, sample_content):
    """layout.tsx must import Google Fonts for display and body typography."""
    from reliantai.agents.websiteforge.renderers.isr_renderer import _layout_tsx
    layout = _layout_tsx("Austin Pro HVAC")

    assert "next/font/google" in layout
    assert "Instrument_Serif" in layout or "Instrument Serif" in layout
    assert "DM_Sans" in layout or "DM Sans" in layout


@pytest.mark.asyncio
async def test_isr_package_json_valid_json(tmp_path: Path, sample_content):
    """package.json must be valid JSON with expected keys."""
    from reliantai.agents.websiteforge.renderers.isr_renderer import _package_json
    raw = _package_json("Austin Pro HVAC")
    pkg = json.loads(raw)

    assert "name" in pkg
    assert "dependencies" in pkg
    assert "next" in pkg["dependencies"]
    assert "react" in pkg["dependencies"]


@pytest.mark.asyncio
async def test_isr_site_content_ts_has_site_export(tmp_path: Path, sample_content):
    """lib/site-content.ts must export SITE constant with correct type."""
    from reliantai.agents.websiteforge.renderers.isr_renderer import _site_content_ts
    ts = _site_content_ts(sample_content)

    assert "export const SITE" in ts
    assert "export interface SiteContent" in ts
    assert '"Austin Pro HVAC"' in ts


@pytest.mark.asyncio
async def test_isr_revalidate_route(tmp_path: Path, sample_content):
    """revalidate route must import revalidatePath from next/cache."""
    from reliantai.agents.websiteforge.renderers.isr_renderer import _revalidate_route
    rv = _revalidate_route()

    assert 'from "next/cache"' in rv or "next/cache" in rv
    assert "revalidatePath" in rv
    assert "async function POST" in rv


@pytest.mark.asyncio
async def test_isr_globals_css_has_theme_vars(tmp_path: Path, sample_content):
    """globals.css must define --color-primary and --color-accent with injected values."""
    out = tmp_path / "isr_css"
    await render_isr_scaffold(sample_content, out)
    css = (out / "app/globals.css").read_text(encoding="utf-8")

    assert "--color-primary" in css, "globals.css must define --color-primary"
    assert "--color-accent" in css, "globals.css must define --color-accent"
    assert "1e3a5f" in css, "globals.css must inject the primary color value"
    assert "0ea5e9" in css, "globals.css must inject the accent color value"


@pytest.mark.asyncio
async def test_isr_page_tsx_has_all_sections(tmp_path: Path, sample_content):
    """page.tsx must render hero, services, reviews, FAQ, contact sections."""
    out = tmp_path / "isr_jsx"
    await render_isr_scaffold(sample_content, out)
    page = out / "app/[slug]/page.tsx"
    text = page.read_text(encoding="utf-8")

    assert "<h1>" in text or "hero-headline" in text, "page.tsx must render hero heading"
    assert "service-card" in text or "services" in text, "page.tsx must render services section"
    assert "review-card" in text or "reviews" in text, "page.tsx must render reviews section"
    assert "faq-item" in text or "faq" in text, "page.tsx must render FAQ section"
    assert "contact-bar" in text or "contact" in text, "page.tsx must render contact section"


@pytest.mark.asyncio
async def test_isr_no_syntax_errors_in_key_files(tmp_path: Path, sample_content):
    """Key generated files must not have obvious brace/quote balance failures."""
    out = tmp_path / "isr_syntax"
    await render_isr_scaffold(sample_content, out)

    key_files = ["app/layout.tsx", "app/[slug]/page.tsx", "lib/site-content.ts"]
    for rel in key_files:
        path = out / rel
        text = path.read_text(encoding="utf-8")
        assert text.count("{") == text.count("}"), f"Brace mismatch in {rel}"
        assert text.count('"') % 2 == 0, f"Unbalanced quotes in {rel}"
        assert text.count("(") == text.count(")"), f"Unbalanced parens in {rel}"


@pytest.mark.asyncio
async def test_isr_output_idempotent(tmp_path: Path, sample_content):
    """render_isr_scaffold must be idempotent — re-run returns same directory."""
    out = tmp_path / "isr_rerun"
    out1 = await render_isr_scaffold(sample_content, out)
    out2 = await render_isr_scaffold(sample_content, out)
    assert out1 == out2, "Re-run should return same output directory"
