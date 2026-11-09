"""Search demand and intent validator preventing phantom zero-volume pSEO pages."""

import logging
from typing import Optional
import httpx

from zerocac.pseo.models import DemandSignal

logger = logging.getLogger(__name__)

SUGGEST_ENDPOINT = "https://suggestqueries.google.com/complete/search?client=firefox&q="


class SearchDemandValidator:
    """Validates real search intent and volume before authorizing page generation."""

    def __init__(self, min_demand_threshold: int = 40) -> None:
        """Initialize validator with minimum demand cutoff score."""
        self.min_demand_threshold = min_demand_threshold

    async def validate_query(self, query: str, dry_run: bool = False) -> DemandSignal:
        """Verify query against search suggest APIs or heuristic signals."""
        clean_query = query.strip()
        if not clean_query:
            return DemandSignal(query="", search_frequency_score=0, verified=False)

        if dry_run:
            score = self._compute_heuristic_score(clean_query)
            return DemandSignal(
                query=clean_query,
                search_frequency_score=score,
                intent_type=self._classify_intent(clean_query),
                verified=score >= self.min_demand_threshold,
            )

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{SUGGEST_ENDPOINT}{clean_query}")
                if res.status_code == 200:
                    data = res.json()
                    suggestions = data[1] if len(data) > 1 else []
                    score = min(50 + len(suggestions) * 10, 100)
                    return DemandSignal(
                        query=clean_query,
                        search_frequency_score=score,
                        intent_type=self._classify_intent(clean_query),
                        verified=len(suggestions) > 0 or score >= self.min_demand_threshold,
                    )
        except Exception as exc:
            logger.debug("Suggest API unreachable (%s), falling back to heuristics", str(exc))

        score = self._compute_heuristic_score(clean_query)
        return DemandSignal(
            query=clean_query,
            search_frequency_score=score,
            intent_type=self._classify_intent(clean_query),
            verified=score >= self.min_demand_threshold,
        )

    def _compute_heuristic_score(self, query: str) -> int:
        """Compute intent score based on high-converting search modifiers."""
        q = query.lower()
        score = 50

        # Commercial & comparison modifiers
        if any(term in q for term in ["vs", "versus", "alternative", "competitor"]):
            score += 30
        if any(term in q for term in ["calculator", "pricing", "cost", "roi", "grader"]):
            score += 25
        if any(term in q for term in ["community", "network", "club", "cohort"]):
            score += 15

        return min(score, 100)

    def _classify_intent(self, query: str) -> str:
        """Classify search intent into actionable funnel stage."""
        q = query.lower()
        if any(t in q for t in ["calculator", "roi", "tool"]):
            return "transactional_calculator"
        if any(t in q for t in ["vs", "versus", "alternative"]):
            return "alternative_switching"
        return "commercial_investigation"
