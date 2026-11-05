"""Unit tests for Phase 4 Product-Led Artifact Virality Engine."""

import pytest
from unittest.mock import AsyncMock, patch

from zerocac.ai.base import LLMResponse
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.engines.virality_loop import (
    ViralityArtifactPackage,
    ViralityEngine,
)


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Fixture providing a product profile for virality loop testing."""
    return ProductProfile(
        product_name="ZeroCAC",
        category="Growth Automation / Developer Tools",
        one_liner="Scale to $0 CAC without paying for Google or Meta ad tokens.",
        core_problem="Paid ads are expensive and create zero compounding equity.",
        solution_mechanism="Autonomous organic growth engines.",
        unique_value_proposition="Scale to $0 CAC without paying for Google or Meta ad tokens.",
        key_features=["Live Intent Radar", "Autonomous Micro-Tools", "Princeton GEO"],
        personas=[
            ICPPersona(
                persona_name="Bootstrapped SaaS Founder",
                core_pain_point="Burning $3k/mo on ads with low conversion.",
                trigger_event="Ad budget exhausted.",
                primary_objection="Is organic fast enough?",
                watering_holes=["r/SaaS", "Hacker News"],
            )
        ],
        competitor_gaps=[
            CompetitorGap(
                competitor_name="AdRoll",
                their_weakness="High monthly fees and ad fatigue.",
                our_advantage="100% organic compounding assets.",
            )
        ],
        search_keywords=["zerocac", "organic marketing agent"],
        high_intent_queries=["how to scale without ads"],
    )


@pytest.mark.asyncio
async def test_virality_dry_run_package(sample_profile: ProductProfile) -> None:
    """Dry run should return complete virality package with SVG, HTML, and loop mechanics."""
    engine = ViralityEngine()
    package = await engine.generate_package(sample_profile, dry_run=True)

    assert isinstance(package, ViralityArtifactPackage)
    assert package.product_name == "ZeroCAC"

    # SVG validation
    assert "<svg" in package.svg_badge
    assert "</svg>" in package.svg_badge
    assert "powered by" in package.svg_badge
    assert "ZeroCAC" in package.svg_badge

    # HTML Snippet validation
    assert "class=\"zerocac-badge\"" in package.html_badge_snippet
    assert "Automated with" in package.html_badge_snippet

    # Markdown Badge
    assert "[![Powered by ZeroCAC]" in package.markdown_badge

    # Loop mechanics
    assert len(package.viral_loop_mechanics) == 4
    assert "1." in package.viral_loop_mechanics[0]


def test_svg_badge_dimensions_and_styling() -> None:
    """SVG badge must be valid vector markup with correct attributes."""
    engine = ViralityEngine()
    svg = engine._render_svg_badge("TestBrand")

    assert 'width="180"' in svg
    assert 'height="28"' in svg
    assert 'TestBrand' in svg
    assert '#10b981' in svg


@pytest.mark.asyncio
async def test_virality_ai_mocked_generation(sample_profile: ProductProfile) -> None:
    """Engine should orchestrate AI call for dynamic viral loop mechanics."""
    router = AIRouter()
    engine = ViralityEngine(router=router)

    mock_json = (
        '{"k_factor_strategy": "Micro-tools create social sharing triggers on calculation completion.", '
        '"viral_loop_mechanics": ["Step 1: Calculate CAC", "Step 2: Share result", "Step 3: Peer visits", "Step 4: Peer adopts ZeroCAC"], '
        '"social_share_card_spec": {"og_title": "How We Saved $36k on Ads", "og_description": "Our organic teardown", "cta_text": "Calculate Yours"}}'
    )

    with patch.object(router, "generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = LLMResponse(content=mock_json, model="mock", provider="mock")

        package = await engine.generate_package(sample_profile, dry_run=False)
        assert "Micro-tools create social sharing" in package.k_factor_strategy
        assert len(package.viral_loop_mechanics) == 4
        assert package.social_share_card_spec["og_title"] == "How We Saved $36k on Ads"
