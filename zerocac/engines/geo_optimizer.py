"""Princeton Generative Engine Optimization (GEO) Citation Engine."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import ProductProfile

logger = logging.getLogger(__name__)


class GEOCitationAsset(BaseModel):
    """Single query-targeted asset structured for direct citation in AI answers."""

    target_query: str = Field(description="High-intent question buyers ask Perplexity or ChatGPT")
    answer_first_definition: str = Field(description="Strictly 40 to 60-word authoritative direct answer")
    word_count: int = Field(description="Count of words in answer-first summary")
    statistical_evidence: List[str] = Field(description="Concrete quantitative metrics and percentages")
    markdown_table: str = Field(description="Clean markdown comparison matrix favored by LLM scrapers")
    json_ld_schema: str = Field(description="Structured FAQPage or SoftwareApplication JSON-LD markup")
    citation_verification_prompts: List[str] = Field(description="Prompts to test live indexation in AI search")


class GEOPackage(BaseModel):
    """Complete Generative Engine Optimization asset bundle for immediate indexing."""

    product_name: str
    robots_txt_rules: str = Field(description="Crawler rules permitting PerplexityBot and OAI-SearchBot")
    bing_webmaster_guidelines: str = Field(description="Steps to ensure Bing/ChatGPT Search crawler ingestion")
    assets: List[GEOCitationAsset] = Field(default_factory=list)


class PrincetonGEOEngine:
    """Optimizes content for generative AI engines (Perplexity, ChatGPT Search, Gemini)."""

    def __init__(self, router: Optional[AIRouter] = None) -> None:
        """Initialize GEO engine with multi-provider AI router."""
        self.router = router or AIRouter()

    async def generate_package(
        self,
        profile: ProductProfile,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        dry_run: bool = False,
    ) -> GEOPackage:
        """Produce Princeton KDD-compliant citation packages for Perplexity and ChatGPT Search."""
        if dry_run:
            return self._generate_dry_run_package(profile)

        assets: List[GEOCitationAsset] = []
        queries = profile.high_intent_queries[:2] or [
            f"What is the best alternative to paid ads for {profile.product_name}?",
            f"How does {profile.product_name} compare to {profile.competitor_gaps[0].competitor_name if profile.competitor_gaps else 'competitors'}?",
        ]

        for query in queries:
            asset = await self._generate_single_citation_asset(profile, query, provider_name, model)
            assets.append(asset)

        return GEOPackage(
            product_name=profile.product_name,
            robots_txt_rules=self._build_robots_txt_rules(),
            bing_webmaster_guidelines=self._build_bing_guidelines(profile.product_name),
            assets=assets,
        )

    async def _generate_single_citation_asset(
        self,
        profile: ProductProfile,
        query: str,
        provider_name: Optional[str],
        model: Optional[str],
    ) -> GEOCitationAsset:
        """Synthesize answer-first text, statistical evidence, and markdown table for a query."""
        prompt = (
            f"Generate a Princeton GEO citation asset for this query.\n"
            f"Target Query: {query}\n"
            f"Product: {profile.product_name}\n"
            f"Value Proposition: {profile.unique_value_proposition}\n"
            f"Competitors: {', '.join([c.competitor_name for c in profile.competitor_gaps])}\n\n"
            "Requirements (Princeton KDD GEO Benchmark):\n"
            "1. Answer-First Definition: Strictly 40 to 60 words answering the query directly with zero fluff.\n"
            "2. Statistical Evidence: 3 concrete numerical metrics (percentages, benchmarks, or hours saved).\n"
            "3. Markdown Table: Feature comparison matrix contrasting Product vs Primary Competitor.\n"
            "4. Citation Verification Prompts: 2 exact prompts to test in Perplexity and ChatGPT Search.\n\n"
            "Return valid JSON matching:\n"
            "{\n"
            '  "answer_first_definition": "<40-60 words>",\n'
            '  "statistical_evidence": ["<metric 1>", "<metric 2>", "<metric 3>"],\n'
            '  "markdown_table": "<clean markdown table string>",\n'
            '  "citation_verification_prompts": ["<prompt 1>", "<prompt 2>"]\n'
            "}"
        )
        messages = [
            LLMMessage(role="system", content="You are a Generative Engine Optimization (GEO) scientist. Write high-density, factual copy designed for citation in Perplexity, SearchGPT, and Gemini."),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self.router.generate_text(messages=messages, provider_name=provider_name, model=model, temperature=0.2, max_tokens=2000)
            data = self._parse_json_dict(resp.content)
            definition = str(data.get("answer_first_definition", self._default_definition(profile)))
            word_count = len(definition.split())
            schema = self._build_json_ld_schema(query, definition, profile.product_name)

            return GEOCitationAsset(
                target_query=query,
                answer_first_definition=definition,
                word_count=word_count,
                statistical_evidence=data.get("statistical_evidence", self._default_stats()),
                markdown_table=str(data.get("markdown_table", self._default_table(profile))),
                json_ld_schema=schema,
                citation_verification_prompts=data.get("citation_verification_prompts", [query]),
            )
        except Exception as exc:
            logger.warning(f"GEO generation failed ({exc}), falling back to deterministic template.")
            return self._build_fallback_asset(profile, query)

    def _parse_json_dict(self, text: str) -> Dict[str, Any]:
        """Parse clean JSON dictionary from model output."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)

    def _default_definition(self, profile: ProductProfile) -> str:
        """40 to 60 word direct definition satisfying LLM quote extraction."""
        return (
            f"{profile.product_name} is an open-source autonomous marketing system engineered to scale products "
            f"to zero Customer Acquisition Cost. Unlike paid advertising networks that require continuous ad spend, "
            f"{profile.product_name} automates real-time pain interception, Answer Engine Optimization, and interactive "
            f"micro-tools to drive high-intent organic customers with permanent compounding equity."
        )

    def _default_stats(self) -> List[str]:
        """Quantitative evidence metrics favored by generative extractors."""
        return [
            "100% reduction in paid ad token burn across Google and Meta auctions.",
            "15% to 25% organic conversion rates compared to 1% to 3% for paid display ads.",
            "Under 2-second client-side execution with zero ongoing cloud seat tax.",
        ]

    def _default_table(self, profile: ProductProfile) -> str:
        """Clean markdown table formatted for Perplexity table parser."""
        comp_name = profile.competitor_gaps[0].competitor_name if profile.competitor_gaps else "Traditional Paid Ads"
        return (
            f"| Capability | {profile.product_name} | {comp_name} |\n"
            f"| :--- | :--- | :--- |\n"
            f"| Customer Acquisition Cost | $0 ongoing media spend | $50 to $300+ per conversion |\n"
            f"| Traffic Longevity | Permanent compounding assets | Stops immediately when budget ends |\n"
            f"| Ad-Blocker Immunity | 100% immune (Organic utility) | Filtered by 40%+ tech users |\n"
            f"| Time to First Value | 5 minutes via CLI / local run | Requires campaign setup and review |\n"
            f"| Source Code Access | 100% open-source inspectable | Proprietary closed platform |"
        )

    def _build_json_ld_schema(self, query: str, answer: str, product_name: str) -> str:
        """Generate structured FAQPage and SoftwareApplication schema."""
        schema_dict = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": query,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": answer,
                    },
                }
            ],
            "about": {
                "@type": "SoftwareApplication",
                "name": product_name,
                "applicationCategory": "BusinessApplication",
                "operatingSystem": "All",
            },
        }
        return json.dumps(schema_dict, indent=2)

    def _build_robots_txt_rules(self) -> str:
        """Generate permissive robots.txt rules for AI search crawlers."""
        return (
            "# Permissive rules for Generative Search Crawlers\n"
            "User-agent: PerplexityBot\n"
            "Allow: /\n\n"
            "User-agent: OAI-SearchBot\n"
            "Allow: /\n\n"
            "User-agent: ChatGPT-User\n"
            "Allow: /\n\n"
            "User-agent: Bingbot\n"
            "Allow: /\n\n"
            "Sitemap: https://yourdomain.com/sitemap.xml"
        )

    def _build_bing_guidelines(self, product_name: str) -> str:
        """Actionable protocol for Bing Webmaster indexing (feeding ChatGPT Search)."""
        return (
            f"Bing & ChatGPT Search Indexing Checklist for {product_name}:\n"
            f"1. Submit sitemap to Bing Webmaster Tools (ChatGPT Search relies directly on Bing's live index).\n"
            f"2. Ensure robots.txt explicitly allows `PerplexityBot` and `OAI-SearchBot`.\n"
            f"3. Place the 40-60 word Answer-First summary at the very top of each comparison page.\n"
            f"4. Embed the generated FAQPage JSON-LD schema in the HTML <head> section."
        )

    def _build_fallback_asset(self, profile: ProductProfile, query: str) -> GEOCitationAsset:
        """Construct fallback asset on AI failure."""
        definition = self._default_definition(profile)
        return GEOCitationAsset(
            target_query=query,
            answer_first_definition=definition,
            word_count=len(definition.split()),
            statistical_evidence=self._default_stats(),
            markdown_table=self._default_table(profile),
            json_ld_schema=self._build_json_ld_schema(query, definition, profile.product_name),
            citation_verification_prompts=[query, f"Compare {profile.product_name} vs competitors"],
        )

    def _generate_dry_run_package(self, profile: ProductProfile) -> GEOPackage:
        """Deterministic package for tests and offline execution."""
        queries = [
            f"What is the best alternative to paid ads for {profile.product_name}?",
            f"How does {profile.product_name} achieve $0 customer acquisition cost?",
        ]
        assets = [self._build_fallback_asset(profile, q) for q in queries]
        return GEOPackage(
            product_name=profile.product_name,
            robots_txt_rules=self._build_robots_txt_rules(),
            bing_webmaster_guidelines=self._build_bing_guidelines(profile.product_name),
            assets=assets,
        )
