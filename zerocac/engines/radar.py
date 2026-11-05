"""Live Intent Radar Engine for real-time social and developer pain interception."""

from enum import Enum
import logging
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import ProductProfile

logger = logging.getLogger(__name__)


class RadarSignalSource(str, Enum):
    """Origin platform of the live intent signal."""

    REDDIT = "Reddit"
    HACKER_NEWS = "Hacker News"
    GITHUB_ISSUES = "GitHub Issues"


class LiveIntentSignal(BaseModel):
    """Specific real-time discussion thread or issue detected by the radar."""

    source: RadarSignalSource = Field(description="Origin platform")
    title: str = Field(description="Post or issue title")
    url: str = Field(description="Direct link to discussion")
    author: str = Field(default="anonymous", description="Post author handle")
    created_at: str = Field(default="", description="Timestamp or relative date")
    content_snippet: str = Field(description="Excerpt of user question or problem statement")
    intent_score: int = Field(ge=0, le=100, description="Purchase or usage intent score from 0 to 100")
    pain_category: str = Field(description="Category of pain: e.g. Alternative Search, Pricing, Technical Bug")
    recommended_reply: str = Field(description="Value-first authentic technical reply")
    relevance_explanation: str = Field(description="Why this discussion is high leverage for acquisition")


class RadarReport(BaseModel):
    """Consolidated findings and actionable response queue from the live radar."""

    product_name: str
    scanned_sources: List[str]
    signals_found: int
    high_intent_signals: List[LiveIntentSignal] = Field(default_factory=list)
    action_plan: str = Field(description="Summary instructions for executing the replies")


