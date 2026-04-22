#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import logging
import os
import random
import re
import shutil
import smtplib
import sys
import textwrap
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
import jsonschema
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from lead_queue import LeadQueueDB, LeadUpsertPayload

PROJECT_ROOT = Path(__file__).resolve().parent
SCHEMA_DIR = PROJECT_ROOT / "schemas"
MARKET_DIR = PROJECT_ROOT / "market"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
LOG_PATH_DEFAULT = str(WORKSPACE_DIR / "logs" / "orchestrator.log")

load_dotenv(PROJECT_ROOT / ".env", override=False)

log = logging.getLogger("citadel.orchestrator")


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        run_id = getattr(record, "run_id", None)
        if run_id is not None and not isinstance(run_id, (str, int, float, bool)):
            run_id = str(run_id)
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": run_id,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


@dataclass
class RuntimeConfig:
    db_path: str
    log_path: str
    default_city: str
    default_state: str
    deploy_backend: str
    deploy_enabled: bool
    email_backend: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_from_email: str
    brand_name: str
    brand_from_name: str
    brand_from_email: str
    brand_postal_address: str
    brand_optout_email: str

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            db_path=os.getenv("CITADEL_DB_PATH", str(WORKSPACE_DIR / "state" / "lead_queue.db")),
            log_path=os.getenv("CITADEL_LOG_PATH", LOG_PATH_DEFAULT),
            default_city=os.getenv("CITADEL_DEFAULT_CITY", "Houston"),
            default_state=os.getenv("CITADEL_DEFAULT_STATE", "TX"),
            deploy_backend=os.getenv("DEPLOY_BACKEND", "local_fs").strip() or "local_fs",
            deploy_enabled=os.getenv("DEPLOY_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
            email_backend=os.getenv("EMAIL_BACKEND", "local_outbox").strip() or "local_outbox",
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"},
            smtp_from_email=os.getenv("SMTP_FROM_EMAIL", os.getenv("BRAND_FROM_EMAIL", "noreply@example.com")),
            brand_name=os.getenv("BRAND_NAME", "ReliantAI"),
            brand_from_name=os.getenv("BRAND_FROM_NAME", "Douglas Mitchell"),
            brand_from_email=os.getenv("BRAND_FROM_EMAIL", "douglas-d-mitchell@outlook.com"),
            brand_postal_address=os.getenv("BRAND_POSTAL_ADDRESS", "Humble, TX"),
            brand_optout_email=os.getenv("BRAND_OPTOUT_EMAIL", "optout@example.com"),
        )


def ensure_dirs() -> None:
    for p in [
        WORKSPACE_DIR / "builds",
        WORKSPACE_DIR / "deploys",
        WORKSPACE_DIR / "logs",
        WORKSPACE_DIR / "state",
        WORKSPACE_DIR / "outbox",
        MARKET_DIR,
    ]:
        p.mkdir(parents=True, exist_ok=True)


def setup_logging(log_path: str) -> None:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    fmt = os.getenv("CITADEL_LOG_FORMAT", "text").strip().lower()
    if fmt == "json":
        formatter = JsonLogFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z")
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout), logging.FileHandler(log_path)]
    for h in handlers:
        h.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


def load_schemas() -> dict[str, dict[str, Any]]:
    format_checker = jsonschema.FormatChecker()
    names = ["qualifier_output", "builder_input", "build_manifest", "outreach_output"]
    out: dict[str, dict[str, Any]] = {}
    for name in names:
        p = SCHEMA_DIR / f"{name}.json"
        schema = json.loads(p.read_text(encoding="utf-8"))
        jsonschema.Draft7Validator.check_schema(schema)
        out[name] = schema
    out["_format_checker"] = format_checker  # type: ignore[assignment]
    return out


def validate_or_raise(name: str, obj: dict[str, Any], schemas: dict[str, dict[str, Any]]) -> None:
    jsonschema.validate(instance=obj, schema=schemas[name], format_checker=schemas["_format_checker"])  # type: ignore[arg-type]


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", text)[:80] or "lead"


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    if not netloc and parsed.path:
        # handle accidental "example.com"
        netloc = parsed.path.lower()
        path = ""
    else:
        path = parsed.path or ""
    path = re.sub(r"/+$", "", path)
    return f"{scheme}://{netloc}{path}"


def make_lead_slug(business_name: str, city: str, state: str, target_url: str) -> str:
    base = slugify(f"{business_name}-{city}-{state}")
    host = (urlparse(normalize_url(target_url)).netloc or "unknown").split(":")[0]
    suffix = re.sub(r"[^a-z0-9]", "", host.lower())[:10]
    if suffix and suffix not in base:
        base = f"{base}-{suffix}"
    return base[:110]


EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?1[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?)\d{3}[\s\-\.]?\d{4}")


def _extract_jsonld_local_business(soup: BeautifulSoup) -> dict[str, Any]:
    for tag in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = (tag.string or tag.text or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            typ = item.get("@type")
            types = [typ] if isinstance(typ, str) else typ if isinstance(typ, list) else []
            if any(isinstance(t, str) and ("LocalBusiness" in t or t in {"Plumber", "Electrician", "HVACBusiness", "AutoRepair"}) for t in types):
                return item
    return {}


def _infer_vertical(text: str) -> str:
    t = text.lower()
    keyword_map = [
        ("plumbing", ["plumb", "water heater", "drain", "sewer"]),
        ("hvac", ["hvac", "air conditioning", "heating", "furnace", "ac repair"]),
        ("electrical", ["electric", "panel upgrade", "generator", "rewire"]),
        ("roofing", ["roof", "shingle", "leak repair"]),
        ("landscaping", ["landscape", "lawn", "sprinkler", "irrigation"]),
        ("medspa", ["med spa", "botox", "laser treatment", "injectables"]),
        ("dental", ["dentist", "dental", "teeth whitening"]),
        ("legal", ["attorney", "law firm", "legal services"]),
        ("home_remodeling", ["remodel", "renovation", "kitchen", "bathroom"]),
        ("auto_repair", ["auto repair", "mechanic", "brake service", "oil change"]),
    ]
    for slug, kws in keyword_map:
        if any(k in t for k in kws):
            return slug
    return "general_services"


def _infer_city_state(text: str, default_city: str, default_state: str) -> tuple[str, str]:
    # Lightweight heuristic focused on Texas/Houston first; falls back to defaults.
    state_patterns = [
        ("TX", [" texas ", " tx ", ", tx", " houston", " humble", " katy", " spring", " cypress", " pasadena"]),
        ("CA", [" california ", " ca ", ", ca"]),
        ("FL", [" florida ", " fl ", ", fl"]),
        ("NY", [" new york ", " ny ", ", ny"]),
    ]
    lowered = f" {text.lower()} "
    state = default_state
    for abbr, hints in state_patterns:
        if any(h in lowered for h in hints):
            state = abbr
            break
    city_candidates = ["Houston", "Humble", "Katy", "Spring", "Cypress", "Pasadena", "Dallas", "Austin", "San Antonio"]
    city = default_city
    for c in city_candidates:
        if c.lower() in lowered:
            city = c
            break
    return city, state


def _fetch_pages(target_url: str) -> list[dict]:
    """Return list of ``{url, html, title}`` dicts via Playwright or httpx fallback."""
    import asyncio

    max_pages = int(os.environ.get("CITADEL_CRAWL_MAX_PAGES", "20"))

    # Try Playwright multi-page crawl
    if max_pages > 1:
        try:
            from crawler import SiteCrawler
            pages = asyncio.run(SiteCrawler(max_pages=max_pages).crawl(target_url))
            if pages:
                return pages
        except Exception as exc:
            log.warning("Playwright crawl failed, falling back to httpx: %s", exc)

    # httpx single-page fallback
    url = normalize_url(target_url)
    headers = {
        "User-Agent": "CitadelScout/1.0 (+https://reliantai.org)",
        "Accept": "text/html,application/xhtml+xml",
    }
    r = httpx.get(url, headers=headers, follow_redirects=True, timeout=20)
    r.raise_for_status()
    content_type = r.headers.get("content-type", "")
    if "html" not in content_type and "<html" not in r.text[:500].lower():
        raise ValueError(f"Target did not return HTML: {content_type}")
    return [{"url": str(r.url), "html": r.text, "title": ""}]


def scout_website(target_url: str, cfg: RuntimeConfig) -> dict[str, Any]:
    pages = _fetch_pages(target_url)
    first_html = pages[0]["html"]
    first_url = pages[0]["url"]

    # Merge signals across all crawled pages
    all_text_parts: list[str] = []
    all_emails: set[str] = set()
    all_phones: set[str] = set()
    jsonld: dict = {}
    title: str | None = None
    meta_desc: str | None = None
    viewport = False
    has_contact_page = False
    has_cta_button = False
    has_gbp = False

    gbp_signals = ["maps.google.com", "google.com/maps", "g.page/", "google.com/search?kgmid"]

    for pg in pages:
        soup = BeautifulSoup(pg["html"], "lxml")
        page_text = " ".join(soup.stripped_strings)
        all_text_parts.append(page_text)

        all_emails.update(m.group(0) for m in EMAIL_RE.finditer(pg["html"]))
        all_phones.update(m.group(0) for m in PHONE_RE.finditer(page_text))

        # First page wins for title / meta / jsonld
        if not jsonld:
            jsonld = _extract_jsonld_local_business(soup)
        if title is None and soup.title and soup.title.string:
            title = soup.title.string.strip()
        if meta_desc is None:
            md_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
            if md_tag:
                meta_desc = md_tag.get("content", "").strip()

        # Accumulate boolean signals (any page having it counts)
        if not viewport:
            viewport = soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)}) is not None
        if not has_contact_page:
            has_contact_page = bool(soup.find("a", href=re.compile("contact", re.I)))
        if not has_cta_button:
            has_cta_button = bool(soup.find(["a", "button"], string=re.compile(r"call|book|schedule|get quote|quote", re.I)))
        if not has_gbp:
            has_gbp = any(sig in pg["html"] for sig in gbp_signals)

    merged_text = " ".join(all_text_parts)
    emails = sorted(all_emails)
    phones = sorted(all_phones)

    # Business name extraction (same logic, first page)
    business_name = None
    if isinstance(jsonld.get("name"), str):
        business_name = jsonld.get("name").strip()
    if not business_name:
        first_soup = BeautifulSoup(first_html, "lxml")
        h1 = first_soup.find("h1")
        if h1 and h1.get_text(strip=True):
            business_name = h1.get_text(" ", strip=True)
    if not business_name and title:
        business_name = re.split(r"[\|\-–•]", title)[0].strip()
    if not business_name:
        business_name = urlparse(first_url).netloc

    # schema.org aggregateRating if present
    rating = None
    rating_count = None
    agg = jsonld.get("aggregateRating") if isinstance(jsonld, dict) else None
    if isinstance(agg, dict):
        try:
            rating = float(agg.get("ratingValue")) if agg.get("ratingValue") is not None else None
        except Exception:
            rating = None
        try:
            rating_count = int(float(agg.get("ratingCount"))) if agg.get("ratingCount") is not None else None
        except Exception:
            rating_count = None

    city, state = _infer_city_state(merged_text + " " + (meta_desc or "") + " " + (title or ""), cfg.default_city, cfg.default_state)
    vertical = _infer_vertical(merged_text + " " + (title or "") + " " + (meta_desc or ""))

    # ML override when enabled
    if os.environ.get("CITADEL_ML_ENABLED", "false").lower() == "true":
        try:
            from inference import extract_location, classify_vertical
            ml_loc = extract_location(all_text_parts)
            if ml_loc.get("city"):
                city = ml_loc["city"]
            if ml_loc.get("state"):
                state = ml_loc["state"]
            ml_vert = classify_vertical(merged_text, [
                "plumbing", "hvac", "electrical", "roofing",
                "landscaping", "painting", "dental", "legal",
                "medspa", "home_remodeling", "auto_repair",
            ])
            if ml_vert:
                vertical = ml_vert
        except Exception as exc:
            log.warning("ML inference failed, using keyword heuristics: %s", exc)

    has_https = first_url.lower().startswith("https://")
    web_presence_score = sum([has_https, viewport, bool(meta_desc), has_contact_page, has_cta_button])  # 0-5

    scout = {
        "target": target_url,
        "fetched_url": first_url,
        "business_name": business_name,
        "vertical": vertical,
        "city": city,
        "state": state,
        "has_website": True,
        "website_url": first_url,
        "phone": phones[0] if phones else None,
        "email": emails[0] if emails else None,
        "rating": rating,
        "rating_count": rating_count,
        "has_gbp": has_gbp,
        "web_presence_score": web_presence_score,
        "meta": {
            "title": title,
            "description": meta_desc,
            "http_status": 200,
            "content_length": sum(len(pg["html"]) for pg in pages),
        },
        "evidence": {
            "emails": emails[:5],
            "phones": phones[:5],
            "viewport": viewport,
            "has_contact_page": has_contact_page,
            "has_cta_button": has_cta_button,
            "jsonld_local_business": bool(jsonld),
            "pages_crawled": len(pages),
        },
        "page_excerpt": merged_text[:4000],
    }
    return scout


