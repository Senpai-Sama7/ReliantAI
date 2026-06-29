"""
competitor_scout — find and rank top competitors in the same market.

Thin wrapper over researcher.find_competitors with ranking logic
to identify the top 3 competitors by relevance.
"""

from __future__ import annotations

from typing import Any

from ...core import get_logger
from .researcher import find_competitors, web_search

log = get_logger("agents.websiteforge.competitor_scout")


async def run(
    company_name: str,
    city: str = "",
    trade: str = "",
    max_results: int = 3,
) -> list[dict[str, Any]]:
    """
    Find and rank top competitors for the given company.

    Args:
        company_name: The company to find competitors for.
        city: Optional city to scope the search.
        trade: Optional trade to scope the search (hvac, plumbing, etc.).
        max_results: Maximum number of competitors to return.

    Returns:
        List of competitor dicts, each with:
        - name: Competitor business name
        - url: Their website URL
        - snippet: Search result snippet
        - relevance: "high" | "medium" | "low"
    """
    log.info(
        "competitor_scout.start",
        company=company_name,
        city=city,
        trade=trade,
    )

    location = f"{city} " if city else ""
    trade_term = trade or "home services"

    query = f"best {trade_term} companies {location}-site:{company_name.lower().replace(' ', '')}.com"
    results = await web_search(query, max_results=max_results + 5)

    competitors: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for r in results:
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("snippet", "")

        if company_name.lower() in title.lower():
            continue
        if url and company_name.lower().replace(" ", "") in url.lower():
            continue

        clean_name = title.split(" - ")[0].split(" | ")[0].strip()
        if clean_name.lower() in seen_names:
            continue
        seen_names.add(clean_name.lower())

        relevance = _rank_relevance(snippet, city, trade)

        competitors.append(
            {
                "name": clean_name,
                "url": url,
                "snippet": snippet[:200],
                "relevance": relevance,
            }
        )

        if len(competitors) >= max_results:
            break

    competitors.sort(
        key=lambda c: {"high": 0, "medium": 1, "low": 2}[c["relevance"]]
    )

    log.info(
        "competitor_scout.complete",
        company=company_name,
        found=len(competitors),
    )
    return competitors


def _rank_relevance(snippet: str, city: str, trade: str) -> str:
    """Rank a competitor's relevance as high, medium, or low."""
    score = 0
    lower = snippet.lower()

    if city and city.lower().split(",")[0] in lower:
        score += 2
    if trade and trade.lower() in lower:
        score += 2
    if any(word in lower for word in ["reviews", "rating", "years", "licensed"]):
        score += 1

    if score >= 3:
        return "high"
    elif score >= 1:
        return "medium"
    return "low"
