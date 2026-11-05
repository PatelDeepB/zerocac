"""Unit tests for Phase 1 Autonomous Edge Deployment and Indexation Engine."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.cli import app as cli_app
from zerocac.deployers.cloudflare import CloudflarePagesDeployer
from zerocac.deployers.indexer import IndexNowClient, SitemapPinger
from zerocac.deployers.manager import EdgeDeploymentManager
from zerocac.deployers.models import (
    DeploymentArtifact,
    DeploymentProvider,
    DeploymentResult,
)
from zerocac.web.app import app as fastapi_app

runner = CliRunner()
client = TestClient(fastapi_app)


@pytest.fixture
def sample_artifact() -> DeploymentArtifact:
    """Fixture providing a sample standalone HTML tool artifact."""
    return DeploymentArtifact(
        project_slug="socius-roi-calculator",
        title="Socius ROI Calculator",
        html_content="<!DOCTYPE html><html><head><title>ROI Calc</title></head><body><h1>Calc</h1></body></html>",
        robots_txt="User-agent: *\nAllow: /\n",
        sitemap_xml='<?xml version="1.0" encoding="UTF-8"?><urlset><url><loc>https://socius.pages.dev/</loc></url></urlset>',
        extra_files={"data.json": '{"status": "active"}'},
    )


def test_cloudflare_deployer_writes_local_bundle(
    tmp_path: Path, sample_artifact: DeploymentArtifact
) -> None:
    """Ensure local bundle directory is constructed correctly with all assets."""
    # Arrange
    deployer = CloudflarePagesDeployer(output_directory=str(tmp_path))

    # Act
    bundle_dir = deployer.write_local_bundle(sample_artifact)

    # Assert
    assert bundle_dir.exists()
    assert (bundle_dir / "index.html").read_text(encoding="utf-8") == sample_artifact.html_content
    assert (bundle_dir / "robots.txt").read_text(encoding="utf-8") == sample_artifact.robots_txt
    assert (bundle_dir / "sitemap.xml").read_text(encoding="utf-8") == sample_artifact.sitemap_xml
    assert (bundle_dir / "data.json").read_text(encoding="utf-8") == '{"status": "active"}'


@pytest.mark.asyncio
async def test_cloudflare_deployer_dry_run_returns_live_url(
    tmp_path: Path, sample_artifact: DeploymentArtifact
) -> None:
    """Ensure dry_run mode generates simulated edge deployment result."""
    # Arrange
    deployer = CloudflarePagesDeployer(output_directory=str(tmp_path))

    # Act
    result = await deployer.deploy(sample_artifact, dry_run=True)

    # Assert
    assert result.success is True
    assert result.provider == DeploymentProvider.CLOUDFLARE_PAGES
    assert result.live_url == "https://socius-roi-calculator.pages.dev"
    assert result.deployment_id.startswith("cf-")
    assert result.error_message is None


@pytest.mark.asyncio
async def test_cloudflare_deployer_handles_api_failure(
    tmp_path: Path, sample_artifact: DeploymentArtifact
) -> None:
    """Ensure API errors from Cloudflare are captured in deployment result."""
    # Arrange
    deployer = CloudflarePagesDeployer(
        account_id="fake-account",
        api_token="fake-token",
        output_directory=str(tmp_path),
    )

    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.text = '{"success": false, "errors": ["Unauthorized"]}'

    # Act
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await deployer.deploy(sample_artifact, dry_run=False)

    # Assert
    assert result.success is False
    assert "403" in (result.error_message or "")


@pytest.mark.asyncio
async def test_indexnow_client_dry_run_returns_true() -> None:
    """Ensure IndexNow dry run returns success without outbound network traffic."""
    # Arrange
    client_indexer = IndexNowClient()

    # Act
    success = await client_indexer.submit_urls(
        host="socius.pages.dev",
        urls=["https://socius.pages.dev/calculator"],
        dry_run=True,
    )

    # Assert
    assert success is True


@pytest.mark.asyncio
async def test_indexnow_client_empty_urls_returns_false() -> None:
    """Ensure empty URL list fails fast."""
    # Arrange
    client_indexer = IndexNowClient()

    # Act
    success = await client_indexer.submit_urls(
        host="socius.pages.dev",
        urls=[],
        dry_run=True,
    )

    # Assert
    assert success is False


@pytest.mark.asyncio
async def test_edge_deployment_manager_orchestrates_deploy_and_index(
    sample_artifact: DeploymentArtifact,
) -> None:
    """Ensure EdgeDeploymentManager triggers both deployment and indexation."""
    # Arrange
    mock_deployer = AsyncMock(spec=CloudflarePagesDeployer)
    mock_deployer.deploy.return_value = DeploymentResult(
        success=True,
        provider=DeploymentProvider.CLOUDFLARE_PAGES,
        live_url="https://socius.pages.dev",
        deployment_id="cf-123456",
    )

    mock_indexer = AsyncMock(spec=IndexNowClient)
    mock_indexer.submit_urls.return_value = True

    mock_pinger = AsyncMock(spec=SitemapPinger)
    mock_pinger.ping_search_engines.return_value = True

    manager = EdgeDeploymentManager(
        cloudflare_deployer=mock_deployer,
        indexnow_client=mock_indexer,
        sitemap_pinger=mock_pinger,
    )

    # Act
    result = await manager.deploy_and_index(sample_artifact, enable_indexing=True, dry_run=True)

    # Assert
    assert result.success is True
    assert result.indexnow_submitted is True
    assert result.indexed_urls == ["https://socius.pages.dev"]
    mock_indexer.submit_urls.assert_awaited_once()


def test_api_deploy_endpoint_success() -> None:
    """Ensure POST /api/v1/deploy returns 200 with deployment details."""
    # Arrange
    payload = {
        "project_slug": "instant-calc",
        "title": "Instant Calc",
        "html_content": "<html><body>Instant Calc</body></html>",
        "provider": "cloudflare_pages",
        "enable_indexing": True,
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/deploy", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["live_url"] == "https://instant-calc.pages.dev"
    assert data["indexnow_submitted"] is True


def test_api_deploy_endpoint_empty_html_returns_400() -> None:
    """Ensure empty HTML payload is rejected with 400."""
    # Arrange
    payload = {
        "project_slug": "empty-tool",
        "html_content": "   ",
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/deploy", json=payload)

    # Assert
    assert response.status_code == 400


def test_cli_deploy_command_with_file(tmp_path: Path) -> None:
    """Ensure zerocac deploy --file executes successfully."""
    # Arrange
    html_file = tmp_path / "test_tool.html"
    html_file.write_text("<html><body>My Test Tool</body></html>", encoding="utf-8")

    # Act
    result = runner.invoke(
        cli_app,
        [
            "deploy",
            "--file",
            str(html_file),
            "--slug",
            "my-test-tool",
            "--dry-run",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "Autonomous Edge Deployment Summary" in result.output
    assert "https://my-test-tool.pages.dev" in result.output
