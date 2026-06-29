"""
WebsiteForgeAgent — autonomous website forge loop.

Extends BaseAgent with the 4-phase forge cycle:
  Discover → Forge → Quality Gate → Render

Each phase calls the appropriate tool (or sub-agent). The agent itself
is the orchestrator — tools are stateless functions that return structured data.

Architecture: Playbook § Advanced — Supervisor pattern.
One agent, four sequential phases. No parallelism needed (each phase depends
on the previous). Sub-agents (renderers) are called per task, not in loop.
"""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ..core import Telemetry, get_logger
from .prompt import build_system_context, build_task_context
from .renderers import render_standalone_html, render_nextjs_scaffold
from .quality_gate import quality_gate_check

log = get_logger("agents.websiteforge")


# ═══════════════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class ForgeMode(str, Enum):
    STANDALONE_HTML = "standalone_html"
    NEXTJS_ISR = "nextjs_isr"
    DUAL = "dual"


@dataclass
class ForgeRequest:
    company_name: str
    company_url: str = ""
    trade: str = ""
    city_state: str = ""
    mode: ForgeMode = ForgeMode.STANDALONE_HTML
    output_dir: str | None = None
    max_iterations: int = 3
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ForgeResult:
    success: bool
    company_name: str
    mode: str
    site_content: dict[str, Any] | None = None
    output_paths: list[str] = field(default_factory=list)
    gate_score: float = 0.0
    gate_violations: list[str] = field(default_factory=list)
    iterations: int = 0
    error: str | None = None
    duration_ms: float = 0
    research: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
#  WEBSITEFORGE AGENT
# ═══════════════════════════════════════════════════════════════════════════

