"""
isr_renderer — Next.js ISR scaffold orchestrator.

Generates a complete Next.js 16 project (App Router, ISR revalidation,
static site-content export) and writes it to output_dir.

Template strings live in nextjs_templates.py; this module only wires them
together and writes the file tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...core import get_logger
from .nextjs_templates import (
    GLOBAL_CSS,
    _layout_tsx,
    _page_tsx,
    _loading_tsx,
    _error_tsx,
    _revalidate_route,
    _site_content_ts,
    _slug_ts,
    _next_config,
    _tailwind_config,
    _postcss_config,
    _tsconfig,
    _package_json,
    _gitignore,
    _readme,
)

log = get_logger("agents.websiteforge.isr_renderer")


async def render_isr_scaffold(
    site_content: dict[str, Any],
    output_dir: Path,
) -> Path:
    """
    Write a full Next.js App Router project to output_dir.

    Creates the complete file tree ready for ``npm install && npm run dev``.
    """
    bus = site_content.get("business", {})
    name = bus.get("business_name", "Site")
    theme = site_content.get("site_config", {}).get("theme", {})
    primary = theme.get("primary", "#1e3a5f")
    accent = theme.get("accent", "#3b82f6")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    css = GLOBAL_CSS.replace("__PRIMARY__", primary).replace("__ACCENT__", accent)

    files: dict[str, str] = {
        "app/globals.css": css,
        "app/layout.tsx": _layout_tsx(name),
        "app/[slug]/page.tsx": _page_tsx(),
        "app/[slug]/loading.tsx": _loading_tsx(),
        "app/[slug]/error.tsx": _error_tsx(),
        "app/api/revalidate/route.ts": _revalidate_route(),
        "lib/site-content.ts": _site_content_ts(site_content),
        "lib/slug.ts": _slug_ts(),
        "package.json": _package_json(name),
        "tsconfig.json": _tsconfig(),
        "tailwind.config.ts": _tailwind_config(),
        "postcss.config.js": _postcss_config(),
        ".gitignore": _gitignore(),
        "README.md": _readme(name),
        "next.config.ts": _next_config(),
        "next-env.d.ts": "/// <reference types=\"next\" />\n",
    }

    for rel_path, content in files.items():
        path = output_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log.info("isr_renderer.wrote", path=str(path), size=len(content))

    log.info(
        "isr_renderer.complete",
        name=name,
        output=str(output_dir),
        file_count=len(files),
    )
    return output_dir
