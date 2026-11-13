"""Unit and integration tests for FastAPI REST endpoints."""

import pytest
from fastapi.testclient import TestClient

from zerocac.web.app import app

client = TestClient(app)


def test_health_check_endpoint_returns_healthy() -> None:
    """Ensure /health endpoint returns HTTP 200 and accurate system metadata."""
    # Arrange & Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.3.0"
    assert "default_provider" in data


def test_serve_dashboard_returns_html() -> None:
    """Ensure GET / serves the compiled static dashboard."""
    # Arrange & Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert "ZeroCAC" in response.text
    assert "<!DOCTYPE html>" in response.text


def test_analyze_endpoint_requires_url_or_description() -> None:
    """Ensure POST /api/v1/analyze rejects requests with neither URL nor description."""
    # Arrange
    payload = {"product_name": "Incomplete"}

    # Act
    response = client.post("/api/v1/analyze", json=payload)

    # Assert
    assert response.status_code == 400
    assert "Either 'url' or 'description'" in response.json()["detail"]


def test_analyze_endpoint_succeeds_with_description() -> None:
    """Ensure POST /api/v1/analyze succeeds when provided with a direct product description."""
    # Arrange
    payload = {
        "product_name": "CloudFast",
        "description": "Ultra fast serverless database that connects in 1 millisecond.",
    }

    # Act
    response = client.post("/api/v1/analyze", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "CloudFast"
    assert len(data["personas"]) >= 1
    assert len(data["competitor_gaps"]) >= 1


def test_radar_endpoint_returns_live_signals() -> None:
    """Ensure POST /api/v1/radar returns scored opportunities in dry-run mode."""
    # Arrange
    payload = {
        "product_name": "ZeroCAC",
        "description": "Autonomous AI agent that scales products to $0 CAC without paid ads.",
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/radar", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "ZeroCAC"
    assert data["signals_found"] >= 3
    assert len(data["high_intent_signals"]) >= 3
    assert "Action Protocol" in data["action_plan"]


def test_microtool_endpoint_returns_html_package() -> None:
    """Ensure POST /api/v1/microtool produces a complete single-file web application."""
    # Arrange
    payload = {
        "product_name": "ZeroCAC",
        "description": "Autonomous AI agent that scales products to $0 CAC without paid ads.",
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/microtool", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Calculator" in data["concept"]["tool_name"]
    assert "<!DOCTYPE html>" in data["html_content"]
    assert "<script>" in data["html_content"]
    assert "Quick Deployment Guide" in data["deployment_instructions"]


def test_geo_endpoint_returns_citation_package() -> None:
    """Ensure POST /api/v1/geo produces Princeton GEO citation package."""
    # Arrange
    payload = {
        "product_name": "ZeroCAC",
        "description": "Autonomous AI agent that scales products to $0 CAC without paid ads.",
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/geo", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "ZeroCAC"
    assert "PerplexityBot" in data["robots_txt_rules"]
    assert len(data["assets"]) >= 1
    assert "ZeroCAC" in data["assets"][0]["answer_first_definition"]


def test_virality_endpoint_returns_loop_assets() -> None:
    """Ensure POST /api/v1/virality produces SVG badges and loop mechanics."""
    # Arrange
    payload = {
        "product_name": "ZeroCAC",
        "description": "Autonomous AI agent that scales products to $0 CAC without paid ads.",
        "dry_run": True,
    }

    # Act
    response = client.post("/api/v1/virality", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "ZeroCAC"
    assert "<svg" in data["svg_badge"]
    assert len(data["viral_loop_mechanics"]) == 4
    assert "[![Powered by ZeroCAC]" in data["markdown_badge"]


def test_generate_endpoint_produces_full_campaign() -> None:
    """Ensure POST /api/v1/generate compiles outputs across all requested organic engines."""
    # Arrange
    profile_payload = {
        "product_name": "TestTool",
        "category": "Developer Tools",
        "one_liner": "The fastest terminal assistant.",
        "core_problem": "Developers forget complex CLI flags.",
        "solution_mechanism": "Natural language to bash translation.",
        "unique_value_proposition": "Runs 100% offline with zero latency.",
        "key_features": ["Offline reasoning", "Terminal integration"],
        "personas": [
            {
                "persona_name": "Backend Dev",
                "core_pain_point": "Kubectl syntax is too verbose",
                "trigger_event": "Broke cluster with wrong flag",
                "primary_objection": "Is it safe?",
                "watering_holes": ["r/golang"],
            }
        ],
        "competitor_gaps": [
            {
                "competitor_name": "GitHub Copilot CLI",
                "their_weakness": "Requires cloud connection and paid license",
                "our_advantage": "Completely offline and free",
            }
        ],
        "search_keywords": ["copilot cli alternative"],
        "high_intent_queries": ["What is an offline alternative to GitHub Copilot for bash?"],
    }

    generate_payload = {
        "profile": profile_payload,
        "engines": ["sniper", "aeo", "narrative", "directory"],
    }

    # Act
    response = client.post("/api/v1/generate", json=generate_payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["product_name"] == "TestTool"
    assert data["sniper"] is not None
    assert len(data["sniper"]["opportunities"]) == 3
    assert data["aeo"] is not None
    assert len(data["aeo"]["comparison_pages"]) == 1
    assert data["narrative"] is not None
    assert len(data["narrative"]["x_thread"]) == 5
    assert data["directory"] is not None
    assert data["directory"]["total_directories"] >= 10


def test_serve_dashboard_contains_mission_control_elements() -> None:
    """Ensure GET / serves all mission control control rooms and vector cards."""
    # Arrange & Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    html = response.text
    assert "ZeroCAC Mission Control" in html
    assert "Day-1 Launch Cockpit" in html
    assert "pSEO Matrix Studio" in html
    assert "Community Interceptor" in html
    assert "Inbound Leads & Paid Ads Replacement Telemetry" in html
    assert "mission-stats-grid" in html
    assert "launch-vectors-container" in html
    assert "pseo-tbody" in html
    assert "intercept-feed-container" in html


def test_static_assets_serve_correctly() -> None:
    """Ensure static CSS and JS bundles serve with HTTP 200."""
    # Act
    css_res = client.get("/static/style.css")
    js_res = client.get("/static/app.js")

    # Assert
    assert css_res.status_code == 200
    assert "stats-grid" in css_res.text
    assert js_res.status_code == 200
    assert "setupLaunchCockpit" in js_res.text

