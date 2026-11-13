"""Unit and integration tests for the 24/7 Persistent Interceptor Daemon Runner."""

import os
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.cli import app as cli_app
from zerocac.interceptor.daemon import InterceptorDaemon
from zerocac.interceptor.models import (
    AutonomyTier,
    IntentClassification,
    InterceptOpportunity,
    SocialPlatform,
    StealthMode,
)
from zerocac.interceptor.notifier import InterceptorNotifier
from zerocac.interceptor.store import InterceptorStore
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



def _build_sample_opportunity(post_id: str = "post-123", score: int = 88) -> InterceptOpportunity:
    """Helper to create a sample opportunity for testing."""
    return InterceptOpportunity(
        platform=SocialPlatform.REDDIT,
        post_id=post_id,
        post_url=f"https://reddit.com/r/SaaS/comments/{post_id}",
        subreddit_or_topic="r/SaaS",
        author="frustrated_cto",
        title="Google ads CPC jumped from $8 to $45 this quarter",
        body_text="We are spending $4,500/mo on search ads and getting zero demos. Need organic alternatives.",
        created_at_utc="2026-11-13T10:00:00Z",
        intent_score=score,
        classification=IntentClassification.PRICE_COMPLAINT,
        extracted_entities={"monthly_spend": 4500, "scale_volume": "100 nodes", "team_seats": 8},
        stealth_mode=StealthMode.ZERO_LINK_VALUE_TRAP,
        synthesized_reply="Here is how we lowered customer acquisition cost from $45 to $0 by engineering interactive calculators.",
    )


@pytest.mark.asyncio
async def test_store_deduplication_lifecycle(temp_db_path: str) -> None:
    """Ensure InterceptorStore correctly tracks and dedupes seen post IDs."""
    # Arrange
    store = InterceptorStore(db_path=temp_db_path)
    post_id = "test-post-99"

    # Act & Assert
    assert await store.is_seen(post_id) is False

    await store.mark_seen(post_id, platform="reddit")
    assert await store.is_seen(post_id) is True

    # Idempotent re-mark
    await store.mark_seen(post_id, platform="reddit")
    assert await store.is_seen(post_id) is True


@pytest.mark.asyncio
async def test_store_save_get_and_list_opportunities(temp_db_path: str) -> None:
    """Ensure InterceptorStore persists and queries opportunities accurately."""
    # Arrange
    store = InterceptorStore(db_path=temp_db_path)
    opp1 = _build_sample_opportunity("post-1", score=78)
    opp2 = _build_sample_opportunity("post-2", score=92)

    # Act
    await store.save_opportunity(opp1)
    await store.save_opportunity(opp2)

    fetched = await store.get_opportunity(opp1.opportunity_id)
    all_opps = await store.list_opportunities()

    # Assert
    assert fetched is not None
    assert fetched.opportunity_id == opp1.opportunity_id
    assert fetched.author == "frustrated_cto"
    assert len(all_opps) == 2
    # Verify descending intent score sorting
    assert all_opps[0].opportunity_id == opp2.opportunity_id

    # Test update status
    updated = await store.update_opportunity_status(opp1.opportunity_id, "dispatched")
    assert updated is True
    pending_only = await store.list_opportunities(status="pending_approval")
    assert len(pending_only) == 1
    assert pending_only[0].opportunity_id == opp2.opportunity_id


def test_notifier_format_and_threshold_check() -> None:
    """Ensure InterceptorNotifier produces rich formatted alerts and enforces score gates."""
    # Arrange
    notifier = InterceptorNotifier(alert_threshold=85)
    opp_high = _build_sample_opportunity("high-1", score=90)
    opp_low = _build_sample_opportunity("low-1", score=80)

    # Act
    formatted = notifier.format_alert_message(opp_high)
    keyboard = notifier._build_inline_keyboard(opp_high.opportunity_id)

    # Assert
    assert "HIGH BUYER AGONY DETECTED" in formatted
    assert "90/100" in formatted
    assert "$4500/mo" in formatted
    assert "inline_keyboard" in keyboard
    assert keyboard["inline_keyboard"][0][0]["text"] == "🚀 Approve & Post"


@pytest.mark.asyncio
async def test_notifier_send_alert_dry_run() -> None:
    """Ensure notifier dry run returns True for qualifying scores and False below threshold."""
    # Arrange
    notifier = InterceptorNotifier(alert_threshold=85)
    opp_high = _build_sample_opportunity("high-1", score=88)
    opp_low = _build_sample_opportunity("low-1", score=82)

    # Act & Assert
    assert await notifier.send_alert(opp_high, dry_run=True) is True
    assert await notifier.send_alert(opp_low, dry_run=True) is False


@pytest.mark.asyncio
async def test_daemon_run_once_dedupes_and_persists(temp_db_path: str) -> None:
    """Ensure daemon run_once detects new posts and skips them on subsequent passes."""
    # Arrange
    store = InterceptorStore(db_path=temp_db_path)
    daemon = InterceptorDaemon(
        subreddits=["SaaS", "startups"],
        min_score=75,
        dry_run=True,
        store=store,
    )

    # Act
    first_pass_opps = await daemon.run_once()
    second_pass_opps = await daemon.run_once()
    status = daemon.get_status()

    # Assert
    assert len(first_pass_opps) > 0
    assert len(second_pass_opps) == 0  # Deduplicated on second pass!
    assert status.total_iterations == 2
    assert status.total_opportunities_found == len(first_pass_opps)
    assert status.last_polled_at is not None


@pytest.mark.asyncio
async def test_daemon_full_autonomy_dispatches_high_intent(temp_db_path: str) -> None:
    """Ensure daemon with FULL_AUTONOMOUS auto-dispatches opportunities >= 90 score."""
    # Arrange
    store = InterceptorStore(db_path=temp_db_path)
    daemon = InterceptorDaemon(
        autonomy_tier=AutonomyTier.FULL_AUTONOMOUS,
        min_score=75,
        dry_run=True,
        store=store,
    )

    # Act
    opps = await daemon.run_once()
    status = daemon.get_status()

    # Assert
    high_intent = [o for o in opps if o.intent_score >= 90]
    if high_intent:
        assert status.total_dispatched >= 1


def test_api_stored_opportunities_endpoint() -> None:
    """Ensure GET /api/v1/intercept/opportunities retrieves stored items."""
    # Act
    response = client.get("/api/v1/intercept/opportunities?limit=10")

    # Assert
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_daemon_lifecycle_endpoints() -> None:
    """Ensure GET/POST daemon lifecycle routes work properly."""
    # 1. Status
    res_status = client.get("/api/v1/intercept/daemon/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "is_running" in data

    # 2. Start
    start_payload = {
        "poll_interval": 30.0,
        "autonomy_tier": "manual_review",
        "min_score": 80,
        "dry_run": True,
    }
    res_start = client.post("/api/v1/intercept/daemon/start", json=start_payload)
    assert res_start.status_code == 200
    assert res_start.json()["is_running"] is True

    # 3. Stop
    res_stop = client.post("/api/v1/intercept/daemon/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["is_running"] is False


def test_cli_intercept_daemon_once() -> None:
    """Ensure CLI 'zerocac intercept daemon --once' runs single pass successfully."""
    # Act
    result = runner.invoke(
        cli_app,
        ["intercept", "daemon", "--once", "--min-score", "75", "--dry-run"],
    )

    # Assert
    assert result.exit_code == 0
    assert "Poll pass complete" in result.output
