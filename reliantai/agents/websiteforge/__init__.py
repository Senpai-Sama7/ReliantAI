"""
WebsiteForge — FAANG-grade, research-driven website generation agent.

Receives a company name (or URL) and autonomously:
  1. Researches the business (brand, competitors, market position)
  2. Forges Awwwards-quality copy and design direction
  3. Evaluates against every quality gate (no AI-slop)
  4. Renders on-brand output: standalone HTML, Next.js scaffold, or Dual mode

Usage:
    from reliantai.agents.websiteforge import WebsiteForgeAgent, ForgeRequest, ForgeMode

    agent = WebsiteForgeAgent()
    request = ForgeRequest(company_name="Acme HVAC", mode=ForgeMode.DUAL)
    result = await agent.run_for(request)
"""

from .agent import WebsiteForgeAgent, ForgeRequest, ForgeMode, ForgeResult
from .quality_gate import quality_gate_check
from .prompt import build_system_context, build_task_context

__all__ = [
    "WebsiteForgeAgent",
    "ForgeRequest",
    "ForgeMode",
    "ForgeResult",
    "quality_gate_check",
    "build_system_context",
    "build_task_context",
]
