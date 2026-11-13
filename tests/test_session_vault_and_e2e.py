"""Unit tests for encrypted session vault and comprehensive end-to-end stress pipeline."""

import os
import tempfile
import pytest
from typer.testing import CliRunner

from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.cli import app as cli_app
from zerocac.engines.microtool import MicroToolEngine
from zerocac.interceptor.daemon import InterceptorDaemon
from zerocac.interceptor.engine import CommunityInterceptorEngine
from zerocac.interceptor.session_vault import SessionVault
from zerocac.interceptor.store import InterceptorStore
from zerocac.launch.orchestrator import LaunchOrchestrator
from zerocac.pseo.engine import PSEOMatrixEngine
from zerocac.telemetry.experiment import ExperimentEngine
from zerocac.virality.tracker import ReferralTracker

runner = CliRunner()


@pytest.fixture
def temp_vault_path():
    """Create a temporary path for testing session vault."""
    with tempfile.NamedTemporaryFile(suffix=".enc", delete=False) as f:
        path = f.name
    yield path
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def test_session_vault_encryption_and_retrieval(temp_vault_path: str) -> None:
    """Ensure SessionVault encrypts credentials and decrypts them accurately."""
    # Arrange
    vault = SessionVault(vault_path=temp_vault_path)
    reddit_session = {"auth_token": "secret_bearer_999", "modhash": "mh_abc123"}

    # Act
    vault.store_session(platform="reddit", username="lead_founder", session_data=reddit_session)
    fetched = vault.get_session(platform="reddit", username="lead_founder")
    sessions = vault.list_active_sessions()

    # Assert
    assert fetched is not None
    assert fetched["auth_token"] == "secret_bearer_999"
    assert fetched["modhash"] == "mh_abc123"
    assert len(sessions) == 1
    assert sessions[0]["username"] == "lead_founder"
    assert "auth_token" in sessions[0]["configured_keys"]

    # Test Revoke
    revoked = vault.revoke_session(platform="reddit", username="lead_founder")
    assert revoked is True
    assert vault.get_session(platform="reddit", username="lead_founder") is None


def test_cli_intercept_login_and_sessions(temp_vault_path: str) -> None:
    """Ensure CLI 'zerocac intercept login' and 'sessions' commands execute cleanly."""
    # Act
    login_res = runner.invoke(
        cli_app,
        ["intercept", "login", "reddit", "bot_user", "--token", "test_tok", "--cookie", "test_cookie"],
    )
    sessions_res = runner.invoke(cli_app, ["intercept", "sessions"])

    # Assert
    assert login_res.exit_code == 0
    assert "Successfully stored encrypted session" in login_res.output
    assert sessions_res.exit_code == 0
    assert "Encrypted Interceptor Session Vault" in sessions_res.output


@pytest.mark.asyncio
async def test_end_to_end_zero_cac_perfection_pipeline() -> None:
    """Complete end-to-end stress verification across all integrated organic engines."""
    # Step 1: Ingest product and synthesize positioning
    analyzer = ProductAnalyzer()
    profile = await analyzer.analyze_text(
        description="Autonomous organic AI marketing engine replacing paid ads with compounding equity.",
        product_name="ZeroCAC",
    )
    assert profile.product_name == "ZeroCAC"

    # Step 2: Generate standalone interactive micro-tool
    tool_engine = MicroToolEngine()
    tool_pkg = await tool_engine.generate_tool(profile, dry_run=True)
    assert tool_pkg.concept.slug is not None
    assert len(tool_pkg.html_content) > 100

    # Step 3: Option A (Day-1 Launch Carpet Bombing Kit)
    launch_orch = LaunchOrchestrator()
    launch_pkg = launch_orch.prepare_launch_kit(
        profile=profile,
        tool_html=tool_pkg.html_content,
        tool_slug=tool_pkg.concept.slug,
        live_url="https://zerocac-tool.pages.dev",
        tool_name=tool_pkg.concept.tool_name,
    )
    assert launch_pkg.github_package is not None
    assert launch_pkg.show_hn is not None
    assert len(launch_pkg.reddit_posts) == 5

    # Step 4: Option B (Programmatic SEO Matrix)
    pseo_engine = PSEOMatrixEngine()
    pseo_pkg = await pseo_engine.generate_matrix(
        profile=profile,
        tool_html=tool_pkg.html_content,
        target_count=3,
        dry_run=True,
    )
    assert len(pseo_pkg.pages) == 3

    # Step 5: Option C (Community Intent Interceptor)
    intercept_engine = CommunityInterceptorEngine()
    opps = await intercept_engine.scan_opportunities(
        profile=profile,
        tool_url="https://zerocac.org",
        min_score=75,
        dry_run=True,
    )
    assert len(opps) > 0

    # Step 6: 24/7 Daemon Polling Pass with Deduplication
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        daemon_db = f.name
    try:
        store = InterceptorStore(db_path=daemon_db)
        daemon = InterceptorDaemon(profile=profile, store=store, dry_run=True)
        detected = await daemon.run_once()
        assert len(detected) > 0
        second_poll = await daemon.run_once()
        assert len(second_poll) == 0  # Deduplication verified
    finally:
        if os.path.exists(daemon_db):
            try:
                os.remove(daemon_db)
            except OSError:
                pass

    # Step 7: Product-Led K-Factor Referral Engine
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        ref_db = f.name
    try:
        ref_tracker = ReferralTracker(db_path=ref_db)
        code = await ref_tracker.get_or_create_referral_code("test_founder@e2e.com")
        await ref_tracker.record_click(code)
        await ref_tracker.record_conversion(code, "friend1@e2e.com")
        stats = await ref_tracker.get_stats("test_founder@e2e.com")
        assert stats.total_conversions == 1
    finally:
        if os.path.exists(ref_db):
            try:
                os.remove(ref_db)
            except OSError:
                pass

    # Step 8: Multi-Variant A/B Experiment & ROI Proof
    exp = ExperimentEngine.generate_experiment("e2e-tool", "E2E Tool")
    assert len(exp.variants) == 3
    roi = ExperimentEngine.calculate_empirical_roi(organic_visitors=1000, leads_captured=25, cpc=35.0, cpl=180.0)
    assert roi["total_ad_dollars_saved_usd"] == 39500.0
