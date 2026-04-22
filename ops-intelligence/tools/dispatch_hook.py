#!/usr/bin/env python3
"""
Dispatch Revenue Hook
=====================
Called by Money/dispatch service (or an event bus subscriber) when a dispatch
completes. Records the billable event and auto-generates an invoice.

Usage (from Money after dispatch completes):
    python tools/dispatch_hook.py --lead-id <id> --reference <dispatch_id> --company "HVAC Co"

Subscribe mode (listens on **Redis** for the same pub/sub channels the integration
Event Bus uses — ``events:*`` — **not** HTTP):
    python tools/dispatch_hook.py --subscribe

Env:
    OPS_API_URL          — ops-intelligence backend (default http://localhost:8095)
    REDIS_HOST / REDIS_PORT / REDIS_PASSWORD — must match the integration Event Bus Redis
    HVAC_DISPATCH_RATE   — default 15.00
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import requests

OPS_API = os.getenv("OPS_API_URL", "http://localhost:8095")
HVAC_DISPATCH_RATE = float(os.getenv("HVAC_DISPATCH_RATE", "15.00"))

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None


def record_dispatch(lead_id: str, reference_id: str, company: str, notes: str = "") -> dict:
    """Record one completed dispatch as a billable revenue event + auto-invoice."""
    # 1. Record revenue event
    resp = requests.post(
        f"{OPS_API}/api/revenue/events/dispatch",
        params={
            "lead_id": lead_id,
            "reference_id": reference_id,
            "notes": notes,
        },
        timeout=10,
    )
    resp.raise_for_status()
    event = resp.json()
    print(f"  Revenue event recorded: ${event['amount']:.2f} for dispatch {reference_id}")

    # 2. Auto-generate invoice
    if company:
        invoice_resp = requests.post(
            f"{OPS_API}/api/revenue/invoices",
            json={
                "lead_id": lead_id,
                "company": company,
                "line_items": [
                    {
                        "description": f"HVAC Dispatch — {notes or reference_id}",
                        "quantity": 1,
                        "unit_price": HVAC_DISPATCH_RATE,
                    }
                ],
            },
            timeout=10,
        )
        invoice_resp.raise_for_status()
        inv = invoice_resp.json()
        print(f"  Invoice created: {inv['id']} — ${inv['subtotal']:.2f} (due {inv['due_date'][:10]})")
        return {"event": event, "invoice": inv}

    return {"event": event}


def subscribe_to_event_bus() -> None:
    """
    Subscribe to Redis channel pattern ``events:*`` (same as integration Event Bus).

    The HTTP Event Bus does not expose GET /events; it publishes JSON to Redis.
    """
    try:
        import redis
    except ImportError:
        print(
            "ERROR: install redis: pip install redis",
            file=sys.stderr,
        )
        sys.exit(1)

    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
    )
    pubsub = r.pubsub()
    pubsub.psubscribe("events:*")
    print(
        f"Listening on Redis {REDIS_HOST}:{REDIS_PORT} pattern events:* "
        "for dispatch.completed ..."
    )

    for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue
        try:
            raw = message["data"]
            data = json.loads(raw)
            meta = data.get("metadata") or {}
            event_type = meta.get("event_type")
            if event_type != "dispatch.completed":
                continue
            payload = data.get("payload") or {}
            dispatch_id = payload.get("dispatch_id") or meta.get("event_id", "")
            record_dispatch(
                lead_id=str(payload.get("lead_id", "")),
                reference_id=str(dispatch_id),
                company=str(payload.get("company", "")),
                notes=str(payload.get("description", "")),
            )
        except Exception as e:
            print(f"  [handler error: {e}]")


def main():
    global OPS_API
    parser = argparse.ArgumentParser(description="Dispatch Revenue Hook")
    parser.add_argument("--api", default=OPS_API)
    parser.add_argument("--lead-id", default="", help="Revenue lead ID")
    parser.add_argument("--reference", default="", help="Dispatch job reference ID")
    parser.add_argument("--company", default="", help="HVAC company name")
    parser.add_argument("--notes", default="", help="Job notes")
    parser.add_argument(
        "--subscribe",
        action="store_true",
        help="Run as Redis subscriber (events:* → dispatch.completed)",
    )
    args = parser.parse_args()

    OPS_API = args.api

    if args.subscribe:
        subscribe_to_event_bus()
    else:
        if not args.reference:
            print("ERROR: --reference required for one-shot mode", file=sys.stderr)
            sys.exit(1)
        result = record_dispatch(args.lead_id, args.reference, args.company, args.notes)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
