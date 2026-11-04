"""Domain models for product positioning, ICP profiling, and competitive analysis."""

from typing import List
from pydantic import BaseModel, Field


class ICPPersona(BaseModel):
    """Profile of an ideal customer archetype most likely to convert organically."""

    persona_name: str = Field(description="Role or title: e.g., Bootstrapped SaaS Founder")
    core_pain_point: str = Field(description="Primary agony or workflow bottleneck")
    trigger_event: str = Field(description="What event forces them to seek a solution right now")
    primary_objection: str = Field(description="Their main hesitation or skepticism")
    watering_holes: List[str] = Field(
        default_factory=list, description="Subreddits, hashtags, and forums they actively browse"
    )


class CompetitorGap(BaseModel):
    """Identified competitor vulnerability and our organic counter-angle."""

    competitor_name: str = Field(description="Name of incumbent competitor")
    their_weakness: str = Field(description="Where the competitor falls short: price, complexity, bloat")
    our_advantage: str = Field(description="Why our product is superior for this specific angle")


class ProductProfile(BaseModel):
    """Comprehensive strategic marketing intelligence for the target product."""

    product_name: str = Field(description="Official name of the product")
    category: str = Field(description="Market category: e.g., Developer Tools, Sales Automation")
    one_liner: str = Field(description="Ultra-punchy one sentence pitch")
    core_problem: str = Field(description="The expensive or painful problem solved")
    solution_mechanism: str = Field(description="How the product solves the problem uniquely")
    unique_value_proposition: str = Field(description="Core UVP distinguishing it from incumbents")
    key_features: List[str] = Field(default_factory=list, description="Top 5-7 product capabilities")
    personas: List[ICPPersona] = Field(
        default_factory=list, description="Top 2-3 target buyer personas"
    )
    competitor_gaps: List[CompetitorGap] = Field(
        default_factory=list, description="Identified competitor gaps to exploit organically"
    )
    search_keywords: List[str] = Field(
        default_factory=list, description="High-intent organic search keywords"
    )
    high_intent_queries: List[str] = Field(
        default_factory=list, description="Questions buyers ask on Reddit/forums when looking for this"
    )
