"""Resilient multi-provider AI Router with automatic fallback routing."""

import logging
from typing import Dict, List, Optional

from zerocac.ai.base import (
    AIProviderError,
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    RateLimitError,
)
from zerocac.ai.claude_provider import ClaudeProvider
from zerocac.ai.deepseek_provider import DeepSeekProvider
from zerocac.ai.gemini_provider import GeminiProvider
from zerocac.ai.nvidia_provider import NVIDIAProvider
from zerocac.ai.openai_provider import OpenAIProvider
from zerocac.config import Settings, get_settings

logger = logging.getLogger(__name__)


class AIRouter:
    """Manages AI providers and coordinates dynamic failover and execution."""

    FALLBACK_PRIORITIES = ["openai", "claude", "gemini", "deepseek", "nvidia"]

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Instantiate configured providers based on application settings."""
        self.providers["openai"] = OpenAIProvider(
            api_key=self.settings.openai_api_key,
            default_model=self.settings.openai_model_fast,
        )
        self.providers["gemini"] = GeminiProvider(
            api_key=self.settings.gemini_api_key,
            default_model=self.settings.gemini_model_fast,
        )
        self.providers["claude"] = ClaudeProvider(
            api_key=self.settings.anthropic_api_key,
            default_model=self.settings.anthropic_model_fast,
        )
        self.providers["nvidia"] = NVIDIAProvider(
            api_key=self.settings.nvidia_api_key,
            base_url=self.settings.nvidia_base_url,
            default_model=self.settings.nvidia_model_fast,
        )
        self.providers["deepseek"] = DeepSeekProvider(
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url,
            default_model=self.settings.deepseek_model_fast,
        )

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Retrieve a specific provider by name or the default provider."""
        provider_name = (name or self.settings.default_ai_provider).lower()
        if provider_name in self.providers:
            return self.providers[provider_name]
        logger.warning("Provider %s not found. Falling back to openai", provider_name)
        return self.providers["openai"]

    async def generate_text(
        self,
        messages: List[LLMMessage],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate text with automatic fallback if primary provider hits rate limits."""
        primary_name = (provider_name or self.settings.default_ai_provider).lower()
        candidate_order = self._determine_candidate_order(primary_name)

        last_exception: Optional[Exception] = None
        for candidate in candidate_order:
            provider = self.providers.get(candidate)
            if not provider:
                continue

            try:
                logger.info("Attempting generation via provider: %s", candidate)
                return await provider.generate_text(
                    messages=messages,
                    model=model if candidate == primary_name else None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except (RateLimitError, AIProviderError) as exc:
                logger.warning(
                    "Provider %s failed (%s). Triggering fallback to next provider.",
                    candidate,
                    exc,
                )
                last_exception = exc

        raise AIProviderError(
            f"All providers exhausted in fallback chain. Last error: {last_exception}",
            provider="router",
        )

    def _determine_candidate_order(self, primary_name: str) -> List[str]:
        """Produce an ordered list of providers beginning with the chosen primary."""
        order = [primary_name]
        for name in self.FALLBACK_PRIORITIES:
            if name not in order:
                order.append(name)
        return order