def load_market_weights() -> dict[str, Any]:
    path = MARKET_DIR / "market_weights.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def qualify_lead(scout: dict[str, Any], market_weights: dict[str, Any]) -> dict[str, Any]:
    vertical = str(scout["vertical"])
    weaknesses: list[str] = []

    if not scout.get("email"):
        weaknesses.append("No email found on site")
    if not scout.get("phone"):
        weaknesses.append("No phone number found in page content")
    if int(scout.get("web_presence_score") or 0) <= 2:
        weaknesses.append("Weak web conversion posture")
    if not scout.get("has_gbp"):
        weaknesses.append("No Google Business Profile signal detected")
    if scout.get("rating_count") in (None, 0):
        weaknesses.append("No visible review count")
    elif int(scout.get("rating_count") or 0) < 10:
        weaknesses.append("Low public review volume")

    density_entry = (((market_weights or {}).get("weights") or {}).get(vertical) or {})
    density_weight = float(density_entry.get("density_weight", 0.5))

    score = 5
    score += 1 if scout.get("email") else 0
    score += 1 if scout.get("phone") else 0
    score += int(scout.get("web_presence_score") or 0) // 2
    score += 1 if scout.get("has_gbp") else 0
    rc = int(scout.get("rating_count") or 0)
    score += 2 if rc >= 25 else 1 if rc >= 5 else 0
    score += 1 if density_weight >= 0.5 else 0

    score = max(1, min(10, int(score)))
    disqualify_reason = None
    if score < 6:
        disqualify_reason = "Opportunity score below threshold"

    out = {
        "lead_slug": make_lead_slug(str(scout["business_name"]), str(scout["city"]), str(scout["state"]), str(scout["website_url"])),
        "business_name": scout["business_name"],
        "vertical": vertical,
        "city": scout["city"],
        "state": scout["state"],
        "has_website": bool(scout["has_website"]),
        "website_url": scout["website_url"],
        "phone": scout.get("phone"),
        "email": scout.get("email"),
        "has_gbp": bool(scout.get("has_gbp")),
        "web_presence_score": int(scout.get("web_presence_score") or 0),
        "rating": float(scout["rating"]) if scout.get("rating") is not None else None,
        "rating_count": rc,
        "opportunity_score": score,
        "weakness_summary": "; ".join(weaknesses[:4]) if weaknesses else "No obvious weakness signals detected",
        "disqualify_reason": disqualify_reason,
        "market_establishments": int(density_entry.get("establishments", 0)),
        "density_weight_applied": density_weight,
        "source_ref": scout["website_url"],
        "source_payload": scout,
    }
    return out


