# apex-agents/api/main.py
"""
APEX Agent API — complete endpoint registry.

Endpoints:
  GET  /health
  POST /agents/layer1/analyze
  POST /agents/layer2/calibration-gate
  POST /agents/layer3/dispatch
  POST /agents/layer4/quality-review
  GET  /workflow/pending
  POST /workflow/hitl/{decision_id}
  GET  /workflow/completed
  POST /memory/search
  POST /memory/save
  POST /workflow/run   ← full L1→L2→L3→L4 pipeline
  GET  /tools          ← list available skill tools
  POST /tools/call     ← execute a skill tool
"""

from __future__ import annotations
import os
import json
import sys
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

import asyncpg
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Auth integration — FAIL FAST if auth is unavailable (do not silently disable security)
try:
    from auth_integration import (
        get_current_user,
        require_authenticated_user,
        AuthIntegration,
        AUTH_ENABLED,
    )

    if not AUTH_ENABLED:
        raise RuntimeError(
            "Auth integration loaded but AUTH_ENABLED=False — "
            "JWT validator unavailable. Refusing to start without auth."
        )
    auth = AuthIntegration()
    print(f"APEX Auth: ENABLED")
except ImportError as e:
    raise RuntimeError(
        f"Auth integration import failed: {e}. "
        "Cannot start API without authentication. "
        "Ensure integration/shared/ is in PYTHONPATH and all dependencies are installed."
    ) from e

from agents.layer2.workflow import run_layer2
from agents.layer3.dispatcher import dispatch as l3_dispatch
from agents.layer4.workflow import run_layer4
from memory.search import search_memory, save_memory

# Cross-system dispatch
from agents.layer3.cross_system_dispatch import (
    cross_system_dispatch,
    EnhancedDispatchResult,
)

# Skill tools — add apex-tools to path for skill_integration imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apex-tools"))
from skill_tools import handle_tool_call, TOOL_LIST

# Layer 1 import
from agents.layer1.workflow import run_layer1

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Set it before starting the Apex Agents API."
    )

app = FastAPI(title="APEX Agent API", version="0.1.0")

# SECURITY FIX: Require explicit APEX_CORS_ORIGINS — no default wildcard.
# If not set, fail closed (no origins allowed). Must be explicitly configured.
_apex_cors_origins_raw = os.getenv("APEX_CORS_ORIGINS", "")
if not _apex_cors_origins_raw:
    raise RuntimeError(
        "APEX_CORS_ORIGINS environment variable is required. "
        "Set it to a comma-separated list of allowed origins (e.g., "
        "http://localhost:3000,https://apex-ui.example.com). "
        "Do NOT use wildcard * or leave unset in production."
    )
_apex_cors_origins = [
    origin.strip() for origin in _apex_cors_origins_raw.split(",") if origin.strip()
]
if "*" in _apex_cors_origins:
    raise RuntimeError(
        "APEX_CORS_ORIGINS contains wildcard '*' which is not allowed with allow_credentials=True. "
        "Specify explicit origins."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_apex_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


# ════════════════════════════════════════════════════════════════════════════
# HEALTH
# ════════════════════════════════════════════════════════════════════════════


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "apex-agents",
        "version": "0.1.0",
    }


# ════════════════════════════════════════════════════════════════════════════
# SKILL TOOLS — /tools/call  (exposes 3 core skills to external callers)
# ════════════════════════════════════════════════════════════════════════════


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


@app.get("/tools")
async def list_skill_tools(
    user: Dict[str, Any] = Depends(require_authenticated_user),
):
    """List all available skill tools with their schemas."""
    return {"tools": TOOL_LIST}


@app.post("/tools/call")
async def call_skill_tool_endpoint(
    req: ToolCallRequest,
    user: Dict[str, Any] = Depends(require_authenticated_user),
):
    """
    Execute a skill tool by name with arguments.

    Tools:
      skill_diagnose   — Strategic Execution Advisor: diagnose a situation
      skill_prospect   — Autonomous Prospect Engine: qualify raw opportunities
      skill_outreach   — Autonomous Prospect Engine: generate outreach for leads
      skill_proposal   — Proposal-to-Contract Pipeline: generate proposal package
    """
    try:
        result = await handle_tool_call(req.name, req.arguments)
        return json.loads(result)
    except (ValueError, KeyError, TypeError) as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__}
    except Exception as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__}


