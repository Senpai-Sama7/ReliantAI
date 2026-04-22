#!/usr/bin/env python3
import argparse
import hashlib
import hmac
import json
import time

import httpx

def main() -> None:
    p = argparse.ArgumentParser(description="Send a signed webhook event to the local Citadel dashboard.")
    p.add_argument("--url", default="http://127.0.0.1:8888/api/webhooks/openclaw")
    p.add_argument("--secret", required=True)
    p.add_argument("--event-type", required=True)
    p.add_argument("--lead-slug", required=True)
    p.add_argument("--event-id", required=True)
    p.add_argument("--payload", default="{}", help="JSON object with extra fields")
    args = p.parse_args()

    extra = json.loads(args.payload)
    payload = {"event_type": args.event_type, "lead_slug": args.lead_slug, "event_id": args.event_id, **extra}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ts = str(int(time.time()))
    sig = hmac.new(args.secret.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Citadel-Timestamp": ts,
        "X-Citadel-Signature": f"sha256={sig}",
    }
    with httpx.Client(timeout=15) as client:
        resp = client.post(args.url, content=raw, headers=headers)
    print(resp.status_code)
    print(resp.text)

if __name__ == "__main__":
    main()
