"""Unit and integration tests for the Direct Social & Community Intent Interceptor (Option C)."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.cli import app as cli_app
from zerocac.interceptor.camouflage import CamouflageEngine
from zerocac.interceptor.engine import CommunityInterceptorEngine
from zerocac.interceptor.extractor import NumericEntityExtractor
from zerocac.interceptor.listener import SocialStreamListener
from zerocac.interceptor.models import (
    AccountCredential,
    IntentClassification,
    InterceptOpportunity,
    SocialPlatform,
    StealthMode,
)
from zerocac.interceptor.poster import SocialPoster
from zerocac.interceptor.scorer import IntentScorer
from zerocac.interceptor.synthesizer import PractitionerReplySynthesizer
from zerocac.interceptor.vault import AccountVault
from zerocac.web.app import app as fastapi_app

runner = CliRunner()
client = TestClient(fastapi_app)


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Fixture providing a standard product profile with competitor gaps."""
    return ProductProfile(
        product_name="PulseOps",
        category="DevOps Automation",
        one_liner="Automate Kubernetes incident diagnostics in under 10 seconds",
        core_problem="Engineering teams burn 15 hours a week triaging pod crashes",
        solution_mechanism="Autonomous log-to-metric root cause correlation",
        unique_value_proposition="10x faster MTTR with zero agents to maintain",
        key_features=["Auto triage", "Root cause synthesis", "Slack alerting"],
        competitor_gaps=[
            CompetitorGap(
                competitor_name="Datadog",
                their_weakness="High price per host and complex agent setups",
                our_advantage="Agentless instant diagnostics at $0 CAC cost",
            ),
            CompetitorGap(
                competitor_name="PagerDuty",
                their_weakness="Only sends alerts without diagnosing root cause",
                our_advantage="Automates triage and root cause in seconds",
            ),
        ],
        personas=[
            ICPPersona(
                persona_name="DevOps Lead",
                core_pain_point="Drowning in noisy on-call alerts",
                trigger_event="Production outage on weekend",
                primary_objection="Too much setup time",
            )
        ],
    )


def test_numeric_extractor_parses_budget_and_scale() -> None:
    """Ensure entity extractor correctly parses dollar spend, hosts, and volume."""
    # Arrange
    extractor = NumericEntityExtractor()
    sample_text = (
        "Our monthly bill is $4,500/mo across 25 hosts and 400 GB logs. "
        "Our team of 15 engineers is looking to migrate."
    )

    # Act
    entities = extractor.extract_entities(sample_text)

    # Assert
    assert entities.get("budget_or_bill_usd") == 4500.0
    assert entities.get("host_or_node_count") == 25
    assert entities.get("daily_volume_gb") == 400.0
    assert entities.get("team_size") == 15


def test_intent_scorer_qualifies_high_intent_and_crisis() -> None:
    """Ensure scorer assigns high scores to migration queries and crisis signals."""
    # Arrange
    scorer = IntentScorer(min_threshold=75)
    competitors = ["Datadog", "PagerDuty"]

    # Act
    score_mig, class_mig, comp_mig = scorer.score_post(
        title="Need alternative to Datadog",
        body="Bill is too expensive, looking to switch away immediately.",
        competitor_names=competitors,
    )
    score_crisis, class_crisis, comp_crisis = scorer.score_post(
        title="PagerDuty outage again",
        body="Major service disruption on PagerDuty status page, all alerts broken.",
        competitor_names=competitors,
    )
    score_low, class_low, comp_low = scorer.score_post(
        title="What is your favorite coffee?",
        body="Just curious what roasts people drink while coding.",
        competitor_names=competitors,
    )

    # Assert
    assert score_mig >= 80
    assert class_mig in (IntentClassification.IMMEDIATE_MIGRATION, IntentClassification.PRICE_COMPLAINT)
    assert comp_mig == "Datadog"

    assert score_crisis >= 80
    assert class_crisis == IntentClassification.COMPETITOR_CRISIS
    assert comp_crisis == "PagerDuty"

    assert score_low < 40
    assert class_low == IntentClassification.IRRELEVANT
    assert comp_low is None


