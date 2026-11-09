"""Synthesizer for Vector 2: Hacker News Show HN Launch."""

import logging
from zerocac.analyzer.models import ProductProfile
from zerocac.launch.models import ShowHNPackage

logger = logging.getLogger(__name__)


class ShowHNEngine:
    """Synthesizes strict, rule-compliant Hacker News Show HN submissions."""

    def synthesize_submission(
        self,
        profile: ProductProfile,
        live_url: str,
        tool_name: str,
    ) -> ShowHNPackage:
        """Construct Show HN title, URL, and technical maker backstory."""
        clean_title = self._format_hn_title(tool_name, profile.category)
        maker_comment = self._format_maker_comment(profile, tool_name, live_url)

        return ShowHNPackage(
            title=clean_title,
            target_url=live_url,
            maker_comment=maker_comment,
            suggested_utc_hour=13,  # 13:00-14:00 UTC captures peak US morning + EU afternoon
        )

    def _format_hn_title(self, tool_name: str, category: str) -> str:
        """Format strictly compliant title without marketing buzzwords under 80 chars."""
        base = f"Show HN: {tool_name} - {category} calculator"
        if len(base) <= 80:
            return base
        return f"Show HN: {tool_name}"[:80]

    def _format_maker_comment(self, profile: ProductProfile, tool_name: str, live_url: str) -> str:
        """Draft in-depth technical backstory addressing engineering decisions."""
        return (
            f"Hey HN,\n\n"
            f"I built {tool_name} ({live_url}) after getting frustrated with: {profile.core_problem}\n\n"
            f"Most solutions in this space either gate their calculations behind sales demos or force users "
            f"to install heavy dependencies. We wanted something that solves this in under 30 seconds for free.\n\n"
            f"### Technical Implementation:\n"
            f"- Built as a standalone single-file web application with zero external framework dependencies.\n"
            f"- All reactive calculations execute client-side in vanilla JavaScript with no server roundtrips.\n"
            f"- State is maintained locally without tracking cookies or user fingerprinting.\n\n"
            f"The tool is live at {live_url}. Would love your feedback on our calculation assumptions "
            f"and any edge cases we should account for in our formula."
        )
