"""Unit tests for Phase 2 Autonomous Micro-Tool Architect (Engineering-as-Marketing)."""

from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

from zerocac.ai.base import LLMResponse
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.engines.microtool import (
    MicroToolConcept,
    MicroToolEngine,
    MicroToolPackage,
)


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Fixture providing a product profile for micro-tool generation."""
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
async def test_microtool_dry_run_generation(sample_profile: ProductProfile) -> None:
    """Engine in dry-run mode should generate valid interactive HTML without calling AI."""
    engine = MicroToolEngine()
    package = await engine.generate_tool(sample_profile, dry_run=True)

    assert isinstance(package, MicroToolPackage)
    assert "Calculator" in package.concept.tool_name
    assert package.concept.slug == "ad-spend-vs-organic-cac-calculator"

    # HTML verification
    html = package.html_content
    assert "<!DOCTYPE html>" in html
    assert "<style>" in html
    assert "<script>" in html
    assert "<main>" in html
    assert "recalculate" in html
    assert "ZeroCAC" in html
    assert package.deployment_instructions.startswith("Quick Deployment Guide")


def test_microtool_export_creates_valid_directory_structure(
    sample_profile: ProductProfile, tmp_path: Path
) -> None:
    """Engine export should write index.html and deployment README to disk."""
    engine = MicroToolEngine()
    package = engine._generate_dry_run_tool(sample_profile)

    exported_path = engine.export_tool(package, tmp_path)
    assert exported_path.is_dir()
    assert (exported_path / "index.html").exists()
    assert (exported_path / "README.md").exists()

    content = (exported_path / "index.html").read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


@pytest.mark.asyncio
async def test_microtool_ai_generation_mocked(sample_profile: ProductProfile) -> None:
    """Engine should orchestrate concept discovery and HTML generation with AI router."""
    router = AIRouter()
    engine = MicroToolEngine(router=router)

    concept_json = (
        '{"tool_name": "API Cost Calculator", "slug": "api-cost-calc", '
        '"headline": "See how much you overpay for tokens.", '
        '"core_functionality": "Calculates token costs across providers.", '
        '"target_icp": "AI Developers", "virality_hook": "Shared on Twitter"}'
    )
    html_output = "<!DOCTYPE html><html><head><title>Test</title></head><body><script>1+1</script></body></html>"

    with patch.object(router, "generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [
            LLMResponse(content=concept_json, model="mock", provider="mock"),
            LLMResponse(content=html_output, model="mock", provider="mock"),
        ]

        package = await engine.generate_tool(sample_profile, dry_run=False)
        assert package.concept.tool_name == "API Cost Calculator"
        assert package.concept.slug == "api-cost-calc"
        assert "<!DOCTYPE html>" in package.html_content


def test_clean_html_strips_markdown_code_fences() -> None:
    """HTML cleaner should cleanly strip markdown backtick fences."""
    engine = MicroToolEngine()
    raw = "```html\n<!DOCTYPE html><html><body>Test</body></html>\n```"
    cleaned = engine._clean_html_code(raw)
    assert cleaned == "<!DOCTYPE html><html><body>Test</body></html>"
