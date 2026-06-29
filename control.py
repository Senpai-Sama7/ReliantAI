"""
ReliantAI Natural Language Control Interface.

Provides intuitive, conversational control over the entire system.
Users can type natural language commands and the system understands
what they want to do.

Usage:
    python3 control.py                          # Interactive mode
    python3 control.py "show me hot prospects"  # Single command
    python3 control.py "add HVAC lead in Dallas" 
    python3 control.py "run prospector"
    python3 control.py "pipeline status"
    python3 control.py "generate outreach for prospect 1"
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from reliantai.agents.core.prospect_engine import ProspectEngine, Prospect

API_URL = os.environ.get("API_URL", "http://localhost:8000")
PROSPECT_DB = os.path.expanduser("~/.local/share/reliantai/prospects.db")


# ─── Intent Parser ───────────────────────────────────────────────

class Intent:
    """Parsed user intent."""
    def __init__(self, action: str, params: dict | None = None, raw: str = ""):
        self.action = action
        self.params = params or {}
        self.raw = raw

    def __repr__(self):
        return f"Intent({self.action}, {self.params})"


def parse_intent(text: str) -> Intent:
    """Parse natural language into a structured intent."""
    text_lower = text.lower().strip()

    # ── Status / Dashboard ──
    if any(w in text_lower for w in ["status", "dashboard", "overview", "how are things", "system status", "health"]):
        return Intent("status")

    # ── Pipeline ──
    if any(w in text_lower for w in ["pipeline", "prospects", "leads", "funnel"]):
        if any(w in text_lower for w in ["hot", "best", "top", "scored"]):
            return Intent("hot_prospects")
        if any(w in text_lower for w in ["warm", "medium"]):
            return Intent("warm_prospects")
        if any(w in text_lower for w in ["cold", "low", "nurture"]):
            return Intent("cold_prospects")
        if any(w in text_lower for w in ["summary", "stats", "metrics", "count"]):
            return Intent("pipeline_summary")
        return Intent("pipeline")

    # ── Advance / Move (before outreach to avoid "prospect" collision) ──
    if any(w in text_lower for w in ["advance", "move", "progress", "update stage", "next stage"]):
        pid = _extract_id(text_lower)
        stage = _extract_stage(text_lower)
        if pid:
            return Intent("advance_stage", {"prospect_id": pid, "stage": stage})
        return Intent("advance_help")

    # ── Outreach ──
    if any(w in text_lower for w in ["outreach", "message", "sms", "email", "reach out", "send"]):
        pid = _extract_id(text_lower)
        stage = _extract_stage(text_lower)
        if pid:
            return Intent("generate_outreach", {"prospect_id": pid, "stage": stage})
        return Intent("outreach_help")

    # ── Add Prospect ──
    if any(w in text_lower for w in ["add", "create", "new lead", "new prospect", "insert"]) or \
       (text_lower.startswith("new ") and any(t in text_lower for t in ["hvac", "plumbing", "electrical", "freight", "saas", "lead", "prospect"])):
        params = _extract_prospect_params(text)
        if params:
            return Intent("add_prospect", params)
        return Intent("add_prospect_help")

    # ── Seed / Demo ──
    if any(w in text_lower for w in ["seed", "demo", "sample", "test data", "populate"]):
        return Intent("seed")

    # ── Run Agent ──
    if any(w in text_lower for w in ["run", "start", "execute", "launch"]):
        agent = _extract_agent(text_lower)
        if agent:
            return Intent("run_agent", {"agent": agent})
        return Intent("run_agent_help")

    # ── Services ──
    if any(w in text_lower for w in ["restart", "stop", "start service"]):
        service = _extract_service(text_lower)
        if service:
            return Intent("service", {"service": service, "action": _extract_service_action(text_lower)})

    # ── Tests ──
    if any(w in text_lower for w in ["test", "tests", "run tests", "pytest"]):
        return Intent("run_tests")

    # ── Help ──
    if any(w in text_lower for w in ["help", "commands", "what can", "how do i", "usage"]):
        return Intent("help")

    # ── Templates ──
    if any(w in text_lower for w in ["template", "templates"]):
        return Intent("templates")

    # ── Quit ──
    if any(w in text_lower for w in ["quit", "exit", "bye", "done", "q"]):
        return Intent("quit")

    return Intent("unknown", {"raw": text})


def _extract_prospect_params(text: str) -> dict | None:
    """Extract prospect fields from natural language."""
    params: dict = {}

    # Company name — look for patterns like "called X" or "named X" or "for X"
    company_match = re.search(r'(?:called|named|for|company|business)\s+["\']?([A-Z][A-Za-z\s&\']+?)["\']?(?:\s+(?:in|at|from|with|that|which)|$)', text)
    if not company_match:
        # Try: "add X" where X starts with capital
        company_match = re.search(r'(?:add|create|new)\s+["\']?([A-Z][A-Za-z\s&\']+?)["\']?(?:\s+(?:in|at|from|with)|$)', text)
    if company_match:
        params["company"] = company_match.group(1).strip()

    # Trade
    for trade in ["hvac", "plumbing", "electrical", "roofing", "painting", "landscaping", "freight", "logistics", "saas", "pest_control", "locksmith"]:
        if trade in text.lower():
            params["trade"] = trade
            break

    # City
    city_match = re.search(r'(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
    if city_match:
        params["city"] = city_match.group(1)

    # State
    state_match = re.search(r',\s*([A-Z]{2})\b', text)
    if not state_match:
        state_match = re.search(r'(?:in|at)\s+[A-Z][a-z]+\s*\(?([A-Z]{2})\)?', text)
    if state_match:
        params["state"] = state_match.group(1)

    # Email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
    if email_match:
        params["email"] = email_match.group(0)

    # Phone
    phone_match = re.search(r'(\+?1?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', text)
    if phone_match:
        params["phone"] = phone_match.group(1)

    # Value
    value_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\b', text)
    if value_match and value_match.group(1):
        try:
            val = float(value_match.group(1).replace(",", ""))
            if "k" in text.lower() or "K" in text:
                val *= 1000
            params["value"] = val
        except ValueError:
            pass

    return params if params.get("company") or params.get("trade") else None


def _extract_id(text: str) -> int | None:
    """Extract a prospect ID from text."""
    match = re.search(r'(?:prospect|lead|id|#)\s*(\d+)', text)
    if match:
        return int(match.group(1))
    # Try standalone number
    match = re.search(r'\b(\d+)\b', text)
    if match:
        return int(match.group(1))
    return None


def _extract_stage(text: str) -> str:
    """Extract pipeline stage from text."""
    stages = {
        "first": "first_contact", "initial": "first_contact", "new": "first_contact",
        "followup": "followup_1", "follow up": "followup_1", "follow-up": "followup_1",
        "second": "followup_2", "third": "followup_3", "last": "followup_3",
        "contacted": "contacted", "qualified": "qualified",
        "negotiation": "negotiation", "negotiating": "negotiation",
        "won": "closed_won", "closed": "closed_won", "lost": "closed_lost",
        "nurture": "nurture",
    }
    for key, val in stages.items():
        if key in text:
            return val
    return "first_contact"


def _extract_agent(text: str) -> str | None:
    """Extract agent name from text."""
    agents = {
        "prospector": "prospector", "prospecting": "prospector", "find": "prospector",
        "outreach": "outreach", "messaging": "outreach",
        "followup": "followup", "follow-up": "followup", "follow up": "followup",
        "site_builder": "site_builder", "site builder": "site_builder", "builder": "site_builder",
        "all": "all",
    }
    for key, val in agents.items():
        if key in text:
            return val
    return None


def _extract_service(text: str) -> str | None:
    """Extract service name from text."""
    services = {
        "api": "api", "backend": "api", "server": "api",
        "frontend": "frontend", "next": "frontend", "nextjs": "frontend",
        "database": "database", "db": "database", "postgres": "database", "postgresql": "database",
        "redis": "redis",
    }
    for key, val in services.items():
        if key in text:
            return val
    return None


def _extract_service_action(text: str) -> str:
    if any(w in text for w in ["restart"]):
        return "restart"
    if any(w in text for w in ["stop", "kill"]):
        return "stop"
    if any(w in text for w in ["start", "launch"]):
        return "start"
    return "status"


# ─── Action Handlers ─────────────────────────────────────────────

def handle_intent(intent: Intent) -> str:
    """Execute an intent and return a human-readable response."""
    handlers = {
        "status": _handle_status,
        "pipeline": _handle_pipeline,
        "hot_prospects": _handle_hot_prospects,
        "warm_prospects": _handle_warm_prospects,
        "cold_prospects": _handle_cold_prospects,
        "pipeline_summary": _handle_pipeline_summary,
        "add_prospect": _handle_add_prospect,
        "add_prospect_help": _handle_add_prospect_help,
        "generate_outreach": _handle_generate_outreach,
        "outreach_help": _handle_outreach_help,
        "advance_stage": _handle_advance_stage,
        "advance_help": _handle_advance_help,
        "seed": _handle_seed,
        "run_agent": _handle_run_agent,
        "run_agent_help": _handle_run_agent_help,
        "service": _handle_service,
        "run_tests": _handle_run_tests,
        "templates": _handle_templates,
        "help": _handle_help,
        "unknown": _handle_unknown,
        "quit": lambda _: "Goodbye!",
    }
    handler = handlers.get(intent.action, _handle_unknown)
    return handler(intent)


def _handle_status(_: Intent) -> str:
    lines = ["=" * 50, "  RELIANTAI SYSTEM STATUS", f"  {datetime.now().strftime('%H:%M:%S')}", "=" * 50]

    # Services
    services = [
        ("API", f"{API_URL}/health"),
        ("Frontend", "http://localhost:3000"),
    ]
    for name, url in services:
        try:
            urllib.request.urlopen(url, timeout=2)
            lines.append(f"  ✅ {name}")
        except Exception:
            lines.append(f"  ❌ {name}")

    # Pipeline
    try:
        engine = ProspectEngine(db_path=PROSPECT_DB)
        summary = engine.get_pipeline_summary()
        lines.append(f"\n  Pipeline: {summary['total_prospects']} prospects | ${summary['total_value']:,.0f} | Avg score: {summary['avg_score']}")
    except Exception:
        lines.append("\n  Pipeline: unavailable")

    lines.append("=" * 50)
    return "\n".join(lines)


def _handle_pipeline(_: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    summary = engine.get_pipeline_summary()
    lines = ["PROSPECT PIPELINE", f"Total: {summary['total_prospects']} | Value: ${summary['total_value']:,.0f} | Avg: {summary['avg_score']}", ""]

    for stage in ["new", "contacted", "qualified", "negotiation", "closed_won", "closed_lost", "nurture"]:
        data = summary["by_stage"].get(stage, {"count": 0, "value": 0})
        if data["count"] > 0:
            lines.append(f"  [{stage.upper()}] {data['count']} prospects (${data['value']:,.0f})")
            prospects = engine.get_prospects(stage=stage)
            for p in prospects:
                lines.append(f"    #{p.id} {p.company_name} (score={p.score:.0f}, {p.trade}, ${p.estimated_value:,.0f})")
    return "\n".join(lines)


def _handle_hot_prospects(_: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    hot = engine.get_hot_prospects()
    if not hot:
        return "No hot prospects (score >= 80). Run 'seed' to add demo data."
    lines = [f"HOT PROSPECTS ({len(hot)} total)", ""]
    for p in hot:
        lines.append(f"  🔥 #{p.id} {p.company_name}")
        lines.append(f"     Score: {p.score:.0f} | Trade: {p.trade} | Location: {p.city}, {p.state}")
        lines.append(f"     Value: ${p.estimated_value:,.0f} | Stage: {p.stage}")
        if p.contact_email:
            lines.append(f"     Email: {p.contact_email}")
        lines.append("")
    return "\n".join(lines)


def _handle_warm_prospects(_: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    warm = engine.get_warm_prospects()
    if not warm:
        return "No warm prospects (score 60-79)."
    lines = [f"WARM PROSPECTS ({len(warm)} total)", ""]
    for p in warm:
        lines.append(f"  🟡 #{p.id} {p.company_name} (score={p.score:.0f}, {p.trade}, ${p.estimated_value:,.0f})")
    return "\n".join(lines)


def _handle_cold_prospects(_: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    cold = engine.get_cold_prospects()
    if not cold:
        return "No cold prospects (score 40-59)."
    lines = [f"COLD PROSPECTS ({len(cold)} total)", ""]
    for p in cold:
        lines.append(f"  🔵 #{p.id} {p.company_name} (score={p.score:.0f}, {p.trade}, ${p.estimated_value:,.0f})")
    return "\n".join(lines)


def _handle_pipeline_summary(_: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    summary = engine.get_pipeline_summary()
    lines = ["PIPELINE SUMMARY", ""]
    lines.append(f"  Total Prospects: {summary['total_prospects']}")
    lines.append(f"  Total Value:     ${summary['total_value']:,.0f}")
    lines.append(f"  Average Score:   {summary['avg_score']}")
    lines.append("")
    for stage in ["new", "contacted", "qualified", "negotiation", "closed_won", "closed_lost", "nurture"]:
        data = summary["by_stage"].get(stage, {"count": 0, "value": 0})
        if data["count"] > 0:
            lines.append(f"  {stage:15s} {data['count']:3d}  (${data['value']:>12,.0f})")
    return "\n".join(lines)


def _handle_add_prospect(intent: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    p = Prospect(
        company_name=intent.params.get("company", ""),
        trade=intent.params.get("trade", ""),
        city=intent.params.get("city", ""),
        state=intent.params.get("state", ""),
        contact_email=intent.params.get("email", ""),
        contact_phone=intent.params.get("phone", ""),
        estimated_value=intent.params.get("value", 0),
    )
    pid = engine.add_prospect(p)
    return f"✅ Added: {p.company_name} (ID: {pid}, Score: {p.score:.0f}, Value: ${p.estimated_value:,.0f})"


def _handle_add_prospect_help(_: Intent) -> str:
    return """To add a prospect, tell me something like:
  "add ABC HVAC in Houston, TX"
  "new plumbing lead called Bob's Plumbing in Dallas"
  "create prospect: CloudScale SaaS in San Francisco, $85k value"
  "add freight company FreightFlow in Atlanta with email ops@freightflow.com"""