# ════════════════════════════════════════════════════════════════════════════
# LAYER 1 — Theory of Mind + Data Model Plan
# ════════════════════════════════════════════════════════════════════════════


class Layer1Request(BaseModel):
    task: str
    context: dict[str, Any] = {}
    trace_id: str | None = None


@app.post("/agents/layer1/analyze")
async def layer1_analyze(
    req: Layer1Request,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    """Layer 1 analysis endpoint."""
    result = await run_layer1(
        task=req.task,
        context=req.context,
        trace_id=req.trace_id or str(uuid4()),
    )
    return result if isinstance(result, dict) else result.model_dump()


# ════════════════════════════════════════════════════════════════════════════
# LAYER 2 — Calibration Gate
# ════════════════════════════════════════════════════════════════════════════


class Layer2Request(BaseModel):
    task: str
    context: dict[str, Any] = {}
    agents: list[str] = []
    trace_id: str | None = None


@app.post("/agents/layer2/calibration-gate")
async def layer2_calibration_gate(
    req: Layer2Request,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    result = await run_layer2(
        task=req.task,
        context=req.context,
        agents=req.agents,
        trace_id=req.trace_id or str(uuid4()),
    )
    return result if isinstance(result, dict) else result


# ════════════════════════════════════════════════════════════════════════════
# LAYER 3 — Specialist Dispatch
# ════════════════════════════════════════════════════════════════════════════


class Layer3Request(BaseModel):
    task: str
    context: dict[str, Any] = {}
    trace_id: str | None = None


@app.post("/agents/layer3/dispatch")
async def layer3_dispatch_endpoint(
    req: Layer3Request,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    result = await l3_dispatch(
        task=req.task,
        context=req.context,
        trace_id=req.trace_id or str(uuid4()),
    )
    return result if isinstance(result, dict) else result.model_dump()


class Layer3CrossSystemRequest(BaseModel):
    task: str
    context: dict[str, Any] = {}
    trace_id: str | None = None
    enable_cross_system: bool = True


@app.post("/agents/layer3/dispatch-cross-system")
async def layer3_dispatch_cross_system_endpoint(
    req: Layer3CrossSystemRequest,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    """
    Cross-system dispatch with A2A integration.

    Routes tasks to appropriate ReliantAI systems:
    - HVAC emergencies -> Money CrewAI
    - Chat/conversational -> Citadel NL Agent
    - Browser/computer use -> APEX MCP Tools
    """
    result = await cross_system_dispatch(
        task=req.task,
        context=req.context,
        prior_summary="",
        trace_id=req.trace_id or str(uuid4()),
        enable_cross_system=req.enable_cross_system,
    )
    return result


# ════════════════════════════════════════════════════════════════════════════
# LAYER 4 — Adversarial Quality Review
# ════════════════════════════════════════════════════════════════════════════


class Layer4Request(BaseModel):
    task: str
    layer3_output: dict[str, Any]
    context: dict[str, Any] = {}
    prior_summary: str = ""
    routing_tier: str = "T2Deliberative"
    prior_confidence: float = 0.75
    trace_id: str | None = None


@app.post("/agents/layer4/quality-review")
async def quality_review(
    req: Layer4Request,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    result = await run_layer4(
        task=req.task,
        layer3_output=req.layer3_output,
        context=req.context,
        prior_summary=req.prior_summary,
        routing_tier=req.routing_tier,
        prior_confidence=req.prior_confidence,
        trace_id=req.trace_id,
    )

    def _safe(obj: Any) -> Any:
        if obj is None:
            return None
        return obj.model_dump() if hasattr(obj, "model_dump") else obj

    return {
        "final_approved": result.get("final_approved"),
        "routing_tier": result.get("routing_tier"),
        "iterations_run": (result.get("iteration") or 1) - 1,
        "audit": _safe(result.get("audit_report")),
        "debate": _safe(result.get("debate_result")),
        "evolver": _safe(result.get("evolver_output")),
        "error": result.get("error"),
    }


# ════════════════════════════════════════════════════════════════════════════
# HITL WORKFLOW
# ════════════════════════════════════════════════════════════════════════════


@app.get("/workflow/pending")
async def get_pending_decisions(
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT id::text, trace_id, task_summary, routing_tier,
                   layer3_output, layer4_review, created_at
            FROM hitl_decisions
            WHERE status = 'pending'
            ORDER BY created_at DESC
            """
        )
        return {
            "count": len(rows),
            "pending": [
                {
                    "id": r["id"],
                    "trace_id": r["trace_id"],
                    "task_summary": r["task_summary"],
                    "routing_tier": r["routing_tier"],
                    "layer3_output": json.loads(r["layer3_output"] or "{}"),
                    "layer4_review": json.loads(r["layer4_review"] or "{}"),
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows
            ],
        }
    finally:
        await conn.close()


class HITLDecision(BaseModel):
    approved: bool
    rationale: str
    reviewer: str = "human"


@app.post("/workflow/hitl/{decision_id}")
async def submit_hitl_decision(
    decision_id: str,
    body: HITLDecision,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            "SELECT id FROM hitl_decisions WHERE id = $1::uuid AND status = 'pending'",
            decision_id,
        )
        if not row:
            raise HTTPException(404, f"Pending HITL decision '{decision_id}' not found")

        status = "approved" if body.approved else "rejected"
        await conn.execute(
            """
            UPDATE hitl_decisions
            SET status      = $1,
                rationale   = $2,
                reviewer    = $3,
                resolved_at = NOW()
            WHERE id = $4::uuid
            """,
            status,
            body.rationale,
            body.reviewer,
            decision_id,
        )
        await conn.execute(
            """
            INSERT INTO audit_log (trace_id, decision_id, outcome, reviewer, rationale)
            SELECT trace_id, id, $1, $2, $3
            FROM hitl_decisions WHERE id = $4::uuid
            """,
            status,
            body.reviewer,
            body.rationale,
            decision_id,
        )
        return {"decision_id": decision_id, "status": status, "reviewer": body.reviewer}
    finally:
        await conn.close()


@app.get("/workflow/completed")
async def get_completed_decisions(
    limit: int = 50,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT al.id::text, al.trace_id, al.outcome, al.reviewer,
                   al.rationale, al.created_at,
                   hd.task_summary, hd.routing_tier
            FROM audit_log al
            LEFT JOIN hitl_decisions hd ON hd.id = al.decision_id
            ORDER BY al.created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return {
            "count": len(rows),
            "completed": [
                {
                    "id": r["id"],
                    "trace_id": r["trace_id"],
                    "outcome": r["outcome"],
                    "reviewer": r["reviewer"],
                    "rationale": r["rationale"],
                    "task_summary": r["task_summary"],
                    "routing_tier": r["routing_tier"],
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows
            ],
        }
    finally:
        await conn.close()


# ════════════════════════════════════════════════════════════════════════════
# MEMORY — pgvector semantic search + save
# ════════════════════════════════════════════════════════════════════════════


class MemorySearchRequest(BaseModel):
    query: str
    memory_type: str = "all"
    limit: int = 5


@app.post("/memory/search")
async def memory_search(
    req: MemorySearchRequest,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    try:
        results = await search_memory(
            query=req.query,
            memory_type=req.memory_type,
            limit=req.limit,
        )
        return {"query": req.query, "count": len(results), "results": results}
    except ValueError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"Memory search failed: {e}")


class MemorySaveRequest(BaseModel):
    agent_name: str
    task_summary: str
    content: str
    memory_type: str = "episodic"
    confidence: float = 0.8
    correction: str | None = None
    outcome: str | None = None


@app.post("/memory/save")
async def memory_save(
    req: MemorySaveRequest,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    try:
        memory_id = await save_memory(
            agent_name=req.agent_name,
            task_summary=req.task_summary,
            content=req.content,
            memory_type=req.memory_type,
            confidence=req.confidence,
            correction=req.correction,
            outcome=req.outcome,
        )
        return {"saved": True, "id": memory_id}
    except ValueError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"Memory save failed: {e}")


# ════════════════════════════════════════════════════════════════════════════
# END-TO-END PIPELINE — POST /workflow/run
# ════════════════════════════════════════════════════════════════════════════


class WorkflowRunRequest(BaseModel):
    task: str
    context: dict[str, Any] = {}
    trace_id: str | None = None
    allow_rerun: bool = True


def _extract(state: Any, key: str, default: Any = None) -> Any:
    """Safe attribute/key accessor for both dicts and Pydantic objects."""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


async def _create_hitl_record(
    conn: asyncpg.Connection,
    trace_id: str,
    task: str,
    routing_tier: str,
    l3_output: Any,
    l4_review: Any,
) -> str:
    def _to_json(obj: Any) -> str:
        if isinstance(obj, dict):
            return json.dumps(obj)
        if hasattr(obj, "model_dump"):
            return json.dumps(obj.model_dump())
        return json.dumps(str(obj))

    row = await conn.fetchrow(
        """
        INSERT INTO hitl_decisions
            (trace_id, task_summary, routing_tier, layer3_output, layer4_review, status)
        VALUES ($1, $2, $3, $4, $5, 'pending')
        RETURNING id::text
        """,
        trace_id,
        task[:500],
        routing_tier,
        _to_json(l3_output),
        _to_json(l4_review),
    )
    return row["id"]


async def _save_audit_entry(
    conn: asyncpg.Connection,
    trace_id: str,
    outcome: str,
    routing_tier: str,
) -> None:
    await conn.execute(
        """
        INSERT INTO audit_log (trace_id, outcome, reviewer, rationale)
        VALUES ($1, $2, 'apex-system', $3)
        """,
        trace_id,
        outcome,
        f"Auto-approved by Layer 4 adversarial review (tier: {routing_tier})",
    )


@app.post("/workflow/run")
async def run_workflow(
    req: WorkflowRunRequest,
    _user: Dict[str, Any] = Depends(require_authenticated_user),
):
    """
    Full APEX execution pipeline:
    L1 → understand task, build Theory of Mind, determine routing tier
    L2 → calibration gate: block if agents are miscalibrated
    L3 → run specialist(s) based on routing tier
    L4 → adversarial quality: audit + debate (T3/T4) + evolver

    Outcomes:
      approved              ← auto-approved, output ready
      pending_human_review  ← HITL record created, awaiting human decision
      conditional_approval  ← low confidence but not blocked
      blocked_by_calibration ← Layer 2 hard-blocked execution
    """
    trace_id = req.trace_id or str(uuid4())
    result: dict[str, Any] = {"trace_id": trace_id, "task": req.task[:200]}

    # ── Layer 1 ──────────────────────────────────────────────────────────────
    l1_state = await run_layer1(task=req.task, context=req.context, trace_id=trace_id)
    if _extract(l1_state, "error"):
        raise HTTPException(500, f"Layer 1 failed: {_extract(l1_state, 'error')}")

    routing_tier = str(_extract(l1_state, "routing_tier", "T2Deliberative"))
    prior_summary = str(_extract(l1_state, "prior_summary", ""))
    l1_confidence = float(_extract(l1_state, "confidence", 0.75))
    result["layer1"] = {"routing_tier": routing_tier, "confidence": l1_confidence}

    # ── Layer 2 ──────────────────────────────────────────────────────────────
    l2_state = await run_layer2(
        task=req.task,
        context={**req.context, "routing_tier": routing_tier},
        agents=[],
        trace_id=trace_id,
    )
    gate_decision = _extract(l2_state, "gate_decision") or {}
    if isinstance(gate_decision, dict) and gate_decision.get("block"):
        return {
            **result,
            "status": "blocked_by_calibration",
            "reason": gate_decision.get("reason", "Calibration gate blocked execution"),
            "layer2": gate_decision,
        }
    result["layer2"] = {"passed": True}

    # ── Layer 3 ──────────────────────────────────────────────────────────────
    l3_context = {
        **req.context,
        "routing_tier": routing_tier,
        "l1_confidence": l1_confidence,
        "prior_summary": prior_summary,
    }
    l3_output = await l3_dispatch(task=req.task, context=l3_context, trace_id=trace_id)
    l3_dict = l3_output if isinstance(l3_output, dict) else l3_output.model_dump()
    l3_confidence = float(l3_dict.get("aggregated_confidence", l1_confidence))
    result["layer3"] = {
        "specialists": l3_dict.get("specialists_used"),
        "confidence": l3_confidence,
    }

    # ── Layer 4 (with optional L3 rerun) ─────────────────────────────────────────
    async def _run_l4(l3_out: dict, confidence: float) -> Any:
        return await run_layer4(
            task=req.task,
            layer3_output=l3_out,
            context={**req.context, "routing_tier": routing_tier},
            prior_summary=prior_summary,
            routing_tier=routing_tier,
            prior_confidence=confidence,
            trace_id=trace_id,
        )

    l4_state = await _run_l4(l3_dict, l3_confidence)
    evolver_out = _extract(l4_state, "evolver_output")
    final_approved = bool(_extract(l4_state, "final_approved", False))
    requires_hitl = bool(
        _extract(evolver_out, "requires_hitl", True) if evolver_out else True
    )
    requires_rerun = bool(
        _extract(evolver_out, "requires_layer3_rerun", False) if evolver_out else False
    )

    # One L3 rerun if Evolver flags it
    if not final_approved and requires_rerun and req.allow_rerun:
        revision_notes = str(
            _extract(evolver_out, "convergence_note", "") if evolver_out else ""
        )
        l3_output = await l3_dispatch(
            task=req.task,
            context={**l3_context, "revision_notes": revision_notes},
            trace_id=trace_id,
        )
        l3_dict = l3_output if isinstance(l3_output, dict) else l3_output.model_dump()
        l3_confidence = float(l3_dict.get("aggregated_confidence", l3_confidence))
        l4_state = await _run_l4(l3_dict, l3_confidence)
        evolver_out = _extract(l4_state, "evolver_output")
        final_approved = bool(_extract(l4_state, "final_approved", False))
        requires_hitl = bool(
            _extract(evolver_out, "requires_hitl", True) if evolver_out else True
        )

    audit_out = _extract(l4_state, "audit_report")
    result["layer4"] = {
        "final_approved": final_approved,
        "audit_verdict": _extract(audit_out, "overall_verdict"),
        "iterations_run": (_extract(l4_state, "iteration", 1) or 1) - 1,
    }

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if final_approved:
            await _save_audit_entry(conn, trace_id, "approved", routing_tier)
            return {
                **result,
                "status": "approved",
                "output": l3_dict,
            }

        if requires_hitl:
            decision_id = await _create_hitl_record(
                conn, trace_id, req.task, routing_tier, l3_dict, l4_state
            )
            return {
                **result,
                "status": "pending_human_review",
                "decision_id": decision_id,
                "reason": "Layer 4 adversarial review escalated to HITL",
            }

        await _save_audit_entry(conn, trace_id, "conditional", routing_tier)
        return {
            **result,
            "status": "conditional_approval",
            "output": l3_dict,
            "warning": "Approved with low confidence — human review recommended",
        }
    finally:
        await conn.close()


# ════════════════════════════════════════════════════════════════════════════
# AUTH INTEGRATION — Protected Endpoints
# ════════════════════════════════════════════════════════════════════════════


@app.get("/auth-test")
async def auth_test(user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Test endpoint to verify auth integration."""
    return {
        "authenticated": True,
        "user": user.get("username") if isinstance(user, dict) else "unknown",
        "roles": user.get("roles", []) if isinstance(user, dict) else [],
        "auth_enabled": AUTH_ENABLED,
    }


@app.get("/auth-status")
async def auth_status(_user: dict = Depends(require_authenticated_user)):
    """Get authentication status for APEX — requires auth."""
    return {
        "auth_enabled": AUTH_ENABLED,
        "service": "apex-agents",
    }
