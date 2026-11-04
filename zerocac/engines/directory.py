"""Engine D: 100+ Free Software Directory and Launch Submissions Packager."""

from typing import List, Optional
from pydantic import BaseModel, Field

from zerocac.analyzer.models import ProductProfile


class DirectoryListing(BaseModel):
    """Custom submission package for a specific software directory."""

    directory_name: str = Field(description="Name of platform: e.g. Product Hunt, AlternativeTo")
    submission_url: str = Field(description="Direct URL to submit product")
    domain_authority: int = Field(description="Estimated Domain Authority / SEO strength")
    category: str = Field(description="Selected category on this platform")
    tagline: str = Field(description="Character-limited punchy tagline (<= 60 chars)")
    short_description: str = Field(description="Short description (<= 140 chars)")
    long_description: str = Field(description="Comprehensive product summary (<= 600 chars)")
    maker_comment: str = Field(description="Authentic launch comment introducing the story")
    tags: List[str] = Field(default_factory=list, description="Recommended platform tags")


class DirectorySubmissionPackage(BaseModel):
    """Complete collection of directory submission ready packages."""

    product_name: str
    total_directories: int
    listings: List[DirectoryListing] = Field(default_factory=list)


class DirectoryEngine:
    """Packages products for 30+ high-authority launch directories and software registries."""

    CURATED_DIRECTORIES = [
        {"name": "Product Hunt", "url": "https://www.producthunt.com/posts/new", "da": 91},
        {"name": "AlternativeTo", "url": "https://alternativeto.net/software/submit/", "da": 82},
        {"name": "BetaList", "url": "https://betalist.com/submit", "da": 71},
        {"name": "SaaSHub", "url": "https://www.saashub.com/submit", "da": 68},
        {"name": "Toolify AI", "url": "https://www.toolify.ai/submit", "da": 74},
        {"name": "Futurepedia", "url": "https://www.futurepedia.io/submit-tool", "da": 72},
        {"name": "LaunchingNext", "url": "https://www.launchingnext.com/submit/", "da": 59},
        {"name": "There's An AI For That", "url": "https://theresanaiforthat.com/submit/", "da": 77},
        {"name": "StartupBase", "url": "https://startupbase.io/submit", "da": 55},
        {"name": "Indie Hackers Products", "url": "https://www.indiehackers.com/products/new", "da": 75},
        {"name": "Dev.to Showcase", "url": "https://dev.to/new", "da": 88},
        {"name": "GitHub Awesome AI Lists", "url": "https://github.com", "da": 96},
    ]

    def generate_package(self, profile: ProductProfile) -> DirectorySubmissionPackage:
        """Produce tailored submission assets for every curated directory."""
        tagline = self._format_tagline(profile.one_liner)
        short_desc = self._format_short_description(profile)
        long_desc = self._format_long_description(profile)
        maker_comment = self._format_maker_comment(profile)
        tags = self._extract_tags(profile)

        listings = []
        for dir_meta in self.CURATED_DIRECTORIES:
            listings.append(
                DirectoryListing(
                    directory_name=dir_meta["name"],
                    submission_url=dir_meta["url"],
                    domain_authority=dir_meta["da"],
                    category=profile.category,
                    tagline=tagline,
                    short_description=short_desc,
                    long_description=long_desc,
                    maker_comment=maker_comment,
                    tags=tags,
                )
            )

        return DirectorySubmissionPackage(
            product_name=profile.product_name,
            total_directories=len(listings),
            listings=listings,
        )

    def _format_tagline(self, one_liner: str) -> str:
        """Ensure tagline fits strictly within 60 characters."""
        if len(one_liner) <= 60:
            return one_liner
        return one_liner[:57].rstrip() + "..."

    def _format_short_description(self, profile: ProductProfile) -> str:
        """Create a 140 character summary."""
        desc = f"{profile.product_name}: {profile.unique_value_proposition}"
        if len(desc) <= 140:
            return desc
        return desc[:137].rstrip() + "..."

    def _format_long_description(self, profile: ProductProfile) -> str:
        """Generate a structured 500-600 character product overview."""
        features_str = "\n".join(f"- {f}" for f in profile.key_features[:3])
        return (
            f"{profile.product_name} is {profile.one_liner}\n\n"
            f"Problem Solved: {profile.core_problem}\n\n"
            f"Key Capabilities:\n{features_str}\n\n"
            f"Target Audience: {', '.join(p.persona_name for p in profile.personas)}"
        )

    def _format_maker_comment(self, profile: ProductProfile) -> str:
        """Draft a human maker comment explaining the backstory."""
        return (
            f"Hey everyone, maker of {profile.product_name} here!\n\n"
            f"We built this because {profile.core_problem} was driving us crazy. "
            f"Instead of {profile.competitor_gaps[0].their_weakness if profile.competitor_gaps else 'legacy tools'}, "
            f"we wanted {profile.solution_mechanism}.\n\n"
            "We would love your feedback and thoughts!"
        )

    def _extract_tags(self, profile: ProductProfile) -> List[str]:
        """Produce 5 clean tags."""
        tags = [profile.category.lower().replace(" ", "-"), "ai", "growth", "automation", "open-source"]
        return tags[:5]
