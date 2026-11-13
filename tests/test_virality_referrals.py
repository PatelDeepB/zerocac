"""Unit and integration tests for product-led K-factor virality and milestone referrals."""

import os
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.cli import app as cli_app
from zerocac.virality.models import RewardTierId
from zerocac.virality.tracker import ReferralTracker
from zerocac.virality.widget import ViralWidgetRenderer
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


@pytest.mark.asyncio
async def test_referral_tracker_creation_and_events(temp_db_path: str) -> None:
    """Ensure referral code is created, clicks/conversions logged, and stats calculated."""
    # Arrange
    tracker = ReferralTracker(db_path=temp_db_path)
    email = "growth_lead@startup.io"

    # Act
    code = await tracker.get_or_create_referral_code(email)
    same_code = await tracker.get_or_create_referral_code(email)

    await tracker.record_click(code, visitor_id="visitor-1")
    await tracker.record_click(code, visitor_id="visitor-2")
    await tracker.record_conversion(code, referred_email="peer1@co.com")

    stats = await tracker.get_stats(email)

    # Assert
    assert code == same_code
    assert code.startswith("ref-")
    assert stats.total_clicks == 2
    assert stats.total_conversions == 1
    assert stats.conversion_rate == 0.5
    assert stats.k_factor > 0.0


@pytest.mark.asyncio
async def test_milestone_reward_unlocks(temp_db_path: str) -> None:
    """Ensure driving 3 and 10 referrals unlocks tiered milestone rewards."""
    # Arrange
    tracker = ReferralTracker(db_path=temp_db_path)
    email = "champion@saas.com"
    code = await tracker.get_or_create_referral_code(email)

    # Act: Drive 3 conversions
    for i in range(3):
        await tracker.record_click(code)
        await tracker.record_conversion(code, referred_email=f"friend_{i}@test.com")

    stats_3 = await tracker.get_stats(email)

    # Assert 3 conversions
    unlocked_ids_3 = [r.tier_id for r in stats_3.unlocked_rewards]
    assert RewardTierId.GEO_PACKAGE_EXPORT in unlocked_ids_3
    assert RewardTierId.UNMETERED_INTERCEPTOR not in unlocked_ids_3
    assert stats_3.next_milestone is not None
    assert stats_3.next_milestone.tier_id == RewardTierId.UNMETERED_INTERCEPTOR

    # Act: Drive 7 more conversions (total 10)
    for i in range(3, 10):
        await tracker.record_click(code)
        await tracker.record_conversion(code, referred_email=f"friend_{i}@test.com")

    stats_10 = await tracker.get_stats(email)
    unlocked_ids_10 = [r.tier_id for r in stats_10.unlocked_rewards]

    # Assert 10 conversions
    assert RewardTierId.UNMETERED_INTERCEPTOR in unlocked_ids_10


@pytest.mark.asyncio
async def test_leaderboard_generation(temp_db_path: str) -> None:
    """Ensure leaderboard ranks champions and calculates saved ad spend."""
    # Arrange
    tracker = ReferralTracker(db_path=temp_db_path)
    code_top = await tracker.get_or_create_referral_code("top_performer@growth.com")
    code_second = await tracker.get_or_create_referral_code("second_place@saas.io")

    for i in range(5):
        await tracker.record_conversion(code_top, f"ref_top_{i}@co.com")
    for i in range(2):
        await tracker.record_conversion(code_second, f"ref_sec_{i}@co.com")

    # Act
    board = await tracker.get_leaderboard(limit=5)

    # Assert
    assert len(board) >= 2
    assert board[0].rank == 1
    assert board[0].referrals_driven == 5
    assert board[0].ad_dollars_saved_usd > 0
    assert board[1].rank == 2
    assert board[1].referrals_driven == 2


def test_widget_renderer_outputs() -> None:
    """Ensure SVG badge and HTML widget produce valid embeddable code."""
    # Arrange
    renderer = ViralWidgetRenderer()

    # Act
    svg = renderer.render_svg_counter_badge("ZeroCAC", 18500.0)

    # Assert
    assert "<svg" in svg
    assert "ZeroCAC" in svg
    assert "$18,500 Saved vs Ads" in svg


def test_api_virality_endpoints() -> None:
    """Ensure REST endpoints for referral creation, tracking, leaderboard, and badge work."""
    unique_user = f"api_user_{uuid.uuid4().hex[:6]}@test.com"
    # 1. Create referral
    create_res = client.post("/api/v1/virality/referral/create", json={"email": unique_user})
    assert create_res.status_code == 200
    ref_code = create_res.json()["referral_code"]

    # 2. Track click
    track_res = client.post("/api/v1/virality/referral/track", json={"referral_code": ref_code})
    assert track_res.status_code == 200
    assert track_res.json()["event"] == "click"

    # 3. Track conversion
    conv_res = client.post(
        "/api/v1/virality/referral/track",
        json={"referral_code": ref_code, "converted_email": "converted@friend.com"},
    )
    assert conv_res.status_code == 200
    assert conv_res.json()["event"] == "conversion"

    # 4. Get stats
    stats_res = client.get(f"/api/v1/virality/referral/{ref_code}")
    assert stats_res.status_code == 200
    assert stats_res.json()["total_conversions"] == 1

    # 5. Leaderboard
    board_res = client.get("/api/v1/virality/leaderboard?limit=5")
    assert board_res.status_code == 200
    assert isinstance(board_res.json(), list)

    # 6. SVG Badge
    badge_res = client.get("/api/v1/virality/badge?product_name=TestTool&savings=12000")
    assert badge_res.status_code == 200
    assert badge_res.headers["content-type"].startswith("image/svg+xml")
    assert "TestTool" in badge_res.text


def test_cli_referral_and_leaderboard_commands() -> None:
    """Ensure CLI 'zerocac referral' and 'zerocac leaderboard' execute cleanly."""
    # Act & Assert Referral
    ref_res = runner.invoke(cli_app, ["referral", "cli_tester@test.com"])
    assert ref_res.exit_code == 0
    assert "Referral Share URL" in ref_res.output
    assert "Milestone Rewards" in ref_res.output

    # Act & Assert Leaderboard
    board_res = runner.invoke(cli_app, ["leaderboard", "--limit", "5"])
    assert board_res.exit_code == 0
    assert "Leaderboard of Organic CAC Killers" in board_res.output
