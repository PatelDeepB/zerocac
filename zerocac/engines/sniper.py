"""Engine A: Intent Sniper for high-converting social community infiltration."""

from typing import List, Optional
from pydantic import BaseModel, Field

from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import ProductProfile


class SniperOpportunity(BaseModel):
    """Specific buyer discussion thread identified for high-intent response."""

    platform: str = Field(description="Community platform: Reddit, Hacker News, X, or Quora")
    community: str = Field(description="Target forum: e.g. r/SaaS, r/webdev, Show HN")
    thread_title: str = Field(description="Simulated or scraped user question")
    intent_score: int = Field(description="Urgency/Intent score from 1 to 100")
    draft_response: str = Field(description="Authentic, value-first technical answer")
    organic_mention_angle: str = Field(description="How the product is naturally woven in")


class SniperCampaign(BaseModel):
    """Collection of staged intent opportunities for review and posting."""

    product_name: str
    opportunities: List[SniperOpportunity] = Field(default_factory=list)


class IntentSniperEngine:
    """Detects high-intent buyer pain queries and generates authentic solutions."""

    def __init__(self, router: Optional[AIRouter] = None) -> None:
        self.router = router or AIRouter()

    async def generate_opportunities(
        self,
        profile: ProductProfile,
        count: int = 3,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> SniperCampaign:
        """Generate high-intent social opportunities with drafted answers."""
        prompt = self._build_prompt(profile, count)
        messages = [
            LLMMessage(role="system", content=self._get_system_instructions()),
            LLMMessage(role="user", content=prompt),
        ]

        response = await self.router.generate_text(
            messages=messages,
            provider_name=provider_name,
            model=model,
            temperature=0.5,
            max_tokens=2500,
        )

        opportunities = self._parse_opportunities(response.content, profile)
        return SniperCampaign(product_name=profile.product_name, opportunities=opportunities)

    def _get_system_instructions(self) -> str:
        """Provide system prompt enforcing authentic human tone and zero AI jargon."""
        return (
            "You are a battle-tested technical founder helping peers on Reddit and Hacker News.\n"
            "CRITICAL RULES:\n"
            "1. NEVER sound like a marketer. No buzzwords ('game changer', 'revolutionary', 'in today's world').\n"
            "2. First 80% of your answer must provide genuine, immediate, technical value solving their problem.\n"
            "3. Last 20% naturally mentions your tool as an open solution or alternative you built to solve this exact headache.\n"
            "4. Keep the tone humble, practitioner-to-practitioner, and concise."
        )

    def _build_prompt(self, profile: ProductProfile, count: int) -> str:
        """Construct user prompt containing product intelligence."""
        queries_str = "\n".join(f"- {q}" for q in profile.high_intent_queries[:3])
        return (
            f"Product: {profile.product_name} ({profile.one_liner})\n"
            f"Core Problem Solved: {profile.core_problem}\n"
            f"Target Personas: {', '.join(p.persona_name for p in profile.personas)}\n"
            f"Sample Buyer Questions:\n{queries_str}\n\n"
            f"Draft {count} distinct community responses across Reddit, Hacker News, and X. "
            f"For each, include:\n"
            f"Platform | Community | Thread Title | Intent Score (80-99) | Response Draft | Angle"
        )

    def _parse_opportunities(self, content: str, profile: ProductProfile) -> List[SniperOpportunity]:
        """Parse completion text or provide high-converting fallback opportunities."""
        if "DryRun" in content or len(content) < 80:
            return self._build_default_opportunities(profile)

        # Build clean structured opportunities from the generated output
        opportunities = []
        platforms = [("Reddit", "r/SaaS"), ("Hacker News", "Ask HN"), ("X / Twitter", "#buildinpublic")]
        sections = [s.strip() for s in content.split("\n\n") if len(s.strip()) > 40]

        for i, (plat, comm) in enumerate(platforms):
            snippet = sections[i] if i < len(sections) else content
            title = profile.high_intent_queries[i % len(profile.high_intent_queries)]
            opportunities.append(
                SniperOpportunity(
                    platform=plat,
                    community=comm,
                    thread_title=title,
                    intent_score=92 - (i * 3),
                    draft_response=snippet,
                    organic_mention_angle="Authentic problem-solver recommendation",
                )
            )
        return opportunities

    def _build_default_opportunities(self, profile: ProductProfile) -> List[SniperOpportunity]:
        """Generate deterministic high-intent opportunities for dry-run/testing."""
        name = profile.product_name
        return [
            SniperOpportunity(
                platform="Reddit",
                community="r/SaaS",
                thread_title="How are you acquiring customers without spending thousands on Google Ads?",
                intent_score=95,
                draft_response=(
                    "The paid ads math is broken for early stage founders. CPCs on Google and Meta "
                    "eat your entire margin before you even hit PMF.\n\n"
                    "What worked for us was focusing on intent-driven organic distribution: finding people "
                    "who are already agonizing over the problem in relevant subreddits and answering with "
                    "actual code/solutions. We built an autonomous agent called "
                    f"{name} specifically to monitor these conversations and craft high-value breakdowns. "
                    "Zero ad spend, and the conversion rate is consistently above 15%."
                ),
                organic_mention_angle="Direct peer founder experience sharing",
            ),
            SniperOpportunity(
                platform="Hacker News",
                community="Ask HN",
                thread_title="Ask HN: What is your stack for organic product marketing?",
                intent_score=91,
                draft_response=(
                    "Most marketing SaaS tools are bloated and require $500/mo subscriptions. "
                    "Instead of manual blog posts nobody reads, we generate programmatic comparison docs "
                    f"and answer engine assets using {name}. It runs locally with frontier LLM keys and "
                    "optimizes your product footprint so SearchGPT and Perplexity cite you."
                ),
                organic_mention_angle="Technical architecture and developer tooling recommendation",
            ),
            SniperOpportunity(
                platform="X / Twitter",
                community="#buildinpublic",
                thread_title="Looking for tools to launch my side project without an agency budget",
                intent_score=88,
                draft_response=(
                    f"Check out {name}. It automatically prepares launch submissions for 100+ software "
                    "directories, generates comparison pages, and writes viral video scripts. "
                    "Costs $0 in ad spend."
                ),
                organic_mention_angle="Direct tool recommendation to an active seeker",
            ),
        ]
