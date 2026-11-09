"""Unit tests for the 8-Vector Day-1 Launch Machine (Option A)."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.analyzer.models import ProductProfile
from zerocac.cli import app as cli_app
from zerocac.launch.directories import DirectoryMatrixEngine
from zerocac.launch.github_packager import GitHubPackager
from zerocac.launch.launch_trio import LaunchTrioEngine
from zerocac.launch.models import (
    HardenedLaunchPackage,
    LaunchVector,
)
from zerocac.launch.orchestrator import LaunchOrchestrator
from zerocac.launch.reddit import RedditLaunchEngine
from zerocac.launch.show_hn import ShowHNEngine
from zerocac.launch.social import SocialLaunchEngine
from zerocac.launch.syndicator import PublishingSyndicator
from zerocac.web.app import app as fastapi_app

runner = CliRunner()
client = TestClient(fastapi_app)


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Fixture providing a standard B2B/DevTool product profile."""
    return ProductProfile(
        product_name="PulseOps",
        category="DevOps Automation",
        one_liner="Automate Kubernetes incident diagnostics in under 10 seconds",
        core_problem="Engineering teams burn 15 hours a week triaging pod crashes",
        solution_mechanism="Autonomous log-to-metric root cause correlation",
        unique_value_proposition="10x faster MTTR with zero agents to maintain",
        key_features=["Auto triage", "Root cause synthesis", "Slack alerting"],
    )


def test_github_packager_compiles_valid_bundle(tmp_path: Path, sample_profile: ProductProfile) -> None:
    """Ensure Vector 1 packager creates README with badges, topics, and exports files."""
    # Arrange
    packager = GitHubPackager()

    # Act
    pkg = packager.package_repository(
        profile=sample_profile,
        tool_html="<html><body>Calc</body></html>",
        tool_slug="k8s-evaluator",
        live_url="https://k8s-evaluator.pages.dev",
    )
    exported_dir = packager.export_repository(pkg, "<html><body>Calc</body></html>", tmp_path)

    # Assert
    assert pkg.repo_name == "k8s-evaluator-app"
    assert "Live-Demo_Application" in pkg.readme_markdown
    assert "https://k8s-evaluator.pages.dev" in pkg.readme_markdown
    assert (exported_dir / "index.html").exists()
    assert (exported_dir / "README.md").exists()
    assert (exported_dir / "LICENSE").exists()


def test_show_hn_engine_enforces_rules(sample_profile: ProductProfile) -> None:
    """Ensure Vector 2 Show HN title complies with guidelines under 80 chars."""
    # Arrange
    engine = ShowHNEngine()

    # Act
    pkg = engine.synthesize_submission(
        profile=sample_profile,
        live_url="https://k8s-evaluator.pages.dev",
        tool_name="K8s MTTR Grader",
    )

    # Assert
    assert pkg.title.startswith("Show HN: ")
    assert len(pkg.title) <= 80
    assert "https://k8s-evaluator.pages.dev" in pkg.maker_comment
    assert "zero external framework dependencies" in pkg.maker_comment
    assert pkg.suggested_utc_hour == 13


def test_launch_trio_engine_respects_constraints(sample_profile: ProductProfile) -> None:
    """Ensure Vector 3 synthesizes Product Hunt, Peerlist, and MicroLaunch payloads."""
    # Arrange
    engine = LaunchTrioEngine()

    # Act
    items = engine.synthesize_trio(sample_profile, "https://live.dev", "K8s Grader")

    # Assert
    assert len(items) == 3
    ph = [i for i in items if i.platform_name == "Product Hunt"][0]
    assert len(ph.tagline) <= 60
    assert len(ph.description) <= 260
    assert "Hey Hunters!" in ph.maker_first_comment


def test_reddit_launch_engine_generates_5_subreddits(sample_profile: ProductProfile) -> None:
    """Ensure Vector 4 generates 5 distinct culturally tailored subreddit posts."""
    # Arrange
    engine = RedditLaunchEngine()

    # Act
    posts = engine.synthesize_campaign(sample_profile, "https://live.dev", "K8s Grader")

    # Assert
    assert len(posts) == 5
    subreddits = {p.subreddit for p in posts}
    assert "r/SideProject" in subreddits
    assert "r/SaaS" in subreddits
    assert "r/webdev" in subreddits
    assert "r/startups" in subreddits
    assert "r/entrepreneur" in subreddits
    for p in posts:
        assert p.first_comment is not None
        assert "https://live.dev" in p.first_comment


