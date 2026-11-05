"""Unit tests for the Typer command-line interface."""

from pathlib import Path
from typer.testing import CliRunner

from zerocac.cli import app

runner = CliRunner()


def test_cli_version_command_outputs_metadata() -> None:
    """Ensure `zerocac version` returns the current version and model list."""
    # Arrange & Act
    result = runner.invoke(app, ["version"])

    # Assert
    assert result.exit_code == 0
    assert "ZeroCAC v0.1.0" in result.stdout
    assert "OpenAI" in result.stdout
    assert "Gemini" in result.stdout
    assert "Nemotron" in result.stdout


def test_cli_analyze_command_succeeds_with_description() -> None:
    """Ensure `zerocac analyze` parses description and displays intelligence panel."""
    # Arrange & Act
    result = runner.invoke(
        app,
        ["analyze", "--desc", "AI tool that generates podcasts from research papers automatically."],
    )

    # Assert
    assert result.exit_code == 0
    assert "Strategic Intelligence Profile" in result.stdout
    assert "Product:" in result.stdout


def test_cli_directories_command_outputs_table() -> None:
    """Ensure `zerocac directories` displays the formatted software directory table."""
    # Arrange & Act
    result = runner.invoke(app, ["directories", "--desc", "Modern headless CRM for B2B teams."])

    # Assert
    assert result.exit_code == 0
    assert "Directory Submissions" in result.stdout
    assert "Product Hunt" in result.stdout


def test_cli_radar_command_outputs_table() -> None:
    """Ensure `zerocac radar` executes dry-run scanning and outputs the signal table."""
    # Arrange & Act
    result = runner.invoke(
        app,
        ["radar", "--desc", "Autonomous open source customer acquisition engine.", "--dry-run"],
    )

    # Assert
    assert result.exit_code == 0
    assert "Live Intent Radar Signals" in result.stdout
    assert "Radar Action Protocol" in result.stdout


def test_cli_microtool_command_generates_files(tmp_path: Path) -> None:
    """Ensure `zerocac microtool` creates the standalone HTML web utility."""
    # Arrange & Act
    out_dir = tmp_path / "tools_export"
    result = runner.invoke(
        app,
        [
            "microtool",
            "--desc",
            "Autonomous open source customer acquisition engine.",
            "--out",
            str(out_dir),
            "--dry-run",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "Engineering-as-Marketing Asset Ready" in result.stdout
    assert (out_dir / "ad-spend-vs-organic-cac-calculator" / "index.html").exists()


def test_cli_geo_command_outputs_panels() -> None:
    """Ensure `zerocac geo` produces Princeton GEO citation panels."""
    # Arrange & Act
    result = runner.invoke(
        app,
        ["geo", "--desc", "Autonomous open source customer acquisition engine.", "--dry-run"],
    )

    # Assert
    assert result.exit_code == 0
    assert "GEO Citation Asset" in result.stdout
    assert "Answer-First" in result.stdout
    assert "Permissive robots.txt" in result.stdout
    assert "Bing / ChatGPT Search Action Plan" in result.stdout


def test_cli_run_command_exports_campaign_artifacts(tmp_path: Path) -> None:
    """Ensure `zerocac run` compiles all 4 engines and writes files to the target directory."""
    # Arrange
    out_dir = tmp_path / "test_campaign"

    # Act
    result = runner.invoke(
        app,
        [
            "run",
            "--desc",
            "Super lightweight task runner for monorepos that replaces Makefiles.",
            "-o",
            str(out_dir),
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert (out_dir / "profile.json").exists()
    assert (out_dir / "sniper_campaign.json").exists()
    assert (out_dir / "viral_campaign.json").exists()
    assert (out_dir / "directories.json").exists()
    assert (out_dir / "aeo_pages").is_dir()
