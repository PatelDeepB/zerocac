"""Pytest configuration and global test fixtures for ZeroCAC.

Ensures unit test suites execute against isolated, deterministic mock
environments without making remote API calls or polluting local state.
"""

from typing import Generator
import pytest

from zerocac.config import Settings


@pytest.fixture(autouse=True)
def clean_test_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Isolate testing environment to prevent live network calls and ensure fast execution."""
    monkeypatch.setenv("DEFAULT_AI_PROVIDER", "openai")
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("NVIDIA_MODEL_STRATEGY", "nemotron-3-ultra")
    monkeypatch.setenv("NVIDIA_MODEL_FAST", "nemotron-3.5-super-vl")
    monkeypatch.setenv("ZEROCAC_ENV", "testing")
    yield
