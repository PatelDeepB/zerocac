"""Synthesizer for Vector 8: 15x High-DA Startup Catalogs and Directories."""

import logging
from typing import List
from zerocac.analyzer.models import ProductProfile
from zerocac.launch.models import DirectoryListing

logger = logging.getLogger(__name__)

TARGET_DIRECTORIES = [
    ("SaaSHub", "https://www.saashub.com/submit"),
    ("Toolify", "https://www.toolify.ai/submit"),
    ("BetaList", "https://betalist.com/submit"),
    ("StartupBase", "https://startupbase.io/submit"),
    ("Uneed", "https://www.uneed.best/submit"),
    ("LaunchingNext", "https://www.launchingnext.com/submit"),
    ("MicroLaunch", "https://microlaunch.net/submit"),
    ("AlternativeTo", "https://alternativeto.net/software/new/"),
    ("Futurepedia", "https://www.futurepedia.io/submit"),
    ("1000Tools", "https://1000.tools/submit"),
    ("PitchWall", "https://pitchwall.co/submit"),
    ("OpenAlternative", "https://openalternative.co/submit"),
    ("SideProjectors", "https://www.sideprojectors.com/submit"),
    ("StartupStash", "https://startupstash.com/submit/"),
    ("AllStartups", "https://allstartups.co/submit"),
]


class DirectoryMatrixEngine:
    """Synthesizes character-constrained directory submission payloads for 15 platforms."""

    def synthesize_matrix(
        self,
        profile: ProductProfile,
        live_url: str,
        tool_name: str,
    ) -> List[DirectoryListing]:
        """Compile complete listing specifications for 15 startup directories."""
        short_pitch = f"Free interactive {tool_name} diagnosing {profile.category.lower()} efficiency in 30s."[:140]
        full_desc = (
            f"{tool_name} is a free, standalone web utility engineered to solve: {profile.core_problem}. "
            f"Built without tracking or paywalls, it provides instant calculations and diagnostic reports "
            f"for modern teams looking to scale at $0 customer acquisition cost."
        )[:700]

        listings = []
        for name, submit_url in TARGET_DIRECTORIES:
            listings.append(
                DirectoryListing(
                    directory_name=name,
                    submission_url=submit_url,
                    title=f"{tool_name}"[:50],
                    short_pitch=short_pitch,
                    full_description=full_desc,
                    tags=[profile.category.lower().replace(" ", "-"), "developer-tools", "free", "saas"],
                )
            )
        return listings