def _handle_generate_outreach(intent: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    pid = intent.params["prospect_id"]
    stage = intent.params.get("stage", "first_contact")
    msg = engine.generate_outreach(pid, stage)
    if msg:
        return f"📨 Outreach for prospect #{pid} ({stage}):\n\n{msg}\n\n({len(msg)} chars)"
    return f"No template found. Check the prospect's trade and stage."


def _handle_outreach_help(_: Intent) -> str:
    return """To generate outreach, say:
  "generate outreach for prospect 1"
  "send first message to lead 3"
  "create follow-up for prospect 2"
  "email template for prospect 5"""


def _handle_advance_stage(intent: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    pid = intent.params["prospect_id"]
    stage = intent.params.get("stage")

    # Fetch the prospect before advancing to get its current name
    with engine._get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM prospects WHERE id = ?", (pid,)).fetchone()
        if not row:
            return f"Prospect #{pid} not found."
        company = row["company_name"]

    engine.advance_stage(pid, stage)

    # Fetch updated stage
    with engine._get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT stage FROM prospects WHERE id = ?", (pid,)).fetchone()
        new_stage = row["stage"] if row else "unknown"

    return f"✅ Advanced #{pid} ({company}) to: {new_stage}"


def _handle_advance_help(_: Intent) -> str:
    return """To advance a prospect, say:
  "advance prospect 1 to contacted"
  "move lead 3 to qualified"
  "mark prospect 2 as closed won"
  "progress lead 5" (auto-advances to next stage)"""


def _handle_seed(_: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    ids = engine.seed_demo_prospects()
    summary = engine.get_pipeline_summary()
    return f"✅ Seeded {len(ids)} demo prospects.\nPipeline: {summary['total_prospects']} prospects, ${summary['total_value']:,.0f} total value"


def _handle_run_agent(intent: Intent) -> str:
    agent = intent.params.get("agent", "all")
    return f"🚀 To run the {agent} agent, use:\n  agents-cli start {agent}\n\nOr run all agents:\n  agents-cli start"


def _handle_run_agent_help(_: Intent) -> str:
    return """Available agents:
  prospector   - Find new leads via Google Places
  outreach     - Send personalized first-contact messages
  followup     - Manage follow-up sequences
  site_builder - Build and register preview sites
  all          - Run all agents

Say "run prospector" or "start outreach agent"."""


def _handle_service(intent: Intent) -> str:
    service = intent.params.get("service", "")
    action = intent.params.get("action", "status")
    return f"Service control: {action} {service}\n\nUse system commands:\n  sudo service postgresql {action}\n  redis-cli ping\n  curl {API_URL}/health"


def _handle_run_tests(_: Intent) -> str:
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "reliantai/tests/", "reliantai/agents/tests/", "-q", "--tb=line"],
            capture_output=True, text=True, timeout=60,
            cwd=PROJECT_ROOT,
            env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return "❌ Tests timed out after 60 seconds"
    except FileNotFoundError:
        return "❌ pytest not found. Run: pip install pytest"

    output = result.stdout[-500:] if result.stdout else ""
    rc = result.returncode
    status = "✅ PASS" if rc == 0 else f"❌ FAIL (exit {rc})"
    return f"Tests: {status}\n{output}"


def _handle_templates(_: Intent) -> str:
    engine = ProspectEngine(db_path=PROSPECT_DB)
    templates = engine.get_templates()
    lines = [f"OUTREACH TEMPLATES ({len(templates)} total)", ""]
    for t in templates:
        lines.append(f"  [{t['vertical']}/{t['channel']}] {t['name']} ({t['stage']})")
        body_preview = t['body'][:60].replace('\n', ' ')
        lines.append(f"    {body_preview}...")
        lines.append("")
    return "\n".join(lines)


def _handle_help(_: Intent) -> str:
    return """RELIANTAI CONTROL — Natural Language Commands

STATUS & MONITORING:
  "status" / "dashboard" / "how are things"
  "pipeline" / "show prospects"
  "hot prospects" / "top leads"
  "pipeline summary" / "stats"

PROSPECT MANAGEMENT:
  "add [company] in [city], [state]"
  "new [trade] lead called [name]"
  "seed" / "load demo data"

OUTREACH:
  "generate outreach for prospect [id]"
  "send first message to lead [id]"
  "create follow-up for prospect [id]"

PIPELINE:
  "advance prospect [id] to [stage]"
  "move lead [id] to qualified"

AGENTS:
  "run prospector" / "start outreach" / "run all agents"

SYSTEM:
  "run tests" / "test"
  "templates" / "show templates"
  "help" / "commands"
  "quit" / "exit"

Examples:
  "add ABC HVAC in Houston, TX"
  "show hot prospects"
  "generate outreach for prospect 1"
  "advance prospect 2 to contacted"
  "run tests" """


def _handle_unknown(intent: Intent) -> str:
    raw = intent.params.get("raw", "")
    return f"I don't understand: '{raw}'\n\nType 'help' for available commands, or try:\n  'show hot prospects'\n  'add [company] in [city]'\n  'run tests'\n  'status'"


# ─── Interactive REPL ─────────────────────────────────────────────

def repl():
    """Run an interactive control session."""
    print("=" * 50)
    print("  RELIANTAI NATURAL LANGUAGE CONTROL")
    print("  Type 'help' for commands, 'quit' to exit")
    print("=" * 50)
    print()

    while True:
        try:
            user_input = input("reliantai> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        intent = parse_intent(user_input)
        if intent.action == "quit":
            print("Goodbye!")
            break

        response = handle_intent(intent)
        print(response)
        print()


# ─── Main ────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1:
        # Single command mode
        user_input = " ".join(sys.argv[1:])
        intent = parse_intent(user_input)
        response = handle_intent(intent)
        print(response)
    else:
        # Interactive mode
        repl()


if __name__ == "__main__":
    main()
