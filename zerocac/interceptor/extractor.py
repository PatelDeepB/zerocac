"""Extracts numeric operational metrics from posts for dynamic calculation injection."""

import re
from typing import Any, Dict


class NumericEntityExtractor:
    """Extracts budget, infrastructure scale, and team size numbers from user posts."""

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Parse text and extract quantitative entities for customized math injection."""
        entities: Dict[str, Any] = {}

        dollar_val = self._extract_dollar_amount(text)
        if dollar_val is not None:
            entities["budget_or_bill_usd"] = dollar_val

        host_val = self._extract_host_count(text)
        if host_val is not None:
            entities["host_or_node_count"] = host_val

        team_val = self._extract_team_size(text)
        if team_val is not None:
            entities["team_size"] = team_val

        vol_val = self._extract_volume_gb(text)
        if vol_val is not None:
            entities["daily_volume_gb"] = vol_val

        return entities

    def _extract_dollar_amount(self, text: str) -> float | None:
        """Extract explicit dollar spend or budget mentions."""
        # Match patterns like $4,500, $5k, $300/mo
        match = re.search(r"\$\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(k|m|thousand|million)?", text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            multiplier = 1.0
            unit = (match.group(2) or "").lower()
            if unit in ("k", "thousand"):
                multiplier = 1000.0
            elif unit in ("m", "million"):
                multiplier = 1000000.0
            try:
                return float(raw) * multiplier
            except ValueError:
                return None
        return None

    def _extract_host_count(self, text: str) -> int | None:
        """Extract node, host, pod, or instance counts."""
        match = re.search(r"\b([0-9]+)\s*(?:hosts?|nodes?|pods?|instances?|servers?)\b", text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    def _extract_team_size(self, text: str) -> int | None:
        """Extract team, engineer, or developer headcount."""
        match = re.search(r"\b([0-9]+)\s*(?:engineers?|devs?|developers?|people|team members?|users?)\b", text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    def _extract_volume_gb(self, text: str) -> float | None:
        """Extract data volume in gigabytes."""
        match = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*(gb|tb|gigabytes?|terabytes?)\b", text, re.IGNORECASE)
        if match:
            raw = match.group(1)
            unit = match.group(2).lower()
            multiplier = 1000.0 if "t" in unit else 1.0
            try:
                return float(raw) * multiplier
            except ValueError:
                return None
        return None
