"""
Unified Control Dashboard for ReliantAI Platform.

Shows status of all services, pipeline metrics, and provides
control commands for the entire system.

Usage:
    python3 dashboard.py status      -- Show all service status
    python3 dashboard.py pipeline    -- Show prospect pipeline
    python3 dashboard.py prospect    -- Add a prospect
    python3 dashboard.py outreach    -- Generate outreach for a prospect
    python3 dashboard.py seed        -- Seed demo prospects
    python3 dashboard.py agent       -- Run agent cycle
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from reliantai.agents.core.prospect_engine import ProspectEngine


API_URL = os.environ.get("API_URL", "http://localhost:8000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
PROSPECT_DB = os.path.expanduser(os.environ.get("PROSPECT_DB", "~/.local/share/reliantai/prospects.db"))
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://reliantai@localhost:5433/reliantai"
)


def check_service(name: str, url: str, timeout: int = 3) -> dict:
    """Check if a service is reachable via HTTP."""
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return {"name": name, "url": url, "status": "UP", "code": resp.status}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        return {"name": name, "url": url, "status": "DOWN", "error": str(e)[:80]}


def check_redis() -> dict:
    """Check if Redis is reachable via PING."""
    try:
        import redis
        rc = redis.Redis.from_url(REDIS_URL)
        rc.ping()
        return {"name": "Redis", "url": REDIS_URL.split("@")[-1], "status": "UP", "code": 200}
    except (ImportError, Exception) as e:
        return {"name": "Redis", "url": "localhost:6379", "status": "DOWN", "error": str(e)[:80]}


def check_postgres() -> dict:
    """Check if PostgreSQL is reachable."""
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return {"name": "PostgreSQL", "url": "localhost:5433", "status": "UP", "code": 200}
    except (ImportError, Exception) as e:
        return {"name": "PostgreSQL", "url": "localhost:5433", "status": "DOWN", "error": str(e)[:80]}


def status():
    """Show status of all services."""
    print("=" * 60)
    print("  RELIANTAI CONTROL DASHBOARD")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    services = [
        check_service("API", f"{API_URL}/health"),
        check_service("Frontend", FRONTEND_URL),
        check_redis(),
        check_postgres(),
    ]

    print("\n--- Services ---")
    for s in services:
        icon = "✅" if s["status"] == "UP" else "❌"
        print(f"  {icon} {s['name']:15s} {s['url']:30s} {s['status']}")

    # Pipeline summary
    print("\n--- Prospect Pipeline ---")
    try:
        engine = ProspectEngine(db_path=PROSPECT_DB)
        summary = engine.get_pipeline_summary()
        print(f"  Total prospects: {summary['total_prospects']}")
        print(f"  Avg score: {summary['avg_score']}")
        print(f"  Total value: ${summary['total_value']:,.0f}")
        print(f"\n  By stage:")
        for stage, data in summary["by_stage"].items():
            if data["count"] > 0:
                print(f"    {stage:15s} {data['count']:3d}  (${data['value']:>10,.0f})")
    except Exception as e:
        print(f"  Error: {e}")

    # Hot prospects
    print("\n--- Hot Prospects (score >= 80) ---")
    try:
        engine = ProspectEngine(db_path=PROSPECT_DB)
        hot = engine.get_hot_prospects()
        if not hot:
            print("  No hot prospects yet. Run 'seed' to add demo data.")
        for p in hot[:5]:
            print(f"  🔥 {p.company_name:30s} score={p.score:5.1f}  ${p.estimated_value:>10,.0f}  {p.trade}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60)


def pipeline():
    """Show full pipeline details."""
    engine = ProspectEngine(db_path=PROSPECT_DB)
    summary = engine.get_pipeline_summary()

    print("=" * 60)
    print("  PROSPECT PIPELINE")
    print("=" * 60)
    print(f"\n  Total: {summary['total_prospects']} | Avg Score: {summary['avg_score']} | Value: ${summary['total_value']:,.0f}")

    for stage in ["new", "contacted", "qualified", "negotiation", "closed_won", "closed_lost", "nurture"]:
        data = summary["by_stage"].get(stage, {"count": 0, "value": 0})
        if data["count"] > 0:
            print(f"\n  [{stage.upper()}] ({data['count']} prospects, ${data['value']:,.0f})")
            prospects = engine.get_prospects(stage=stage)
            for p in prospects:
                print(f"    {p.company_name:35s} score={p.score:5.1f}  {p.trade:10s}  ${p.estimated_value:>10,.0f}")


def seed():
    """Seed demo prospects."""
    engine = ProspectEngine(db_path=PROSPECT_DB)
    ids = engine.seed_demo_prospects()
    print(f"Seeded {len(ids)} demo prospects.")
    summary = engine.get_pipeline_summary()
    print(f"Pipeline: {summary['total_prospects']} prospects, ${summary['total_value']:,.0f} total value")


def prospect(company: str = "", trade: str = "", city: str = "", state: str = "",
             email: str = "", phone: str = "", website: str = "", value: float = 0):
    """Add a prospect to the pipeline."""
    from reliantai.agents.core.prospect_engine import Prospect

    engine = ProspectEngine(db_path=PROSPECT_DB)
    p = Prospect(
        company_name=company,
        trade=trade,
        city=city,
        state=state,
        contact_email=email,
        contact_phone=phone,
        website=website,
        estimated_value=value,
    )
    pid = engine.add_prospect(p)
    print(f"Added: {company} (ID: {pid}, Score: {p.score})")


def outreach(prospect_id: int, stage: str = "first_contact"):
    """Generate outreach for a prospect."""
    engine = ProspectEngine(db_path=PROSPECT_DB)
    msg = engine.generate_outreach(prospect_id, stage)
    if msg:
        print(f"Outreach generated ({len(msg)} chars):")
        print(f"  {msg}")
    else:
        print("No template found for this prospect's trade/stage.")


def main():
    if len(sys.argv) < 2:
        status()
        return

    cmd = sys.argv[1]

    if cmd == "status":
        status()
    elif cmd == "pipeline":
        pipeline()
    elif cmd == "seed":
        seed()
    elif cmd == "prospect":
        args: dict[str, str] = {}
        i = 2
        while i < len(sys.argv):
            if sys.argv[i].startswith("--") and i + 1 < len(sys.argv):
                args[sys.argv[i][2:]] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        val = float(args.pop("value", "0"))
        prospect(**args, value=val)
    elif cmd == "outreach":
        pid = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        stage = sys.argv[3] if len(sys.argv) > 3 else "first_contact"
        outreach(pid, stage)
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: status, pipeline, seed, prospect, outreach")


if __name__ == "__main__":
    main()