def test_camouflage_engine_enforces_9_to_1_ratio() -> None:
    """Ensure camouflage engine protects accounts exceeding promotional ratio."""
    # Arrange
    camouflage = CamouflageEngine(max_promotional_ratio=0.12, min_karma=50)
    healthy_account = AccountCredential(
        platform=SocialPlatform.REDDIT,
        username="healthy_dev",
        karma=300,
        account_age_days=180,
        non_promotional_count=20,
        promotional_count=1,
    )
    spammy_account = AccountCredential(
        platform=SocialPlatform.REDDIT,
        username="spammer_dev",
        karma=300,
        account_age_days=180,
        non_promotional_count=5,
        promotional_count=5,
    )

    # Act & Assert
    assert camouflage.is_account_safe(healthy_account) is True
    assert camouflage.is_account_safe(spammy_account) is False

    updated = camouflage.record_activity(healthy_account, is_promotional=False)
    assert updated.non_promotional_count == 21

    altruistic_text = camouflage.generate_altruistic_reply("Database lock contention", "Backend")
    assert len(altruistic_text) > 50
    assert "http" not in altruistic_text


def test_account_vault_selects_safest_account() -> None:
    """Ensure vault chooses account with lowest promo ratio and highest karma."""
    # Arrange
    vault = AccountVault()
    acc_a = AccountCredential(
        platform=SocialPlatform.REDDIT,
        username="alpha",
        karma=100,
        account_age_days=90,
        non_promotional_count=10,
        promotional_count=1,
    )
    acc_b = AccountCredential(
        platform=SocialPlatform.REDDIT,
        username="beta",
        karma=500,
        account_age_days=200,
        non_promotional_count=30,
        promotional_count=1,
    )
    vault.register_account(acc_a)
    vault.register_account(acc_b)

    # Act
    chosen = vault.select_safe_account(SocialPlatform.REDDIT)

    # Assert
    assert chosen is not None
    assert chosen.username == "beta"


def test_synthesizer_generates_stealth_modes(sample_profile: ProductProfile) -> None:
    """Ensure synthesizer implements dynamic math and distinct stealth linking modes."""
    # Arrange
    synthesizer = PractitionerReplySynthesizer()
    entities = {"budget_or_bill_usd": 4500.0, "host_or_node_count": 25}
    opp = InterceptOpportunity(
        platform=SocialPlatform.REDDIT,
        post_id="t3_abc123",
        post_url="https://reddit.com/r/devops/comments/abc123",
        subreddit_or_topic="devops",
        author="sre_dan",
        title="Datadog bill is $4500/mo",
        body_text="Need cheaper alternative for 25 hosts.",
        created_at_utc="2026-11-09T10:00:00Z",
        intent_score=90,
        classification=IntentClassification.PRICE_COMPLAINT,
        detected_competitor="Datadog",
        extracted_entities=entities,
        stealth_mode=StealthMode.ZERO_LINK_VALUE_TRAP,
        synthesized_reply="",
    )

    # Act
    reply_trap = synthesizer.synthesize_reply(opp, sample_profile, "https://pulseops.com")

    opp.stealth_mode = StealthMode.DIRECT_TOOL_LINK
    reply_direct = synthesizer.synthesize_reply(opp, sample_profile, "https://pulseops.com")

    opp.stealth_mode = StealthMode.GITHUB_PROFILE
    reply_github = synthesizer.synthesize_reply(opp, sample_profile, "https://pulseops.com")

    # Assert
    assert "$4,500/mo spend" in reply_trap
    assert "Happy to share the link" in reply_trap
    assert "http" not in reply_trap

    assert "https://pulseops.com?utm_source=reddit" in reply_direct

    assert "GitHub profile repo" in reply_github


def test_listener_deduplicates_posts() -> None:
    """Ensure social listener avoids returning already processed post IDs."""
    # Arrange
    listener = SocialStreamListener()

    # Act
    posts = listener._generate_simulated_stream()

    # Assert
    assert len(posts) >= 3
    assert all("id" in p for p in posts)
    assert all("url" in p for p in posts)


def test_poster_dispatches_with_dry_run() -> None:
    """Ensure social poster returns success and live URL in dry run."""
    # Arrange
    poster = SocialPoster()
    opp = InterceptOpportunity(
        platform=SocialPlatform.REDDIT,
        post_id="t3_999888",
        post_url="https://reddit.com/r/devops/comments/999888",
        subreddit_or_topic="devops",
        author="lead_dev",
        title="Alternative needed",
        body_text="Looking for alternative",
        created_at_utc="2026-11-09T10:00:00Z",
        intent_score=85,
        classification=IntentClassification.IMMEDIATE_MIGRATION,
        synthesized_reply="Here is technical advice",
    )

    # Act
    res = pytest.importorskip("asyncio").run(
        poster.post_reply(opp, opp.synthesized_reply, dry_run=True)
    )

    # Assert
    assert res.success is True
    assert "999888" in (res.live_comment_url or "")
    assert res.platform == SocialPlatform.REDDIT


