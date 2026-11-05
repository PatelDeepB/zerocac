"""Unit tests for Phase 4 Closed-Loop Telemetry & Autonomous Self-Tuning."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.cli import app as cli_app
from zerocac.telemetry.engine import TelemetryEngine
from zerocac.telemetry.models import (
    AssetMetrics,
    OptimizationAction,
    PerformanceTier,
)
from zerocac.web.app import app as fastapi_app

runner = CliRunner()
client = TestClient(fastapi_app)


@pytest.fixture
def sample_metrics() -> list[AssetMetrics]:
    """Fixture providing a diverse set of asset telemetry records."""
    return [
        AssetMetrics(
            slug="underperforming-calc",
            impressions=500,
            clicks=5,  # 1.0% CTR (below 2.0%)
            leads_captured=0,
        ),
        AssetMetrics(
            slug="viral-dealflow-grader",
            impressions=1000,
            clicks=60,  # 6.0% CTR
            leads_captured=10,  # 16.6% conv (above 8.0%)
        ),
        AssetMetrics(
            slug="healthy-geo-page",
            impressions=300,
            clicks=12,  # 4.0% CTR
            leads_captured=1,  # 8.3% conv
        ),
    ]


@pytest.mark.asyncio
async def test_telemetry_engine_classifies_underperformer_and_prescribes_healing(
    sample_metrics: list[AssetMetrics],
) -> None:
    """Ensure engine identifies low-CTR assets and triggers headline rewrite."""
    # Arrange
    engine = TelemetryEngine()

    # Act
    report = await engine.audit_assets(manual_metrics=sample_metrics)

    # Assert
    assert report.total_assets == 3
    assert report.total_leads_acquired == 11
    assert report.estimated_ad_savings_usd == 11 * 25.0  # $275 USD saved

    under = [a for a in report.assets if a.slug == "underperforming-calc"][0]
    assert under.tier == PerformanceTier.UNDERPERFORMING
    assert under.recommended_action == OptimizationAction.REWRITE_HEADLINE
    assert any("underperforming-calc" in note for note in report.autonomous_actions_taken)

    winner = [a for a in report.assets if a.slug == "viral-dealflow-grader"][0]
    assert winner.tier == PerformanceTier.OUTPERFORMING
    assert winner.recommended_action == OptimizationAction.EXPAND_CLUSTER


def test_api_telemetry_report_endpoint() -> None:
    """Ensure GET /api/v1/telemetry/report returns 200 with valid schema."""
    # Act
    response = client.get("/api/v1/telemetry/report")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "total_assets" in data
    assert "estimated_ad_savings_usd" in data
    assert "assets" in data


def test_api_telemetry_audit_endpoint() -> None:
    """Ensure POST /api/v1/telemetry/audit accepts custom metrics and computes ROI."""
    # Arrange
    payload = {
        "assets": [
            {
                "slug": "custom-tool",
                "impressions": 200,
                "clicks": 10,
                "leads_captured": 2,
            }
        ],
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/telemetry/audit", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_assets"] == 1
    assert data["total_leads_acquired"] == 2
    assert data["estimated_ad_savings_usd"] == 50.0


def test_cli_telemetry_command() -> None:
    """Ensure zerocac telemetry CLI command outputs summary and table."""
    # Act
    result = runner.invoke(cli_app, ["telemetry"])

    # Assert
    assert result.exit_code == 0
    assert "Closed-Loop Telemetry" in result.output
    assert "Total Leads Acquired" in result.output
    assert "Estimated Ad Budget Saved" in result.output
