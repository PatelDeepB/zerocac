"""Synthesizer and API client for Vector 5: Multi-Platform Tech Publishing."""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from zerocac.analyzer.models import ProductProfile
from zerocac.launch.models import TechnicalArticle

logger = logging.getLogger(__name__)

DEVTO_API_URL = "https://dev.to/api/articles"


class PublishingSyndicator:
    """Publishes technical case studies to Dev.to, Hashnode, and Medium with canonical tags."""

    def __init__(self, devto_api_key: Optional[str] = None) -> None:
        """Initialize with Dev.to API key."""
        self.devto_api_key = devto_api_key or os.getenv("DEVTO_API_KEY")

    def synthesize_articles(
        self,
        profile: ProductProfile,
        live_url: str,
        tool_name: str,
    ) -> List[TechnicalArticle]:
        """Generate long-form engineering case studies with canonical attribution."""
        article_md = (
            f"# Why We Ditched Paid Ads to Build an Open {profile.category} Tool\n\n"
            f"Customer Acquisition Cost (CAC) is at an all-time high. In 2026, blowing venture capital or bootstrapped "
            f"savings on Google and Meta ads creates zero permanent enterprise equity.\n\n"
            f"## The Problem with Traditional Marketing\n"
            f"We repeatedly encountered founders and teams complaining that: *{profile.core_problem}*\n\n"
            f"Traditional marketing says: write a 2,000-word SEO article or spend $5 per click. "
            f"We chose a third path: **Engineering-as-Marketing**.\n\n"
            f"## Building {tool_name}\n"
            f"Instead of asking users to read about a solution, we built an interactive tool that gives them "
            f"the solution instantly: [{tool_name}]({live_url}).\n\n"
            f"### Architecture Highlights:\n"
            f"- Single-file vanilla HTML/CSS/JS deployed to the edge.\n"
            f"- Zero telemetry bloat or heavy client frameworks.\n"
            f"- Sub-5ms client-side calculation reactivity.\n\n"
            f"You can explore the live calculator here: [{live_url}]({live_url})."
        )

        return [
            TechnicalArticle(
                platform="devto",
                title=f"How We Replaced Paid Ads with a Free {profile.category} Utility",
                markdown_content=article_md,
                canonical_url=live_url,
                tags=["webdev", "javascript", "showdev", "opensource"],
            ),
            TechnicalArticle(
                platform="hashnode",
                title=f"Engineering-as-Marketing: Building {tool_name} for $0 CAC",
                markdown_content=article_md,
                canonical_url=live_url,
                tags=["software-development", "saas", "frontend"],
            ),
        ]

    async def publish_to_devto(
        self,
        article: TechnicalArticle,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Dispatch article to Dev.to REST API."""
        if not self.devto_api_key or dry_run:
            logger.info("Simulated Dev.to article publication: '%s'", article.title)
            return {
                "success": True,
                "url": f"https://dev.to/simulated/{article.title.lower().replace(' ', '-')}",
                "dry_run": True,
            }

        headers = {
            "api-key": self.devto_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "article": {
                "title": article.title,
                "published": True,
                "body_markdown": article.markdown_content,
                "tags": article.tags[:4],
                "canonical_url": article.canonical_url,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(DEVTO_API_URL, headers=headers, json=payload)
                if res.status_code in [200, 201]:
                    data = res.json()
                    return {"success": True, "url": data.get("url"), "dry_run": False}
                return {"success": False, "error": f"Dev.to API error {res.status_code}: {res.text}"}
        except httpx.HTTPError as exc:
            return {"success": False, "error": str(exc)}
