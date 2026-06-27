"""
Web research tools for WebsiteForge Discovery phase.

Robust web search + brand analysis with graceful degradation.
Uses httpx for HTTP (sync-compatible via asyncio).
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import httpx

from ...core import get_logger

log = get_logger("agents.websiteforge.researcher")

USER_AGENT = "WebsiteForge/0.1 (research bot; +https://reliantai.org/bot)"
REQUEST_TIMEOUT = 10.0


async def _get(url: str, params: dict | None = None) -> dict | None:
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return {"status": resp.status_code, "text": resp.text[:8000]}
    except Exception as exc:
        log.warning("http_get_failed", url=url, error=str(exc))
    return None


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web. Uses DuckDuckGo HTML endpoint (no API key required).
    Returns list of {title, url, snippet}.
    """
    results: list[dict] = []
    try:
        data = await _get(
            "https://html.duckduckgo.com/html/",
            params={"q": query, "kl": "us-en"},
        )
        if not data:
            return results

        # Parse DDG HTML results
        text = data["text"]
        titles = re.findall(r'<a[^>]+class="result__a"[^>]*>(.*?)</a>', text, re.S)
        urls = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"', text)
        snippets = re.findall(
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', text, re.S
        )

        for i in range(min(max_results, len(titles))):
            results.append(
                {
                    "title": re.sub(r"<.*?>", "", titles[i]).strip(),
                    "url": urls[i] if i < len(urls) else "",
                    "snippet": re.sub(r"<.*?>", "", snippets[i]).strip()
                    if i < len(snippets)
                    else "",
                }
            )
    except Exception as exc:
        log.warning("web_search_failed", query=query, error=str(exc))

    log.info("web_search_complete", query=query, results=len(results))
    return results


async def fetch_page_text(url: str, max_chars: int = 5000) -> str:
    """Fetch a page and return cleaned text content."""
    data = await _get(url)
    if not data:
        return ""

    # Strip tags, collapse whitespace
    text = re.sub(r"<script[^>]*>.*?</script>", " ", data["text"], flags=re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


async def analyze_brand(company_name: str, url: str = "") -> dict[str, Any]:
    """
    Research a company's brand, market position, and target audience.
    Searches web + fetches homepage if URL provided.
    """
    queries = [
        f'"{company_name}" reviews services',
        f'"{company_name}" about us mission',
        f'"{company_name}" BBB rating complaints',
    ]
    if url:
        queries.insert(0, f'"{company_name}" site:{url}')

    all_results: list[dict] = []
    for q in queries:
        results = await web_search(q, max_results=3)
        all_results.extend(results)

    # Try fetching their homepage
    homepage_text = ""
    if url:
        homepage_text = await fetch_page_text(url, max_chars=4000)
    elif all_results:
        first_url = all_results[0].get("url", "")
        if first_url and first_url.startswith("http"):
            homepage_text = await fetch_page_text(first_url, max_chars=4000)

    # Extract brand signals
    signals: dict[str, Any] = {
        "name": company_name,
        "homepage_content": homepage_text[:2000] if homepage_text else None,
        "top_search_results": [
            {"title": r["title"], "url": r["url"], "snippet": r["snippet"]}
            for r in all_results[:6]
        ],
    }

    # Detect city from search results
    city_match = re.search(
        r"(?:in|serving|located|based in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})",
        homepage_text or " ".join(r["snippet"] for r in all_results),
    )
    if city_match:
        signals["city"] = f"{city_match.group(1)}, {city_match.group(2)}"

    # Detect trade from content
    trade_keywords = {
        "hvac": ["hvac", "heating", "cooling", "air conditioning", "ac repair"],
        "plumbing": ["plumbing", "plumber", "drain", "water heater"],
        "electrical": ["electrician", "electrical", "wiring", "panel"],
        "roofing": ["roofing", "roofer", "roof repair", "shingle"],
        "painting": ["painting", "painter", "interior paint", "exterior paint"],
        "landscaping": ["landscaping", "landscaper", "lawn care", "irrigation"],
    }
    combined = (homepage_text + " " + " ".join(r["snippet"] for r in all_results)).lower()
    detected_trade = "hvac"
    for trade, keywords in trade_keywords.items():
        if any(kw in combined for kw in keywords):
            detected_trade = trade
            break
    signals["trade"] = detected_trade

    # Extract facts (citations for copy generation)
    facts: list[str] = []
    for r in all_results:
        if r["snippet"] and len(r["snippet"]) > 20:
            facts.append(r["snippet"][:200])

    audience: dict[str, Any] = {
        "detected_from": "search_snippets + homepage",
        "indicators": [],  # Could be enhanced with more NLP
    }

    return {
        "signals": signals,
        "audience": audience,
        "trade": detected_trade,
        "facts": facts[:10],
        "queries": queries,
        "city": signals.get("city", ""),
    }


async def find_competitors(company_name: str, city: str = "", max_results: int = 3) -> list[dict]:
    """Find top competitors in the same market."""
    location = city or ""
    query = f'best {company_name} competitors {location}'
    results = await web_search(query, max_results=max_results + 2)

    competitors = []
    for r in results:
        url = r.get("url", "")
        if url and company_name.lower() not in r["title"].lower():
            competitors.append(
                {
                    "name": r["title"],
                    "url": url,
                    "snippet": r["snippet"],
                }
            )
        if len(competitors) >= max_results:
            break

    return competitors
