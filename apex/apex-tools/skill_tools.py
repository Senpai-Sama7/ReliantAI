"""
Apex Skill Tools — exposes the 3 core skills as MCP-style tools for Apex agents.

This module provides tool definitions and handlers that Apex agents
can call via the standard tool call protocol.

Tools:
  skill_diagnose      — Strategic Execution Advisor
  skill_prospect      — Autonomous Prospect Engine (qualify)
  skill_outreach      — Autonomous Prospect Engine (outreach)
  skill_proposal      — Proposal-to-Contract Pipeline
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any, Annotated

# Add integration dir to path for skill_integration import
# skill_integration.py is at ReliantAI/integration/skill_integration.py
# apex-tools/ is at ReliantAI/apex/apex-tools/
# So we need to go up 2 levels from apex-tools/ to reach ReliantAI/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integration"))

from skill_integration import (
    diagnose,
    qualify_prospects,
    generate_outreach,
    generate_proposal_package,
    TOOL_DESCRIPTIONS,
    call_skill_tool,
)

# ─────────────────────────────────────────────────────────────────────────────
# Tool Schemas (for Apex MCP protocol)
# ─────────────────────────────────────────────────────────────────────────────

TOOL_LIST = [
    {
        "name": name,
        "description": desc["description"],
        "inputSchema": desc["input_schema"],
    }
    for name, desc in TOOL_DESCRIPTIONS.items()
]


# ─────────────────────────────────────────────────────────────────────────────
# Tool Handlers — called by the Apex agent runtime
# ─────────────────────────────────────────────────────────────────────────────


async def handle_skill_diagnose(arguments: dict[str, Any]) -> str:
    """Handle skill_diagnose tool call."""
    result = await call_skill_tool("skill_diagnose", arguments)
    return json.dumps(result, indent=2)


async def handle_skill_prospect(arguments: dict[str, Any]) -> str:
    """Handle skill_prospect tool call."""
    result = await call_skill_tool("skill_prospect", arguments)
    return json.dumps(result, indent=2)


async def handle_skill_outreach(arguments: dict[str, Any]) -> str:
    """Handle skill_outreach tool call."""
    result = await call_skill_tool("skill_outreach", arguments)
    return json.dumps(result, indent=2)


async def handle_skill_proposal(arguments: dict[str, Any]) -> str:
    """Handle skill_proposal tool call."""
    result = await call_skill_tool("skill_proposal", arguments)
    return json.dumps(result, indent=2)


TOOL_HANDLERS = {
    "skill_diagnose": handle_skill_diagnose,
    "skill_prospect": handle_skill_prospect,
    "skill_outreach": handle_skill_outreach,
    "skill_proposal": handle_skill_proposal,
}


async def handle_tool_call(tool_name: str, arguments: dict[str, Any]) -> str:
    """Route a tool call to the appropriate handler."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"ok": False, "error": f"Unknown tool: {tool_name}"})
    return await handler(arguments)


# ─────────────────────────────────────────────────────────────────────────────
# CLI for testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def test():
        # Test diagnose
        result = await call_skill_tool(
            "skill_diagnose",
            {
                "context": "The team is stuck between microservices and monolith. Multiple priorities competing."
            },
        )
        print("DIAGNOSE:", json.dumps(result, indent=2)[:300])

        # Test prospect
        result = await call_skill_tool(
            "skill_prospect",
            {
                "criteria": "React and TypeScript development",
                "skills": ["React", "TypeScript", "Node.js"],
                "raw_opportunities": "Need React developer at Acme Corp - budget $15K, 2 weeks\n"
                "Startup needs Python backend, $3K budget, 4 weeks",
            },
        )
        print("\nPROSPECT:", json.dumps(result, indent=2)[:300])

        # Test proposal
        result = await call_skill_tool(
            "skill_proposal",
            {
                "client_name": "Alice Smith",
                "company": "Acme Corp",
                "project_title": "React Migration",
                "description": "Migrate legacy app to React 19",
                "budget_usd": 30000,
                "timeline_weeks": 8,
                "skills": ["React", "TypeScript"],
            },
        )
        print(
            "\nPROPOSAL:",
            list(result.get("result", {}).keys())
            if isinstance(result.get("result"), dict)
            else "ok",
        )

    asyncio.run(test())
