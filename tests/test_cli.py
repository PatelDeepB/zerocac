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
            "--out",
            str(out_dir),
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "Successfully exported complete campaign" in result.stdout
    assert (out_dir / "profile.json").exists()
    assert (out_dir / "sniper_campaign.json").exists()
    assert (out_dir / "viral_campaign.json").exists()
    assert (out_dir / "directories.json").exists()
    assert (out_dir / "aeo_pages").exists()
