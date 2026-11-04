"""Unit tests for the URLScraper and ProductRawData extractor."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from zerocac.crawler.schema import CrawlerError, ProductRawData
from zerocac.crawler.scraper import URLScraper

MOCK_LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AcmeCloud - Serverless Database for Developers</title>
    <meta name="description" content="Scale your database globally with zero configuration and instant read replicas.">
    <meta property="og:title" content="AcmeCloud: The Serverless Database">
</head>
<body>
    <header>
        <h1>Instant Global Serverless Postgres</h1>
        <h2>Built for modern TypeScript and Python stacks</h2>
    </header>
    <main>
        <p>AcmeCloud automatically provisions serverless Postgres databases in under 300 milliseconds.</p>
        <p>Say goodbye to connection pool limits, manual failover configurations, and high monthly baseline charges.</p>
        <ul>
            <li>Sub-millisecond connection pooling built-in</li>
            <li>Branching workflows matching your Git branches</li>
            <li>Automatic scaling down to zero when idle</li>
        </ul>
        <div>
            <span>Starting at $0/month free tier</span>
            <a href="/signup">Get Started Free</a>
            <button>Try Interactive Sandbox</button>
        </div>
    </main>
</body>
</html>
"""


def test_url_scraper_parses_html_elements_accurately() -> None:
    """Ensure scraper extracts title, headers, bullets, and CTAs correctly."""
    # Arrange
    scraper = URLScraper()
    url = "https://acmecloud.example.com"

    # Act
    raw_data = scraper.parse_html(html=MOCK_LANDING_PAGE_HTML, url=url)

    # Assert
    assert raw_data.url == url
    assert "AcmeCloud - Serverless Database" in raw_data.title
    assert "Scale your database globally" in raw_data.meta_description
    assert any("Instant Global Serverless Postgres" in h for h in raw_data.headers)
    assert any("Sub-millisecond connection pooling" in b for b in raw_data.bullet_points)
    assert any("Get Started Free" in cta for cta in raw_data.calls_to_action)
    assert any("$0/month" in p or "free" in p.lower() for p in raw_data.pricing_hints)


def test_product_raw_data_condensed_text_generation() -> None:
    """Ensure to_condensed_text aggregates DOM signals within limit."""
    # Arrange
    raw_data = ProductRawData(
        url="https://acme.com",
        title="Acme Super",
        meta_description="Fastest widget in town",
        headers=["H1: Fast", "H2: Reliable"],
        bullet_points=["Point 1", "Point 2"],
        calls_to_action=["Start Free"],
    )

    # Act
    condensed = raw_data.to_condensed_text(max_chars=500)

    # Assert
    assert "URL: https://acme.com" in condensed
    assert "Title: Acme Super" in condensed
    assert "Point 1" in condensed
    assert len(condensed) <= 500


@pytest.mark.asyncio
async def test_url_scraper_raises_crawler_error_on_http_failure() -> None:
    """Ensure HTTP 404 or 500 raises typed CrawlerError."""
    # Arrange
    scraper = URLScraper()
    mock_response = AsyncMock()
    mock_response.status_code = 404

    # Act & Assert
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        with pytest.raises(CrawlerError) as exc_info:
            await scraper.crawl_url("https://missing.example.com")

        assert "HTTP 404" in str(exc_info.value)
        assert exc_info.value.status_code == 404
