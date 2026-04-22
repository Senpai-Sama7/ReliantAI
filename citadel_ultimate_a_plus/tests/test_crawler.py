"""Tests for crawler.py — BFS crawling with mocked Playwright."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from crawler import SiteCrawler


# ---------------------------------------------------------------------------
# Helpers — build a fake Playwright object graph
# ---------------------------------------------------------------------------

def _make_page(pages_map: dict[str, tuple[int, str, str]]):
    """Return a mock Playwright page whose goto/content/title respond per *pages_map*.

    pages_map: {url: (status, html, title)}
    """
    page = AsyncMock()
    visited: list[str] = []

    async def _goto(url, **_kw):
        visited.append(url)
        status, html, title = pages_map.get(url, (404, "", ""))
        resp = MagicMock()
        resp.status = status
        resp.headers = {"content-type": "text/html"}
        page.content.return_value = html
        page.title.return_value = title
        # Return links embedded in the HTML as hrefs
        hrefs = []
        import re
        for m in re.finditer(r'href="([^"]+)"', html):
            hrefs.append(m.group(1))
        page.eval_on_selector_all.return_value = hrefs
        return resp

    page.goto = _goto
    page._visited = visited
    return page


def _make_playwright(page):
    """Wrap a mock page in the full async_playwright context manager chain."""
    browser = AsyncMock()
    browser.new_page.return_value = page
    browser.close = AsyncMock()

    pw = AsyncMock()
    pw.chromium.launch.return_value = browser

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=pw)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_crawl_returns_at_least_one_page():
    pages_map = {
        "https://example.com": (200, "<html><title>Home</title><body>Hello</body></html>", "Home"),
    }
    page = _make_page(pages_map)

    with patch("playwright.async_api.async_playwright", return_value=_make_playwright(page)):
        results = asyncio.run(SiteCrawler(max_pages=5).crawl("https://example.com"))

    assert len(results) >= 1
    assert results[0]["url"] == "https://example.com"
    assert "Hello" in results[0]["html"]
    assert results[0]["title"] == "Home"


def test_respects_max_pages_limit():
    pages_map = {
        "https://example.com": (200, '<html><body><a href="https://example.com/a">A</a><a href="https://example.com/b">B</a></body></html>', "Home"),
        "https://example.com/a": (200, "<html><body>Page A</body></html>", "A"),
        "https://example.com/b": (200, "<html><body>Page B</body></html>", "B"),
    }
    page = _make_page(pages_map)

    with patch("playwright.async_api.async_playwright", return_value=_make_playwright(page)):
        results = asyncio.run(SiteCrawler(max_pages=2).crawl("https://example.com"))

    assert len(results) == 2


def test_does_not_follow_cross_domain_links():
    pages_map = {
        "https://example.com": (200, '<html><body><a href="https://other.com/page">External</a></body></html>', "Home"),
        "https://other.com/page": (200, "<html><body>Other</body></html>", "Other"),
    }
    page = _make_page(pages_map)

    with patch("playwright.async_api.async_playwright", return_value=_make_playwright(page)):
        results = asyncio.run(SiteCrawler(max_pages=10).crawl("https://example.com"))

    assert len(results) == 1
    assert all(r["url"].startswith("https://example.com") for r in results)


def test_handles_navigation_error_gracefully():
    page = AsyncMock()

    call_count = 0

    async def _goto(url, **_kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("Navigation timeout")
        return None  # second call won't happen since queue is empty after first

    page.goto = _goto
    page.eval_on_selector_all = AsyncMock(return_value=[])

    with patch("playwright.async_api.async_playwright", return_value=_make_playwright(page)):
        results = asyncio.run(SiteCrawler(max_pages=3).crawl("https://example.com"))

    # Should not crash — returns empty list since the only page errored
    assert isinstance(results, list)


def test_returns_correct_dict_structure():
    pages_map = {
        "https://example.com": (200, "<html><title>Test</title><body>Content</body></html>", "Test"),
    }
    page = _make_page(pages_map)

    with patch("playwright.async_api.async_playwright", return_value=_make_playwright(page)):
        results = asyncio.run(SiteCrawler(max_pages=1).crawl("https://example.com"))

    assert len(results) == 1
    r = results[0]
    assert "url" in r
    assert "html" in r
    assert "title" in r
    assert isinstance(r["url"], str)
    assert isinstance(r["html"], str)
    assert isinstance(r["title"], str)
