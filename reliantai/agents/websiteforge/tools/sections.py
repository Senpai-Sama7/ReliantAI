"""
sections — HTML section renderers for standalone site output.

Each function accepts a SiteContent dict and returns an HTML string fragment.
All dynamic values are HTML-escaped to prevent stored XSS.
"""

from __future__ import annotations

import html
import json
from typing import Any


def _e(value: Any) -> str:
    """Escape a value for safe HTML text/attribute interpolation."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def render_schema_org(site_content: dict[str, Any]) -> str:
    """Render JSON-LD schema script tag with XSS-safe serialization."""
    schema = site_content.get("schema_org")
    if not schema or not isinstance(schema, dict):
        business = site_content.get("business", {})
        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": business.get("business_name", ""),
            "telephone": business.get("phone", ""),
            "address": business.get("address", ""),
        }
    if not schema:
        return ""
    payload = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    return (
        '\n<script type="application/ld+json">\n'
        + payload
        + "\n</script>\n"
    )


def render_hero(site_content: dict[str, Any]) -> str:
    hero = site_content.get("hero", {})
    business = site_content.get("business", {})
    phone = _e(business.get("phone", ""))
    trust_bar = hero.get("trust_bar", []) or []
    chips = "\n    ".join(
        f'<span class="trust-chip">{_e(t)}</span>' for t in trust_bar
    )
    return f"""\
    <section class="hero">
      <div class="hero-copy">
        <h1>{_e(hero.get("headline", ""))}</h1>
        <p class="subhead">{_e(hero.get("subheadline", ""))}</p>
        <div class="cta-row">
          <a href="tel:{phone}" class="btn btn-primary">
            <span>Call Now</span> <span>&rarr;</span>
          </a>
          <a href="#contact" class="btn btn-secondary">Get a Free Quote</a>
        </div>
        <div class="trust-bar">{chips}</div>
      </div>
      <div class="hero-visual">
        <div style="
          width:100%;aspect-ratio:1/1;max-width:420px;
          background: var(--color-primary);opacity:0.06;
          border-radius: var(--radius-lg);margin-left:auto;
        "></div>
      </div>
    </section>
"""


def render_services(site_content: dict[str, Any]) -> str:
    services = site_content.get("services", [])
    if not services:
        return ""
    cards = "\n    ".join(render_service_card(s) for s in services)
    return f"""\
    <section class="services" id="services">
      <div class="section-header">
        <h2>What We Do</h2>
        <p class="lead">Trade-specific services for homeowners in your area.</p>
      </div>
      <div class="service-grid">
        {cards}
      </div>
    </section>
"""


def render_service_card(service: dict[str, Any]) -> str:
    title = _e(service.get("title", ""))
    desc = _e(service.get("description", ""))
    cta = _e(service.get("cta_text", "Learn More"))
    icon = _e(service.get("icon", "\u2699"))
    return f"""\
      <div class="service-card">
        <div class="service-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{desc}</p>
        <span class="card-cta">{cta} &rarr;</span>
      </div>
"""


def render_about(site_content: dict[str, Any]) -> str:
    about = site_content.get("about", {})
    business = site_content.get("business", {})
    story = _e(about.get("story", ""))
    trust_points = about.get("trust_points", []) or []
    certs = about.get("certifications", []) or []
    tp_list = "\n    ".join(f"<li>{_e(t)}</li>" for t in trust_points)
    cert_grid = (
        "\n    ".join(f'<div class="cert-badge">{_e(c)}</div>' for c in certs)
        if certs
        else ""
    )
    return f"""\
    <section class="about" id="about">
      <div class="about-inner">
        <div>
          <h2>About {_e(business.get("business_name", "Us"))}</h2>
          <p class="founder">{story}</p>
          <ul class="trust-points">{tp_list}</ul>
        </div>
        <div>
          <h3>Certifications</h3>
          <div class="cert-grid">{cert_grid}</div>
        </div>
      </div>
    </section>
"""


def render_reviews(site_content: dict[str, Any]) -> str:
    reviews_block = site_content.get("reviews", {})
    reviews = reviews_block.get("reviews", []) if isinstance(reviews_block, dict) else []
    aggregate = _e(reviews_block.get("aggregate_line", "") if isinstance(reviews_block, dict) else "")
    if not reviews:
        return ""
    cards = "\n    ".join(render_review_card(r) for r in reviews)
    return f"""\
    <section class="reviews" id="reviews">
      <div class="section-header">
        <h2>What Neighbors Say</h2>
        <p class="lead">{aggregate}</p>
      </div>
      <div class="review-grid">
        {cards}
      </div>
    </section>
"""


def render_review_card(review: dict[str, Any]) -> str:
    try:
        rating = int(round(float(review.get("rating", 5))))
    except (TypeError, ValueError):
        rating = 5
    rating = max(0, min(5, rating))
    stars = "\u2605" * rating
    return f"""\
      <div class="review-card">
        <div class="review-stars">{stars}</div>
        <p class="review-text">&quot;{_e(review.get("text", ""))}&quot;</p>
        <p class="review-author">&mdash; {_e(review.get("author", "Customer"))}</p>
      </div>
"""


def render_faq(site_content: dict[str, Any]) -> str:
    faqs = site_content.get("faq", [])
    if not faqs:
        return ""
    items = "\n    ".join(
        f"""\
      <details class="faq-item">
        <summary>{_e(item.get("question", ""))}</summary>
        <p>{_e(item.get("answer", ""))}</p>
      </details>"""
        for item in faqs
    )
    return f"""\
    <section class="faq" id="faq">
      <div class="faq-inner">
        <div class="section-header"><h2>Common Questions</h2></div>
        {items}
      </div>
    </section>
"""


def render_contact(site_content: dict[str, Any]) -> str:
    business = site_content.get("business", {})
    phone = _e(business.get("phone", ""))
    email = _e(business.get("email", ""))
    email_href = f"mailto:{email}" if email else "#contact"
    return f"""\
    <section class="contact-bar" id="contact">
      <h2>Ready to get started?</h2>
      <p>Call now for a free estimate or send us a message.</p>
      <div class="phone">
        <a href="tel:{phone}">{phone}</a>
      </div>
      <a href="{email_href}" class="btn btn-secondary" style="border-color:#444;color:#fff">Email Us</a>
    </section>
"""


def render_footer(site_content: dict[str, Any]) -> str:
    business = site_content.get("business", {})
    biz_name = _e(business.get("business_name", ""))
    return f"""\
    <footer class="footer">
      <p>&copy; 2025 {biz_name}. All rights reserved. Licensed &amp; insured.</p>
    </footer>
"""
