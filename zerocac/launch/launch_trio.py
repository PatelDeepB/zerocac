"""Synthesizer for Vector 3: The Launch Trio (Product Hunt + Peerlist + MicroLaunch)."""

import logging
from typing import List
from zerocac.analyzer.models import ProductProfile
from zerocac.launch.models import LaunchTrioItem

logger = logging.getLogger(__name__)


class LaunchTrioEngine:
    """Synthesizes structured launch assets for Product Hunt, Peerlist, and MicroLaunch."""

    def synthesize_trio(
        self,
        profile: ProductProfile,
        live_url: str,
        tool_name: str,
    ) -> List[LaunchTrioItem]:
        """Compile complete launch payloads across all 3 aggregator networks."""
        return [
            self._build_product_hunt_item(profile, live_url, tool_name),
            self._build_peerlist_item(profile, live_url, tool_name),
            self._build_microlaunch_item(profile, live_url, tool_name),
        ]

    def _build_product_hunt_item(self, profile: ProductProfile, live_url: str, tool_name: str) -> LaunchTrioItem:
        """Construct Product Hunt payload adhering to character limits."""
        raw_tagline = f"Free {tool_name} for {profile.category}"
        tagline = raw_tagline[:60] if len(raw_tagline) > 60 else raw_tagline

        desc = f"Instant interactive {tool_name}. Diagnose {profile.core_problem[:100]} in 30 seconds for free."[:260]

        maker_comment = (
            f"Hey Hunters!\n\n"
            f"We built {tool_name} ({live_url}) because paying thousands for enterprise tools just to calculate "
            f"basic unit economics made no sense.\n\n"
            f"This utility gives you instant numbers without sign-ups or demo calls. "
            f"Let us know what you think in the comments below!"
        )

        return LaunchTrioItem(
            platform_name="Product Hunt",
            tagline=tagline,
            description=desc,
            maker_first_comment=maker_comment,
            topic_tags=["developer-tools", "productivity", "growth", "saas"],
        )

    def _build_peerlist_item(self, profile: ProductProfile, live_url: str, tool_name: str) -> LaunchTrioItem:
        """Construct Peerlist Project Showcase payload."""
        return LaunchTrioItem(
            platform_name="Peerlist",
            tagline=f"Showcasing {tool_name}: Zero-dependency {profile.category} app",
            description=f"A fast, client-side utility built for modern practitioners to solve {profile.core_problem[:120]}.",
            maker_first_comment=f"Built with vanilla JS and deployed to the edge at {live_url}. Feedback appreciated!",
            topic_tags=["Frontend", "Open Source", "JavaScript", "Tools"],
        )

    def _build_microlaunch_item(self, profile: ProductProfile, live_url: str, tool_name: str) -> LaunchTrioItem:
        """Construct MicroLaunch directory payload."""
        return LaunchTrioItem(
            platform_name="MicroLaunch",
            tagline=f"{tool_name} - Free {profile.category} diagnostic tool",
            description=profile.one_liner[:260],
            maker_first_comment=f"Available free on the edge: {live_url}",
            topic_tags=["Bootstrap", "Indie Maker", "Micro SaaS"],
        )
