#!/usr/bin/env python3
"""
Autonomous Revenue Watchdog
===========================
Runs continuously (or on a cron). Monitors income health and fires alerts
when revenue signals go bad.

Run as daemon:
    python tools/revenue_watchdog.py --interval 3600

Cron (hourly):
    0 * * * * cd /path/to/ops-intelligence && python tools/revenue_watchdog.py --once >> logs/watchdog.log 2>&1
"""

import argparse
import os
import sys
import time
import json
import requests
from datetime import datetime, timezone

OPS_API = os.getenv("OPS_API_URL", "http://localhost:8095")

# Alert thresholds
REVENUE_DROP_THRESHOLD_PCT = 50   # alert if 7d revenue < 50% of 30d average daily
DISPATCH_RATE_MIN = 1             # minimum dispatches per day to be considered healthy


def check_income_health() -> dict:
    resp = requests.get(f"{OPS_API}/api/revenue/health", timeout=10)
    resp.raise_for_status()
    return resp.json()


def check_global_summary() -> dict:
    resp = requests.get(f"{OPS_API}/api/summary", timeout=10)
    resp.raise_for_status()
    return resp.json()


def format_alert(signal: dict) -> str:
    icon = "🚨" if signal["severity"] == "HIGH" else "⚠️"
    return f"{icon} [{signal['severity']}] {signal['message']}"


def send_alert(message: str, severity: str = "HIGH") -> None:
    """
    Alert channel: stdout (+ can extend to Slack/email/PagerDuty).
    To add Slack: set SLACK_WEBHOOK_URL env var.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    formatted = f"[{ts}] REVENUE WATCHDOG {severity}: {message}"
    print(formatted)

    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    if slack_url:
        try:
            requests.post(slack_url, json={"text": formatted}, timeout=5)
        except (requests.TimeoutException, requests.RequestError) as e:
            print(f"  [Slack alert failed: {e}]")

    pagerduty_key = os.getenv("PAGERDUTY_ROUTING_KEY")
    if pagerduty_key and severity == "HIGH":
        try:
            requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json={
                    "routing_key": pagerduty_key,
                    "event_action": "trigger",
                    "payload": {
                        "summary": message,
                        "severity": "critical" if severity == "HIGH" else "warning",
                        "source": "ops-intelligence-watchdog",
                    },
                },
                timeout=5,
            )
        except (requests.TimeoutException, requests.RequestError) as e:
            print(f"  [PagerDuty alert failed: {e}]")


def run_checks() -> bool:
    """Returns True if all checks passed (healthy)."""
    all_healthy = True
    ts = datetime.now(timezone.utc).strftime("%H:%M UTC")

    try:
        health = check_income_health()
    except requests.TimeoutException:
        send_alert("ops-intelligence API timeout", "HIGH")
        return False
    except (requests.HTTPError, requests.RequestError) as e:
        send_alert(f"Cannot reach ops-intelligence API: {e}", "HIGH")
        return False
    except (ValueError, KeyError) as e:
        send_alert(f"Invalid API response: {e}", "HIGH")
        return False

    # Print status line
    icon = "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "warning" else "🚨"
    print(f"[{ts}] Income health: {icon} {health['status'].upper()} | "
          f"7d revenue: ${health['revenue_7d']:.2f} | "
          f"30d revenue: ${health['revenue_30d']:.2f} | "
          f"pipeline: ${health['pipeline_value']:.2f}")

    # Fire alerts for each signal
    for signal in health.get("signals", []):
        send_alert(signal["message"], signal["severity"])
        all_healthy = False

    # Extra check: revenue velocity drop
    if health["revenue_30d"] > 0:
        daily_avg_30d = health["revenue_30d"] / 30
        daily_avg_7d = health["revenue_7d"] / 7
        if daily_avg_7d < daily_avg_30d * (1 - REVENUE_DROP_THRESHOLD_PCT / 100):
            send_alert(
                f"Revenue velocity dropped {REVENUE_DROP_THRESHOLD_PCT}%+: "
                f"7d avg ${daily_avg_7d:.2f}/day vs 30d avg ${daily_avg_30d:.2f}/day",
                "HIGH"
            )
            all_healthy = False

    # Check overdue invoices
    if health.get("overdue_invoices", 0) > 0:
        send_alert(
            f"{health['overdue_invoices']} overdue invoice(s) — cash flow at risk",
            "HIGH"
        )
        all_healthy = False

    return all_healthy


def main():
    parser = argparse.ArgumentParser(description="Revenue Watchdog")
    parser.add_argument("--api", default=OPS_API)
    parser.add_argument("--interval", type=int, default=3600,
                        help="Check interval in seconds (default: 3600 = 1hr)")
    parser.add_argument("--once", action="store_true",
                        help="Run once and exit (for cron use)")
    args = parser.parse_args()

    global OPS_API
    OPS_API = args.api

    print(f"Revenue Watchdog starting — interval: {args.interval}s | API: {OPS_API}")

    if args.once:
        healthy = run_checks()
        sys.exit(0 if healthy else 1)

    while True:
        try:
            run_checks()
        except KeyboardInterrupt:
            print("\nWatchdog stopped.")
            break
        except (requests.RequestError, ValueError, KeyError) as e:
            print(f"[ERROR] Check failed: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
