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
    assert data["version"] == "0.1.0"
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


def test_generate_endpoint_produces_full_campaign() -> None:
    """Ensure POST /api/v1/generate compiles outputs across all 4 organic engines."""
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