def test_publishing_syndicator_generates_canonical_articles(sample_profile: ProductProfile) -> None:
    """Ensure Vector 5 generates technical articles with canonical attribution."""
    # Arrange
    syndicator = PublishingSyndicator()

    # Act
    articles = syndicator.synthesize_articles(sample_profile, "https://live.dev", "K8s Grader")

    # Assert
    assert len(articles) == 2
    devto = articles[0]
    assert devto.platform == "devto"
    assert devto.canonical_url == "https://live.dev"
    assert "Engineering-as-Marketing" in devto.markdown_content


def test_directory_matrix_engine_generates_15_listings(sample_profile: ProductProfile) -> None:
    """Ensure Vector 8 generates 15 high-DA directory records under character limits."""
    # Arrange
    engine = DirectoryMatrixEngine()

    # Act
    listings = engine.synthesize_matrix(sample_profile, "https://live.dev", "K8s Grader")

    # Assert
    assert len(listings) == 15
    for item in listings:
        assert len(item.title) <= 50
        assert len(item.short_pitch) <= 140
        assert len(item.full_description) <= 700


@pytest.mark.asyncio
async def test_launch_orchestrator_compiles_all_8_vectors(sample_profile: ProductProfile) -> None:
    """Ensure master orchestrator compiles complete 8-Vector package and executes dispatch."""
    # Arrange
    orchestrator = LaunchOrchestrator()

    # Act 1: Prepare
    pkg = orchestrator.prepare_launch_kit(
        profile=sample_profile,
        tool_html="<html><body>Tool</body></html>",
        tool_slug="k8s-evaluator",
        live_url="https://k8s-evaluator.pages.dev",
        tool_name="K8s MTTR Grader",
    )

    # Assert 1
    assert pkg.product_name == "PulseOps"
    assert len(pkg.launch_trio) == 3
    assert len(pkg.reddit_posts) == 5
    assert len(pkg.directories) == 15

    # Act 2: Execute (dry-run)
    report = await orchestrator.execute_launch(pkg, dry_run=True)

    # Assert 2
    assert report.total_vectors_attempted >= 7
    assert report.successful_vectors >= 7
    assert report.estimated_day1_visitors_floor >= 800


def test_api_launch_prepare_and_execute(sample_profile: ProductProfile) -> None:
    """Ensure FastAPI endpoints prepare and execute 8-Vector launch kit."""
    # 1. Prepare
    req_prepare = {
        "description": "Kubernetes automated root cause incident diagnostic tool",
        "product_name": "PulseOps",
        "live_url": "https://pulseops.pages.dev",
        "dry_run": True,
    }
    res_prepare = client.post("/api/v1/launch/prepare", json=req_prepare)
    assert res_prepare.status_code == 200
    pkg_data = res_prepare.json()
    assert pkg_data["product_name"] == "PulseOps"
    assert "github_package" in pkg_data
    assert "show_hn" in pkg_data
    assert len(pkg_data["reddit_posts"]) == 5

    # 2. Execute
    req_execute = {
        "package": pkg_data,
        "dry_run": True,
    }
    res_execute = client.post("/api/v1/launch/execute", json=req_execute)
    assert res_execute.status_code == 200
    report_data = res_execute.json()
    assert report_data["successful_vectors"] >= 7
    assert report_data["estimated_day1_visitors_floor"] >= 800


def test_cli_launch_prepare_and_execute_commands(tmp_path: Path) -> None:
    """Ensure Typer CLI `zerocac launch prepare` and `execute` subcommands work end-to-end."""
    # 1. Prepare
    out_dir = tmp_path / "dist_test_launch"
    res_prepare = runner.invoke(
        cli_app,
        [
            "launch",
            "prepare",
            "--desc",
            "Kubernetes incident triage tool",
            "--name",
            "PulseOps",
            "--out",
            str(out_dir),
            "--dry-run",
        ],
    )
    assert res_prepare.exit_code == 0
    assert "8-Vector Day-1 Launch Package" in res_prepare.output
    pkg_file = out_dir / "launch_package.json"
    assert pkg_file.exists()

    # 2. Execute
    res_execute = runner.invoke(
        cli_app,
        [
            "launch",
            "execute",
            str(pkg_file),
            "--dry-run",
        ],
    )
    assert res_execute.exit_code == 0
    assert "Day-1 Multi-Wave Execution Report" in res_execute.output
    assert "Day-1 Launch Impact Projection" in res_execute.output
