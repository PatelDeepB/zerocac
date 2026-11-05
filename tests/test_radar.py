"""Unit tests for Phase 1 Live Intent Radar Engine."""

import pytest
from unittest.mock import AsyncMock, patch

from zerocac.ai.base import LLMResponse
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.engines.radar import (
    LiveIntentRadarEngine,
    LiveIntentSignal,
    RadarReport,
    RadarSignalSource,
)


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Fixture providing a realistic B2B/DevTool product profile."""
    return ProductProfile(
        product_name="ZeroCAC",
        category="Growth Automation / Developer Tools",
        one_liner="Scale to $0 CAC without paying for Google or Meta ad tokens.",
        core_problem="Paid ads are expensive, burn cash, and create zero permanent equity.",
        solution_mechanism="Autonomous organic distribution via AEO, micro-tools, and radar.",
        unique_value_proposition="Scale to $0 CAC without paying for Google or Meta ad tokens.",
        key_features=["Live Intent Radar", "Autonomous Micro-Tools", "Princeton GEO"],
        personas=[
            ICPPersona(
                persona_name="Bootstrapped SaaS Founder",
                core_pain_point="Priced out of Google Ads with zero media budget.",
                trigger_event="Ad budget exhausted after poor ROAS.",
                primary_objection="Will organic marketing take too long to produce results?",
                watering_holes=["r/SaaS", "r/startups", "Hacker News"],
            )
        ],
        competitor_gaps=[
            CompetitorGap(
                competitor_name="AdRoll",
                their_weakness="Expensive monthly subscriptions and high ad fatigue.",
                our_advantage="100% organic with permanent compounding assets.",
            )
        ],
        search_keywords=["zerocac", "organic marketing agent", "zero cac"],
        high_intent_queries=["alternative to paid ads", "how to scale without ads"],
    )


@pytest.mark.asyncio
async def test_radar_dry_run_returns_high_intent_signals(sample_profile: ProductProfile) -> None:
    """Radar in dry-run mode should return structured, scored signals without calling live APIs."""
    engine = LiveIntentRadarEngine()
    report = await engine.scan_live_feeds(sample_profile, dry_run=True)

    assert isinstance(report, RadarReport)
    assert report.product_name == "ZeroCAC"
    assert len(report.high_intent_signals) >= 3
    assert report.signals_found >= 3

    sources = {s.source for s in report.high_intent_signals}
    assert RadarSignalSource.REDDIT in sources
    assert RadarSignalSource.HACKER_NEWS in sources
    assert RadarSignalSource.GITHUB_ISSUES in sources

    for signal in report.high_intent_signals:
        assert signal.intent_score >= 80
        assert "ZeroCAC" in signal.recommended_reply
        assert len(signal.recommended_reply) > 20
        assert signal.url.startswith("http")


def test_radar_resolves_search_terms_accurately(sample_profile: ProductProfile) -> None:
    """Search terms should prioritize custom keywords or derive from product and competitors."""
    engine = LiveIntentRadarEngine()

    custom_terms = engine._resolve_search_terms(sample_profile, ["seo tools", "growth agent"])
    assert custom_terms == ["seo tools", "growth agent"]

    derived_terms = engine._resolve_search_terms(sample_profile, None)
    assert "zerocac" in derived_terms
    assert any("alternative to adroll" in term for term in derived_terms)


@pytest.mark.asyncio
async def test_radar_evaluates_mocked_network_feeds(sample_profile: ProductProfile) -> None:
    """Radar should query feeds, pass items through AI evaluation, and sort by intent score."""
    router = AIRouter()
    engine = LiveIntentRadarEngine(router=router)

    mock_raw_items = [
        {
            "source": RadarSignalSource.REDDIT,
            "title": "Need alternative to expensive ad platforms",
            "url": "https://reddit.com/r/SaaS/123",
            "author": "tester_1",
            "created_at": "1h ago",
            "snippet": "Google ads are burning $20 per click, what else works?",
        }
    ]

    mock_ai_json = (
        '{"intent_score": 92, "pain_category": "Pricing Grievance", '
        '"relevance_explanation": "Direct inquiry on ad alternative", '
        '"recommended_reply": "Check out ZeroCAC for organic growth."}'
    )

    with patch.object(engine, "_gather_all_feeds", new_callable=AsyncMock) as mock_gather:
        mock_gather.return_value = mock_raw_items
        with patch.object(router, "generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = LLMResponse(content=mock_ai_json, model="dry-run", provider="dry-run")

            report = await engine.scan_live_feeds(sample_profile, dry_run=False)

            assert report.signals_found == 1
            signal = report.high_intent_signals[0]
            assert signal.intent_score == 92
            assert signal.pain_category == "Pricing Grievance"
            assert "ZeroCAC" in signal.recommended_reply


@pytest.mark.asyncio
async def test_radar_falls_back_gracefully_when_feeds_empty(sample_profile: ProductProfile) -> None:
    """When public feeds return no results, radar should fall back safely to dry-run signals."""
    engine = LiveIntentRadarEngine()

    with patch.object(engine, "_gather_all_feeds", new_callable=AsyncMock) as mock_gather:
        mock_gather.return_value = []

        report = await engine.scan_live_feeds(sample_profile, dry_run=False)
        assert report.signals_found >= 3
        assert report.product_name == "ZeroCAC"
