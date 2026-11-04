"""Google Gemini provider implementation for Gemini 4 Argon and Gemini 3.8 Flash."""

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


class GeminiProvider(BaseLLMProvider):
    """Integrates Google Gemini REST API with frontier 2026 models."""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-3.8-flash"

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
        return "gemini"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Call Gemini generateContent endpoint."""
        target_model = model or self.default_model

        if not self.api_key or self.api_key.startswith("your_"):
            return self._generate_dry_run_response(messages, target_model)

        url = f"{self.base_url.rstrip('/')}/models/{target_model}:generateContent?key={self.api_key}"
        payload = self._build_gemini_payload(messages, temperature, max_tokens)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
            except httpx.RequestError as exc:
                raise InvalidResponseError(f"Network request failed: {exc}", self.provider_name) from exc

        self._validate_http_status(response)
        return self._parse_gemini_response(response.json(), target_model)

    def _build_gemini_payload(
        self, messages: List[LLMMessage], temperature: float, max_tokens: int
    ) -> dict:
        """Convert standard messages into Gemini API content format."""
        contents = []
        for msg in messages:
            role = "user" if msg.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        return {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

    def _validate_http_status(self, response: httpx.Response) -> None:
        """Validate HTTP status codes and raise typed errors."""
        if response.status_code in (401, 403):
            raise AuthenticationError("Invalid Gemini API key", self.provider_name, response.status_code)
        if response.status_code == 429:
            raise RateLimitError("Gemini rate limit exceeded", self.provider_name, 429)
        if response.is_error:
            raise InvalidResponseError(
                f"HTTP {response.status_code}: {response.text}",
                self.provider_name,
                response.status_code,
            )

    def _parse_gemini_response(self, data: dict, target_model: str) -> LLMResponse:
        """Extract candidate text and token counts from Gemini response."""
        try:
            candidates = data["candidates"]
            text = candidates[0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            return LLMResponse(
                content=text,
                provider=self.provider_name,
                model=target_model,
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
            )
        except (KeyError, IndexError) as exc:
            raise InvalidResponseError(
                f"Malformed Gemini payload: {exc}", self.provider_name
            ) from exc

    def _generate_dry_run_response(
        self, messages: List[LLMMessage], target_model: str
    ) -> LLMResponse:
        """Produce deterministic mock response when running without live API keys."""
        last_message = messages[-1].content if messages else "No content"
        mock_body = (
            f"[DryRun Gemini/{target_model}]\n"
            f"Processed prompt with {len(messages)} messages.\n"
            f"Target context snippet: {last_message[:120]}"
        )
        return LLMResponse(
            content=mock_body,
            provider=self.provider_name,
            model=target_model,
            prompt_tokens=140,
            completion_tokens=75,
        )
