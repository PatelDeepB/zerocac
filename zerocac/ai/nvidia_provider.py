"""NVIDIA NIM provider implementation for Nemotron 3 Ultra and 3.5 Super VL."""

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


class NVIDIAProvider(BaseLLMProvider):
    """Integrates NVIDIA NIM microservices API for Nemotron models."""

    DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
    DEFAULT_MODEL = "nemotron-3.5-super-vl"

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
        return "nvidia"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Call NVIDIA NIM chat completions endpoint."""
        target_model = model or self.default_model

        if not self.api_key or self.api_key.startswith("your_"):
            return self._generate_dry_run_response(messages, target_model)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": target_model,
            "messages": [msg.model_dump() for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.RequestError as exc:
                raise InvalidResponseError(f"Network request failed: {exc}", self.provider_name) from exc

        self._validate_http_status(response)
        return self._parse_completion(response.json(), target_model)

    def _validate_http_status(self, response: httpx.Response) -> None:
        """Validate response status codes from NVIDIA NIM."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid NVIDIA API key provided", self.provider_name, 401)
        if response.status_code == 429:
            raise RateLimitError("NVIDIA NIM quota or rate limit exceeded", self.provider_name, 429)
        if response.is_error:
            raise InvalidResponseError(
                f"HTTP {response.status_code}: {response.text}",
                self.provider_name,
                response.status_code,
            )

    def _parse_completion(self, data: dict, target_model: str) -> LLMResponse:
        """Extract completion text and usage metrics from NVIDIA response."""
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})
            return LLMResponse(
                content=content,
                provider=self.provider_name,
                model=target_model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )
        except (KeyError, IndexError) as exc:
            raise InvalidResponseError(
                f"Malformed NVIDIA NIM payload: {exc}", self.provider_name
            ) from exc

    def _generate_dry_run_response(
        self, messages: List[LLMMessage], target_model: str
    ) -> LLMResponse:
        """Produce deterministic mock response when running without live API keys."""
        last_message = messages[-1].content if messages else "No content"
        mock_body = (
            f"[DryRun NVIDIA/{target_model}]\n"
            f"Processed prompt with {len(messages)} messages.\n"
            f"Target context snippet: {last_message[:120]}"
        )
        return LLMResponse(
            content=mock_body,
            provider=self.provider_name,
            model=target_model,
            prompt_tokens=150,
            completion_tokens=80,
        )