def build_builder_input(q: dict[str, Any]) -> dict[str, Any]:
    services_map = {
        "plumbing": ["Drain cleaning", "Water heater repair", "Leak detection", "Emergency service"],
        "hvac": ["AC repair", "Heating service", "System tune-up", "Indoor air quality"],
        "electrical": ["Panel upgrades", "Generator installs", "Troubleshooting", "EV charger installs"],
        "roofing": ["Roof repair", "Leak inspection", "Replacement quotes", "Storm damage service"],
        "landscaping": ["Lawn maintenance", "Irrigation repair", "Seasonal cleanups", "Landscape design"],
        "medspa": ["Injectables", "Laser treatment", "Skin consultations", "Membership plans"],
        "dental": ["Preventive care", "Whitening", "Emergency visits", "Insurance guidance"],
        "legal": ["Case review", "Consultation booking", "Document support", "Court representation"],
        "home_remodeling": ["Kitchen remodels", "Bathroom remodels", "Flooring", "Project estimates"],
        "auto_repair": ["Brake service", "Diagnostics", "Oil changes", "Engine repair"],
        "general_services": ["Consultation", "Quotes", "Fast scheduling", "Local service"],
    }
    services = services_map.get(q["vertical"], services_map["general_services"])
    return {
        "lead_slug": q["lead_slug"],
        "business_name": q["business_name"],
        "vertical": q["vertical"],
        "city": q["city"],
        "state": q["state"],
        "brand_voice": "credible-local-operator",
        "primary_offer": f"Fast {q['vertical'].replace('_', ' ')} service in {q['city']}",
        "primary_cta": "Request a Quote",
        "phone": q.get("phone"),
        "email": q.get("email"),
        "services": services,
        "social_proof": {
            "rating": q.get("rating"),
            "rating_count": q.get("rating_count"),
            "review_snippet": "Trusted local service with fast response times.",
        },
        "design_tokens": {
            "primary": "#0B1220",
            "accent": "#0EA5E9",
            "bg": "#F8FAFC",
            "text": "#0F172A",
        },
        "seo": {
            "title": f"{q['business_name']} | {q['vertical'].replace('_', ' ').title()} in {q['city']}, {q['state']}",
            "description": f"Need {q['vertical'].replace('_',' ')} help in {q['city']}? Contact {q['business_name']} for fast quotes and local service.",
        },
    }


