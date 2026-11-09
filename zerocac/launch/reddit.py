"""Synthesizer for Vector 4: Multi-Subreddit Value Seeding (5 Target Communities)."""

import logging
from typing import List
from zerocac.analyzer.models import ProductProfile
from zerocac.launch.models import SubredditPost

logger = logging.getLogger(__name__)


class RedditLaunchEngine:
    """Generates culturally adapted, non-promotional value posts for 5 subreddits."""

    def synthesize_campaign(
        self,
        profile: ProductProfile,
        live_url: str,
        tool_name: str,
    ) -> List[SubredditPost]:
        """Generate 5 distinct subreddit posts matching individual community norms."""
        return [
            self._build_sideproject_post(profile, live_url, tool_name),
            self._build_saas_post(profile, live_url, tool_name),
            self._build_webdev_post(profile, live_url, tool_name),
            self._build_startups_post(profile, live_url, tool_name),
            self._build_entrepreneur_post(profile, live_url, tool_name),
        ]

    def _build_sideproject_post(self, profile: ProductProfile, live_url: str, tool_name: str) -> SubredditPost:
        """Construct r/SideProject build-in-public post."""
        return SubredditPost(
            subreddit="r/SideProject",
            angle_type="build_in_public",
            title=f"I got tired of paying for {profile.category} tools, so I built a free standalone calculator",
            body_markdown=(
                f"Hey everyone,\n\n"
                f"Like many here, I was frustrated that most {profile.category.lower()} tools lock simple "
                f"calculations behind sales calls and monthly subscriptions.\n\n"
                f"I spent the weekend writing {tool_name}. It runs completely client-side in your browser, "
                f"has zero tracking scripts, and gives you instant numbers.\n\n"
                f"What other metrics should I add to the formulas?"
            ),
            first_comment=f"Here is the link for anyone interested: {live_url}",
        )

    def _build_saas_post(self, profile: ProductProfile, live_url: str, tool_name: str) -> SubredditPost:
        """Construct r/SaaS teardown post."""
        return SubredditPost(
            subreddit="r/SaaS",
            angle_type="financial_teardown",
            title=f"Why paid ad CAC is unsustainable in 2026 and how organic engineering-as-marketing beats it",
            body_markdown=(
                f"Founders often blow $10,000 on Google and Meta ads before figuring out their unit economics.\n\n"
                f"Instead of burning capital, we built a free interactive tool ({tool_name}) that acts as a permanent "
                f"lead generator at $0 marginal cost. The calculation reveals exact burn versus compounding organic yield.\n\n"
                f"Would love to hear how other B2B founders are keeping CAC under control right now."
            ),
            first_comment=f"You can run your own numbers here: {live_url}",
        )

    def _build_webdev_post(self, profile: ProductProfile, live_url: str, tool_name: str) -> SubredditPost:
        """Construct r/webdev technical frontend post."""
        return SubredditPost(
            subreddit="r/webdev",
            angle_type="technical_architecture",
            title=f"Built a zero-dependency, single-file interactive calculator in vanilla JS",
            body_markdown=(
                f"I wanted to test how far modern vanilla JS and CSS can go without pulling in React, Tailwind, or Vite.\n\n"
                f"Result: A responsive single-file HTML utility with sub-5ms reactive recalculation, accessible semantic markup, "
                f"and zero external CDN dependencies.\n\n"
                f"How do you feel about zero-framework micro-apps versus modern bundlers for small utilities?"
            ),
            first_comment=f"Live demo if you want to inspect source: {live_url}",
        )

    def _build_startups_post(self, profile: ProductProfile, live_url: str, tool_name: str) -> SubredditPost:
        """Construct r/startups problem-solving post."""
        return SubredditPost(
            subreddit="r/startups",
            angle_type="problem_validation",
            title=f"We solved {profile.core_problem.lower()[:70]} with a free public tool",
            body_markdown=(
                f"When talking to early adopters, the #1 complaint was: {profile.core_problem}\n\n"
                f"Rather than writing another generic blog post, we engineered {tool_name} to give practitioners "
                f"an immediate answer in 30 seconds. In initial tests, it converted 12% of visitors into qualified leads.\n\n"
                f"Curious if others have had success using engineering-as-marketing over traditional content marketing."
            ),
            first_comment=f"Tool is free with no registration required: {live_url}",
        )

    def _build_entrepreneur_post(self, profile: ProductProfile, live_url: str, tool_name: str) -> SubredditPost:
        """Construct r/entrepreneur resource post."""
        return SubredditPost(
            subreddit="r/entrepreneur",
            angle_type="free_resource",
            title=f"Free interactive calculator to diagnose {profile.category.lower()} efficiency",
            body_markdown=(
                f"Put together an interactive tool for teams working on {profile.category.lower()}.\n\n"
                f"It takes your current metrics and calculates potential annual savings and optimal allocation.\n\n"
                f"Sharing here in case anyone finds it useful for their strategic planning this quarter."
            ),
            first_comment=f"Link to test it: {live_url}",
        )
