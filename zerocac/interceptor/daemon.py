"""24/7 background polling daemon for continuous social opportunity interception."""

import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import List, Optional

from zerocac.analyzer.models import ProductProfile
from zerocac.interceptor.engine import CommunityInterceptorEngine
from zerocac.interceptor.models import (
    AutonomyTier,
    DaemonStatusReport,
    InterceptOpportunity,
    StealthMode,
)
from zerocac.interceptor.notifier import InterceptorNotifier
from zerocac.interceptor.store import InterceptorStore

logger = logging.getLogger(__name__)


class InterceptorDaemon:
    """Continuously monitors developer feeds, dedupes against SQLite, and dispatches tiered responses."""

    def __init__(
        self,
        profile: Optional[ProductProfile] = None,
        tool_url: str = "https://zerocac.org",
        subreddits: Optional[List[str]] = None,
        min_score: int = 75,
        alert_threshold: int = 85,
        stealth_mode: StealthMode = StealthMode.ZERO_LINK_VALUE_TRAP,
        autonomy_tier: AutonomyTier = AutonomyTier.MANUAL_REVIEW,
        poll_interval: float = 60.0,
        dry_run: bool = True,
        store: Optional[InterceptorStore] = None,
        engine: Optional[CommunityInterceptorEngine] = None,
        notifier: Optional[InterceptorNotifier] = None,
    ) -> None:
        """Initialize daemon configuration and dependencies."""
        self.profile = profile or self._build_default_profile()
        self.tool_url = tool_url
        self.subreddits = subreddits
        self.min_score = min_score
        self.alert_threshold = alert_threshold
        self.stealth_mode = stealth_mode
        self.autonomy_tier = autonomy_tier
        self.poll_interval = poll_interval
        self.dry_run = dry_run

        self.store = store or InterceptorStore()
        self.engine = engine or CommunityInterceptorEngine()
        self.notifier = notifier or InterceptorNotifier(alert_threshold=alert_threshold)

        self._is_running = False
        self._start_time: Optional[float] = None
        self._iteration_count = 0
        self._opportunities_found = 0
        self._total_dispatched = 0
        self._last_polled_at: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

    def _build_default_profile(self) -> ProductProfile:
        """Construct fallback product profile if none provided."""
        return ProductProfile(
            product_name="ZeroCAC",
            category="Autonomous Organic Growth Engine",
            one_liner="Scale products to $0 CAC without paid ads",
            core_problem="Rising CPCs and paid ad fatigue",
            solution_mechanism="Autonomous microtools and social intent interception",
            unique_value_proposition="Compounding organic equity that beats paid ads",
            key_features=["Micro-tools", "Live Radar", "pSEO Matrix", "Community Interceptor"],
        )

    async def run_once(self) -> List[InterceptOpportunity]:
        """Execute a single polling iteration across configured social feeds."""
        self._iteration_count += 1
        self._last_polled_at = datetime.now(timezone.utc).isoformat()
        logger.info("Executing interceptor daemon poll pass #%d", self._iteration_count)

        raw_opportunities = await self.engine.scan_opportunities(
            profile=self.profile,
            tool_url=self.tool_url,
            subreddits=self.subreddits,
            min_score=self.min_score,
            stealth_mode=self.stealth_mode,
            dry_run=self.dry_run,
        )

        new_opportunities: List[InterceptOpportunity] = []
        for opp in raw_opportunities:
            if await self.store.is_seen(opp.post_id):
                continue

            await self.store.mark_seen(opp.post_id, opp.platform.value)
            await self.store.save_opportunity(opp)
            self._opportunities_found += 1
            new_opportunities.append(opp)
            await self._process_autonomy_tier(opp)

        return new_opportunities

    async def _process_autonomy_tier(self, opp: InterceptOpportunity) -> None:
        """Evaluate autonomy policy for newly detected qualified opportunity."""
        if self.autonomy_tier == AutonomyTier.FULL_AUTONOMOUS and opp.intent_score >= 90:
            logger.info("Full autonomy dispatching for %s (Score: %d)", opp.opportunity_id, opp.intent_score)
            res = await self.engine.dispatch_reply(opportunity=opp, dry_run=self.dry_run)
            if res.success:
                self._total_dispatched += 1
                await self.store.update_opportunity_status(opp.opportunity_id, "dispatched")
            return

        if self.autonomy_tier == AutonomyTier.CAMOUFLAGE_AUTONOMOUS:
            await self._handle_camouflage_tier(opp)
            return

        # Default MANUAL_REVIEW
        if opp.intent_score >= self.alert_threshold:
            await self.notifier.send_alert(opp, dry_run=self.dry_run)

    async def _handle_camouflage_tier(self, opp: InterceptOpportunity) -> None:
        """Handle 9:1 camouflage checks and notify or dispatch accordingly."""
        if opp.intent_score >= self.alert_threshold:
            await self.notifier.send_alert(opp, dry_run=self.dry_run)

    def mark_started(self) -> None:
        """Mark daemon as active before entering polling loop."""
        self._is_running = True
        if self._start_time is None:
            self._start_time = time.time()

    async def start(self) -> None:
        """Start the continuous background polling loop."""
        self.mark_started()
        logger.info("Interceptor daemon started with poll interval %.1fs", self.poll_interval)


        while self._is_running:
            try:
                await self.run_once()
            except Exception as exc:
                logger.error("Error during interceptor daemon iteration: %s", exc)

            if not self._is_running:
                break
            await asyncio.sleep(self.poll_interval)

    def stop(self) -> None:
        """Halt the background polling loop."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Interceptor daemon stopped after %d iterations", self._iteration_count)

    def get_status(self) -> DaemonStatusReport:
        """Calculate and return real-time operational status report."""
        uptime = (time.time() - self._start_time) if (self._is_running and self._start_time) else 0.0
        return DaemonStatusReport(
            is_running=self._is_running,
            uptime_seconds=round(uptime, 2),
            poll_interval_seconds=self.poll_interval,
            autonomy_tier=self.autonomy_tier,
            total_iterations=self._iteration_count,
            total_opportunities_found=self._opportunities_found,
            total_dispatched=self._total_dispatched,
            last_polled_at=self._last_polled_at,
        )
