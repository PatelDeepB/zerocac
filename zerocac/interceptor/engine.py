"""Master Community Interceptor Engine orchestrating detection, scoring, and dispatch."""

import logging
from typing import Any, Dict, List, Optional

from zerocac.analyzer.models import ProductProfile
from zerocac.interceptor.extractor import NumericEntityExtractor
from zerocac.interceptor.listener import DEFAULT_SUBREDDITS, SocialStreamListener
from zerocac.interceptor.models import (
    InterceptDispatchResult,
    InterceptOpportunity,
    StealthMode,
)
from zerocac.interceptor.poster import SocialPoster
from zerocac.interceptor.scorer import IntentScorer
from zerocac.interceptor.synthesizer import PractitionerReplySynthesizer
from zerocac.interceptor.vault import AccountVault

logger = logging.getLogger(__name__)


class CommunityInterceptorEngine:
    """Detects high-intent buyer pain queries and coordinates authentic practitioner replies."""

    def __init__(
        self,
        listener: Optional[SocialStreamListener] = None,
        extractor: Optional[NumericEntityExtractor] = None,
        scorer: Optional[IntentScorer] = None,
        synthesizer: Optional[PractitionerReplySynthesizer] = None,
        vault: Optional[AccountVault] = None,
        poster: Optional[SocialPoster] = None,
    ) -> None:
        """Initialize engine with modular subcomponents."""
        self.listener = listener or SocialStreamListener()
        self.extractor = extractor or NumericEntityExtractor()
        self.scorer = scorer or IntentScorer()
        self.synthesizer = synthesizer or PractitionerReplySynthesizer()
        self.vault = vault or AccountVault()
        self.poster = poster or SocialPoster()
        self._history: List[InterceptOpportunity] = []

    async def scan_opportunities(
        self,
        profile: ProductProfile,
        tool_url: str = "https://yourproduct.com",
        subreddits: Optional[List[str]] = None,
        min_score: int = 75,
        stealth_mode: StealthMode = StealthMode.ZERO_LINK_VALUE_TRAP,
        dry_run: bool = False,
    ) -> List[InterceptOpportunity]:
        """Scan live social feeds, score buying intent, and synthesize practitioner answers."""
        target_subs = subreddits or DEFAULT_SUBREDDITS
        raw_posts = await self.listener.fetch_live_posts(subreddits=target_subs, dry_run=dry_run)
        competitor_names = [g.competitor_name for g in profile.competitor_gaps]

        opportunities: List[InterceptOpportunity] = []
        for post in raw_posts:
            score, classification, detected_comp = self.scorer.score_post(
                title=post["title"],
                body=post["body"],
                competitor_names=competitor_names,
            )

            if score < min_score:
                continue

            entities = self.extractor.extract_entities(f"{post['title']} {post['body']}")
            opp = InterceptOpportunity(
                platform=post["platform"],
                post_id=post["id"],
                post_url=post["url"],
                subreddit_or_topic=post["subreddit_or_topic"],
                author=post["author"],
                title=post["title"],
                body_text=post["body"],
                created_at_utc=post["created_at_utc"],
                intent_score=score,
                classification=classification,
                detected_competitor=detected_comp,
                extracted_entities=entities,
                stealth_mode=stealth_mode,
                synthesized_reply="",
            )

            opp.synthesized_reply = self.synthesizer.synthesize_reply(opp, profile, tool_url)
            opportunities.append(opp)
            self._history.append(opp)

        return opportunities

    async def dispatch_reply(
        self,
        opportunity: InterceptOpportunity,
        account_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> InterceptDispatchResult:
        """Publish approved reply using an optimal account from the vault."""
        account = self.vault.get_account(account_id) if account_id else self.vault.select_safe_account(opportunity.platform)
        res = await self.poster.post_reply(opportunity, opportunity.synthesized_reply, account=account, dry_run=dry_run)

        if res.success and account:
            self.vault.camouflage.record_activity(account, is_promotional=True)
            opportunity.status = "dispatched"

        return res

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Compute aggregated interception metrics and displaced Google Ads budget."""
        total_intercepts = len(self._history)
        dispatched_count = sum(1 for o in self._history if o.status == "dispatched")
        est_clicks = dispatched_count * 45
        est_leads = int(est_clicks * 0.12)
        ad_savings_usd = est_leads * 35.0

        return {
            "total_opportunities_detected": total_intercepts,
            "total_dispatched": dispatched_count,
            "estimated_inbound_clicks": est_clicks,
            "estimated_leads_acquired": est_leads,
            "estimated_ad_savings_usd": ad_savings_usd,
        }
