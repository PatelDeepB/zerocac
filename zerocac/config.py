"""Application configuration and environment variable loading.

Uses Pydantic Settings to load and validate configurations from
environment variables and .env files.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for ZeroCAC execution environment and AI models."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", alias="ZEROCAC_HOST")
    port: int = Field(default=8000, alias="ZEROCAC_PORT")
    env: str = Field(default="development", alias="ZEROCAC_ENV")
    debug: bool = Field(default=False, alias="ZEROCAC_DEBUG")

    # Primary provider routing
    default_ai_provider: str = Field(default="openai", alias="DEFAULT_AI_PROVIDER")
    default_strategy_model: str = Field(default="gpt-6-astra", alias="DEFAULT_STRATEGY_MODEL")
    default_fast_model: str = Field(default="gpt-6.1-luna", alias="DEFAULT_FAST_MODEL")

    # OpenAI configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model_strategy: str = Field(default="gpt-6-astra", alias="OPENAI_MODEL_STRATEGY")
    openai_model_fast: str = Field(default="gpt-6.1-luna", alias="OPENAI_MODEL_FAST")

    # Google Gemini configuration
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model_strategy: str = Field(default="gemini-4-argon", alias="GEMINI_MODEL_STRATEGY")
    gemini_model_fast: str = Field(default="gemini-3.8-flash", alias="GEMINI_MODEL_FAST")

    # Anthropic Claude configuration
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model_strategy: str = Field(default="claude-opus-5-5", alias="ANTHROPIC_MODEL_STRATEGY")
    anthropic_model_fast: str = Field(default="claude-sonnet-5-5", alias="ANTHROPIC_MODEL_FAST")

    # NVIDIA NIM configuration
    nvidia_api_key: Optional[str] = Field(default=None, alias="NVIDIA_API_KEY")
    nvidia_base_url: str = Field(default="https://integrate.api.nvidia.com/v1", alias="NVIDIA_BASE_URL")
    nvidia_model_strategy: str = Field(default="nemotron-3-ultra", alias="NVIDIA_MODEL_STRATEGY")
    nvidia_model_fast: str = Field(default="nemotron-3.5-super-vl", alias="NVIDIA_MODEL_FAST")

    # DeepSeek configuration
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL")
    deepseek_model_strategy: str = Field(default="deepseek-r1", alias="DEEPSEEK_MODEL_STRATEGY")
    deepseek_model_fast: str = Field(default="deepseek-v4.1-flash", alias="DEEPSEEK_MODEL_FAST")

    # Local Ollama fallback
    ollama_base_url: str = Field(default="http://localhost:11434/v1", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.3", alias="OLLAMA_MODEL")


def get_settings() -> Settings:
    """Retrieve the application settings singleton."""
    return Settings()
