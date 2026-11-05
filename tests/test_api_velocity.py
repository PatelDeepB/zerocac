"""Integration tests for all 8 unified organic and high-velocity engines."""

import pytest
from fastapi.testclient import TestClient

from zerocac.web.app import app

client = TestClient(app)


def test_generate_all_eight_engines() -> None:
    """Ensure POST /api/v1/generate compiles outputs across all 8 engines simultaneously."""
    profile_payload = {
        "product_name": "ZeroCAC",
        "category": "Developer Tools / Growth Automation",
        "one_liner": "Scale to $0 CAC without paying for Google or Meta ad tokens.",
        "core_problem": "Paid ads are expensive, burn cash, and create zero permanent equity.",
        "solution_mechanism": "Autonomous organic distribution via AEO, micro-tools, and radar.",
        "unique_value_proposition": "Scale to $0 CAC without paying for Google or Meta ad tokens.",
        "key_features": ["Live Intent Radar", "Autonomous Micro-Tools", "Princeton GEO", "Virality Loops"],
        "personas": [
            {
                "persona_name": "Bootstrapped SaaS Founder",
                "core_pain_point": "Priced out of Google Ads with zero media budget.",
                "trigger_event": "Ad budget exhausted after poor ROAS.",
                "primary_objection": "Will organic marketing take too long to produce results?",
                "watering_holes": ["r/SaaS", "r/startups", "Hacker News"],
            }
        ],
        "competitor_gaps": [
            {
                "competitor_name": "AdRoll",
                "their_weakness": "Expensive monthly subscriptions and high ad fatigue.",
                "our_advantage": "100% organic with permanent compounding assets.",
            }
        ],
        "search_keywords": ["zerocac", "organic marketing agent", "zero cac"],
        "high_intent_queries": ["alternative to paid ads", "how to scale without ads"],
    }

    generate_payload = {
        "profile": profile_payload,
        "engines": [
            "sniper",
            "aeo",
            "narrative",
            "directory",
            "radar",
            "microtool",
            "geo",
            "virality",
        ],
    }

    # Act
    response = client.post("/api/v1/generate", json=generate_payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["product_name"] == "ZeroCAC"

    # Engine 1: Sniper
    assert data["sniper"] is not None
    assert len(data["sniper"]["opportunities"]) == 3

    # Engine 2: AEO
    assert data["aeo"] is not None
    assert len(data["aeo"]["comparison_pages"]) == 1

    # Engine 3: Narrative
    assert data["narrative"] is not None
    assert len(data["narrative"]["x_thread"]) == 5

    # Engine 4: Directory
    assert data["directory"] is not None
    assert data["directory"]["total_directories"] >= 10

    # Engine 5: Radar
    assert data["radar"] is not None
    assert data["radar"]["signals_found"] >= 3

    # Engine 6: Micro-Tool
    assert data["microtool"] is not None
    assert "<!DOCTYPE html>" in data["microtool"]["html_content"]

    # Engine 7: Princeton GEO
    assert data["geo"] is not None
    assert len(data["geo"]["assets"]) >= 1

    # Engine 8: Virality Loop
    assert data["virality"] is not None
    assert "<svg" in data["virality"]["svg_badge"]
