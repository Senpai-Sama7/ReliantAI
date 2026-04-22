#!/usr/bin/env python3
"""
Autonomous Lead Pipeline
========================
Reads Lindy AI CSVs, scores every lead, imports into Ops Intelligence,
and prints a prioritized action plan.

Run:
    python tools/lead_pipeline.py [--api http://localhost:8095] [--dry-run]

Cron (run daily at 8am):
    0 8 * * * cd /path/to/ops-intelligence && python tools/lead_pipeline.py >> logs/leads.log 2>&1
"""

import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────
OPS_API = os.getenv("OPS_API_URL", "http://localhost:8095")

# Lindy AI lead file locations (relative to workspace root)
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]  # goes up to /home/donovan/Projects
LEAD_SOURCES = [
    {
        "path": WORKSPACE_ROOT / "products" / "lindy_ai" / "hvac_leads.csv",
        "product_line": "hvac",
        "deal_value": 300.0,   # avg annual value per HVAC client ($15/dispatch * 20 jobs)
        "schema": "hvac",
    },
    {
        "path": WORKSPACE_ROOT / "products" / "lindy_ai" / "pipeline_data.csv",
        "product_line": "enterprise",
        "deal_value": 5000.0,
        "schema": "enterprise",
    },
    {
        "path": WORKSPACE_ROOT / "products" / "lindy_ai" / "smb_leads.csv",
        "product_line": "hvac",
        "deal_value": 150.0,
        "schema": "smb",
    },
]


# ── Lead scoring ──────────────────────────────────────────────────────────────

def score_hvac_lead(row: dict) -> float:
    """HVAC scoring: rating quality + review volume + website credibility."""
    raw_rating = row.get("rating", "0")
    # Rating may be "4.8 (260)" — extract numeric
    try:
        rating = float(str(raw_rating).split("(")[0].strip())
    except ValueError:
        rating = 0.0

    review_count = 0
    if "(" in str(raw_rating):
        try:
            review_count = int(str(raw_rating).split("(")[1].rstrip(")").strip())
        except ValueError:
            pass

    has_website = str(row.get("website", "")).strip().lower() not in ("none", "", "unknown", "facebook only")
    return round(
        min(100, rating * 15 + math.log1p(review_count) * 4 + (10 if has_website else 0)), 2
    )


def score_enterprise_lead(row: dict) -> float:
    """Enterprise scoring: deal value + probability."""
    value = float(row.get("value", 0) or 0)
    prob = float(row.get("probability", 0) or 0)
    return round(min(100, value / 100 + prob * 20), 2)


def parse_hvac_row(row: dict, deal_value: float) -> dict:
    raw_rating = row.get("rating", "0")
    try:
        rating = float(str(raw_rating).split("(")[0].strip())
    except ValueError:
        rating = 0.0
    review_count = 0
    if "(" in str(raw_rating):
        try:
            review_count = int(str(raw_rating).split("(")[1].rstrip(")").strip())
        except ValueError:
            pass
    has_website = str(row.get("website", "")).strip().lower() not in ("none", "", "unknown", "facebook only")
    return {
        "external_id": str(row.get("id", "")),
        "company": row.get("company", "").strip(),
        "phone": row.get("phone", "").strip(),
        "city": row.get("city", "").strip(),
        "rating": rating,
        "review_count": review_count,
        "has_website": has_website,
        "deal_value": deal_value,
        "product_line": "hvac",
        "source": "lindy_ai_csv",
    }


def parse_enterprise_row(row: dict, deal_value: float) -> dict:
    return {
        "external_id": str(row.get("id", "")),
        "company": row.get("company", "").strip(),
        "contact_name": row.get("contact", "").strip(),
        "notes": f"Role: {row.get('role', '')} | Status: {row.get('status', '')}",
        "deal_value": float(row.get("value", deal_value) or deal_value),
        "product_line": "enterprise",
        "source": "lindy_ai_pipeline",
    }


def parse_smb_row(row: dict, deal_value: float) -> dict:
    # Use hvac parser as fallback
    result = parse_hvac_row(row, deal_value)
    result["product_line"] = "hvac"
    return result


PARSERS = {
    "hvac": (parse_hvac_row, score_hvac_lead),
    "enterprise": (parse_enterprise_row, score_enterprise_lead),
    "smb": (parse_smb_row, score_hvac_lead),
}


