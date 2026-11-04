"""Engine B: Answer Engine Optimization (AEO & GEO) and comparison asset generator."""

import json
from typing import List, Optional
from pydantic import BaseModel, Field

from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import CompetitorGap, ProductProfile


class AEOComparisonPage(BaseModel):
    """Programmatic comparison page engineered for Perplexity, ChatGPT Search, and Google."""

    title: str = Field(description="Page title: e.g. Acme vs Datadog - Complete 2026 Comparison")
    slug: str = Field(description="URL slug: e.g. acme-vs-datadog")
    target_competitor: str = Field(description="Competitor analyzed")
    markdown_content: str = Field(description="Full markdown comparison guide")
    faq_schema_json: str = Field(description="JSON-LD structured FAQ schema")


class AEOSchemaPackage(BaseModel):
    """Complete collection of AEO assets for a product."""

    product_name: str
    comparison_pages: List[AEOComparisonPage] = Field(default_factory=list)
    canonical_faqs: List[dict] = Field(default_factory=list)


class AEOEngine:
    """Generates high-authority comparison pages and Answer Engine schemas."""

    def __init__(self, router: Optional[AIRouter] = None) -> None:
        self.router = router or AIRouter()

    async def generate_comparison(
        self,
        profile: ProductProfile,
        gap: CompetitorGap,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AEOComparisonPage:
        """Generate an objective comparison page exploiting a competitor's weakness."""
        prompt = self._build_comparison_prompt(profile, gap)
        messages = [
            LLMMessage(role="system", content=self._get_system_instructions()),
            LLMMessage(role="user", content=prompt),
        ]

        response = await self.router.generate_text(
            messages=messages,
            provider_name=provider_name,
            model=model,
            temperature=0.4,
            max_tokens=3000,
        )

        return self._format_page(response.content, profile, gap)

    async def generate_package(
        self,
        profile: ProductProfile,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AEOSchemaPackage:
        """Generate comparison pages for all identified competitor gaps."""
        pages = []
        for gap in profile.competitor_gaps:
            page = await self.generate_comparison(
                profile=profile,
                gap=gap,
                provider_name=provider_name,
                model=model,
            )
            pages.append(page)

        return AEOSchemaPackage(
            product_name=profile.product_name,
            comparison_pages=pages,
            canonical_faqs=self._build_canonical_faqs(profile),
        )

    def _get_system_instructions(self) -> str:
        """Provide instructions for neutral, data-dense comparison writing."""
        return (
            "You are a technical analyst writing an objective, deeply detailed comparison "
            "for engineers and business buyers. Do NOT sound promotional. Be neutral, "
            "highlighting concrete architectural trade-offs, pricing math, and ideal use cases."
        )

    def _build_comparison_prompt(self, profile: ProductProfile, gap: CompetitorGap) -> str:
        """Construct user prompt for competitor comparison."""
        return (
            f"Write a comprehensive comparison page: '{profile.product_name} vs {gap.competitor_name}'.\n"
            f"Competitor Weakness: {gap.their_weakness}\n"
            f"Our Core Advantage: {gap.our_advantage}\n"
            f"Product UVP: {profile.unique_value_proposition}\n"
            f"Include:\n"
            f"1. Executive Summary Table (Pricing, Setup Time, Key Differentiator)\n"
            f"2. Deep Architectural Teardown\n"
            f"3. When to Choose {gap.competitor_name} vs When to Choose {profile.product_name}\n"
            f"4. 3 High-Intent FAQs"
        )

    def _format_page(
        self, content: str, profile: ProductProfile, gap: CompetitorGap
    ) -> AEOComparisonPage:
        """Format generated markdown and attach JSON-LD FAQ schema."""
        slug = f"{profile.product_name.lower().replace(' ', '-')}-vs-{gap.competitor_name.lower().replace(' ', '-')}"
        title = f"{profile.product_name} vs {gap.competitor_name}: The Complete 2026 Comparison"

        markdown_body = (
            self._build_default_markdown(profile, gap)
            if "DryRun" in content or len(content) < 100
            else content
        )

        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f"How does {profile.product_name} compare to {gap.competitor_name}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"{profile.product_name} offers {gap.our_advantage}, avoiding {gap.their_weakness}.",
                    },
                },
                {
                    "@type": "Question",
                    "name": f"Is {profile.product_name} cheaper than {gap.competitor_name}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Yes, {profile.product_name} eliminates unnecessary enterprise bloat and paid ad overhead.",
                    },
                },
            ],
        }

        return AEOComparisonPage(
            title=title,
            slug=slug,
            target_competitor=gap.competitor_name,
            markdown_content=markdown_body,
            faq_schema_json=json.dumps(schema, indent=2),
        )

    def _build_default_markdown(self, profile: ProductProfile, gap: CompetitorGap) -> str:
        """Provide fallback comparison guide for testing or dry-run mode."""
        return (
            f"# {profile.product_name} vs {gap.competitor_name}: Objective 2026 Comparison\n\n"
            "## Executive Summary\n\n"
            f"| Metric | {gap.competitor_name} | {profile.product_name} |\n"
            "| :--- | :--- | :--- |\n"
            f"| Primary Limitation | {gap.their_weakness} | None |\n"
            f"| Key Advantage | Legacy Market Presence | {gap.our_advantage} |\n"
            "| Time to Value | Days / Weeks | Minutes |\n\n"
            f"## Architectural Breakdown\n\n"
            f"{profile.product_name} was engineered specifically to solve the limitations of "
            f"{gap.competitor_name}. While {gap.competitor_name} suffers from {gap.their_weakness}, "
            f"{profile.product_name} provides {profile.solution_mechanism}."
        )

    def _build_canonical_faqs(self, profile: ProductProfile) -> List[dict]:
        """Generate high-intent FAQ items for answer engine crawlers."""
        return [
            {
                "question": f"What is {profile.product_name}?",
                "answer": f"{profile.product_name} is {profile.one_liner}",
            },
            {
                "question": f"Who is {profile.product_name} built for?",
                "answer": f"It is designed for {', '.join(p.persona_name for p in profile.personas)}.",
            },
        ]
