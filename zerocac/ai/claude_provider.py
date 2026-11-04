"""Anthropic Claude provider implementation for Claude Opus 5.5 and Sonnet 5.5."""

from typing import List, Optional

import httpx

from zerocac.ai.base import (
    AuthenticationError,
    BaseLLMProvider,
    InvalidResponseError,
    LLMMessage,
    LLMResponse,
    RateLimitError,
)


class ClaudeProvider(BaseLLMProvider):
    """Integrates Anthropic Claude Messages API with frontier 2026 models."""

    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-sonnet-5-5"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
    ) -> None:
        resolved_base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key=api_key, base_url=resolved_base_url)
        self.default_model = default_model

    @property
    def provider_name(self) -> str:
        return "claude"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Call Anthropic Messages endpoint."""
        target_model = model or self.default_model

        if not self.api_key or self.api_key.startswith("your_"):
            return self._generate_dry_run_response(messages, target_model)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        system_prompt, user_messages = self._separate_system_messages(messages)
        payload = {
            "model": target_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": m.role, "content": m.content} for m in user_messages],
        }
        if system_prompt:
            payload["system"] = system_prompt

        url = f"{self.base_url.rstrip('/')}/messages"
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.RequestError as exc:
                raise InvalidResponseError(f"Network request failed: {exc}", self.provider_name) from exc

        self._validate_http_status(response)
        return self._parse_claude_response(response.json(), target_model)

    def _separate_system_messages(
        self, messages: List[LLMMessage]
    ) -> tuple[Optional[str], List[LLMMessage]]:
        """Extract system messages to top-level system parameter for Claude."""
        system_parts = [m.content for m in messages if m.role == "system"]
        user_messages = [m for m in messages if m.role != "system"]
        system_prompt = "\n\n".join(system_parts) if system_parts else None
        return system_prompt, user_messages

    def _validate_http_status(self, response: httpx.Response) -> None:
        """Validate HTTP response status for Anthropic API."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid Anthropic API key", self.provider_name, 401)
        if response.status_code == 429:
            raise RateLimitError("Anthropic rate limit exceeded", self.provider_name, 429)
        if response.is_error:
            raise InvalidResponseError(
                f"HTTP {response.status_code}: {response.text}",
                self.provider_name,
                response.status_code,
            )

    def _parse_claude_response(self, data: dict, target_model: str) -> LLMResponse:
        """Extract text content and token usage from Claude response."""
        try:
            content_blocks = data.get("content", [])
            text = "".join(block["text"] for block in content_blocks if block.get("type") == "text")
            usage = data.get("usage", {})
            return LLMResponse(
                content=text,
                provider=self.provider_name,
                model=target_model,
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
            )
        except (KeyError, IndexError) as exc:
            raise InvalidResponseError(
                f"Malformed Anthropic payload: {exc}", self.provider_name
            ) from exc

    def _generate_dry_run_response(
        self, messages: List[LLMMessage], target_model: str
    ) -> LLMResponse:
        """Produce deterministic mock response when running without live API keys."""
        last_message = messages[-1].content if messages else "No content"
        mock_body = (
            f"[DryRun Claude/{target_model}]\n"
            f"Processed prompt with {len(messages)} messages.\n"
            f"Target context snippet: {last_message[:120]}"
        )
        return LLMResponse(
            content=mock_body,
            provider=self.provider_name,
            model=target_model,
            prompt_tokens=160,
            completion_tokens=85,
        )
