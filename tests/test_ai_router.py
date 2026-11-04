"""Unit tests for multi-LLM providers and the AIRouter fallback orchestrator."""

from unittest.mock import AsyncMock, patch
import pytest

from zerocac.ai.base import (
    AuthenticationError,
    LLMMessage,
    RateLimitError,
)
from zerocac.ai.claude_provider import ClaudeProvider
from zerocac.ai.deepseek_provider import DeepSeekProvider
from zerocac.ai.gemini_provider import GeminiProvider
from zerocac.ai.nvidia_provider import NVIDIAProvider
from zerocac.ai.openai_provider import OpenAIProvider
from zerocac.ai.router import AIRouter
from zerocac.config import Settings


@pytest.fixture
def sample_messages() -> list[LLMMessage]:
    """Provide a standard chat message history."""
    return [
        LLMMessage(role="system", content="You are a marketing strategist."),
        LLMMessage(role="user", content="Explain how organic distribution beats paid ads."),
    ]


@pytest.mark.asyncio
async def test_openai_provider_dry_run_generation(sample_messages: list[LLMMessage]) -> None:
    """Ensure OpenAI provider generates deterministic dry-run text when unconfigured."""
    # Arrange
    provider = OpenAIProvider(api_key=None, default_model="gpt-6.1-luna")

    # Act
    response = await provider.generate_text(sample_messages)

    # Assert
    assert response.provider == "openai"
    assert response.model == "gpt-6.1-luna"
    assert "DryRun OpenAI" in response.content
    assert response.prompt_tokens > 0


@pytest.mark.asyncio
async def test_gemini_provider_dry_run_generation(sample_messages: list[LLMMessage]) -> None:
    """Ensure Gemini provider generates deterministic dry-run text when unconfigured."""
    # Arrange
    provider = GeminiProvider(api_key=None, default_model="gemini-3.8-flash")

    # Act
    response = await provider.generate_text(sample_messages)

    # Assert
    assert response.provider == "gemini"
    assert response.model == "gemini-3.8-flash"
    assert "DryRun Gemini" in response.content


@pytest.mark.asyncio
async def test_claude_provider_dry_run_generation(sample_messages: list[LLMMessage]) -> None:
    """Ensure Claude provider handles system prompt extraction in dry-run mode."""
    # Arrange
    provider = ClaudeProvider(api_key=None, default_model="claude-sonnet-5-5")

    # Act
    response = await provider.generate_text(sample_messages)

    # Assert
    assert response.provider == "claude"
    assert response.model == "claude-sonnet-5-5"
    assert "DryRun Claude" in response.content


@pytest.mark.asyncio
async def test_nvidia_provider_dry_run_generation(sample_messages: list[LLMMessage]) -> None:
    """Ensure NVIDIA provider generates deterministic dry-run text."""
    # Arrange
    provider = NVIDIAProvider(api_key=None, default_model="nemotron-3.5-super-vl")

    # Act
    response = await provider.generate_text(sample_messages)

    # Assert
    assert response.provider == "nvidia"
    assert response.model == "nemotron-3.5-super-vl"
    assert "DryRun NVIDIA" in response.content


@pytest.mark.asyncio
async def test_deepseek_provider_dry_run_generation(sample_messages: list[LLMMessage]) -> None:
    """Ensure DeepSeek provider generates deterministic dry-run text."""
    # Arrange
    provider = DeepSeekProvider(api_key=None, default_model="deepseek-v4.1-flash")

    # Act
    response = await provider.generate_text(sample_messages)

    # Assert
    assert response.provider == "deepseek"
    assert response.model == "deepseek-v4.1-flash"
    assert "DryRun DeepSeek" in response.content


def test_ai_router_initializes_all_providers() -> None:
    """Ensure AIRouter initializes each registered provider from settings."""
    # Arrange & Act
    router = AIRouter(settings=Settings())

    # Assert
    assert "openai" in router.providers
    assert "gemini" in router.providers
    assert "claude" in router.providers
    assert "nvidia" in router.providers
    assert "deepseek" in router.providers


@pytest.mark.asyncio
async def test_ai_router_routes_to_requested_provider(sample_messages: list[LLMMessage]) -> None:
    """Ensure router directly queries the requested provider."""
    # Arrange
    router = AIRouter(settings=Settings())

    # Act
    response = await router.generate_text(sample_messages, provider_name="claude")

    # Assert
    assert response.provider == "claude"
    assert "DryRun Claude" in response.content


@pytest.mark.asyncio
async def test_ai_router_falls_back_on_rate_limit(sample_messages: list[LLMMessage]) -> None:
    """Ensure router automatically falls back to secondary provider upon RateLimitError."""
    # Arrange
    router = AIRouter(settings=Settings())
    # Mock primary provider (openai) to raise RateLimitError
    failing_openai = OpenAIProvider(api_key="mock_key")
    failing_openai.generate_text = AsyncMock(  # type: ignore
        side_effect=RateLimitError("Rate limit hit", "openai", 429)
    )
    router.providers["openai"] = failing_openai

    # Act
    response = await router.generate_text(sample_messages, provider_name="openai")

    # Assert: Should have failed on openai and fallen back to claude (next in priority)
    assert response.provider == "claude"
    assert "DryRun Claude" in response.content


def test_claude_provider_separates_system_messages(sample_messages: list[LLMMessage]) -> None:
    """Verify system message extraction helper for Anthropic API."""
    # Arrange
    provider = ClaudeProvider()

    # Act
    system_text, user_msgs = provider._separate_system_messages(sample_messages)

    # Assert
    assert system_text == "You are a marketing strategist."
    assert len(user_msgs) == 1
    assert user_msgs[0].role == "user"
