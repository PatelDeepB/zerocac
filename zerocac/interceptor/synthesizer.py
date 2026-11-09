"""Synthesizes practitioner-grade responses with dynamic math and stealth modes."""

import logging
from typing import Any, Dict
from urllib.parse import quote_plus

from zerocac.analyzer.models import ProductProfile
from zerocac.interceptor.models import InterceptOpportunity, StealthMode

logger = logging.getLogger(__name__)


class PractitionerReplySynthesizer:
    """Generates authentic engineer responses avoiding sales fluff and spam detection."""

    def synthesize_reply(
        self,
        opportunity: InterceptOpportunity,
        profile: ProductProfile,
        tool_url: str,
    ) -> str:
        """Compose 3-part practitioner response with dynamic math and chosen stealth link."""
        p1 = self._build_technical_advice(opportunity, profile)
        p2 = self._build_unit_economic_math(opportunity.extracted_entities, opportunity.detected_competitor or "the incumbent")
        p3 = self._build_stealth_closing(opportunity, tool_url)

        return f"{p1}\n\n{p2}\n\n{p3}"

    def _build_technical_advice(self, opp: InterceptOpportunity, profile: ProductProfile) -> str:
        """Draft first paragraph addressing the technical core of the post."""
        comp = opp.detected_competitor or "traditional vendor tooling"
        return (
            f"Having migrated multiple production stacks off {comp}, the hidden trap is almost always "
            f"in custom metric retention and ingest fees rather than baseline host count. Before committing "
            f"to a heavy rip-and-replace, look at decoupling your ingestion path from your dashboard tier. "
            f"Adopting an open or edge-deployed diagnostic model eliminates the perpetual seat tax while "
            f"dropping mean-time-to-resolution to under a minute."
        )

    def _build_unit_economic_math(self, entities: Dict[str, Any], competitor_name: str) -> str:
        """Draft second paragraph performing dynamic calculations on extracted numbers."""
        budget = entities.get("budget_or_bill_usd")
        volume = entities.get("daily_volume_gb")
        hosts = entities.get("host_or_node_count")

        if budget:
            est_new_cost = max(budget * 0.15, 50.0)
            return (
                f"Quick math on your current ${int(budget):,}/mo spend: with {competitor_name}, roughly 70% "
                f"of that invoice is margin on ingest indexing. An optimized modern pipeline handles this for "
                f"under ${int(est_new_cost):,}/mo, yielding a net annual recovery of ~${int((budget - est_new_cost) * 12):,}."
            )
        elif volume:
            est_cost = volume * 0.10 * 30
            est_savings = est_cost * 0.80
            return (
                f"Running the numbers on {int(volume)} GB daily ingest: legacy indexing charges ~$0.10/GB, "
                f"costing you ~${int(est_cost):,}/mo. Running an edge-deployed aggregator drops that bill by "
                f"80% (~${int(est_savings):,}/mo saved) by filtering noise prior to retention."
            )
        elif hosts:
            return (
                f"At {hosts} active nodes, seat licenses and per-agent host overhead rapidly compound. "
                f"Switching to an agentless, API-driven diagnostic loop eliminates per-host fees entirely, "
                f"keeping ongoing maintenance near $0 marginal CAC."
            )

        return (
            f"On typical deployments, teams migrating away from {competitor_name} observe an immediate 75% "
            f"reduction in monthly observability infrastructure overhead within their first billing cycle."
        )

    def _build_stealth_closing(self, opp: InterceptOpportunity, tool_url: str) -> str:
        """Draft third paragraph based on selected stealth mode."""
        if opp.stealth_mode == StealthMode.DIRECT_TOOL_LINK:
            clean_url = f"{tool_url.rstrip('/')}?utm_source={opp.platform.value}&utm_medium=intercept&utm_campaign={opp.opportunity_id}"
            return f"I built an interactive calculator modeling this exact unit cost breakdown if you want to test your numbers: {clean_url}"

        if opp.stealth_mode == StealthMode.GITHUB_PROFILE:
            return "I documented the complete reference architecture and migration scripts in my GitHub profile repo if you want to inspect the setup."

        # Default: Zero-Link Value Trap (0 bans, highest trust)
        return (
            "I ended up building an interactive cost calculator and benchmark model for our own infrastructure "
            "to calculate these numbers before migrating. Happy to share the link if it helps your team evaluate options."
        )
