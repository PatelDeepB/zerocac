"""Web scraper extracting clean structural and semantic signals from product landing pages."""

import re
from typing import List
from bs4 import BeautifulSoup
import httpx

from zerocac.crawler.schema import CrawlerError, ProductRawData


class URLScraper:
    """Fetches and parses landing pages into structured raw signals."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def crawl_url(self, url: str) -> ProductRawData:
        """Fetch URL content and parse into ProductRawData."""
        html = await self._fetch_html(url)
        return self.parse_html(html=html, url=url)

    async def _fetch_html(self, url: str) -> str:
        """Perform HTTP GET request and return raw HTML text."""
        headers = {"User-Agent": self.DEFAULT_USER_AGENT}
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.RequestError as exc:
                raise CrawlerError(f"Network error: {exc}", url) from exc

        if response.status_code >= 400:
            raise CrawlerError(f"HTTP {response.status_code}", url, response.status_code)

        return response.text

    def parse_html(self, html: str, url: str) -> ProductRawData:
        """Parse raw HTML string into structured ProductRawData."""
        soup = BeautifulSoup(html, "html.parser")
        self._remove_noise_elements(soup)

        return ProductRawData(
            url=url,
            title=self._extract_title(soup),
            meta_description=self._extract_meta(soup, "description"),
            og_title=self._extract_meta(soup, "og:title"),
            og_description=self._extract_meta(soup, "og:description"),
            headers=self._extract_headers(soup),
            body_paragraphs=self._extract_paragraphs(soup),
            bullet_points=self._extract_list_items(soup),
            calls_to_action=self._extract_ctas(soup),
            pricing_hints=self._extract_pricing(soup),
        )

    def _remove_noise_elements(self, soup: BeautifulSoup) -> None:
        """Strip non-content elements from the DOM."""
        for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
            tag.decompose()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else ""

    def _extract_meta(self, soup: BeautifulSoup, name: str) -> str:
        """Extract content attribute for meta tag matching name or property."""
        tag = soup.find("meta", attrs={"name": name}) or soup.find(
            "meta", attrs={"property": name}
        )
        return tag.get("content", "").strip() if tag else ""

    def _extract_headers(self, soup: BeautifulSoup) -> List[str]:
        """Extract text from H1, H2, and H3 headers."""
        headers = []
        for header in soup.find_all(["h1", "h2", "h3"]):
            text = header.get_text(strip=True)
            if text and len(text) > 3 and text not in headers:
                headers.append(text)
        return headers[:15]

    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extract meaningful body paragraph snippets."""
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 25 and text not in paragraphs:
                paragraphs.append(text)
        return paragraphs[:10]

    def _extract_list_items(self, soup: BeautifulSoup) -> List[str]:
        """Extract key feature bullet points."""
        items = []
        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if 10 < len(text) < 160 and text not in items:
                items.append(text)
        return items[:15]

    def _extract_ctas(self, soup: BeautifulSoup) -> List[str]:
        """Identify actionable call-to-action button and link labels."""
        ctas = []
        action_keywords = {"start", "try", "get", "join", "sign", "free", "demo", "buy"}
        for element in soup.find_all(["button", "a"]):
            text = element.get_text(strip=True)
            if text and any(kw in text.lower() for kw in action_keywords) and len(text) < 35:
                if text not in ctas:
                    ctas.append(text)
        return ctas[:6]

    def _extract_pricing(self, soup: BeautifulSoup) -> List[str]:
        """Extract potential pricing figures and tier labels."""
        pricing = []
        price_pattern = re.compile(r"(\$\d+(?:\.\d{2})?(?:/(?:mo|month|yr|year))?|free|open source)", re.I)
        for element in soup.find_all(["span", "div", "p"]):
            text = element.get_text(strip=True)
            if price_pattern.search(text) and len(text) < 50:
                if text not in pricing:
                    pricing.append(text)
        return pricing[:6]