def render_site_files(builder_input: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    business = html.escape(builder_input["business_name"])
    vertical_title = html.escape(builder_input["vertical"].replace("_", " ").title())
    city = html.escape(builder_input["city"])
    state = html.escape(builder_input["state"])
    phone = html.escape(builder_input.get("phone") or "")
    email_addr = html.escape(builder_input.get("email") or "")
    primary_offer = html.escape(builder_input["primary_offer"])
    primary_cta = html.escape(builder_input["primary_cta"])
    seo_title = html.escape(builder_input["seo"]["title"])
    seo_desc = html.escape(builder_input["seo"]["description"])
    colors = builder_input["design_tokens"]
    services_html = "".join(f"<li>{html.escape(s)}</li>" for s in builder_input["services"])

    review_line = ""
    sp = builder_input.get("social_proof") or {}
    if sp.get("rating") and sp.get("rating_count"):
        review_line = f"<p class='review'>★ {float(sp['rating']):.1f} ({int(sp['rating_count'])} reviews)</p>"
    elif sp.get("review_snippet"):
        review_line = f"<p class='review'>{html.escape(str(sp['review_snippet']))}</p>"

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{seo_title}</title>
  <meta name="description" content="{seo_desc}">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">{vertical_title} • {city}, {state}</p>
      <h1>{business}</h1>
      <p class="sub">{primary_offer}</p>
      {review_line}
      <div class="cta-row">
        <a class="btn btn-primary" href="#contact">{primary_cta}</a>
        {"<a class='btn' href='tel:" + phone + "'>Call " + phone + "</a>" if phone else ""}
      </div>
    </div>
  </header>

  <main class="wrap grid">
    <section class="card">
      <h2>Services</h2>
      <ul class="service-list">{services_html}</ul>
    </section>

    <section class="card">
      <h2>Why local customers choose us</h2>
      <p>Fast scheduling, clear estimates, and a simple path to get help without long forms or dead ends.</p>
      <ul class="checklist">
        <li>Mobile-first page speed</li>
        <li>Direct call and quote actions</li>
        <li>SEO-ready metadata</li>
        <li>Trust-focused layout</li>
      </ul>
    </section>

    <section class="card" id="contact">
      <h2>Request a quote</h2>
      <form id="quote-form" novalidate>
        <label>Name <input name="name" required></label>
        <label>Phone <input name="phone" inputmode="tel" required></label>
        <label>What do you need help with? <textarea name="message" rows="4" required></textarea></label>
        <button type="submit" class="btn btn-primary">{primary_cta}</button>
      </form>
      <p id="form-result" class="form-result" aria-live="polite"></p>
      {"<p>Email: <a href='mailto:" + email_addr + "'>" + email_addr + "</a></p>" if email_addr else ""}
      {"<p>Phone: <a href='tel:" + phone + "'>" + phone + "</a></p>" if phone else ""}
    </section>
  </main>

  <footer class="wrap footer">
    <p>{business} • {city}, {state}</p>
    <p>Preview generated by Citadel</p>
  </footer>

  <script src="app.js"></script>
</body>
</html>
"""
    css_doc = f""":root {{
  --bg: {colors['bg']};
  --text: {colors['text']};
  --primary: {colors['primary']};
  --accent: {colors['accent']};
  --card: #ffffff;
  --border: #e2e8f0;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  color: var(--text);
  background: var(--bg);
  line-height: 1.5;
}}
.wrap {{ width: min(1040px, calc(100% - 2rem)); margin: 0 auto; }}
.hero {{
  background: radial-gradient(circle at 15% 20%, rgba(14,165,233,.15), transparent 45%), linear-gradient(180deg, #fff, #f8fafc);
  border-bottom: 1px solid var(--border);
}}
.hero .wrap {{ padding: 3rem 0 2.5rem; }}
.eyebrow {{ margin: 0 0 .5rem; color: #475569; font-weight: 600; letter-spacing: .02em; }}
h1 {{ margin: 0; font-size: clamp(2rem, 4vw, 3rem); color: var(--primary); line-height: 1.05; }}
.sub {{ margin-top: .75rem; font-size: 1.1rem; color: #334155; max-width: 60ch; }}
.review {{ margin-top: .5rem; color: #0f172a; font-weight: 600; }}
.cta-row {{ margin-top: 1rem; display: flex; gap: .75rem; flex-wrap: wrap; }}
.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: .7rem 1rem;
  border-radius: .75rem;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--text);
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
}}
.btn-primary {{
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  padding: 1rem 0 2rem;
}}
.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 10px 24px rgba(15,23,42,.04);
}}
.card h2 {{ margin-top: 0; font-size: 1.05rem; color: #0f172a; }}
.service-list, .checklist {{ margin: .25rem 0 0; padding-left: 1rem; }}
label {{ display: block; margin-bottom: .75rem; font-weight: 600; }}
input, textarea {{
  width: 100%;
  margin-top: .25rem;
  border: 1px solid #cbd5e1;
  border-radius: .6rem;
  padding: .65rem .75rem;
  font: inherit;
}}
.form-result {{ min-height: 1.25rem; margin-top: .5rem; color: #0f766e; font-weight: 600; }}
.footer {{
  padding: 1rem 0 2rem;
  color: #475569;
  border-top: 1px solid var(--border);
}}
@media (prefers-reduced-motion: no-preference) {{
  .card {{ transition: transform .15s ease, box-shadow .15s ease; }}
  .card:hover {{ transform: translateY(-2px); box-shadow: 0 14px 30px rgba(15,23,42,.08); }}
}}
"""
    js_doc = """const form = document.getElementById('quote-form');
const result = document.getElementById('form-result');
if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const fd = new FormData(form);
    const payload = Object.fromEntries(fd.entries());
    localStorage.setItem('citadel_quote_form', JSON.stringify(payload));
    result.textContent = 'Quote request captured locally. Connect a backend or webhook to send it live.';
    form.reset();
  });
}
"""
    robots = "User-agent: *\nAllow: /\n"

    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")
    (out_dir / "styles.css").write_text(css_doc, encoding="utf-8")
    (out_dir / "app.js").write_text(js_doc, encoding="utf-8")
    (out_dir / "robots.txt").write_text(robots, encoding="utf-8")

    size_bytes = sum(p.stat().st_size for p in out_dir.iterdir() if p.is_file())
    lighthouse_est = {
        "performance": 90,
        "accessibility": 94,
        "best_practices": 96,
        "seo": 97,
    }
    if not builder_input.get("phone"):
        lighthouse_est["seo"] -= 2
    if not builder_input.get("email"):
        lighthouse_est["best_practices"] -= 1

    manifest = {
        "lead_slug": builder_input["lead_slug"],
        "build_dir": str(out_dir),
        "entrypoint": "index.html",
        "artifacts": ["index.html", "styles.css", "app.js", "robots.txt"],
        "preview_url": out_dir.joinpath("index.html").resolve().as_uri(),
        "qa_notes": "Static preview generated and file set written locally.",
        "build_sha": f"{random.getrandbits(64):016x}",
        "lighthouse_estimate": lighthouse_est,
        "size_bytes": size_bytes,
    }
    return manifest


def make_compliance_footer(cfg: RuntimeConfig) -> str:
    return (
        f"Sent by {cfg.brand_name} on behalf of {cfg.brand_from_name}. "
        f"Mailing address: {cfg.brand_postal_address}. "
        f"Reply \"stop\" or email {cfg.brand_optout_email} to opt out."
    )


def make_outreach_payload(q: dict[str, Any], manifest: dict[str, Any], cfg: RuntimeConfig) -> dict[str, Any]:
    weak = q["weakness_summary"]
    subject = f"{q['business_name']}: quick fix to capture more {q['city']} quote requests"
    preview_text = f"Built a faster quote-first page concept for {q['business_name']} based on public website signals."
    cta_url = manifest["preview_url"]
    footer = make_compliance_footer(cfg)

    beats = {
        "pattern_break": f"I audited {q['business_name']}'s public site and rebuilt the quote path into a cleaner one-page version with direct CTA placement.",
        "cost_of_inaction": f"Right now, weak conversion signals ({weak.lower()}) likely leak high-intent visitors before they call or submit a quote.",
        "belief_shift": f"The fastest win is usually not more traffic. It is a tighter page that converts the traffic you already paid for.",
        "mechanism": f"I generated a local preview with mobile-first layout, click-to-call, quote capture, and SEO metadata tailored to {q['city']}, {q['state']}.",
        "proof_unit": f"Your preview is live locally right now: {cta_url}. It includes a direct quote form and trust-first structure.",
        "offer": "If you want, I can deploy this version and wire the form into your inbox/CRM without changing your current domain until you approve.",
        "action": "Reply with 'send live' and the best email for quote notifications, and I will package the deployment plan.",
    }

    text_body = textwrap.dedent(f"""
    Hi {q['business_name']} team,

    I checked your public website and rebuilt the quote path into a cleaner, faster one-page version.

    What I noticed:
    - {q['weakness_summary']}
    - Opportunity score: {q['opportunity_score']}/10 for conversion lift
    - Market density signal: {q.get('market_establishments', 0)} similar businesses in your county

    Why this matters:
    Most local service businesses lose leads from friction (buried CTAs, weak mobile layout, no direct contact path), not from lack of demand.

    What I built:
    - Mobile-first service page
    - Direct quote CTA and call action
    - SEO title/description for {q['city']}, {q['state']}
    - Trust-first layout with social proof placement

    Preview:
    {cta_url}

    If you want, reply "send live" and I will package deployment + inbox wiring next.

    {footer}
    """).strip()

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#111827;line-height:1.5">
      <p>Hi {html.escape(q['business_name'])} team,</p>
      <p>I checked your public website and rebuilt the quote path into a cleaner, faster one-page version.</p>
      <ul>
        <li>{html.escape(q['weakness_summary'])}</li>
        <li>Opportunity score: {q['opportunity_score']}/10</li>
        <li>Market density signal: {int(q.get('market_establishments', 0))} local businesses</li>
      </ul>
      <p>Preview: <a href="{html.escape(cta_url)}">{html.escape(cta_url)}</a></p>
      <p>Reply <strong>send live</strong> and I will package deployment + inbox wiring next.</p>
      <p style="font-size:12px;color:#475569">{html.escape(footer)}</p>
    </body></html>
    """.strip()

    outreach = {
        "lead_slug": q["lead_slug"],
        "channel": "email",
        "to_email": q.get("email"),
        "subject": subject,
        "preview_text": preview_text,
        "body_text": text_body,
        "body_html": html_body,
        "cta_url": cta_url,
        "compliance_footer": footer,
        "disclosures_included": True,
        "beat_audit": beats,
        "beat_compliance_warning": [],
    }
    return outreach


def deploy_local_fs(manifest: dict[str, Any], lead_slug: str) -> dict[str, Any]:
    source_dir = Path(manifest["build_dir"]).resolve()
    dest_dir = (WORKSPACE_DIR / "deploys" / lead_slug).resolve()
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(source_dir, dest_dir)
    return {
        "provider": "local_fs",
        "success": True,
        "preview_url": manifest["preview_url"],
        "live_url": dest_dir.joinpath("index.html").as_uri(),
        "external_ref": f"local-{lead_slug}-{int(time.time())}",
    }


def send_email_local_outbox(outreach: dict[str, Any], cfg: RuntimeConfig) -> dict[str, Any]:
    msg = EmailMessage()
    msg["From"] = f"{cfg.brand_from_name} <{cfg.brand_from_email}>"
    to_email = outreach.get("to_email") or cfg.brand_from_email
    msg["To"] = to_email
    msg["Subject"] = outreach["subject"]
    msg.set_content(outreach["body_text"])
    if outreach.get("body_html"):
        msg.add_alternative(outreach["body_html"], subtype="html")

    ts = int(time.time())
    out_path = WORKSPACE_DIR / "outbox" / f"{outreach['lead_slug']}-{ts}.eml"
    out_path.write_bytes(bytes(msg))
    return {"backend": "local_outbox", "external_ref": out_path.name, "to_email": to_email, "path": str(out_path)}


def send_email_smtp(outreach: dict[str, Any], cfg: RuntimeConfig) -> dict[str, Any]:
    if not (cfg.smtp_host and cfg.smtp_from_email):
        raise RuntimeError("SMTP backend selected but SMTP_HOST/SMTP_FROM_EMAIL not configured")
    msg = EmailMessage()
    msg["From"] = f"{cfg.brand_from_name} <{cfg.smtp_from_email}>"
    msg["To"] = outreach.get("to_email") or cfg.smtp_from_email
    msg["Subject"] = outreach["subject"]
    msg.set_content(outreach["body_text"])
    if outreach.get("body_html"):
        msg.add_alternative(outreach["body_html"], subtype="html")

    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as smtp:
        if cfg.smtp_use_tls:
            smtp.starttls()
        if cfg.smtp_username:
            smtp.login(cfg.smtp_username, cfg.smtp_password)
        smtp.send_message(msg)

    return {"backend": "smtp", "external_ref": f"smtp-{int(time.time())}", "to_email": msg["To"]}


def run_pipeline(
    target_url: str,
    *,
    dry_run: bool,
    approve: bool,
    send_email: bool,
) -> dict[str, Any]:
    ensure_dirs()
    cfg = RuntimeConfig.from_env()
    setup_logging(cfg.log_path)

    db = LeadQueueDB(cfg.db_path)
    db.init_db()
    schemas = load_schemas()
    market = load_market_weights()

    run_id = f"run-{int(time.time())}"
    scout = scout_website(target_url, cfg)
    qualified = qualify_lead(scout, market)
    validate_or_raise("qualifier_output", qualified, schemas)

    lead_row = db.upsert_lead(
        LeadUpsertPayload(
            lead_slug=qualified["lead_slug"],
            business_name=qualified["business_name"],
            vertical=qualified["vertical"],
            city=qualified["city"],
            state=qualified["state"],
            has_website=qualified["has_website"],
            website_url=qualified.get("website_url"),
            phone=qualified.get("phone"),
            email=qualified.get("email"),
            opportunity_score=int(qualified["opportunity_score"]),
            target=str(target_url),
            source_payload_json=json.dumps(qualified["source_payload"], separators=(",", ":"), sort_keys=True),
        ),
        run_id=run_id,
    )

    result: dict[str, Any] = {"run_id": run_id, "lead_slug": qualified["lead_slug"], "qualified": qualified}

    if qualified.get("disqualify_reason"):
        db.set_status(qualified["lead_slug"], "disqualified", actor="qualifier", run_id=run_id, payload={"reason": qualified["disqualify_reason"]})
        result["status"] = "disqualified"
        return result

    db.set_status(qualified["lead_slug"], "qualified", actor="qualifier", run_id=run_id)

    builder_input = build_builder_input(qualified)
    validate_or_raise("builder_input", builder_input, schemas)

    build_dir = WORKSPACE_DIR / "builds" / qualified["lead_slug"] / run_id
    manifest = render_site_files(builder_input, build_dir)
    validate_or_raise("build_manifest", manifest, schemas)
    db.record_build(
        qualified["lead_slug"],
        manifest["build_dir"],
        manifest["entrypoint"],
        manifest["artifacts"],
        manifest["qa_notes"],
        manifest["preview_url"],
        manifest=manifest,
        run_id=run_id,
    )
    db.set_status(qualified["lead_slug"], "built", actor="builder", run_id=run_id)

    outreach = make_outreach_payload(qualified, manifest, cfg)
    validate_or_raise("outreach_output", outreach, schemas)
    outreach_id = db.record_outreach_draft(
        qualified["lead_slug"],
        outreach["subject"],
        outreach["body_text"],
        to_email=outreach.get("to_email"),
        body_html=outreach.get("body_html"),
        compliance_footer=outreach.get("compliance_footer"),
        beat_audit=outreach.get("beat_audit"),
        payload=outreach,
        run_id=run_id,
    )

    result["builder_input"] = builder_input
    result["build_manifest"] = manifest
    result["outreach"] = outreach
    result["outreach_id"] = outreach_id
    result["status"] = "built"

    if dry_run:
        return result

    if not approve:
        return result

    db.set_status(qualified["lead_slug"], "approved", actor="operator", run_id=run_id)

    deployment = None
    if cfg.deploy_enabled:
        if cfg.deploy_backend == "local_fs":
            deployment = deploy_local_fs(manifest, qualified["lead_slug"])
        else:
            raise RuntimeError(f"Unsupported DEPLOY_BACKEND: {cfg.deploy_backend}")
        db.record_deployment(
            qualified["lead_slug"],
            deployment["provider"],
            bool(deployment["success"]),
            deployment.get("live_url"),
            deployment.get("preview_url"),
            deployment.get("external_ref"),
            deployment,
            run_id=run_id,
        )
        if deployment["success"]:
            db.set_status(qualified["lead_slug"], "deployed", actor="deployer", run_id=run_id)

    result["deployment"] = deployment
    result["status"] = "deployed" if deployment and deployment.get("success") else result["status"]

    if send_email:
        if cfg.email_backend == "local_outbox":
            send_meta = send_email_local_outbox(outreach, cfg)
        elif cfg.email_backend == "smtp":
            send_meta = send_email_smtp(outreach, cfg)
        else:
            raise RuntimeError(f"Unsupported EMAIL_BACKEND: {cfg.email_backend}")
        db.mark_outreach_sent(outreach_id, send_meta["external_ref"], run_id=run_id, payload=send_meta)
        db.set_status(qualified["lead_slug"], "emailed", actor="mailer", run_id=run_id, payload={"outreach_id": outreach_id})
        result["email"] = send_meta
        result["status"] = "emailed"

    return result


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Citadel local pipeline orchestrator")
    parser.add_argument("target_url", help="Public website URL to scout/build/outreach against")
    parser.add_argument("--dry-run", action="store_true", help="Scout + qualify + build + draft outreach only")
    parser.add_argument("--approve", action="store_true", help="Approve the lead and run deployment backend")
    parser.add_argument("--send-email", action="store_true", help="Send outreach using configured EMAIL_BACKEND")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")
    args = parser.parse_args()

    result = run_pipeline(args.target_url, dry_run=args.dry_run, approve=args.approve, send_email=args.send_email)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"lead_slug": result["lead_slug"], "status": result["status"]}, indent=2))


if __name__ == "__main__":
    _cli()
