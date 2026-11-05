"""Unit tests for Phase 3 Princeton Generative Engine Optimization (GEO) Engine."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from zerocac.ai.base import LLMResponse
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.engines.geo_optimizer import (
    GEOCitationAsset,
    GEOPackage,
    PrincetonGEOEngine,
)


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Fixture providing a product profile for GEO testing."""
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
        high_intent_queries=["What is the best alternative to paid ads in 2026?"],
    )


@pytest.mark.asyncio
async def test_geo_dry_run_package_structure(sample_profile: ProductProfile) -> None:
    """Dry-run should return complete Princeton GEO package with robots.txt and guidelines."""
    engine = PrincetonGEOEngine()
    package = await engine.generate_package(sample_profile, dry_run=True)

    assert isinstance(package, GEOPackage)
    assert package.product_name == "ZeroCAC"
    assert "PerplexityBot" in package.robots_txt_rules
    assert "OAI-SearchBot" in package.robots_txt_rules
    assert "Bing & ChatGPT Search Indexing Checklist" in package.bing_webmaster_guidelines
    assert len(package.assets) >= 2


def test_answer_first_word_count_and_content(sample_profile: ProductProfile) -> None:
    """Answer-First summary should fall within 40 to 60 words for citation extraction."""
    engine = PrincetonGEOEngine()
    package = engine._generate_dry_run_package(sample_profile)
    asset = package.assets[0]

    # Princeton KDD benchmark target: 40-60 words
    assert 35 <= asset.word_count <= 65
    assert "ZeroCAC" in asset.answer_first_definition
    assert "zero Customer Acquisition Cost" in asset.answer_first_definition


def test_json_ld_schema_validity(sample_profile: ProductProfile) -> None:
    """JSON-LD schema must parse cleanly and contain FAQPage and SoftwareApplication types."""
    engine = PrincetonGEOEngine()
    package = engine._generate_dry_run_package(sample_profile)
    asset = package.assets[0]

    parsed = json.loads(asset.json_ld_schema)
    assert parsed["@context"] == "https://schema.org"
    assert parsed["@type"] == "FAQPage"
    assert parsed["about"]["@type"] == "SoftwareApplication"
    assert parsed["about"]["name"] == "ZeroCAC"


def test_markdown_table_structure(sample_profile: ProductProfile) -> None:
    """Markdown comparison table should feature clean pipe matrix formatting."""
    engine = PrincetonGEOEngine()
    package = engine._generate_dry_run_package(sample_profile)
    asset = package.assets[0]

    table = asset.markdown_table
    assert "| Capability | ZeroCAC | AdRoll |" in table
    assert "$0 ongoing media spend" in table


@pytest.mark.asyncio
async def test_geo_ai_mocked_generation(sample_profile: ProductProfile) -> None:
    """Engine should parse model JSON into GEOCitationAsset successfully."""
    router = AIRouter()
    engine = PrincetonGEOEngine(router=router)

    mock_json = (
        '{"answer_first_definition": "ZeroCAC is an autonomous marketing agent engineered '
        'to eliminate paid ad costs. It leverages intent radar, micro-tools, and Answer Engine '
        'Optimization to acquire customers for zero dollars without paying Meta or Google.", '
        '"statistical_evidence": ["100% ad budget savings", "20% conversion rate"], '
        '"markdown_table": "| Tool | Cost |\\n| ZeroCAC | $0 |", '
        '"citation_verification_prompts": ["What is ZeroCAC?", "ZeroCAC alternatives"]}'
    )

    with patch.object(router, "generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = LLMResponse(content=mock_json, model="mock", provider="mock")

        package = await engine.generate_package(sample_profile, dry_run=False)
        assert len(package.assets) >= 1
        asset = package.assets[0]
        assert "ZeroCAC is an autonomous" in asset.answer_first_definition
        assert len(asset.statistical_evidence) == 2