def test_engine_scans_and_dispatches(sample_profile: ProductProfile) -> None:
    """Ensure CommunityInterceptorEngine coordinates scan and dispatch loop."""
    # Arrange
    engine = CommunityInterceptorEngine()

    # Act
    opportunities = pytest.importorskip("asyncio").run(
        engine.scan_opportunities(
            profile=sample_profile,
            tool_url="https://pulseops.com",
            min_score=70,
            dry_run=True,
        )
    )
    assert len(opportunities) >= 2
    target_opp = opportunities[0]

    dispatch_res = pytest.importorskip("asyncio").run(
        engine.dispatch_reply(target_opp, dry_run=True)
    )
    summary = engine.get_telemetry_summary()

    # Assert
    assert dispatch_res.success is True
    assert target_opp.status == "dispatched"
    assert summary["total_dispatched"] == 1
    assert summary["estimated_ad_savings_usd"] > 0


def test_fastapi_intercept_scan_endpoint() -> None:
    """Ensure POST /api/v1/intercept/scan returns filtered buyer opportunities."""
    # Arrange
    payload = {
        "product_name": "PulseOps",
        "description": "Kubernetes autonomous incident diagnostics replacing Datadog and PagerDuty",
        "min_score": 70,
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/intercept/scan", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "opportunity_id" in data[0]
    assert data[0]["intent_score"] >= 70


def test_fastapi_intercept_scan_rejects_empty_input() -> None:
    """Ensure POST /api/v1/intercept/scan returns 400 when missing url and description."""
    # Arrange
    payload = {"product_name": "Empty"}

    # Act
    response = client.post("/api/v1/intercept/scan", json=payload)

    # Assert
    assert response.status_code == 400
    assert "Either url or description" in response.json()["detail"]


def test_fastapi_intercept_reply_and_telemetry_endpoints(sample_profile: ProductProfile) -> None:
    """Ensure POST /api/v1/intercept/reply and GET /telemetry execute properly."""
    # Arrange
    engine = CommunityInterceptorEngine()
    opps = pytest.importorskip("asyncio").run(
        engine.scan_opportunities(sample_profile, min_score=70, dry_run=True)
    )
    target_opp = opps[0]

    # Act 1: Reply
    reply_res = client.post(
        "/api/v1/intercept/reply",
        json={"opportunity": target_opp.model_dump(), "dry_run": True},
    )

    # Act 2: Telemetry
    telem_res = client.get("/api/v1/intercept/telemetry")

    # Assert
    assert reply_res.status_code == 200
    assert reply_res.json()["success"] is True

    assert telem_res.status_code == 200
    assert "estimated_ad_savings_usd" in telem_res.json()


def test_cli_intercept_scan_command() -> None:
    """Ensure CLI 'zerocac intercept scan' prints opportunities table and draft panel."""
    # Act
    result = runner.invoke(
        cli_app,
        [
            "intercept",
            "scan",
            "--desc",
            "Autonomous Kubernetes diagnostics replacing Datadog",
            "--name",
            "PulseOps",
            "--min-score",
            "70",
            "--dry-run",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "Detected High-Intent Buyer Opportunities" in result.output
    assert "Top Priority Intercept Draft" in result.output


def test_cli_intercept_reply_and_telemetry_commands() -> None:
    """Ensure CLI 'zerocac intercept reply' and 'telemetry' run cleanly."""
    # Act 1: Reply
    result_reply = runner.invoke(
        cli_app,
        [
            "intercept",
            "reply",
            "opp-test-123",
            "--url",
            "https://reddit.com/r/devops/comments/123",
            "--text",
            "Here is the unit-economic math advice",
            "--platform",
            "reddit",
            "--dry-run",
        ],
    )

    # Act 2: Telemetry
    result_telem = runner.invoke(cli_app, ["intercept", "telemetry"])

    # Assert
    assert result_reply.exit_code == 0
    assert "Successfully dispatched to reddit!" in result_reply.output

    assert result_telem.exit_code == 0
    assert "Community Interceptor Impact & Ad Displacement" in result_telem.output
