"""Product-Led Virality & K-Factor Distribution Engine."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import ProductProfile

logger = logging.getLogger(__name__)


class ViralityArtifactPackage(BaseModel):
    """Complete product-led distribution package for embedding virality into workflows."""

    product_name: str
    k_factor_strategy: str = Field(description="Explanation of the natural virality trigger in user workflow")
    svg_badge: str = Field(description="Scalable vector graphic badge for UI or GitHub embed")
    html_badge_snippet: str = Field(description="Copy-pasteable HTML embed snippet for footers or tools")
    markdown_badge: str = Field(description="Markdown badge for README.md repositories")
    social_share_card_spec: Dict[str, Any] = Field(description="OpenGraph card specification and copy")
    viral_loop_mechanics: List[str] = Field(description="Step-by-step cycle time and conversion loop")


class ViralityEngine:
    """Designs and renders product-led viral loops, embeddable badges, and share artifacts."""

    def __init__(self, router: Optional[AIRouter] = None) -> None:
        """Initialize virality engine with multi-provider AI router."""
        self.router = router or AIRouter()

    async def generate_package(
        self,
        profile: ProductProfile,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        dry_run: bool = False,
    ) -> ViralityArtifactPackage:
        """Analyze product workflow and synthesize embeddable badges and K-factor loops."""
        if dry_run:
            return self._generate_dry_run_package(profile)

        svg_badge = self._render_svg_badge(profile.product_name)
        markdown_badge = self._render_markdown_badge(profile.product_name)
        html_snippet = self._render_html_snippet(profile.product_name)

        strategy_data = await self._synthesize_k_factor_strategy(profile, provider_name, model)

        return ViralityArtifactPackage(
            product_name=profile.product_name,
            k_factor_strategy=strategy_data.get("k_factor_strategy", self._default_strategy(profile)),
            svg_badge=svg_badge,
            html_badge_snippet=html_snippet,
            markdown_badge=markdown_badge,
            social_share_card_spec=strategy_data.get("social_share_card_spec", self._default_social_card(profile)),
            viral_loop_mechanics=strategy_data.get("viral_loop_mechanics", self._default_loop_mechanics(profile)),
        )

    async def _synthesize_k_factor_strategy(
        self,
        profile: ProductProfile,
        provider_name: Optional[str],
        model: Optional[str],
    ) -> Dict[str, Any]:
        """Query AI for contextual viral loop mechanics tailored to the product."""
        prompt = (
            f"Design a product-led viral loop (K-factor mechanism) for:\n"
            f"Product: {profile.product_name}\n"
            f"One-Liner: {profile.one_liner}\n"
            f"Target Audience: {profile.personas[0].persona_name if profile.personas else 'Builders'}\n\n"
            "Requirements:\n"
            "1. Identify the natural artifact users produce that can be shown to third parties (like Calendly links or Loom videos).\n"
            "2. Define the exact 4-step viral loop mechanics.\n"
            "3. Generate an OpenGraph social share card specification.\n\n"
            "Return valid JSON matching:\n"
            "{\n"
            '  "k_factor_strategy": "<1-2 sentence core loop rationale>",\n'
            '  "viral_loop_mechanics": ["Step 1: ...", "Step 2: ...", "Step 3: ...", "Step 4: ..."],\n'
            '  "social_share_card_spec": {\n'
            '    "og_title": "<punchy title>",\n'
            '    "og_description": "<high conversion description>",\n'
            '    "cta_text": "<Action button>"\n'
            "  }\n"
            "}"
        )
        messages = [
            LLMMessage(role="system", content="You are a product-led growth (PLG) viral architect. Design natural, unobtrusive viral distribution loops."),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self.router.generate_text(messages=messages, provider_name=provider_name, model=model, temperature=0.3)
            return self._parse_json_dict(resp.content)
        except Exception as exc:
            logger.warning(f"Virality synthesis failed ({exc}), serving built-in PLG framework.")
            return {
                "k_factor_strategy": self._default_strategy(profile),
                "viral_loop_mechanics": self._default_loop_mechanics(profile),
                "social_share_card_spec": self._default_social_card(profile),
            }

    def _render_svg_badge(self, product_name: str) -> str:
        """Render clean, dark-mode SVG status badge with green accent."""
        label = "powered by"
        value = product_name
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="180" height="28" role="img" aria-label="{label}: {value}">'
            f'<linearGradient id="g" x2="0" y2="100%"><stop offset="0" stop-color="#1e293b"/><stop offset="1" stop-color="#0f172a"/></linearGradient>'
            f'<clipPath id="r"><rect width="180" height="28" rx="6" fill="#fff"/></clipPath>'
            f'<g clip-path="url(#r)">'
            f'<rect width="85" height="28" fill="#0f172a"/>'
            f'<rect x="85" width="95" height="28" fill="#10b981"/>'
            f'</g>'
            f'<g fill="#fff" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="11" font-weight="600">'
            f'<text x="42.5" y="18" fill="#94a3b8">{label}</text>'
            f'<text x="132.5" y="18" fill="#022c22">{value}</text>'
            f'</g>'
            f'</svg>'
        )

    def _render_markdown_badge(self, product_name: str) -> str:
        """Generate markdown link with embedded SVG badge for GitHub READMEs."""
        return (
            f"[![Powered by {product_name}]"
            f"(https://img.shields.io/badge/Powered%20by-{product_name}-10b981?style=flat-square&logo=github)]"
            f"(https://github.com/PatelDeepB/zerocac)"
        )

    def _render_html_snippet(self, product_name: str) -> str:
        """Generate accessible HTML footer snippet with link to product."""
        return (
            f'<div class="zerocac-badge" style="display:inline-flex;align-items:center;gap:6px;'
            f'font-family:sans-serif;font-size:12px;color:#94a3b8;background:#0f172a;'
            f'padding:4px 10px;border-radius:6px;border:1px solid #1e293b;">\n'
            f'  <span>Automated with</span>\n'
            f'  <a href="https://github.com/PatelDeepB/zerocac" target="_blank" rel="noopener" '
            f'style="color:#10b981;font-weight:600;text-decoration:none;">{product_name}</a>\n'
            f'</div>'
        )

    def _default_strategy(self, profile: ProductProfile) -> str:
        """Default PLG strategy explanation."""
        return (
            f"Every campaign asset and micro-tool generated embeds a lightweight attribution badge. "
            f"When prospects interact with the tool or read documentation, the visible badge acts as a "
            f"frictionless referral channel back to {profile.product_name}."
        )

    def _default_loop_mechanics(self, profile: ProductProfile) -> List[str]:
        """4-step closed-circuit viral loop sequence."""
        return [
            f"1. User deploys a free micro-tool or publishes an AEO comparison page generated by {profile.product_name}.",
            "2. External visitors browse the tool to solve their problem with zero login friction.",
            f"3. Visitors notice the subtle 'Powered by {profile.product_name}' badge and click to inspect the tool.",
            f"4. A portion of visitors (5% to 12%) adopt {profile.product_name} to generate their own marketing assets, resetting the loop.",
        ]

    def _default_social_card(self, profile: ProductProfile) -> Dict[str, Any]:
        """OpenGraph social card metadata."""
        return {
            "og_title": f"Stop Paying the Ad Tax: How We Scaled {profile.product_name} to $0 CAC",
            "og_description": f"Detailed teardown of autonomous organic growth, real-time intent interception, and micro-tools.",
            "cta_text": "Read the $0 CAC Blueprint",
        }

    def _parse_json_dict(self, text: str) -> Dict[str, Any]:
        """Parse clean JSON dictionary from model output."""
        import json
        import re

        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)

    def _generate_dry_run_package(self, profile: ProductProfile) -> ViralityArtifactPackage:
        """Deterministic package for tests and offline execution."""
        return ViralityArtifactPackage(
            product_name=profile.product_name,
            k_factor_strategy=self._default_strategy(profile),
            svg_badge=self._render_svg_badge(profile.product_name),
            html_badge_snippet=self._render_html_snippet(profile.product_name),
            markdown_badge=self._render_markdown_badge(profile.product_name),
            social_share_card_spec=self._default_social_card(profile),
            viral_loop_mechanics=self._default_loop_mechanics(profile),
        )