class WebsiteForgeAgent:
    """
    Autonomous website forge.

    One-shot design agent. Call .run_for() with a company name (or URL)
    and receive a complete, production-grade website.

    Quality bar: Awwwards + FAANG. No AI-slop. Research-driven.
    """

    def __init__(
        self,
        output_dir: str = "./website_forge_output",
        model: str = "pro",  # "pro" for quality, "flash" for speed
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = model
        self.logger = get_logger("agents.websiteforge")

    # ──────────────────────────────────────────────────────────────────────
    #  PUBLIC API
    # ──────────────────────────────────────────────────────────────────────

    async def run_for(self, request: ForgeRequest) -> ForgeResult:
        """
        Run the full forge cycle and return polished output.

        Phases: DISCOVER → FORGE → EVALUATE → RENDER
        Max iterations: 3 (forge+gate loops before render)
        """
        t0 = time.monotonic()
        self.logger.info(
            "forge_start", company=request.company_name, mode=request.mode.value
        )

        try:
            # ── PHASE 1: DISCOVER ───────────────────────────────────────────
            with Telemetry(
                operation="websiteforge.discover", agent="websiteforge"
            ):
                research = await self._discover(request)

            # ── PHASE 2: FORGE (once) ────────────────────────────────────────
            with Telemetry(
                operation="websiteforge.forge",
                agent="websiteforge",
            ):
                site_content = await self._forge_content(request, research)

            # ── PHASE 3: GATE + REPAIR LOOP ──────────────────────────────────
            gate_score = 0.0
            gate_violations: list[str] = []
            iterations = 0

            for iteration in range(1, request.max_iterations + 1):
                iterations = iteration

                with Telemetry(
                    operation="websiteforge.gate",
                    agent="websiteforge",
                    iteration=iteration,
                ):
                    gate_result = await quality_gate_check(site_content)
                    gate_score = gate_result["score"]
                    gate_violations = gate_result["violations"]

                self.logger.info(
                    "forge_iteration",
                    iteration=iteration,
                    gate_score=gate_score,
                    violations=len(gate_violations),
                )

                if gate_score >= 0.85 and not gate_violations:
                    break

                if iteration < request.max_iterations:
                    with Telemetry(
                        operation="websiteforge.repair",
                        agent="websiteforge",
                        iteration=iteration,
                    ):
                        site_content = await self._repair_content(
                            request, site_content, gate_violations, research
                        )

            # ── PHASE 4: RENDER ─────────────────────────────────────────────
            with Telemetry(
                operation="websiteforge.render", agent="websiteforge"
            ):
                output_paths = await self._render(
                    request, site_content or {}, gate_score
                )

            duration = (time.monotonic() - t0) * 1000
            self.logger.info(
                "forge_complete",
                company=request.company_name,
                gate_score=gate_score,
                iterations=iterations,
                outputs=len(output_paths),
                duration_ms=round(duration, 1),
            )

            return ForgeResult(
                success=gate_score >= 0.85,
                company_name=request.company_name,
                mode=request.mode.value,
                site_content=site_content,
                output_paths=output_paths,
                gate_score=gate_score,
                gate_violations=gate_violations,
                iterations=iterations,
                duration_ms=round(duration, 1),
                research=research,
            )

        except Exception as exc:
            duration = (time.monotonic() - t0) * 1000
            self.logger.error(
                "forge_failed", company=request.company_name, error=str(exc)
            )
            return ForgeResult(
                success=False,
                company_name=request.company_name,
                mode=request.mode.value,
                error=str(exc),
                duration_ms=round(duration, 1),
            )

    # ──────────────────────────────────────────────────────────────────────
    #  PHASE 1: DISCOVER
    # ──────────────────────────────────────────────────────────────────────

    async def _discover(self, request: ForgeRequest) -> dict[str, Any]:
        """
        Research the company. Uses web_search + brand_analyzer tools.
        Falls back gracefully when external APIs are unavailable.
        """
        name = request.company_name
        url = request.company_url
        city = request.city_state

        self.logger.info("discover_start", company=name, url=url)

        research: dict[str, Any] = {
            "company_name": name,
            "url": url,
            "city_state": city,
            "brand_signals": {},
            "competitors": [],
            "audience": {},
            "trade": request.trade or "hvac",
            "facts": [],
            "search_queries_used": [],
        }

        # Try web research (graceful fallback)
        try:
            from .tools.researcher import WebResearcher

            researcher = WebResearcher()
            brand_result = await researcher.analyze_brand(name, url)
            research["brand_signals"] = brand_result.get("signals", {})
            research["audience"] = brand_result.get("audience", {})
            research["facts"] = brand_result.get("facts", [])
            research["search_queries_used"] = brand_result.get("queries", [])

            if not research["trade"] or research["trade"] == "hvac":
                research["trade"] = brand_result.get("trade", "hvac")

            if not city and brand_result.get("city"):
                research["city_state"] = brand_result["city"]

            competitors = await researcher.find_competitors(name, research.get("city_state", ""))
            research["competitors"] = competitors[:3]

        except Exception as exc:
            self.logger.warning(
                "discover_web_failed", company=name, error=str(exc)
            )
            # Graceful fallback — minimal research from request data
            research["brand_signals"] = {
                "name": name,
                "city": city or "their service area",
                "differentiators": [f"Local {request.trade or 'home service'} expert"],
            }
            research["facts"] = [
                f"Company name: {name}",
                f"Trade: {request.trade or 'home services'}",
                f"Location: {city or 'not provided'}",
            ]

        return research

    # ──────────────────────────────────────────────────────────────────────
    #  PHASE 2: FORGE CONTENT
    # ──────────────────────────────────────────────────────────────────────

    async def _forge_content(
        self, request: ForgeRequest, research: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Call content_forge tool to generate structured WebsiteContent JSON.
        Uses the appropriate model based on self.model setting.
        """
        try:
            from .tools.content_forge import forge_site_content

            return await forge_site_content(
                company_name=request.company_name,
                research=research,
                mode=request.mode.value,
                model=self.model,
            )
        except ImportError:
            raise RuntimeError(
                "content_forge tool unavailable — check Google API key"
            )

    # ──────────────────────────────────────────────────────────────────────
    #  REPAIR (post-gate failure)
    # ──────────────────────────────────────────────────────────────────────

    async def _repair_content(
        self,
        request: ForgeRequest,
        content: dict[str, Any],
        violations: list[str],
        research: dict[str, Any],
    ) -> dict[str, Any]:
        """
        After a quality gate failure, ask the model to repair content
        addressing specific violations.
        """
        from .tools.content_forge import repair_site_content

        repaired = await repair_site_content(
            content=content,
            violations=violations,
            research=research,
            model=self.model,
        )
        return repaired

    # ──────────────────────────────────────────────────────────────────────
    #  PHASE 4: RENDER
    # ──────────────────────────────────────────────────────────────────────

    async def _render(
        self, request: ForgeRequest, site_content: dict[str, Any], gate_score: float
    ) -> list[str]:
        """
        Render output in the requested mode(s).
        Always produces standalone HTML (the universal deliverable).
        Also produces ISR scaffold when mode requires it.
        """
        company_slug = self._make_slug(request.company_name)
        out_dir = request.output_dir or str(self.output_dir / company_slug)
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        outputs: list[str] = []

        # Always: standalone HTML (the hand-to-any-company artifact)
        html_path = await render_standalone_html(
            site_content, out_dir, company_slug
        )
        outputs.append(html_path)
        self.logger.info("render.html_complete", path=html_path)

        # Conditional: Next.js ISR scaffold
        if request.mode in (ForgeMode.NEXTJS_ISR, ForgeMode.DUAL):
            isr_dir = await render_nextjs_scaffold(site_content, out_dir, company_slug)
            outputs.append(str(isr_dir))
            self.logger.info("render.isr_complete", path=str(isr_dir))

        return outputs

    # ──────────────────────────────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_slug(company_name: str) -> str:
        """Company name → URL-safe slug."""
        slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
        return slug[:50] or "site"
