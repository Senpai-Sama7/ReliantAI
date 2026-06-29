"""
CLI entry point for WebsiteForge.

Usage:
    python -m reliantai.agents.websiteforge "Acme HVAC"
    python -m reliantai.agents.websiteforge "Acme HVAC" --url https://acmehvac.com --mode dual
    python -m reliantai.agents.websiteforge "Acme HVAC" --trade hvac --city "Austin, TX" --output-dir ./output
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .agent import ForgeMode, ForgeRequest, WebsiteForgeAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="websiteforge",
        description="FAANG-grade, research-driven website generation agent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "Acme HVAC"
  %(prog)s "Acme HVAC" --url https://acmehvac.com --mode dual
  %(prog)s "Acme HVAC" --trade hvac --city "Austin, TX" --model flash
""",
    )
    parser.add_argument(
        "company_name",
        help="Company name to generate a website for.",
    )
    parser.add_argument(
        "--url",
        default="",
        help="Company website URL (optional, improves research).",
    )
    parser.add_argument(
        "--trade",
        default="",
        choices=["", "hvac", "plumbing", "electrical", "roofing", "painting", "landscaping"],
        help="Trade slug (auto-detected from research if omitted).",
    )
    parser.add_argument(
        "--city",
        default="",
        help='City, State (e.g., "Austin, TX"). Auto-detected if omitted.',
    )
    parser.add_argument(
        "--mode",
        default="standalone_html",
        choices=["standalone_html", "nextjs_isr", "dual"],
        help="Output mode (default: standalone_html).",
    )
    parser.add_argument(
        "--output-dir",
        default="./website_forge_output",
        help="Output directory (default: ./website_forge_output).",
    )
    parser.add_argument(
        "--model",
        default="pro",
        choices=["pro", "flash"],
        help="LLM model tier: pro for quality, flash for speed (default: pro).",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Max forge-repair iterations (default: 3).",
    )
    return parser


async def run(args: argparse.Namespace) -> int:
    mode_map = {
        "standalone_html": ForgeMode.STANDALONE_HTML,
        "nextjs_isr": ForgeMode.NEXTJS_ISR,
        "dual": ForgeMode.DUAL,
    }

    request = ForgeRequest(
        company_name=args.company_name,
        company_url=args.url,
        trade=args.trade,
        city_state=args.city,
        mode=mode_map[args.mode],
        output_dir=args.output_dir,
        max_iterations=args.max_iterations,
    )

    agent = WebsiteForgeAgent(
        output_dir=args.output_dir,
        model=args.model,
    )

    print(f"\n  WebsiteForge — forging website for: {args.company_name}")
    print(f"  Mode: {args.mode} | Model: {args.model} | Output: {args.output_dir}")
    print(f"  {'─' * 60}\n")

    result = await agent.run_for(request)

    print(f"  {'═' * 60}")
    if result.success:
        print(f"  ✅ SUCCESS — gate score: {result.gate_score:.3f}")
    else:
        print(f"  ⚠️  PARTIAL — gate score: {result.gate_score:.3f}")
        if result.gate_violations:
            print(f"  Violations ({len(result.gate_violations)}):")
            for v in result.gate_violations[:5]:
                print(f"    • {v}")

    print(f"  Iterations: {result.iterations}")
    print(f"  Duration: {result.duration_ms:.0f}ms")
    print(f"  Output files:")
    for p in result.output_paths:
        print(f"    → {p}")

    if result.error:
        print(f"  Error: {result.error}")

    content_path = Path(args.output_dir) / agent._make_slug(args.company_name) / "site-content.json"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        json.dumps(result.site_content, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"    → {content_path} (site content JSON)")

    print()
    return 0 if result.success else 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    exit_code = asyncio.run(run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
