"""Unit and integration tests for the Programmatic SEO (pSEO) Matrix Engine (Option B)."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.cli import app as cli_app
from zerocac.pseo.compiler import PSEOPageCompiler
from zerocac.pseo.deployer import PSEOBatchDeployer
from zerocac.pseo.engine import PSEOMatrixEngine
from zerocac.pseo.generator import PSEOMatrixGenerator
from zerocac.pseo.mesh import InternalLinkingMesh
from zerocac.pseo.models import (
    PSEOAxis,
    PSEODeploymentReport,
    PSEOMatrixPackage,
    PSEOPage,
)
from zerocac.pseo.validator import SearchDemandValidator
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


@pytest.fixture
def sample_tool_html() -> str:
    """Fixture providing mock microtool HTML."""
    return "<div id='app'>PulseOps Incident Cost Calculator</div>"


def test_validator_computes_demand_signals() -> None:
    """Ensure search demand validator scores search volume and intent heuristics."""
    # Arrange
    validator = SearchDemandValidator()

    # Act
    signal = pytest.importorskip("asyncio").run(
        validator.validate_query("datadog alternatives", dry_run=True)
    )

    # Assert
    assert signal.verified is True
    assert signal.search_frequency_score >= 50
    assert signal.intent_type == "alternative_switching"


def test_generator_creates_multi_axis_candidates(sample_profile: ProductProfile) -> None:
    """Ensure generator spans all 3 programmatic axes with valid slugs."""
    # Arrange
    generator = PSEOMatrixGenerator()

    # Act
    candidates = pytest.importorskip("asyncio").run(
        generator.generate_candidates(sample_profile, target_count=9, dry_run=True)
    )

    # Assert
    assert len(candidates) >= 3
    axes_found = {c.axis for c in candidates}
    assert PSEOAxis.COMPETITOR_ALTERNATIVE in axes_found
    assert PSEOAxis.REGIONAL_ECOSYSTEM in axes_found
    assert PSEOAxis.CALCULATOR_SLICE in axes_found
    for c in candidates:
        assert c.slug
        assert "/" not in c.slug
        assert " " not in c.slug


def test_compiler_embeds_trojan_horse_and_calculator(
    sample_profile: ProductProfile,
    sample_tool_html: str,
) -> None:
    """Ensure compiler embeds Answer-First summary, comparison matrix, and reactive tool."""
    # Arrange
    generator = PSEOMatrixGenerator()
    compiler = PSEOPageCompiler()
    candidates = pytest.importorskip("asyncio").run(
        generator.generate_candidates(sample_profile, target_count=3, dry_run=True)
    )
    candidate = candidates[0]

    # Act
    compiled = compiler.compile_page(
        candidate=candidate,
        profile=sample_profile,
        tool_html=sample_tool_html,
        parent_hub_url="/vs/",
    )

    # Assert
    assert '<div class="geo-answer">' in compiled.html_content
    assert '<div class="table-wrap">' in compiled.html_content
    assert sample_tool_html in compiled.html_content
    assert 'id="zerocac-lead-gate"' in compiled.html_content
    assert "application/ld+json" in compiled.html_content
    assert compiled.h1_title
    assert compiled.answer_first_summary


def test_internal_linking_mesh_guarantees_zero_orphans(
    sample_profile: ProductProfile,
    sample_tool_html: str,
) -> None:
    """Ensure mesh links each page to parent hub and sibling pages."""
    # Arrange
    generator = PSEOMatrixGenerator()
    compiler = PSEOPageCompiler()
    mesh = InternalLinkingMesh()

    candidates = pytest.importorskip("asyncio").run(
        generator.generate_candidates(sample_profile, target_count=6, dry_run=True)
    )
    compiled = [
        compiler.compile_page(c, sample_profile, sample_tool_html, parent_hub_url="/vs/")
        for c in candidates
    ]

    # Act
    meshed = mesh.build_mesh(compiled, base_url="https://pulseops.com")
    hub_html = mesh.generate_hub_page(meshed, sample_profile.product_name)
    sitemap = mesh.generate_sitemap_xml(meshed, base_url="https://pulseops.com")
    proxy_config = mesh.generate_reverse_proxy_config("pulseops-pseo")

    # Assert
    for page in meshed:
        assert len(page.sibling_links) >= 1
        assert '<nav class="internal-mesh"' in page.html_content
        assert "/vs/" in page.html_content

    assert "Solutions & Alternatives Directory" in hub_html
    assert "<urlset xmlns=" in sitemap
    assert "https://pulseops.com/vs/" in sitemap
    assert "url.pathname.startsWith('/vs/')" in proxy_config["cloudflare_worker_js"]


def test_batch_deployer_dispatches_artifacts(
    sample_profile: ProductProfile,
    sample_tool_html: str,
) -> None:
    """Ensure deployer bundles pages and triggers IndexNow."""
    # Arrange
    engine = PSEOMatrixEngine()
    deployer = PSEOBatchDeployer()

    package = pytest.importorskip("asyncio").run(
        engine.generate_matrix(
            profile=sample_profile,
            tool_html=sample_tool_html,
            target_count=3,
            dry_run=True,
        )
    )

    # Act
    report = pytest.importorskip("asyncio").run(
        deployer.deploy_matrix(package, dry_run=True)
    )

    # Assert
    assert report.total_pages_deployed == len(package.pages)
    assert report.indexnow_submitted is True
    assert len(report.indexed_urls) == len(package.pages) + 1
    assert report.reverse_proxy_mounted is True


def test_pseo_engine_end_to_end(
    sample_profile: ProductProfile,
    sample_tool_html: str,
) -> None:
    """Ensure PSEOMatrixEngine coordinates entire pipeline into valid package."""
    # Arrange
    engine = PSEOMatrixEngine()

    # Act
    package = pytest.importorskip("asyncio").run(
        engine.generate_matrix(
            profile=sample_profile,
            tool_html=sample_tool_html,
            target_count=6,
            dry_run=True,
        )
    )

    # Assert
    assert package.product_name == "PulseOps"
    assert len(package.pages) >= 3
    assert package.hub_page_html
    assert package.sitemap_xml
    assert package.reverse_proxy_config


def test_fastapi_pseo_generate_endpoint() -> None:
    """Ensure POST /api/v1/pseo/generate returns full programmatic matrix."""
    # Arrange
    payload = {
        "product_name": "PulseOps",
        "description": "Kubernetes autonomous root cause diagnostic engine for DevOps teams",
        "count": 6,
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/pseo/generate", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "PulseOps"
    assert len(data["pages"]) >= 3
    assert "hub_page_html" in data
    assert "sitemap_xml" in data


def test_fastapi_pseo_generate_rejects_empty_input() -> None:
    """Ensure POST /api/v1/pseo/generate returns 400 when neither url nor desc given."""
    # Arrange
    payload = {"product_name": "Empty"}

    # Act
    response = client.post("/api/v1/pseo/generate", json=payload)

    # Assert
    assert response.status_code == 400
    assert "Either url or description" in response.json()["detail"]


def test_fastapi_pseo_deploy_endpoint(
    sample_profile: ProductProfile,
    sample_tool_html: str,
) -> None:
    """Ensure POST /api/v1/pseo/deploy accepts package and returns report."""
    # Arrange
    engine = PSEOMatrixEngine()
    package = pytest.importorskip("asyncio").run(
        engine.generate_matrix(
            profile=sample_profile,
            tool_html=sample_tool_html,
            target_count=3,
            dry_run=True,
        )
    )

    # Act
    response = client.post(
        "/api/v1/pseo/deploy",
        json={"package": package.model_dump(), "dry_run": True},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_pages_deployed"] == len(package.pages)
    assert data["indexnow_submitted"] is True


def test_cli_pseo_generate_command(tmp_path: Path) -> None:
    """Ensure CLI 'zerocac pseo generate' compiles matrix files to disk."""
    # Arrange
    out_dir = tmp_path / "pseo_export"

    # Act
    result = runner.invoke(
        cli_app,
        [
            "pseo",
            "generate",
            "--desc",
            "Kubernetes autonomous incident diagnostics for DevOps engineers",
            "--name",
            "PulseOps",
            "--count",
            "6",
            "--out",
            str(out_dir),
            "--dry-run",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert (out_dir / "pseo_package.json").exists()
    assert (out_dir / "index.html").exists()
    assert (out_dir / "sitemap-pseo.xml").exists()
    assert (out_dir / "vs").exists()


def test_cli_pseo_deploy_command(
    tmp_path: Path,
    sample_profile: ProductProfile,
    sample_tool_html: str,
) -> None:
    """Ensure CLI 'zerocac pseo deploy' reads package file and executes edge deploy."""
    # Arrange
    engine = PSEOMatrixEngine()
    package = pytest.importorskip("asyncio").run(
        engine.generate_matrix(
            profile=sample_profile,
            tool_html=sample_tool_html,
            target_count=3,
            dry_run=True,
        )
    )
    pkg_file = tmp_path / "pseo_package.json"
    pkg_file.write_text(package.model_dump_json(indent=2), encoding="utf-8")

    # Act
    result = runner.invoke(
        cli_app,
        ["pseo", "deploy", str(pkg_file), "--dry-run"],
    )

    # Assert
    assert result.exit_code == 0
    assert "Programmatic SEO Deployment Report" in result.output
    assert "SUBMITTED" in result.output
