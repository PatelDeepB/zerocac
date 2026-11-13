"""Unit and integration tests for multi-variant A/B experiments and self-healing bandit reallocation."""

import os
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.cli import app as cli_app
from zerocac.telemetry.experiment import (
    ExperimentEngine,
    VariantAngle,
)
from zerocac.telemetry.store import ExperimentStore
from zerocac.web.app import app as web_app

client = TestClient(web_app)
runner = CliRunner()


@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def test_generate_experiment_creates_3_variants() -> None:
    """Ensure ExperimentEngine synthesizes 3 psychological angle variants."""
    # Arrange & Act
    exp = ExperimentEngine.generate_experiment(
        asset_slug="dealflow-evaluator",
        base_title="Startup Dealflow Calculator",
        category="Fintech",
    )

    # Assert
    assert exp.asset_slug == "dealflow-evaluator"
    assert len(exp.variants) == 3
    angles = {v.angle for v in exp.variants}
    assert angles == {VariantAngle.UTILITARIAN, VariantAngle.CONTRARIAN, VariantAngle.QUANTITATIVE}
    assert all(v.traffic_allocation_pct > 30.0 for v in exp.variants)


def test_record_event_updates_variant_metrics() -> None:
    """Ensure logging impressions, clicks, and conversions computes accurate CTR and conv rate."""
    # Arrange
    exp = ExperimentEngine.generate_experiment("test-calc", "Test Calc")
    variant_id = exp.variants[0].variant_id

    # Act
    ExperimentEngine.record_event(exp, variant_id, "impression")
    ExperimentEngine.record_event(exp, variant_id, "impression")
    ExperimentEngine.record_event(exp, variant_id, "click")
    ExperimentEngine.record_event(exp, variant_id, "conversion")

    # Assert
    v = exp.variants[0]
    assert v.impressions == 2
    assert v.clicks == 1
    assert v.conversions == 1
    assert v.ctr == 50.0
    assert v.conversion_rate == 100.0


def test_multi_armed_bandit_reallocation() -> None:
    """Ensure multi-armed bandit allocates 80% to top converter after sample threshold."""
    # Arrange
    exp = ExperimentEngine.generate_experiment("saas-evaluator", "SaaS Evaluator")
    v_winner = exp.variants[0]
    v_runner_up = exp.variants[1]
    v_loser = exp.variants[2]

    # Act: Simulate interactions (winner: 10 conversions / 20 clicks = 50%, runner up: 2/10 = 20%, loser: 0/10 = 0%)
    for _ in range(20):
        ExperimentEngine.record_event(exp, v_winner.variant_id, "click")
    for _ in range(10):
        ExperimentEngine.record_event(exp, v_winner.variant_id, "conversion")

    for _ in range(10):
        ExperimentEngine.record_event(exp, v_runner_up.variant_id, "click")
    for _ in range(2):
        ExperimentEngine.record_event(exp, v_runner_up.variant_id, "conversion")

    for _ in range(10):
        ExperimentEngine.record_event(exp, v_loser.variant_id, "click")

    actions = ExperimentEngine.optimize_allocations(exp)

    # Assert
    assert exp.winner_variant_id == v_winner.variant_id
    assert v_winner.traffic_allocation_pct == 80.0
    assert v_runner_up.traffic_allocation_pct == 10.0
    assert v_loser.traffic_allocation_pct == 10.0
    assert any("80% traffic" in act for act in actions)


def test_empirical_roi_formula() -> None:
    """Ensure calculate_empirical_roi computes mathematically exact displacement."""
    # Arrange
    visitors = 1000
    leads = 20
    cpc = 35.0
    cpl = 180.0

    # Act
    roi = ExperimentEngine.calculate_empirical_roi(visitors, leads, cpc, cpl)

    # Assert
    assert roi["traffic_displacement_usd"] == 35000.0
    assert roi["lead_displacement_usd"] == 3600.0
    assert roi["total_ad_dollars_saved_usd"] == 38600.0


@pytest.mark.asyncio
async def test_experiment_store_persistence(temp_db_path: str) -> None:
    """Ensure ExperimentStore saves, retrieves, and lists experiments."""
    # Arrange
    store = ExperimentStore(db_path=temp_db_path)
    exp = ExperimentEngine.generate_experiment("store-slug", "Store Title")

    # Act
    await store.save_experiment(exp)
    fetched = await store.get_experiment("store-slug")
    all_exps = await store.list_experiments()

    # Assert
    assert fetched is not None
    assert fetched.asset_slug == "store-slug"
    assert len(fetched.variants) == 3
    assert len(all_exps) >= 1


def test_api_experiment_endpoints() -> None:
    """Ensure REST endpoints create, record events, optimize, and return ROI proof."""
    unique_slug = f"exp_slug_{uuid.uuid4().hex[:6]}"

    # 1. Create
    create_res = client.post(
        "/api/v1/telemetry/experiments/create",
        json={"slug": unique_slug, "title": "API Test Tool"},
    )
    assert create_res.status_code == 200
    exp_data = create_res.json()
    assert exp_data["asset_slug"] == unique_slug
    variant_id = exp_data["variants"][0]["variant_id"]

    # 2. Get
    get_res = client.get(f"/api/v1/telemetry/experiments/{unique_slug}")
    assert get_res.status_code == 200
    assert get_res.json()["asset_slug"] == unique_slug

    # 3. Log event
    event_res = client.post(
        "/api/v1/telemetry/experiments/event",
        json={"slug": unique_slug, "variant_id": variant_id, "event_type": "click"},
    )
    assert event_res.status_code == 200

    # 4. Optimize
    opt_res = client.post(
        "/api/v1/telemetry/experiments/optimize",
        json={"slug": unique_slug},
    )
    assert opt_res.status_code == 200
    assert "actions_taken" in opt_res.json()

    # 5. ROI
    roi_res = client.get("/api/v1/telemetry/roi?visitors=500&leads=10&cpc=30&cpl=150")
    assert roi_res.status_code == 200
    assert roi_res.json()["total_ad_dollars_saved_usd"] == 16500.0


def test_cli_experiment_and_roi_commands() -> None:
    """Ensure CLI 'zerocac experiment' and 'zerocac roi' execute properly."""
    # Act & Assert CLI experiment
    exp_res = runner.invoke(cli_app, ["experiment", "cli-test-tool", "--title", "CLI Tool"])
    assert exp_res.exit_code == 0
    assert "A/B Headline Experiment: cli-test-tool" in exp_res.output

    # Act & Assert CLI ROI
    roi_res = runner.invoke(cli_app, ["roi", "--visitors", "1000", "--leads", "25"])
    assert roi_res.exit_code == 0
    assert "Empirical Organic Ad Spend Displacement Proof" in roi_res.output
    assert "Total Displaced Paid Ad Spend:" in roi_res.output
