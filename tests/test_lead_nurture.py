"""Unit tests for Phase 2 Inbound Lead Capture and Behavioral Nurture Engine."""

from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.analyzer.models import ProductProfile
from zerocac.cli import app as cli_app
from zerocac.engines.microtool import MicroToolEngine
from zerocac.leads.dispatcher import ResendDispatcher
from zerocac.leads.injector import LeadCaptureInjector
from zerocac.leads.models import Lead, LeadStatus
from zerocac.leads.nurture import NurtureEngine
from zerocac.leads.repository import LeadRepository
from zerocac.web.app import app as fastapi_app

runner = CliRunner()
client = TestClient(fastapi_app)


@pytest.fixture
def temp_repo(tmp_path: Path) -> LeadRepository:
    """Fixture providing isolated temporary SQLite lead repository."""
    db_file = tmp_path / "test_leads.db"
    return LeadRepository(db_path=str(db_file))


@pytest.fixture
def sample_lead() -> Lead:
    """Fixture providing a standard captured lead."""
    return Lead(
        email="founder@socius.io",
        full_name="Aarav Sharma",
        company="Socius Network",
        project_slug="socius-calculator",
        tool_inputs={"expected_deals": 5, "city": "Mumbai"},
        intent_score=90,
    )


@pytest.fixture
def sample_profile() -> ProductProfile:
    """Fixture providing a minimal product profile."""
    return ProductProfile(
        product_name="Socius",
        category="Private Founder Network",
        one_liner="Curated founder community in India and Singapore",
        core_problem="Noisy networking groups without high-value dealflow",
        solution_mechanism="Vetted private membership",
        unique_value_proposition="Direct peer-to-peer dealflow without ad noise",
        key_features=["Vetted network", "Private syndicate", "City cohorts"],
    )


@pytest.mark.asyncio
async def test_lead_repository_save_and_retrieve(temp_repo: LeadRepository, sample_lead: Lead) -> None:
    """Ensure lead persists and can be queried by ID."""
    # Act
    saved = await temp_repo.save_lead(sample_lead)
    retrieved = await temp_repo.get_lead(saved.lead_id)

    # Assert
    assert retrieved is not None
    assert retrieved.email == "founder@socius.io"
    assert retrieved.full_name == "Aarav Sharma"
    assert retrieved.project_slug == "socius-calculator"
    assert retrieved.tool_inputs.get("city") == "Mumbai"
    assert retrieved.status == LeadStatus.CAPTURED


@pytest.mark.asyncio
async def test_lead_repository_list_and_filter(temp_repo: LeadRepository, sample_lead: Lead) -> None:
    """Ensure listing supports filtering by project slug."""
    # Arrange
    await temp_repo.save_lead(sample_lead)
    second_lead = Lead(
        email="alex@other.io",
        project_slug="pulseops-calculator",
    )
    await temp_repo.save_lead(second_lead)

    # Act
    all_leads = await temp_repo.list_leads()
    socius_leads = await temp_repo.list_leads(project_slug="socius-calculator")

    # Assert
    assert len(all_leads) == 2
    assert len(socius_leads) == 1
    assert socius_leads[0].email == "founder@socius.io"


@pytest.mark.asyncio
async def test_lead_repository_update_status(temp_repo: LeadRepository, sample_lead: Lead) -> None:
    """Ensure lead lifecycle status transitions correctly."""
    # Arrange
    await temp_repo.save_lead(sample_lead)

    # Act
    updated = await temp_repo.update_status(sample_lead.lead_id, LeadStatus.NURTURED)
    retrieved = await temp_repo.get_lead(sample_lead.lead_id)

    # Assert
    assert updated is True
    assert retrieved is not None
    assert retrieved.status == LeadStatus.NURTURED


def test_lead_capture_injector_adds_form_to_html() -> None:
    """Ensure injector inserts lead form and does not duplicate if already present."""
    # Arrange
    injector = LeadCaptureInjector()
    raw_html = "<html><body><h1>Calculator</h1></body></html>"

    # Act
    injected = injector.inject_lead_form(raw_html)
    re_injected = injector.inject_lead_form(injected)

    # Assert
    assert "zerocac-lead-gate" in injected
    assert "submitZeroCACLead" in injected
    assert injected.count("zerocac-lead-gate") == 1
    assert re_injected.count("zerocac-lead-gate") == 1


def test_nurture_engine_synthesizes_personalized_stages(
    sample_lead: Lead, sample_profile: ProductProfile
) -> None:
    """Ensure 3-stage nurture sequence incorporates user inputs and valid HTML."""
    # Arrange
    engine = NurtureEngine()

    # Act
    sequence = engine.build_default_sequence(sample_lead, sample_profile)

    # Assert
    assert len(sequence.stages) == 3
    assert sequence.product_name == "Socius"
    assert "Aarav Sharma" in sequence.stages[0].body_markdown
    assert "Mumbai" in sequence.stages[0].body_markdown
    assert sequence.stages[0].delay_hours == 0
    assert sequence.stages[1].delay_hours == 48
    assert sequence.stages[2].delay_hours == 96
    assert "Unsubscribe" in sequence.stages[0].body_html


@pytest.mark.asyncio
async def test_resend_dispatcher_dry_run() -> None:
    """Ensure dispatcher dry run returns simulated success without network calls."""
    # Arrange
    dispatcher = ResendDispatcher()
    stage = NurtureEngine().build_default_sequence(
        Lead(email="test@user.com", project_slug="app"),
        ProductProfile(
            product_name="PulseOps",
            category="DevOps",
            one_liner="Incident triage",
            core_problem="Manual triage",
            solution_mechanism="Root cause AI",
            unique_value_proposition="10x faster MTTR",
            key_features=["Auto triage"],
        ),
    ).stages[0]

    # Act
    res = await dispatcher.dispatch_stage(stage, "test@user.com", dry_run=True)

    # Assert
    assert res["success"] is True
    assert res["dry_run"] is True
    assert "sim-re-1" in res["id"]


def test_api_capture_lead_endpoint(tmp_path: Path) -> None:
    """Ensure POST /api/v1/leads/capture records lead and dispatches stage 1."""
    # Arrange
    payload = {
        "email": "sarah@growth.co",
        "full_name": "Sarah Connor",
        "company": "Cyberdyne",
        "project_slug": "cac-calculator",
        "tool_inputs": {"monthly_spend": 10000},
        "dry_run": True,
    }

    # Act
    with patch("zerocac.web.routers.leads.LeadRepository", return_value=LeadRepository(db_path=str(tmp_path / "leads.db"))):
        response = client.post("/api/v1/leads/capture", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["lead_id"].startswith("lead-")


def test_microtool_engine_automatically_includes_lead_form(sample_profile: ProductProfile) -> None:
    """Ensure microtools generated by MicroToolEngine embed the lead capture gate."""
    # Arrange
    engine = MicroToolEngine()

    # Act
    pkg = engine._generate_dry_run_tool(sample_profile)

    # Assert
    assert "zerocac-lead-gate" in pkg.html_content
    assert "submitZeroCACLead" in pkg.html_content
