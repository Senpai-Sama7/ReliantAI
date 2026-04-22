"""BFS site crawler with Playwright JS rendering for multi-page signal extraction."""
from __future__ import annotations

import asyncio
import logging
import os
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("citadel.crawler")


class SiteCrawler:
    """Breadth-first, same-domain crawler using Playwright headless Chromium."""

    def __init__(
        self,
        max_pages: int | None = None,
        timeout_ms: int | None = None,
    ) -> None:
        self.max_pages = max_pages or int(os.environ.get("CITADEL_CRAWL_MAX_PAGES", "20"))
        self.timeout_ms = timeout_ms or int(os.environ.get("CITADEL_CRAWL_TIMEOUT_MS", "15000"))

    async def crawl(self, start_url: str) -> list[dict]:
        """Crawl *start_url* and return list of ``{url, html, title}`` dicts."""
        from playwright.async_api import async_playwright

        parsed_start = urlparse(start_url)
        domain = parsed_start.netloc.lower()

        visited: set[str] = set()
        queue: list[str] = [start_url]
        results: list[dict] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()

            while queue and len(results) < self.max_pages:
                url = queue.pop(0)
                normalized = self._normalize(url)
                if normalized in visited:
                    continue
                visited.add(normalized)

                try:
                    resp = await page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)
                    if resp is None or resp.status >= 400:
                        logger.warning("skip %s (status %s)", url, resp.status if resp else "None")
                        continue
                    ct = resp.headers.get("content-type", "")
                    if "html" not in ct:
                        continue

                    html = await page.content()
                    title = await page.title()
                    results.append({"url": url, "html": html, "title": title})

                    # Extract same-domain links
                    hrefs = await page.eval_on_selector_all(
                        "a[href]", "els => els.map(e => e.href)"
                    )
                    for href in hrefs:
                        abs_url = urljoin(url, href)
                        p = urlparse(abs_url)
                        if p.netloc.lower() == domain and self._normalize(abs_url) not in visited:
                            queue.append(abs_url)

                except Exception as exc:  # noqa: BLE001
                    logger.warning("error crawling %s: %s", url, exc)

            await browser.close()

        logger.info("crawled %d pages from %s", len(results), start_url)
        return results

    @staticmethod
    def _normalize(url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path.rstrip('/')}".lower()