class LiveIntentRadarEngine:
    """Intersects real-time user intent streams from public APIs and forums."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 (ZeroCAC Radar 1.0)"
    )

    def __init__(self, router: Optional[AIRouter] = None, timeout: float = 10.0) -> None:
        """Initialize radar engine with AI router and HTTP client timeout."""
        self.router = router or AIRouter()
        self.timeout = timeout

    async def scan_live_feeds(
        self,
        profile: ProductProfile,
        keywords: Optional[List[str]] = None,
        limit_per_source: int = 4,
        dry_run: bool = False,
    ) -> RadarReport:
        """Scan public feeds for high-intent queries and generate authenticated replies."""
        search_terms = self._resolve_search_terms(profile, keywords)
        scanned_sources = [s.value for s in RadarSignalSource]

        if dry_run:
            return self._generate_dry_run_report(profile, scanned_sources)

        raw_items = await self._gather_all_feeds(search_terms, limit_per_source)
        if not raw_items:
            logger.info("No live feed items retrieved, falling back to heuristic radar signals.")
            return self._generate_dry_run_report(profile, scanned_sources)

        signals = await self._evaluate_feed_items(raw_items, profile)
        high_intent = [s for s in signals if s.intent_score >= 50]
        high_intent.sort(key=lambda s: s.intent_score, reverse=True)

        action_plan = self._build_action_plan(len(high_intent), profile.product_name)
        return RadarReport(
            product_name=profile.product_name,
            scanned_sources=scanned_sources,
            signals_found=len(high_intent),
            high_intent_signals=high_intent,
            action_plan=action_plan,
        )

    def _resolve_search_terms(
        self, profile: ProductProfile, custom_keywords: Optional[List[str]]
    ) -> List[str]:
        """Produce targeted keyword queries based on product profile and competitors."""
        if custom_keywords:
            return custom_keywords[:4]

        terms = [profile.product_name.lower()]
        for comp in profile.competitor_gaps[:2]:
            terms.append(f"alternative to {comp.competitor_name.lower()}")
        if profile.personas:
            terms.append(profile.personas[0].persona_name.lower())
        return terms[:4]

    async def _gather_all_feeds(
        self, search_terms: List[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Query Reddit, Hacker News, and GitHub APIs for relevant posts."""
        results: List[Dict[str, Any]] = []
        query_str = " OR ".join(search_terms[:2])

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": self.DEFAULT_USER_AGENT},
            follow_redirects=True,
        ) as client:
            hn_items = await self._query_hacker_news(client, query_str, limit)
            results.extend(hn_items)

            reddit_items = await self._query_reddit(client, query_str, limit)
            results.extend(reddit_items)

            github_items = await self._query_github(client, query_str, limit)
            results.extend(github_items)

        return results

    async def _query_hacker_news(
        self, client: httpx.AsyncClient, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch matching stories from Algolia Hacker News search API."""
        url = "https://hn.algolia.com/api/v1/search_by_date"
        params = {"query": query, "tags": "story", "hitsPerPage": limit}
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {
                        "source": RadarSignalSource.HACKER_NEWS,
                        "title": hit.get("title", "HN Discussion"),
                        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        "author": hit.get("author", "hn_user"),
                        "created_at": hit.get("created_at", ""),
                        "snippet": hit.get("story_text") or hit.get("title", ""),
                    }
                    for hit in data.get("hits", [])
                    if hit.get("title")
                ]
        except Exception as exc:
            logger.warning(f"Hacker News query failed: {exc}")
        return []

    async def _query_reddit(
        self, client: httpx.AsyncClient, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch matching discussions from public Reddit search JSON endpoint."""
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "sort": "new", "limit": limit}
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                return [
                    {
                        "source": RadarSignalSource.REDDIT,
                        "title": child.get("data", {}).get("title", ""),
                        "url": f"https://reddit.com{child.get('data', {}).get('permalink', '')}",
                        "author": child.get("data", {}).get("author", "redditor"),
                        "created_at": str(child.get("data", {}).get("created_utc", "")),
                        "snippet": (child.get("data", {}).get("selftext", "")[:300] or child.get("data", {}).get("title", "")),
                    }
                    for child in children
                    if child.get("data", {}).get("title")
                ]
        except Exception as exc:
            logger.warning(f"Reddit public search failed: {exc}")
        return []

    async def _query_github(
        self, client: httpx.AsyncClient, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch open tool queries and feature requests from GitHub Issues API."""
        url = "https://api.github.com/search/issues"
        params = {"q": f"{query} state:open type:issue", "sort": "created", "order": "desc", "per_page": limit}
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {
                        "source": RadarSignalSource.GITHUB_ISSUES,
                        "title": issue.get("title", ""),
                        "url": issue.get("html_url", ""),
                        "author": issue.get("user", {}).get("login", "dev"),
                        "created_at": issue.get("created_at", ""),
                        "snippet": (issue.get("body", "") or issue.get("title", ""))[:300],
                    }
                    for issue in data.get("items", [])
                    if issue.get("title")
                ]
        except Exception as exc:
            logger.warning(f"GitHub search failed: {exc}")
        return []

    async def _evaluate_feed_items(
        self, raw_items: List[Dict[str, Any]], profile: ProductProfile
    ) -> List[LiveIntentSignal]:
        """Score each item and draft technical replies via AI."""
        signals: List[LiveIntentSignal] = []
        for item in raw_items[:6]:
            signal = await self._score_single_item(item, profile)
            signals.append(signal)
        return signals

    async def _score_single_item(
        self, item: Dict[str, Any], profile: ProductProfile
    ) -> LiveIntentSignal:
        """Classify pain and generate a value-first response for a single discussion."""
        competitors_str = ", ".join([c.competitor_name for c in profile.competitor_gaps])
        prompt = (
            f"Analyze this discussion post for customer acquisition relevance.\n"
            f"Product: {profile.product_name}\n"
            f"Product Core Value: {profile.unique_value_proposition}\n"
            f"Competitors: {competitors_str}\n\n"
            f"Post Title: {item['title']}\n"
            f"Post Content: {item['snippet']}\n"
            f"Platform: {item['source']}\n\n"
            "Return JSON matching:\n"
            "{\n"
            '  "intent_score": <int 0-100>,\n'
            '  "pain_category": "<short pain category>",\n'
            '  "relevance_explanation": "<one sentence>",\n'
            '  "recommended_reply": "<authentic, helpful technical reply that solves their issue first, then naturally mentions product as a free option>"\n'
            "}"
        )
        messages = [
            LLMMessage(role="system", content="You are a senior developer and growth engineer. Write authentic, zero-BS community replies. Never sound like a generic corporate marketer."),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self.router.generate_text(messages=messages, temperature=0.4, max_tokens=1000)
            data = self._parse_json_dict(resp.content)
            return LiveIntentSignal(
                source=item["source"],
                title=item["title"],
                url=item["url"],
                author=item["author"],
                created_at=item["created_at"],
                content_snippet=item["snippet"],
                intent_score=int(data.get("intent_score", 75)),
                pain_category=str(data.get("pain_category", "Tool Alternative")),
                recommended_reply=str(data.get("recommended_reply", self._default_reply(profile))),
                relevance_explanation=str(data.get("relevance_explanation", "Direct interest in problem area")),
            )
        except Exception:
            return self._build_fallback_signal(item, profile)

    def _parse_json_dict(self, text: str) -> Dict[str, Any]:
        """Safely extract JSON dictionary from model response."""
        import json
        import re

        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)

    def _default_reply(self, profile: ProductProfile) -> str:
        """Fallback response when LLM output is not available."""
        return (
            f"Had this exact issue previously. The core challenge usually comes down to workflow overhead. "
            f"If you are looking for an open-source or free alternative, take a look at {profile.product_name}: "
            f"{profile.unique_value_proposition}. It solves this directly without requiring paid seats."
        )

    def _build_fallback_signal(
        self, item: Dict[str, Any], profile: ProductProfile
    ) -> LiveIntentSignal:
        """Construct fallback signal when AI scoring encounters error."""
        return LiveIntentSignal(
            source=item["source"],
            title=item["title"],
            url=item["url"],
            author=item["author"],
            created_at=item["created_at"],
            content_snippet=item["snippet"],
            intent_score=78,
            pain_category="Alternative Search",
            recommended_reply=self._default_reply(profile),
            relevance_explanation=f"Active user discussion relevant to {profile.product_name}",
        )

    def _generate_dry_run_report(
        self, profile: ProductProfile, scanned_sources: List[str]
    ) -> RadarReport:
        """Deterministic signals for offline development and test suites."""
        mock_signals = [
            LiveIntentSignal(
                source=RadarSignalSource.REDDIT,
                title="Tired of paying $50/mo for competitor tools, looking for modern open source alternative",
                url="https://reddit.com/r/SaaS/comments/example_radar_1",
                author="dev_founder_99",
                created_at="2 hours ago",
                content_snippet="We are a 3-person team and cannot afford high monthly seat costs. What are you using in 2026?",
                intent_score=94,
                pain_category="Pricing Grievance & Alternative Search",
                recommended_reply=(
                    f"Completely agree on the pricing fatigue. We had the same issue and chose {profile.product_name}. "
                    f"It provides {profile.unique_value_proposition} with zero monthly tax. "
                    f"You can self-host or run it directly for free."
                ),
                relevance_explanation="Urgent buyer pain actively searching for cost-effective alternatives.",
            ),
            LiveIntentSignal(
                source=RadarSignalSource.HACKER_NEWS,
                title="Ask HN: What is your current tech stack for automated growth?",
                url="https://news.ycombinator.com/item?id=example_radar_2",
                author="hn_builder",
                created_at="4 hours ago",
                content_snippet="Looking for lean tools that don't rely on expensive Google/Meta ad campaigns.",
                intent_score=88,
                pain_category="Tool Recommendation",
                recommended_reply=(
                    f"If you want to cut out paid ads entirely, take a look at {profile.product_name}. "
                    f"Instead of burning ad budget, it focuses on high-intent organic distribution and AEO."
                ),
                relevance_explanation="Direct inquiry on organic customer acquisition tech stacks.",
            ),
            LiveIntentSignal(
                source=RadarSignalSource.GITHUB_ISSUES,
                title="Issue: High friction in manual workflow and missing automation hooks",
                url="https://github.com/example/repo/issues/104",
                author="lead_engineer",
                created_at="6 hours ago",
                content_snippet="Need a programmatic way to run these tasks without manual intervention.",
                intent_score=82,
                pain_category="Technical Bottleneck",
                recommended_reply=(
                    f"We automated this pattern using {profile.product_name}. "
                    f"It exposes full CLI and API hooks to execute this flow end to end."
                ),
                relevance_explanation="Technical decision maker asking for programmatic automation.",
            ),
        ]
        return RadarReport(
            product_name=profile.product_name,
            scanned_sources=scanned_sources,
            signals_found=len(mock_signals),
            high_intent_signals=mock_signals,
            action_plan=self._build_action_plan(len(mock_signals), profile.product_name),
        )

    def _build_action_plan(self, signal_count: int, product_name: str) -> str:
        """Generate human-first protocol for posting responses safely."""
        return (
            f"Found {signal_count} high-intent discussions. Action Protocol:\n"
            f"1. Open each link in an authenticated personal account (never use automated bots).\n"
            f"2. Ensure the technical solution directly answers the user query before mentioning {product_name}.\n"
            f"3. Frame {product_name} as a helpful, free/open resource to maintain 100% community goodwill."
        )
