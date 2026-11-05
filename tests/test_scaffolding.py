"""Unit tests verifying project scaffolding and repository structure."""

from pathlib import Path

from zerocac import __version__
from zerocac.config import Settings, get_settings


def test_package_metadata_should_be_defined() -> None:
    """Ensure the package version is valid and semantic."""
    # Arrange & Act
    version = __version__

    # Assert
    assert version == "0.2.0"
    assert isinstance(version, str)


def test_settings_should_have_sensible_defaults() -> None:
    """Ensure settings load expected frontier 2026 default models."""
    # Arrange & Act
    settings = get_settings()

    # Assert
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.default_ai_provider == "openai"
    assert settings.openai_model_strategy == "gpt-6-astra"
    assert settings.openai_model_fast == "gpt-6.1-luna"
    assert settings.gemini_model_strategy == "gemini-4-argon"
    assert settings.gemini_model_fast == "gemini-3.8-flash"
    assert settings.anthropic_model_strategy == "claude-opus-5-5"
    assert settings.anthropic_model_fast == "claude-sonnet-5-5"
    assert settings.nvidia_model_strategy == "nemotron-3-ultra"
    assert settings.nvidia_model_fast == "nemotron-3.5-super-vl"
    assert settings.deepseek_model_strategy == "deepseek-r1"
    assert settings.deepseek_model_fast == "deepseek-v4.1-flash"


def test_settings_should_support_explicit_overrides() -> None:
    """Ensure settings can be instantiated with custom configurations."""
    # Arrange
    custom_port = 9090
    custom_provider = "gemini"

    # Act
    settings = Settings(
        ZEROCAC_PORT=custom_port,
        DEFAULT_AI_PROVIDER=custom_provider,
    )

    # Assert
    assert settings.port == custom_port
    assert settings.default_ai_provider == custom_provider


def test_community_and_repo_standards_files_should_exist() -> None:
    """Verify that all GitHub open source community health files exist."""
    # Arrange
    root = Path(__file__).resolve().parent.parent
    required_files = [
        "pyproject.toml",
        ".gitignore",
        ".env.example",
        "LICENSE",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "Dockerfile",
        "docker-compose.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
    ]

    # Act & Assert
    for file_name in required_files:
        file_path = root / file_name
        assert file_path.exists(), f"Required repository standard file missing: {file_name}"
        assert file_path.stat().st_size > 0, f"File should not be empty: {file_name}"
