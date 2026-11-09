"""Multi-stream social listener polling Reddit, Hacker News, and X for buyer signals."""

import logging
from typing import Any, Dict, List, Set
import httpx

from zerocac.interceptor.models import SocialPlatform

logger = logging.getLogger(__name__)

DEFAULT_SUBREDDITS = ["SaaS", "devops", "startups", "webdev", "sysadmin", "SideProject"]


class SocialStreamListener:
    """Listens to public Reddit JSON feeds, Hacker News Algolia, and social streams."""

    def __init__(self) -> None:
        """Initialize listener with in-memory deduplication set."""
        self._seen_post_ids: Set[str] = set()

    async def fetch_live_posts(
        self,
        subreddits: List[str] = DEFAULT_SUBREDDITS,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch fresh posts across supported platforms filtering previously seen IDs."""
        if dry_run:
            return self._generate_simulated_stream()

        posts: List[Dict[str, Any]] = []
        for sub in subreddits:
            sub_posts = await self._fetch_reddit_subreddit(sub)
            posts.extend(sub_posts)

        hn_posts = await self._fetch_hacker_news_stream()
        posts.extend(hn_posts)

        new_posts = [p for p in posts if p["id"] not in self._seen_post_ids]
        for p in new_posts:
            self._seen_post_ids.add(p["id"])

        return new_posts

    async def _fetch_reddit_subreddit(self, subreddit: str) -> List[Dict[str, Any]]:
        """Fetch latest posts from Reddit public JSON feed."""
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=10"
        headers = {"User-Agent": "ZeroCAC-Interceptor-Engine/1.0"}
        results: List[Dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    children = data.get("data", {}).get("children", [])
                    for c in children:
                        d = c.get("data", {})
                        results.append(self._normalize_reddit_post(d, subreddit))
        except Exception as exc:
            logger.debug("Failed fetching /r/%s: %s", subreddit, str(exc))

        return results

    async def _fetch_hacker_news_stream(self) -> List[Dict[str, Any]]:
        """Fetch latest Ask HN and stories via Algolia API."""
        url = "https://hn.algolia.com/api/v1/search_by_date?tags=(story,ask_hn)&hitsPerPage=10"
        results: List[Dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    hits = res.json().get("hits", [])
                    for h in hits:
                        results.append(self._normalize_hn_post(h))
        except Exception as exc:
            logger.debug("Failed fetching HN stream: %s", str(exc))

        return results

    def _normalize_reddit_post(self, data: Dict[str, Any], sub: str) -> Dict[str, Any]:
        """Convert raw Reddit post dict into standardized format."""
        return {
            "id": data.get("name", f"t3_{data.get('id', '')}"),
            "platform": SocialPlatform.REDDIT,
            "title": data.get("title", ""),
            "body": data.get("selftext", ""),
            "author": data.get("author", "[deleted]"),
            "url": f"https://reddit.com{data.get('permalink', '')}",
            "subreddit_or_topic": sub,
            "created_at_utc": str(data.get("created_utc", "")),
        }

    def _normalize_hn_post(self, hit: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw Algolia hit dict into standardized format."""
        story_id = str(hit.get("objectID", ""))
        return {
            "id": f"hn_{story_id}",
            "platform": SocialPlatform.HACKER_NEWS,
            "title": hit.get("title", ""),
            "body": hit.get("story_text", "") or "",
            "author": hit.get("author", "unknown"),
            "url": f"https://news.ycombinator.com/item?id={story_id}",
            "subreddit_or_topic": "Hacker News",
            "created_at_utc": hit.get("created_at", ""),
        }

    def _generate_simulated_stream(self) -> List[Dict[str, Any]]:
        """Return simulated realistic high-intent buyer posts for dry-run testing."""
        return [
            {
                "id": "t3_sim101",
                "platform": SocialPlatform.REDDIT,
                "title": "Need alternative to Datadog - bill just jumped to $4,500/mo for 25 hosts",
                "body": "Our monthly observability invoice doubled overnight. We have 25 nodes and 400 GB logs. What do you guys use instead of Datadog?",
                "author": "cloud_founder_88",
                "url": "https://reddit.com/r/devops/comments/sim101/datadog_alternative",
                "subreddit_or_topic": "devops",
                "created_at_utc": "2026-11-09T10:00:00Z",
            },
            {
                "id": "t3_sim102",
                "platform": SocialPlatform.REDDIT,
                "title": "Anyone switched away from PagerDuty recently?",
                "body": "Sick of paying $39/seat for 15 engineers just to route alerts. Looking for a modern lightweight alternative.",
                "author": "infra_lead_dan",
                "url": "https://reddit.com/r/SaaS/comments/sim102/pagerduty_switch",
                "subreddit_or_topic": "SaaS",
                "created_at_utc": "2026-11-09T10:15:00Z",
            },
            {
                "id": "hn_sim103",
                "platform": SocialPlatform.HACKER_NEWS,
                "title": "Ask HN: What are you using for incident diagnostics in 2026?",
                "body": "Looking to replace our legacy vendor monitoring setup with something faster and self-hosted or edge deployed.",
                "author": "bytecraft",
                "url": "https://news.ycombinator.com/item?id=sim103",
                "subreddit_or_topic": "Hacker News",
                "created_at_utc": "2026-11-09T10:30:00Z",
            },
        ]
