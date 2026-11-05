"""Search engine indexation client for immediate crawler discovery."""

import logging
from typing import List, Optional
import httpx

from zerocac.deployers.models import IndexNowPayload

logger = logging.getLogger(__name__)

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_TEST_KEY = "zerocac-indexnow-auto-key"


class IndexNowClient:
    """Client for dispatching URLs to Bing and Yandex via the IndexNow protocol."""

    def __init__(self, endpoint: str = INDEXNOW_ENDPOINT, api_key: Optional[str] = None) -> None:
        """Initialize IndexNow client with verification key and endpoint."""
        self.endpoint = endpoint
        self.api_key = api_key or DEFAULT_TEST_KEY

    async def submit_urls(
        self,
        host: str,
        urls: List[str],
        key_location: Optional[str] = None,
        dry_run: bool = False,
    ) -> bool:
        """Submit updated or new URLs to the IndexNow protocol."""
        if not urls:
            logger.info("No URLs provided for IndexNow submission")
            return False

        if dry_run:
            logger.info("IndexNow dry-run: Simulated submission for %d URLs on %s", len(urls), host)
            return True

        payload = IndexNowPayload(
            host=host,
            key=self.api_key,
            key_location=key_location,
            url_list=urls,
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload.model_dump(exclude_none=True),
                    headers={"Content-Type": "application/json; charset=utf-8"},
                )
                if response.status_code in [200, 202]:
                    logger.info("IndexNow submitted successfully for %s (%d URLs)", host, len(urls))
                    return True
                logger.warning(
                    "IndexNow returned non-success status %d: %s",
                    response.status_code,
                    response.text,
                )
                return False
        except httpx.HTTPError as exc:
            logger.error("Failed to connect to IndexNow endpoint: %s", str(exc))
            return False


class SitemapPinger:
    """Dispatches sitemap updates to Google and Bing ping endpoints."""

    async def ping_search_engines(self, sitemap_url: str, dry_run: bool = False) -> bool:
        """Notify major search engines of an updated sitemap XML file."""
        if dry_run or not sitemap_url.startswith("http"):
            logger.info("Simulated search engine sitemap ping for %s", sitemap_url)
            return True

        ping_endpoints = [
            f"https://www.google.com/ping?sitemap={sitemap_url}",
            f"https://www.bing.com/ping?sitemap={sitemap_url}",
        ]

        success_count = 0
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in ping_endpoints:
                try:
                    res = await client.get(url)
                    if res.status_code in [200, 204]:
                        success_count += 1
                except httpx.HTTPError as exc:
                    logger.debug("Failed pinging endpoint %s: %s", url, str(exc))

        return success_count > 0
