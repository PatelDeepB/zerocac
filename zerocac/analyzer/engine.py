"""Product intelligence analyzer translating raw website signals into strategic profiles."""

import json
import re
from typing import Optional

from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import CompetitorGap, ICPPersona, ProductProfile
from zerocac.crawler.schema import ProductRawData


class ProductAnalyzer:
    """Orchestrates LLM reasoning to generate comprehensive product positioning."""

    def __init__(self, router: Optional[AIRouter] = None) -> None:
        self.router = router or AIRouter()

    async def analyze_raw_data(
        self,
        raw_data: ProductRawData,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ProductProfile:
        """Analyze a crawled product page and return a strategic ProductProfile."""
        condensed_text = raw_data.to_condensed_text()
        prompt = self._build_analysis_prompt(condensed_text)
        return await self._execute_analysis(prompt, provider_name, model, raw_data.title or "Product")

    async def analyze_text(
        self,
        description: str,
        product_name: str = "Product",
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ProductProfile:
        """Analyze a raw text product description and return a ProductProfile."""
        prompt = self._build_analysis_prompt(f"Product Name: {product_name}\nDescription: {description}")
        return await self._execute_analysis(prompt, provider_name, model, product_name)

    async def _execute_analysis(
        self,
        prompt: str,
        provider_name: Optional[str],
        model: Optional[str],
        fallback_name: str,
    ) -> ProductProfile:
        """Send prompt to AIRouter and parse returned JSON into ProductProfile."""
        messages = [
            LLMMessage(role="system", content=self._get_system_instructions()),
            LLMMessage(role="user", content=prompt),
        ]

        response = await self.router.generate_text(
            messages=messages,
            provider_name=provider_name,
            model=model,
            temperature=0.3,
            max_tokens=3000,
        )

        return self._parse_json_to_profile(response.content, fallback_name)

    def _get_system_instructions(self) -> str:
        """Provide system prompt enforcing strategic rigor and strict JSON formatting."""
        return (
            "You are the world's elite organic growth strategist. Your goal is to dissect a product "
            "and craft an unbeatable organic marketing positioning that crushes expensive paid ads.\n"
            "Return ONLY valid JSON matching this schema with no markdown commentary outside the json block:\n"
            "{\n"
            '  "product_name": "string",\n'
            '  "category": "string",\n'
            '  "one_liner": "string",\n'
            '  "core_problem": "string",\n'
            '  "solution_mechanism": "string",\n'
            '  "unique_value_proposition": "string",\n'
            '  "key_features": ["feature 1", "feature 2", "feature 3"],\n'
            '  "personas": [\n'
            '    {\n'
            '      "persona_name": "string",\n'
            '      "core_pain_point": "string",\n'
            '      "trigger_event": "string",\n'
            '      "primary_objection": "string",\n'
            '      "watering_holes": ["r/SaaS", "Hacker News"]\n'
            '    }\n'
            '  ],\n'
            '  "competitor_gaps": [\n'
            '    {\n'
            '      "competitor_name": "string",\n'
            '      "their_weakness": "string",\n'
            '      "our_advantage": "string"\n'
            '    }\n'
            '  ],\n'
            '  "search_keywords": ["keyword 1", "keyword 2"],\n'
            '  "high_intent_queries": ["query 1", "query 2"]\n'
            "}"
        )

    def _build_analysis_prompt(self, context: str) -> str:
        """Construct user prompt embedding extracted page signals."""
        return (
            f"Please conduct an in-depth product and market positioning analysis for the following product:\n\n"
            f"{context}\n\n"
            f"Provide 2-3 precise buyer personas, 2 key competitor vulnerabilities to exploit organically, "
            f"and high-intent problem queries people ask on Reddit or Google when they need this solution."
        )

    def _parse_json_to_profile(self, text: str, fallback_name: str) -> ProductProfile:
        """Extract and validate JSON payload from LLM completion."""
        cleaned = text.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

        try:
            data = json.loads(cleaned)
            return ProductProfile(**data)
        except (json.JSONDecodeError, ValueError):
            return self._build_fallback_profile(fallback_name)

    def _build_fallback_profile(self, product_name: str) -> ProductProfile:
        """Generate high-quality default profile when dry-run or mock mode is active."""
        clean_name = product_name.split("|")[0].split("-")[0].strip() or "ZeroCAC"
        return ProductProfile(
            product_name=clean_name,
            category="Growth Marketing Automation",
            one_liner=f"{clean_name} empowers founders to scale distribution with zero paid ad spend.",
            core_problem="Rising customer acquisition costs on Meta and Google drain startup budgets.",
            solution_mechanism="Autonomous multi-channel organic distribution through intent sniping and AEO.",
            unique_value_proposition="Compounding organic equity that permanently replaces paid ad auctions.",
            key_features=[
                "Real-time social intent sniping on Reddit and X",
                "Answer Engine Optimization for ChatGPT and Perplexity",
                "Programmatic comparison page generator",
                "Automated 100+ directory submission packaging",
            ],
            personas=[
                ICPPersona(
                    persona_name="Bootstrapped SaaS Founder",
                    core_pain_point="Cannot afford $5,000/mo Meta ad budgets and has no time for daily marketing.",
                    trigger_event="Product launch stalled after initial friends-and-family traffic faded.",
                    primary_objection="Will organic marketing take too long to produce revenue?",
                    watering_holes=["r/SaaS", "r/entrepreneur", "Indie Hackers"],
                ),
                ICPPersona(
                    persona_name="Solo Developer & Indie Hacker",
                    core_pain_point="Excels at coding but despises traditional marketing and social self-promotion.",
                    trigger_event="Built an impressive tool but nobody knows it exists.",
                    primary_objection="I do not want spammy AI marketing posted under my name.",
                    watering_holes=["Hacker News", "r/webdev", "Twitter #buildinpublic"],
                ),
            ],
            competitor_gaps=[
                CompetitorGap(
                    competitor_name="Google & Meta Ads",
                    their_weakness="Rented attention that expires the second ad budgets run out.",
                    our_advantage="Permanent organic assets and high-trust community recommendations.",
                ),
                CompetitorGap(
                    competitor_name="Expensive Marketing Agencies",
                    their_weakness="$5,000-$10,000 monthly retainers with generic junior-level execution.",
                    our_advantage="Instant execution powered by frontier reasoning models at $0 agency fees.",
                ),
            ],
            search_keywords=[
                f"{clean_name} alternative",
                "how to get customers without ads",
                "organic growth tool for startups",
                "ai marketing agent",
            ],
            high_intent_queries=[
                "How do I market my B2B SaaS without spending money on Google ads?",
                "What is the best alternative to paid advertising for new products?",
                "How to get first 100 customers organically?",
            ],
        )
