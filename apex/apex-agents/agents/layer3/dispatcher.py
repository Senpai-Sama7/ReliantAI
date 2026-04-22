# apex-agents/agents/layer3/dispatcher.py
from __future__ import annotations
import asyncio
from typing import TypedDict, Any
from uuid import uuid4

from agents.layer3.research  import run_research,  ResearchReport
from agents.layer3.creative  import run_creative,  CreativeOutput
from agents.layer3.analytics import run_analytics, AnalyticsReport
from agents.layer3.sales     import run_sales,     SalesStrategy


SPECIALIST_MAP: dict[str, list[str]] = {
    "research":  ["research"],
    "creative":  ["creative"],
    "analytics": ["analytics"],
    "sales":     ["sales"],
    "marketing": ["research", "creative"],
    "campaign":  ["research", "creative", "analytics"],
    "deal":      ["research", "analytics", "sales"],
    "default":   ["research"],
}


class DispatchResult(TypedDict):
    task_type:   str
    specialists: list[str]
    results:     dict[str, Any]
    errors:      dict[str, str]
    confidence:  float


def _detect_type(task: str) -> str:
    t = task.lower()
    if any(w in t for w in ["write", "copy", "email", "ad", "message", "creative"]):
        return "creative"
    if any(w in t for w in ["analyze", "report", "data", "metric", "performance"]):
        return "analytics"
    if any(w in t for w in ["sell", "prospect", "deal", "close", "objection", "outreach"]):
        return "sales"
    if any(w in t for w in ["research", "find", "look up", "what is", "search"]):
        return "research"
    if any(w in t for w in ["campaign", "launch", "market"]):
        return "campaign"
    return "default"


async def dispatch(
    task:          str,
    context:       dict,
    prior_summary: str,
    task_type:     str | None = None,
    trace_id:      str | None = None,
) -> DispatchResult:
    tid         = trace_id or str(uuid4())
    ttype       = task_type or _detect_type(task)
    specialists = SPECIALIST_MAP.get(ttype, SPECIALIST_MAP["default"])

    async def _run(name: str):
        fn = {
            "research":  run_research,
            "creative":  run_creative,
            "analytics": run_analytics,
            "sales":     run_sales,
        }[name]
        return name, await fn(task, context, prior_summary, tid)

    settled = await asyncio.gather(*[_run(s) for s in specialists], return_exceptions=True)

    results:     dict[str, Any] = {}
    errors:      dict[str, str] = {}
    confidences: list[float]    = []

    for item in settled:
        if isinstance(item, Exception):
            errors["unknown"] = str(item)
            continue
        name, result = item
        results[name] = result
        if hasattr(result, "confidence"):
            confidences.append(result.confidence)

    mean_conf = sum(confidences) / len(confidences) if confidences else 0.3

    return DispatchResult(
        task_type=ttype,
        specialists=specialists,
        results=results,
        errors=errors,
        confidence=round(mean_conf, 3),
    )
