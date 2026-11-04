"""Unit tests for the ProductAnalyzer engine and domain models."""

import pytest
from unittest.mock import AsyncMock

from zerocac.ai.base import LLMResponse
from zerocac.ai.router import AIRouter
from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.analyzer.models import ProductProfile
from zerocac.crawler.schema import ProductRawData


@pytest.fixture
def mock_profile_json() -> str:
    """Return valid strategic JSON matching ProductProfile schema."""
    return """
    {
        "product_name": "DevPulse",
        "category": "Developer Observability",
        "one_liner": "Autonomous eBPF-powered Kubernetes profiling with zero instrumentation.",
        "core_problem": "Developers waste days reproducing latency spikes across microservices.",
        "solution_mechanism": "Continuous kernel-level tracing that pinpoints bottlenecks automatically.",
        "unique_value_proposition": "100x lower overhead than Datadog at 1/10th the cost.",
        "key_features": [
            "Kernel-level eBPF tracing",
            "Zero code changes required",
            "Instant flame graph generation"
        ],
        "personas": [
            {
                "persona_name": "DevOps Engineer",
                "core_pain_point": "High APM cloud bills and CPU overhead.",
                "trigger_event": "Production latency incident caused customer churn.",
                "primary_objection": "Will eBPF cause kernel panics?",
                "watering_holes": ["r/devops", "Hacker News"]
            }
        ],
        "competitor_gaps": [
            {
                "competitor_name": "Datadog",
                "their_weakness": "Astronomical custom metrics bills and complex SDKs.",
                "our_advantage": "Drop-in single binary with predictable flat pricing."
            }
        ],
        "search_keywords": ["datadog alternative", "kubernetes profiling tool"],
        "high_intent_queries": ["What is a cheaper alternative to Datadog for Kubernetes?"]
    }
    """


@pytest.mark.asyncio
async def test_product_analyzer_parses_json_response_cleanly(mock_profile_json: str) -> None:
    """Ensure ProductAnalyzer properly deserializes LLM JSON output."""
    # Arrange
    mock_router = AsyncMock(spec=AIRouter)
    mock_router.generate_text.return_value = LLMResponse(
        content=f"```json\n{mock_profile_json}\n```",
        provider="openai",
        model="gpt-6-astra",
    )
    analyzer = ProductAnalyzer(router=mock_router)

    # Act
    profile = await analyzer.analyze_text("Test description", product_name="DevPulse")

    # Assert
    assert profile.product_name == "DevPulse"
    assert profile.category == "Developer Observability"
    assert len(profile.personas) == 1
    assert profile.personas[0].persona_name == "DevOps Engineer"
    assert len(profile.competitor_gaps) == 1
    assert profile.competitor_gaps[0].competitor_name == "Datadog"
    assert "datadog alternative" in profile.search_keywords


@pytest.mark.asyncio
async def test_product_analyzer_uses_fallback_profile_on_dry_run() -> None:
    """Ensure ProductAnalyzer handles unconfigured dry-run output gracefully."""
    # Arrange
    mock_router = AsyncMock(spec=AIRouter)
    mock_router.generate_text.return_value = LLMResponse(
        content="[DryRun OpenAI/gpt-6-astra] Mock output without JSON",
        provider="openai",
        model="gpt-6-astra",
    )
    analyzer = ProductAnalyzer(router=mock_router)

    raw_data = ProductRawData(
        url="https://testapp.com",
        title="TestApp - The Smart CRM",
    )

    # Act
    profile = await analyzer.analyze_raw_data(raw_data)

    # Assert
    assert isinstance(profile, ProductProfile)
    assert profile.product_name == "TestApp"
    assert len(profile.personas) >= 2
    assert len(profile.competitor_gaps) >= 2
    assert len(profile.search_keywords) > 0
