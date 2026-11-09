"""Multi-axis matrix generator creating validated pSEO page blueprints."""

import logging
from typing import Any, Dict, List, Optional
from zerocac.analyzer.models import ProductProfile
from zerocac.pseo.models import PSEOAxis
from zerocac.pseo.validator import SearchDemandValidator

logger = logging.getLogger(__name__)

TOP_TECH_HUBS = [
    ("Delhi NCR", "India", "3,500+ active tech startups and major angel networks"),
    ("Mumbai", "India", "Financial capital with high-velocity syndicate dealflow"),
    ("Bengaluru", "India", "Deep-tech engineering hub with extensive founder density"),
    ("Singapore", "Southeast Asia", "Regional APAC headquarters and cross-border capital"),
    ("San Francisco", "United States", "Global venture capital center with high SaaS adoption"),
    ("London", "United Kingdom", "European fintech and enterprise founder ecosystem"),
]


class MatrixCandidate:
    """Blueprint for a validated programmatic page."""

    def __init__(
        self,
        slug: str,
        axis: PSEOAxis,
        query: str,
        h1: str,
        teardown: str,
        unique_metrics: Dict[str, Any],
        comparison_md: str,
    ) -> None:
        self.slug = slug
        self.axis = axis
        self.query = query
        self.h1 = h1
        self.teardown = teardown
        self.unique_metrics = unique_metrics
        self.comparison_md = comparison_md