# ── Import ────────────────────────────────────────────────────────────────────

def import_csv(source: dict, dry_run: bool = False) -> list[dict]:
    path: Path = source["path"]
    if not path.exists():
        print(f"  [SKIP] File not found: {path}")
        return []

    parse_fn, score_fn = PARSERS[source["schema"]]
    leads = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("company", "").strip():
                continue
            parsed = parse_fn(row, source["deal_value"])
            parsed["lead_score"] = score_fn(row)
            leads.append(parsed)

    leads.sort(key=lambda x: x["lead_score"], reverse=True)

    if dry_run:
        print(f"  [DRY RUN] Would import {len(leads)} leads from {path.name}")
        return leads

    resp = requests.post(f"{OPS_API}/api/revenue/leads/import", json={"leads": leads}, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    print(f"  Imported {result['imported']} leads from {path.name}")
    return leads


def print_action_plan(all_leads: list[dict]) -> None:
    """Print prioritized outreach action plan."""
    top = sorted(all_leads, key=lambda x: x["lead_score"], reverse=True)[:10]

    print()
    print("═" * 60)
    print(" AUTONOMOUS LEAD ACTION PLAN")
    print(f" Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("═" * 60)
    print()

    for i, lead in enumerate(top, 1):
        score = lead.get("lead_score", 0)
        priority = "🔴 CONTACT NOW" if score >= 80 else "🟡 HIGH" if score >= 60 else "🟢 MEDIUM"
        company = lead.get("company", "Unknown")
        phone = lead.get("phone", "N/A")
        city = lead.get("city", "")
        product = lead.get("product_line", "").upper()
        value = lead.get("deal_value", 0)

        print(f"  {i:2}. [{priority}] {company}")
        print(f"      Product: {product} | Score: {score:.0f}/100 | Est. Value: ${value:.0f}/yr")
        if phone:
            print(f"      Phone: {phone}")
        if city:
            print(f"      City: {city}")
        if lead.get("contact_name"):
            print(f"      Contact: {lead['contact_name']}")
        print()

    print("─" * 60)
    hvac_count = sum(1 for l in all_leads if l.get("product_line") == "hvac")
    ent_count = sum(1 for l in all_leads if l.get("product_line") == "enterprise")
    total_value = sum(l.get("deal_value", 0) for l in all_leads)
    print(f"  HVAC leads: {hvac_count} | Enterprise leads: {ent_count}")
    print(f"  Total pipeline value if all won: ${total_value:,.0f}/yr")
    print(f"  Top 10 expected value (avg 20% close): ${total_value * 0.20 / len(all_leads) * 10:,.0f}/yr")
    print("═" * 60)


def get_health_status() -> None:
    """Print income health status from ops-intelligence."""
    try:
        resp = requests.get(f"{OPS_API}/api/revenue/health", timeout=5)
        health = resp.json()
        status_icon = "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "warning" else "🚨"
        print(f"\n  Income Health: {status_icon} {health['status'].upper()}")
        print(f"  Revenue (30d): ${health['revenue_30d']:,.2f}")
        print(f"  Revenue (7d):  ${health['revenue_7d']:,.2f}")
        print(f"  Pipeline:      ${health['pipeline_value']:,.2f}")
        if health["signals"]:
            for s in health["signals"]:
                icon = "🚨" if s["severity"] == "HIGH" else "⚠️"
                print(f"  {icon} {s['message']}")
    except Exception as e:
        print(f"\n  [Health check failed: {e}]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    global OPS_API  # noqa: PLW0603
    parser = argparse.ArgumentParser(description="Autonomous Lead Pipeline")
    parser.add_argument("--api", default=OPS_API, help="Ops Intelligence API URL")
    parser.add_argument("--dry-run", action="store_true", help="Score leads without importing")
    args = parser.parse_args()
    OPS_API = args.api

    print(f"Autonomous Lead Pipeline — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"API: {OPS_API}")
    print()

    all_leads = []
    for source in LEAD_SOURCES:
        print(f"Processing: {source['path'].name} ({source['product_line']})")
        leads = import_csv(source, dry_run=args.dry_run)
        all_leads.extend(leads)

    if all_leads:
        print_action_plan(all_leads)

    if not args.dry_run:
        get_health_status()

    print()
    print("Done. Run with --dry-run to preview without importing.")


if __name__ == "__main__":
    main()
