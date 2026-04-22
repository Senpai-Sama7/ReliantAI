#!/usr/bin/env python3
"""
ReliantAI Skill Integration Layer

Exposes the 3 core skills to ReliantAI's multi-agent system via:
1. Direct Python import (for Apex agents and Python services)
2. CLI bridge (for shell-based agent integration)
3. FastAPI HTTP endpoints (for service-to-service calls)

Usage:
  python3 skill_integration.py diagnose <context>
  python3 skill_integration.py prospect <criteria> <skills_csv> <raw_text>
  python3 skill_integration.py proposal <client> <company> <title> <desc> <budget> <weeks> <skills_csv>
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Any
from functools import partial

# ─────────────────────────────────────────────────────────────────────────────
# Path Setup — skills are in ../skills/ relative to this file
# ─────────────────────────────────────────────────────────────────────────────

SKILL_INTEGRATION_DIR = Path(__file__).parent
RELINTAI_ROOT = SKILL_INTEGRATION_DIR.parent
SKILLS_ROOT = RELINTAI_ROOT / "skills"

SEA_SCRIPTS = SKILLS_ROOT / "strategic-execution-advisor" / "scripts"
PROSPECT_SCRIPTS = SKILLS_ROOT / "autonomous-prospect-engine" / "scripts"
PROPOSAL_SCRIPTS = SKILLS_ROOT / "proposal-to-contract" / "scripts"


def _load_module(name: str, script_path: Path):
    """Dynamically load a Python skill script as a module."""
    from importlib.util import spec_from_file_location, module_from_spec

    spec = spec_from_file_location(name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Could not create loader for skill '{name}' at '{script_path}'. "
            f"File may not exist or is not a valid Python module."
        )
    mod = module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load skill '{name}' from '{script_path}': {e.__class__.__name__}: {e}"
        ) from e
    return mod


# ─────────────────────────────────────────────────────────────────────────────
# Strategic Execution Advisor
# ─────────────────────────────────────────────────────────────────────────────


def diagnose(context: str) -> dict[str, Any]:
    """
    Diagnose a project situation and return ranked action recommendations.

    Args:
        context: Free-text description of the project situation

    Returns:
        dict with bottleneck_type, situation_summary, top_actions, etc.
    """
    sea = _load_module("sea", SEA_SCRIPTS / "script.py")
    return sea.diagnose(context)


async def diagnose_async(context: str) -> dict[str, Any]:
    """Async version of diagnose."""
    return await asyncio.to_thread(diagnose, context)


# ─────────────────────────────────────────────────────────────────────────────
# Autonomous Prospect Engine
# ─────────────────────────────────────────────────────────────────────────────


def qualify_prospects(
    criteria: str, skills: list[str], raw_opportunities: str
) -> dict[str, Any]:
    """
    Score and qualify raw opportunity text into a pipeline report.

    Args:
        criteria: Search criteria (e.g. "React and TypeScript development")
        skills: List of relevant skills for fit scoring
        raw_opportunities: Raw text with one opportunity per line

    Returns:
        dict with hot_count, warm_count, pipeline_value, opportunities, etc.
    """
    pe = _load_module("prospect", PROSPECT_SCRIPTS / "script.py")
    engine = pe.ProspectEngine(criteria, skills)
    engine.ingest_opportunities(raw_opportunities)
    engine.qualify_all()
    report = engine.build_pipeline_report()

    opportunities = []
    for opp in engine.prospects:
        opportunities.append(
            {
                "name": opp.company,
                "budget": opp.budget,
                "timeline_weeks": opp.timeline_weeks,
                "score": opp.total_score(),
                "tier": opp.tier(),
                "source": opp.source,
                "recommendation": opp.recommendation(),
            }
        )
    report["opportunities"] = opportunities
    return report


async def qualify_prospects_async(
    criteria: str, skills: list[str], raw_opportunities: str
) -> dict[str, Any]:
    """Async version of qualify_prospects."""
    return await asyncio.to_thread(
        qualify_prospects, criteria, skills, raw_opportunities
    )


def generate_outreach(
    criteria: str, skills: list[str], raw_opportunities: str, your_name: str = ""
) -> str:
    """
    Generate personalized outreach emails for HOT and WARM leads.

    Returns formatted outreach text.
    """
    pe = _load_module("prospect", PROSPECT_SCRIPTS / "script.py")
    engine = pe.ProspectEngine(criteria, skills)
    engine.ingest_opportunities(raw_opportunities)
    engine.qualify_all()

    outputs = []
    for opp in engine.prospects:
        if opp.tier() in ("HOT", "WARM"):
            outreach = engine.generate_outreach(opp, your_name, skills)
            outputs.append(f"=== {opp.company} ({opp.tier()}) ===\n{outreach}")
    return "\n\n".join(outputs)


# ─────────────────────────────────────────────────────────────────────────────
# Proposal-to-Contract Pipeline
# ─────────────────────────────────────────────────────────────────────────────


def generate_proposal_package(
    client_name: str,
    company: str,
    project_title: str,
    description: str,
    budget_usd: float,
    timeline_weeks: int,
    skills: list[str],
) -> dict[str, str]:
    """
    Generate a complete proposal package.

    Returns:
        dict with keys: proposal, sow, contract, followup
    """
    p2c = _load_module("p2c", PROPOSAL_SCRIPTS / "script.py")
    return p2c.generate_complete_package(
        client_name,
        company,
        project_title,
        description,
        budget_usd,
        timeline_weeks,
        skills,
    )


async def generate_proposal_package_async(
    client_name: str,
    company: str,
    project_title: str,
    description: str,
    budget_usd: float,
    timeline_weeks: int,
    skills: list[str],
) -> dict[str, str]:
    """Async version of generate_proposal_package."""
    return await asyncio.to_thread(
        generate_proposal_package,
        client_name,
        company,
        project_title,
        description,
        budget_usd,
        timeline_weeks,
        skills,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Apex Agent Integration — expose as callable tool
# ─────────────────────────────────────────────────────────────────────────────

TOOL_DESCRIPTIONS = {
    "skill_diagnose": {
        "description": "Diagnose a project situation and get ranked action recommendations. "
        "Input: free-text context. Output: bottleneck type + top 3 actions.",
        "input_schema": {
            "type": "object",
            "properties": {"context": {"type": "string"}},
            "required": ["context"],
        },
    },
    "skill_prospect": {
        "description": "Score and qualify raw opportunity text into a pipeline report. "
        "Input: criteria, skills list, raw text. Output: HOT/WARM/COLD leads + pipeline value.",
        "input_schema": {
            "type": "object",
            "properties": {
                "criteria": {"type": "string"},
                "skills": {"type": "array", "items": {"type": "string"}},
                "raw_opportunities": {"type": "string"},
            },
            "required": ["criteria", "skills", "raw_opportunities"],
        },
    },
    "skill_outreach": {
        "description": "Generate personalized outreach for HOT/WARM leads. "
        "Input: criteria, skills, raw text, your name. Output: formatted email templates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "criteria": {"type": "string"},
                "skills": {"type": "array", "items": {"type": "string"}},
                "raw_opportunities": {"type": "string"},
                "your_name": {"type": "string"},
            },
            "required": ["criteria", "skills", "raw_opportunities"],
        },
    },
    "skill_proposal": {
        "description": "Generate a complete proposal package: proposal doc, SOW, contract, follow-up sequence. "
        "Input: client info, budget, timeline, skills. Output: all 4 documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "company": {"type": "string"},
                "project_title": {"type": "string"},
                "description": {"type": "string"},
                "budget_usd": {"type": "number"},
                "timeline_weeks": {"type": "integer"},
                "skills": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "client_name",
                "company",
                "project_title",
                "budget_usd",
                "timeline_weeks",
            ],
        },
    },
}


def _missing_field(tool: str, field: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": f"skill_diagnose: Missing required field: {field}",
        "type": "ValidationError",
    }


def _validate_skill_diagnose(input: dict[str, Any]) -> str | None:
    if "context" not in input:
        return "context"
    if not isinstance(input.get("context"), str):
        return "context (must be string)"
    return None


def _validate_skill_prospect(input: dict[str, Any]) -> str | None:
    for field in ("criteria", "skills", "raw_opportunities"):
        if field not in input:
            return field
    if not isinstance(input.get("criteria"), str):
        return "criteria (must be string)"
    if not isinstance(input.get("skills"), list):
        return "skills (must be list)"
    if not isinstance(input.get("raw_opportunities"), str):
        return "raw_opportunities (must be string)"
    return None


def _validate_skill_proposal(input: dict[str, Any]) -> str | None:
    for field in ("client_name", "company", "project_title"):
        if field not in input:
            return field
    return None


async def call_skill_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Route a tool call to the appropriate skill function.
    Used by Apex agents to invoke skills via the MCP protocol.
    """
    if tool_name == "skill_diagnose":
        if (err := _validate_skill_diagnose(tool_input)) is not None:
            return {
                "ok": False,
                "error": f"skill_diagnose: Missing required field: {err}",
                "type": "ValidationError",
            }
        try:
            result = await diagnose_async(tool_input["context"])
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e), "type": type(e).__name__}

    elif tool_name == "skill_prospect":
        if (err := _validate_skill_prospect(tool_input)) is not None:
            return {
                "ok": False,
                "error": f"skill_prospect: Missing required field: {err}",
                "type": "ValidationError",
            }
        try:
            result = await qualify_prospects_async(
                tool_input["criteria"],
                tool_input["skills"],
                tool_input["raw_opportunities"],
            )
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e), "type": type(e).__name__}

    elif tool_name == "skill_outreach":
        if tool_input.get("criteria") is None or not isinstance(
            tool_input.get("criteria"), str
        ):
            return {
                "ok": False,
                "error": "skill_outreach: Missing required field: criteria",
                "type": "ValidationError",
            }
        if tool_input.get("skills") is None or not isinstance(
            tool_input.get("skills"), list
        ):
            return {
                "ok": False,
                "error": "skill_outreach: Missing required field: skills",
                "type": "ValidationError",
            }
        if tool_input.get("raw_opportunities") is None:
            return {
                "ok": False,
                "error": "skill_outreach: Missing required field: raw_opportunities",
                "type": "ValidationError",
            }
        try:
            result = generate_outreach(
                tool_input["criteria"],
                tool_input["skills"],
                tool_input["raw_opportunities"],
                tool_input.get("your_name", ""),
            )
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e), "type": type(e).__name__}

    elif tool_name == "skill_proposal":
        if (err := _validate_skill_proposal(tool_input)) is not None:
            return {
                "ok": False,
                "error": f"skill_proposal: Missing required field: {err}",
                "type": "ValidationError",
            }
        try:
            result = await generate_proposal_package_async(
                tool_input["client_name"],
                tool_input["company"],
                tool_input["project_title"],
                tool_input.get("description", ""),
                tool_input.get("budget_usd", 0),
                tool_input.get("timeline_weeks", 4),
                tool_input.get("skills", []),
            )
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e), "type": type(e).__name__}

    else:
        return {
            "ok": False,
            "error": f"Unknown tool: {tool_name}",
            "type": "ValueError",
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────


def _cli_outreach(args: list[str]) -> dict[str, Any]:
    """Validated wrapper for generate_outreach CLI invocation."""
    pe = _load_module("prospect", PROSPECT_SCRIPTS / "script.py")
    criteria = args[0] if len(args) > 0 else ""
    skills = args[1].split(",") if len(args) > 1 else []
    raw = args[2] if len(args) > 2 else ""
    your_name = args[3] if len(args) > 3 else ""
    engine = pe.ProspectEngine(criteria, skills)
    engine.ingest_opportunities(raw)
    engine.qualify_all()
    outputs = []
    for opp in engine.prospects:
        if opp.tier() in ("HOT", "WARM"):
            outreach = engine.generate_outreach(opp, your_name, skills)
            outputs.append(
                {
                    "company": opp.company,
                    "tier": opp.tier(),
                    "outreach": outreach,
                }
            )
    return {"opportunities": outputs}


def _cli_proposal(args: list[str]) -> dict[str, Any]:
    """Validated wrapper for generate_proposal_package CLI invocation."""
    try:
        budget = float(args[4]) if len(args) > 4 else 0
    except (ValueError, TypeError):
        raise ValueError("budget_usd must be a number")
    try:
        timeline = int(args[5]) if len(args) > 5 else 4
    except (ValueError, TypeError):
        raise ValueError("timeline_weeks must be an integer")
    return generate_proposal_package(
        args[0] if len(args) > 0 else "",
        args[1] if len(args) > 1 else "",
        args[2] if len(args) > 2 else "",
        args[3] if len(args) > 3 else "",
        budget,
        timeline,
        args[6].split(",") if len(args) > 6 else [],
    )


COMMANDS = {
    "diagnose": lambda args: diagnose(args[0] if args else ""),
    "prospect": lambda args: qualify_prospects(
        args[0] if len(args) > 0 else "",
        args[1].split(",") if len(args) > 1 else [],
        args[2] if len(args) > 2 else "",
    ),
    "outreach": lambda args: _cli_outreach(args),
    "proposal": lambda args: _cli_proposal(args),
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: skill_integration.py <command> [args...]")
        print("Commands: " + ", ".join(COMMANDS.keys()))
        print("Tools: " + ", ".join(TOOL_DESCRIPTIONS.keys()))
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        result = COMMANDS[cmd](args)
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result)
    except Exception as e:
        # SECURITY: Do not expose full traceback in production output.
        print(
            json.dumps(
                {
                    "error": str(e),
                    "type": type(e).__name__,
                }
            )
        )
        sys.exit(1)
