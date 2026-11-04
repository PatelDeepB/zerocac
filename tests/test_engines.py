"""Unit tests for the 4 core organic distribution execution engines."""

import json
import pytest
from unittest.mock import AsyncMock

from zerocac.ai.base import LLMResponse
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.engines.aeo import AEOEngine
from zerocac.engines.directory import DirectoryEngine
from zerocac.engines.narrative import ViralNarrativeEngine
from zerocac.engines.sniper import IntentSniperEngine


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Provide a realistic sample ProductProfile for engine tests."""
    return ProductProfile(
        product_name="PulseOps",
        category="DevOps Automation",
        one_liner="Automate Kubernetes incident diagnostics in under 10 seconds.",
        core_problem="Engineering teams burn 15 hours a week manually triaging cluster errors.",
        solution_mechanism="Autonomous log-to-metric root cause correlation.",
        unique_value_proposition="10x faster MTTR with zero agents to maintain.",
        key_features=["Auto triage", "Root cause synthesis", "Slack alerting"],
        personas=[
            ICPPersona(
                persona_name="Site Reliability Engineer",
                core_pain_point="Woken up at 3 AM for ambiguous pod crashes.",
                trigger_event="Severe customer outage caused SLA breach.",
                primary_objection="Is it safe to run in production?",
                watering_holes=["r/kubernetes", "r/devops"],
            )
        ],
        competitor_gaps=[
            CompetitorGap(
                competitor_name="LegacyAPM",
                their_weakness="Massive manual configuration and complex dashboard sprawl.",
                our_advantage="Instant actionable root cause summaries without configuring charts.",
            )
        ],
        search_keywords=["kubernetes troubleshooting tool", "legacyapm alternative"],
        high_intent_queries=["What is the fastest way to debug crashloopbackoff in k8s?"],
    )


@pytest.mark.asyncio
async def test_intent_sniper_generates_opportunities(sample_profile: ProductProfile) -> None:
    """Ensure IntentSniper produces high-intent opportunities with authentic responses."""
    # Arrange
    engine = IntentSniperEngine(router=AIRouter())

    # Act
    campaign = await engine.generate_opportunities(profile=sample_profile, count=3)

    # Assert
    assert campaign.product_name == "PulseOps"
    assert len(campaign.opportunities) == 3
    for opp in campaign.opportunities:
        assert opp.platform in ["Reddit", "Hacker News", "X / Twitter"]
        assert 80 <= opp.intent_score <= 100
        assert len(opp.draft_response) > 50
        assert "PulseOps" in opp.draft_response


@pytest.mark.asyncio
async def test_aeo_engine_generates_comparison_page_and_schema(
    sample_profile: ProductProfile,
) -> None:
    """Ensure AEOEngine produces clean markdown comparison and valid JSON-LD schema."""
    # Arrange
    engine = AEOEngine(router=AIRouter())
    gap = sample_profile.competitor_gaps[0]

    # Act
    page = await engine.generate_comparison(profile=sample_profile, gap=gap)

    # Assert
    assert "PulseOps vs LegacyAPM" in page.title
    assert page.slug == "pulseops-vs-legacyapm"
    assert "LegacyAPM" in page.markdown_content
    # Validate that faq_schema_json is valid JSON
    schema_data = json.loads(page.faq_schema_json)
    assert schema_data["@type"] == "FAQPage"
    assert len(schema_data["mainEntity"]) == 2


@pytest.mark.asyncio
async def test_viral_narrative_generates_multi_modal_assets(
    sample_profile: ProductProfile,
) -> None:
    """Ensure ViralNarrativeEngine produces X thread, carousel slides, and video script."""
    # Arrange
    engine = ViralNarrativeEngine(router=AIRouter())

    # Act
    campaign = await engine.generate_campaign(profile=sample_profile)

    # Assert
    assert campaign.product_name == "PulseOps"
    assert len(campaign.x_thread) == 5
    assert any("PulseOps" in tweet for tweet in campaign.x_thread)
    assert len(campaign.linkedin_carousel) == 5
    assert "[Visual" in campaign.video_script_60s
    assert "[Audio" in campaign.video_script_60s


def test_directory_engine_generates_valid_listings(sample_profile: ProductProfile) -> None:
    """Ensure DirectoryEngine respects character constraints across directories."""
    # Arrange
    engine = DirectoryEngine()

    # Act
    package = engine.generate_package(profile=sample_profile)

    # Assert
    assert package.product_name == "PulseOps"
    assert package.total_directories >= 10
    for listing in package.listings:
        assert len(listing.tagline) <= 60
        assert len(listing.short_description) <= 140
        assert len(listing.long_description) <= 700
        assert len(listing.tags) >= 3
        assert "http" in listing.submission_url
        assert listing.domain_authority >= 50
