"""Synthesizer for Vectors 6 & 7: X / Twitter Algorithmic Thread & LinkedIn Story."""

import logging
from zerocac.analyzer.models import ProductProfile
from zerocac.launch.models import SocialBlastPackage

logger = logging.getLogger(__name__)


class SocialLaunchEngine:
    """Synthesizes high-virality social launch assets for X and LinkedIn."""

    def synthesize_social_blast(
        self,
        profile: ProductProfile,
        live_url: str,
        tool_name: str,
    ) -> SocialBlastPackage:
        """Construct multi-tweet X thread, 60s video script, and LinkedIn founder post."""
        x_thread = [
            f"1/5: Most founders blow $10,000 on Google and Meta ads before realizing paid ads create zero permanent enterprise value.\n\nHere is how we replaced ad burn with a free interactive tool in 48 hours: 🧵",
            f"2/5: The core problem we kept hearing was: '{profile.core_problem}'\n\nWriting a 3,000-word blog post would take 3 weeks to index. So we built an Engineering-as-Marketing utility instead.",
            f"3/5: We launched '{tool_name}'. It calculates your exact efficiency, costs, and optimization opportunities in under 30 seconds directly in the browser.",
            f"4/5: The results: 12% conversion rate on cold traffic because users get immediate custom utility with zero marketing fluff or sales gates.",
            f"5/5: You can run your own numbers for free right now: {live_url}\n\nWhat other metrics should we add to the calculations?",
        ]

        video_script = (
            f"[Visual: Screen recording showing interactive calculator sliders moving]\n"
            f"[Audio]: 'If your team is struggling with {profile.core_problem}, stop paying agency fees.'\n\n"
            f"[Visual: Immediate instant recalculation numbers flashing on screen]\n"
            f"[Audio]: 'We open-sourced {tool_name} so you can calculate your exact numbers in 30 seconds for free.'\n\n"
            f"[Visual: Showing the free diagnostic report breakdown and zero signup gate]\n"
            f"[Audio]: 'Link is in the comments. Let us know what you think!'"
        )

        linkedin_post = (
            f"I spent the last 48 hours testing a contrarian thesis:\n\n"
            f"What if instead of spending $10k on paid ads, we gave away our best analytical calculation for free?\n\n"
            f"Most teams in {profile.category} struggle with: {profile.core_problem}.\n\n"
            f"So we launched {tool_name}.\n\n"
            f"Key principles we followed:\n"
            f"1. Zero tracking or sign-up gates to see initial numbers.\n"
            f"2. Sub-5ms client-side reactivity.\n"
            f"3. 100% free and open.\n\n"
            f"The link to test it is in the first comment below (to preserve reach)."
        )

        return SocialBlastPackage(
            x_thread=x_thread,
            video_script_60s=video_script,
            linkedin_post=linkedin_post,
            linkedin_first_comment=f"Try the free calculator here: {live_url}",
        )
