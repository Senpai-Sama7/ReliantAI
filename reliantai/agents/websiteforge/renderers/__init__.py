"""
Renderers package — adapter layer between agent.py and the renderer tools.

agent.py calls:
  await render_standalone_html(site_content, out_dir, slug) -> str
  await render_nextjs_scaffold(site_content, out_dir, slug) -> str

Underlying:
  html_renderer.render_html_file(site_content, Path) -> Path   (sync)
  isr_renderer.render_isr_scaffold(site_content, Path) -> Path  (async)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..tools.html_renderer import render_html_file
from .isr_renderer import render_isr_scaffold

__all__ = ["render_standalone_html", "render_nextjs_scaffold"]


async def render_standalone_html(
    site_content: dict[str, Any],
    out_dir: str | Path,
    slug: str = "",
) -> str:
    """Render a standalone HTML file and return its path as a string."""
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    path = render_html_file(site_content, target)
    return str(path)


async def render_nextjs_scaffold(
    site_content: dict[str, Any],
    out_dir: str | Path,
    slug: str = "",
) -> str:
    """Render a full Next.js ISR scaffold and return the output directory as a string."""
    target = Path(out_dir) / "nextjs-isr"
    target.mkdir(parents=True, exist_ok=True)
    path = await render_isr_scaffold(site_content, target)
    return str(path)
