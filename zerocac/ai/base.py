"""Abstract base class and error hierarchies for AI LLM providers.

Defines the contract that all model drivers (OpenAI, Gemini, Claude,
NVIDIA NIM, DeepSeek) must satisfy.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIProviderError(Exception):
    """Base exception for all AI provider failures."""

    def __init__(self, message: str, provider: str, status_code: Optional[int] = None) -> None:
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
        self.status_code = status_code


class AuthenticationError(AIProviderError):
    """Raised when an API key is missing, invalid, or unauthorized."""


class RateLimitError(AIProviderError):
    """Raised when an upstream provider rate limits or exhausts quota."""


class InvalidResponseError(AIProviderError):
    """Raised when an upstream provider returns unparseable or corrupted payload."""


class LLMMessage(BaseModel):
    """Standardized representation of a chat message."""

    role: str = Field(description="Role of the author: system, user, or assistant")
    content: str = Field(description="Raw text content of the message")


class LLMResponse(BaseModel):
    """Standardized result returned by any LLM provider."""

    content: str = Field(description="Generated completion text")
    provider: str = Field(description="Name of the provider that fulfilled the request")
    model: str = Field(description="Specific model identifier utilized")
    prompt_tokens: int = Field(default=0, description="Estimated or reported input tokens")
    completion_tokens: int = Field(default=0, description="Estimated or reported output tokens")


class BaseLLMProvider(ABC):
    """Contract for multi-provider LLM integrations."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.api_key = api_key
        self.base_url = base_url

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique lowercase name of the provider."""

    @abstractmethod
    async def generate_text(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate text completion from a sequence of chat messages."""