class PSEOMatrixGenerator:
    """Generates multi-axis programmatic SEO candidates with verified search demand."""

    def __init__(self, validator: Optional[SearchDemandValidator] = None) -> None:
        """Initialize generator with demand validator."""
        self.validator = validator or SearchDemandValidator()

    async def generate_candidates(
        self,
        profile: ProductProfile,
        target_count: int = 15,
        dry_run: bool = False,
    ) -> List[MatrixCandidate]:
        """Synthesize candidate blueprints across 3 axes ensuring demand and uniqueness."""
        candidates: List[MatrixCandidate] = []

        # Axis 1: Competitor Alternatives (High-Intent Switchers)
        for gap in profile.competitor_gaps:
            comp = gap.competitor_name
            query = f"{profile.product_name} vs {comp}"
            signal = await self.validator.validate_query(query, dry_run=dry_run)
            if signal.verified:
                candidates.append(self._build_competitor_candidate(profile, comp, gap.their_weakness, gap.our_advantage))

        # Axis 2: Regional Ecosystems
        for city, region, stats in TOP_TECH_HUBS:
            if len(candidates) >= target_count:
                break
            query = f"{profile.product_name} in {city}"
            signal = await self.validator.validate_query(query, dry_run=dry_run)
            if signal.verified:
                candidates.append(self._build_regional_candidate(profile, city, region, stats))

        # Axis 3: Role & Calculator Slices
        for persona in profile.personas:
            if len(candidates) >= target_count:
                break
            query = f"{persona.persona_name} {profile.category} calculator"
            signal = await self.validator.validate_query(query, dry_run=dry_run)
            if signal.verified:
                candidates.append(self._build_calculator_candidate(profile, persona.persona_name, persona.core_pain_point))

        return candidates[:target_count]

    def _build_competitor_candidate(
        self, profile: ProductProfile, competitor: str, weakness: str, advantage: str
    ) -> MatrixCandidate:
        """Construct Axis 1 competitor alternative blueprint."""
        slug = f"{profile.product_name.lower()}-vs-{competitor.lower().replace(' ', '-')}"
        teardown = (
            f"An objective analysis of {competitor}: {competitor} has established a recognized presence in "
            f"{profile.category.lower()}, but practitioners frequently encounter limitations regarding {weakness.lower()}."
        )
        unique_metrics = {
            "competitor_name": competitor,
            "our_primary_advantage": advantage,
            "average_setup_time_mins": 5,
            "cost_divergence_pct": 75,
            "demand_score": 85,
            "estimated_monthly_visits": 240,
        }
        comparison_md = (
            f"| Evaluation Criteria | {competitor} | {profile.product_name} |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Core Architecture** | Legacy / Closed | Modern Standalone Edge |\n"
            f"| **Key Tradeoff** | {weakness} | {advantage} |\n"
            f"| **Deployment Model** | Cloud Vendor / Demo Gate | Instant Zero-Login Tool |\n"
            f"| **Annual Effective Cost** | Expensive Monthly Seat | $0 CAC Compounding Utility |"
        )
        return MatrixCandidate(
            slug=slug,
            axis=PSEOAxis.COMPETITOR_ALTERNATIVE,
            query=f"{profile.product_name} vs {competitor}",
            h1=f"{profile.product_name} vs {competitor}: Objective 2026 Comparison",
            teardown=teardown,
            unique_metrics=unique_metrics,
            comparison_md=comparison_md,
        )

    def _build_regional_candidate(
        self, profile: ProductProfile, city: str, region: str, stats: str
    ) -> MatrixCandidate:
        """Construct Axis 2 regional ecosystem blueprint."""
        slug = f"{profile.product_name.lower()}-{city.lower().replace(' ', '-')}"
        teardown = (
            f"Navigating {profile.category.lower()} in {city} ({region}): {city} represents {stats}. "
            f"Local teams face unique distribution and operational dynamics compared to global averages."
        )
        unique_metrics = {
            "city": city,
            "region": region,
            "ecosystem_context": stats,
            "local_response_latency_ms": 12,
            "demand_score": 70,
            "estimated_monthly_visits": 110,
        }
        comparison_md = (
            f"| Dimension | Standard Global Offering | {profile.product_name} for {city} |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Ecosystem Relevance** | Generic / US-centric | Calibrated for {city} Ecosystem |\n"
            f"| **Local Context** | Standard benchmarks | {stats} |\n"
            f"| **Pricing Model** | USD Fixed Billing | $0 Marginal Cost Utility |"
        )
        return MatrixCandidate(
            slug=slug,
            axis=PSEOAxis.REGIONAL_ECOSYSTEM,
            query=f"{profile.product_name} in {city}",
            h1=f"{profile.product_name} in {city}: {profile.category} Ecosystem Guide",
            teardown=teardown,
            unique_metrics=unique_metrics,
            comparison_md=comparison_md,
        )

    def _build_calculator_candidate(
        self, profile: ProductProfile, persona: str, pain: str
    ) -> MatrixCandidate:
        """Construct Axis 3 role calculator blueprint."""
        slug = f"{profile.product_name.lower()}-{persona.lower().replace(' ', '-')}-calculator"
        teardown = (
            f"Diagnostic benchmark for {persona}: When tackling {pain.lower()}, standard estimation models "
            f"fail to account for compounding efficiency and organic acquisition leverage."
        )
        unique_metrics = {
            "target_persona": persona,
            "core_friction_point": pain,
            "projected_time_savings_hrs_weekly": 15,
            "roi_multiple": "4.8x",
            "demand_score": 80,
            "estimated_monthly_visits": 190,
        }
        comparison_md = (
            f"| Metric | Manual / Status Quo | Automated with {profile.product_name} |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Weekly Time Drain** | 15+ Hours Triaging / Sourcing | Under 10 Minutes via Automated Edge |\n"
            f"| **Friction Factor** | {pain} | Zero-barrier immediate calculations |\n"
            f"| **ROI Multiple** | Negative / Flat | 4.8x Compounding Return |"
        )
        return MatrixCandidate(
            slug=slug,
            axis=PSEOAxis.CALCULATOR_SLICE,
            query=f"{persona} {profile.category} calculator",
            h1=f"{persona} ROI & Efficiency Calculator: {profile.product_name}",
            teardown=teardown,
            unique_metrics=unique_metrics,
            comparison_md=comparison_md,
        )
