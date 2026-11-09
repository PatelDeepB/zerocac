"""Commercial purchase intent and customer agony scoring engine."""

import logging
from typing import List, Optional, Tuple

from zerocac.interceptor.models import IntentClassification

logger = logging.getLogger(__name__)

MIGRATION_TRIGGERS = [
    "alternative to",
    "alternatives to",
    "switching from",
    "moving away from",
    "migrating from",
    "replace",
    "recommend me",
    "what do you use instead",
    "anyone switched",
    "leaving",
]

PRICE_TRIGGERS = [
    "too expensive",
    "price hike",
    "pricing increased",
    "outrageous bill",
    "insane cost",
    "seat tax",
    "cost is killing",
    "hidden fees",
    "over budget",
]

CRISIS_TRIGGERS = [
    "outage",
    "down again",
    "status page",
    "service disruption",
    "license change",
    "data breach",
    "breaking change",
]

FRUSTRATION_TRIGGERS = [
    "broken",
    "clunky",
    "impossible to configure",
    "memory leak",
    "flaky",
    "horrible support",
    "slow as hell",
]


class IntentScorer:
    """Scores buyer intent and agony from 0 to 100 with classification."""

    def __init__(self, min_threshold: int = 75) -> None:
        """Initialize scorer with qualification cutoff."""
        self.min_threshold = min_threshold

    def score_post(
        self,
        title: str,
        body: str,
        competitor_names: List[str],
    ) -> Tuple[int, IntentClassification, Optional[str]]:
        """Compute composite score (0-100), classification, and detected competitor."""
        full_text = f"{title.lower()} {body.lower()}"
        detected_comp = self._detect_competitor(full_text, competitor_names)

        score = 20
        classification = IntentClassification.IRRELEVANT

        # Evaluate triggers
        if any(t in full_text for t in CRISIS_TRIGGERS) and detected_comp:
            score += 65
            classification = IntentClassification.COMPETITOR_CRISIS
        elif any(t in full_text for t in MIGRATION_TRIGGERS):
            score += 55
            classification = IntentClassification.IMMEDIATE_MIGRATION
        elif any(t in full_text for t in PRICE_TRIGGERS):
            score += 45
            classification = IntentClassification.PRICE_COMPLAINT
        elif "recommend" in full_text or "best tool" in full_text:
            score += 35
            classification = IntentClassification.TOOL_RECOMMENDATION
        elif any(t in full_text for t in FRUSTRATION_TRIGGERS):
            score += 30
            classification = IntentClassification.TECHNICAL_FRUSTRATION

        # Competitor presence bonus
        if detected_comp:
            score += 20

        # Title presence bonus
        if any(t in title.lower() for t in MIGRATION_TRIGGERS + PRICE_TRIGGERS):
            score += 10

        bounded_score = min(max(score, 0), 100)
        return bounded_score, classification, detected_comp

    def _detect_competitor(self, text: str, competitor_names: List[str]) -> Optional[str]:
        """Identify which competitor is mentioned in the text."""
        for comp in competitor_names:
            if comp.lower() in text:
                return comp
        return None
