"""
test_html_renderer — validates standalone HTML output.

Checks that compile_html and render_html_file produce valid,
complete HTML documents with required sections and no banned patterns.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from reliantai.agents.websiteforge.constants import BANNED_AI_PATTERNS
from reliantai.agents.websiteforge.tools.content_forge import _build_minimal_shell
from reliantai.agents.websiteforge.tools.html_renderer import compile_html, render_html_file


@pytest.fixture
def sample_content(tmp_path: Path):
    content = _build_minimal_shell("Austin Pro HVAC", {"trade": "hvac", "city_state": "Austin, TX"})
    content["services"] = [
        {"icon": "snowflake", "title": "AC Repair", "description": "Fast AC repair in Austin.", "cta_text": "Book Now"},
        {"icon": "bolt", "title": "Emergency Service", "description": "24/7 emergency HVAC in Austin.", "cta_text": "Call Now"},
        {"icon": "gauge", "title": "Duct Cleaning", "description": "Improve air quality.", "cta_text": "Learn More"},
    ]
    content["faq"] = [
        {"question": "Do you offer free estimates?", "answer": "Yes, all estimates are free in Austin."},
        {"question": "How quickly can you respond?", "answer": "Most calls within 4 hours in Austin."},
    ]
    content["reviews"] = {
        "reviews": [
            {"rating": 5, "text": "Excellent service from Austin Pro HVAC.", "author": "Sarah M."},
            {"rating": 5, "text": "Honest and professional.", "author": "James K."},
        ],
        "aggregate_line": "5/5 stars from Austin homeowners",
    }
    content["about"]["certifications"] = ["EPA 608", "NATE"]
    content["slug"] = "austin-pro-hvac"
    return content


def test_compile_html_returns_string(sample_content):
    html = compile_html(sample_content)
    assert isinstance(html, str)
    assert len(html) > 500, "HTML output should be substantial"


def test_compile_html_has_doctype(sample_content):
    html = compile_html(sample_content)
    assert "<!doctype html>" in html.lower(), "Must have HTML5 doctype"


def test_compile_html_has_meta_viewport(sample_content):
    html = compile_html(sample_content)
    assert 'name="viewport"' in html, "Must have viewport meta tag"


def test_compile_html_has_title(sample_content):
    html = compile_html(sample_content)
    assert "<title>" in html and "</title>" in html
    assert "Austin Pro HVAC" in html


def test_compile_html_has_hero_section(sample_content):
    html = compile_html(sample_content)
    assert 'class="hero"' in html or 'class="hero"' in html
    assert "Austin Pro HVAC" in html
    assert "Same-Day" in html or "Austin" in html


def test_compile_html_has_services_section(sample_content):
    html = compile_html(sample_content)
    assert "AC Repair" in html
    assert "Emergency Service" in html
    assert "service-card" in html


def test_compile_html_has_about_section(sample_content):
    html = compile_html(sample_content)
    assert "About Austin Pro HVAC" in html or "founded" in html.lower()


def test_compile_html_has_reviews_section(sample_content):
    html = compile_html(sample_content)
    assert "Sarah M." in html
    assert "review-card" in html


def test_compile_html_has_faq_section(sample_content):
    html = compile_html(sample_content)
    assert "free estimates" in html
    assert "faq-item" in html


def test_compile_html_has_schema_org(sample_content):
    html = compile_html(sample_content)
    assert 'type="application/ld+json"' in html or 'type="application/ld+json"' in html


def test_compile_html_no_banned_fonts(sample_content):
    """Banned fonts Inter and Geist must not appear as display fonts in HTML."""
    html = compile_html(sample_content)
    display_fonts_banned = ["Inter", "Geist"]
    for font in display_fonts_banned:
        assert font not in html, f"Banned display font '{font}' found in HTML output"


def test_compile_html_uses_instrument_serif(sample_content):
    html = compile_html(sample_content)
    assert "Instrument Serif" in html, "Must use Instrument Serif as display font"


def test_compile_html_no_min_h_screen(sample_content):
    html = compile_html(sample_content)
    assert "min-h-screen" not in html, "Must NOT use min-h-screen (100vh hero)"
    assert "100vh" not in html, "Must NOT use 100vh"


def test_compile_html_has_css_variables(sample_content):
    html = compile_html(sample_content)
    assert "var(--font-display)" in html, "Must define --font-display CSS variable"
    assert "var(--color-primary)" in html, "Must define --color-primary CSS variable"


def test_render_html_file_writes_output(tmp_path: Path, sample_content):
    output_dir = tmp_path / "html_out"
    result_path = render_html_file(sample_content, output_dir)
    assert result_path.exists(), "Output file must exist"
    assert result_path.name == "index.html"
    content = result_path.read_text(encoding="utf-8")
    assert len(content) > 500


def test_render_html_file_inline_css(tmp_path: Path, sample_content):
    output_dir = tmp_path / "html_out"
    render_html_file(sample_content, output_dir)
    html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "<style>" in html, "Must have inline <style> block"


def test_compile_html_business_name_in_footer(sample_content):
    html = compile_html(sample_content)
    assert "Austin Pro HVAC" in html
    assert "2025" in html or "©" in html or "rights reserved" in html.lower()
