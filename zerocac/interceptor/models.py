"""Data models for the Direct Social & Community Intent Interceptor."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class SocialPlatform(str, Enum):
    """Supported social and developer community platforms."""

    REDDIT = "reddit"
    HACKER_NEWS = "hacker_news"
    X_TWITTER = "x_twitter"
    GITHUB_DISCUSSIONS = "github_discussions"


class StealthMode(str, Enum):
    """Link stealth modes to bypass spam filters and maximize upvotes."""

    DIRECT_TOOL_LINK = "direct_tool_link"
    ZERO_LINK_VALUE_TRAP = "zero_link_value_trap"
    GITHUB_PROFILE = "github_profile"


class IntentClassification(str, Enum):
    """Classification of buyer search intent and agony."""

    IMMEDIATE_MIGRATION = "immediate_migration"
    PRICE_COMPLAINT = "price_complaint"
    TOOL_RECOMMENDATION = "tool_recommendation"
    TECHNICAL_FRUSTRATION = "technical_frustration"
    COMPETITOR_CRISIS = "competitor_crisis"
    IRRELEVANT = "irrelevant"


class AutonomyTier(str, Enum):
    """Autonomous decision tiers for live social interception."""

    MANUAL_REVIEW = "manual_review"
    CAMOUFLAGE_AUTONOMOUS = "camouflage_autonomous"
    FULL_AUTONOMOUS = "full_autonomous"



class AccountCredential(BaseModel):
    """Social account profile and anti-ban karma metrics."""

    account_id: str = Field(
        default_factory=lambda: f"acc-{uuid.uuid4().hex[:8]}",
        description="Unique account identifier",
    )
    platform: SocialPlatform = Field(..., description="Target platform")
    username: str = Field(..., description="Account username or handle")
    karma: int = Field(default=250, description="Platform karma or follower count")
    account_age_days: int = Field(default=180, description="Age of account in days")
    non_promotional_count: int = Field(default=9, description="Count of altruistic comments")
    promotional_count: int = Field(default=1, description="Count of product-mention comments")
    is_active: bool = Field(default=True, description="Whether account is currently active")

    @property
    def promotional_ratio(self) -> float:
        """Calculate promotional post ratio against total posts."""
        total = self.non_promotional_count + self.promotional_count
        return (self.promotional_count / total) if total > 0 else 0.0


class InterceptOpportunity(BaseModel):
    """A qualified buyer discussion ready for practitioner interception."""

    opportunity_id: str = Field(
        default_factory=lambda: f"opp-{uuid.uuid4().hex[:10]}",
        description="Unique opportunity identifier",
    )
    platform: SocialPlatform = Field(..., description="Source platform")
    post_id: str = Field(..., description="External post or comment ID")
    post_url: str = Field(..., description="Direct URL to thread")
    subreddit_or_topic: str = Field(..., description="Subreddit name or topic tag")
    author: str = Field(..., description="Original poster username")
    title: str = Field(..., description="Post title")
    body_text: str = Field(..., description="Post body or comment text")
    created_at_utc: str = Field(..., description="Post creation timestamp")
    intent_score: int = Field(..., ge=0, le=100, description="Purchase intent score (0-100)")
    classification: IntentClassification = Field(..., description="Classified intent category")
    detected_competitor: Optional[str] = Field(default=None, description="Incumbent competitor mentioned")
    extracted_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted metrics: host count, volume, budget",
    )
    stealth_mode: StealthMode = Field(
        default=StealthMode.ZERO_LINK_VALUE_TRAP,
        description="Selected stealth linking strategy",
    )
    synthesized_reply: str = Field(..., description="Practitioner-grade drafted response")
    status: str = Field(default="pending_approval", description="Workflow state")


class InterceptDispatchResult(BaseModel):
    """Outcome report for an intercepted response dispatch."""

    opportunity_id: str = Field(..., description="Opportunity identifier")
    platform: SocialPlatform = Field(..., description="Target platform")
    success: bool = Field(..., description="Whether posting succeeded")
    live_comment_url: Optional[str] = Field(default=None, description="Published comment URL")
    error_message: Optional[str] = Field(default=None, description="Error reason if failed")
    dispatched_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of dispatch",
    )


class InterceptTelemetryRecord(BaseModel):
    """Aggregated conversion and ad spend displacement metrics."""

    opportunity_id: str = Field(..., description="Opportunity identifier")
    platform: SocialPlatform = Field(..., description="Target platform")
    upvotes: int = Field(default=0, description="Net upvote score")
    replies_count: int = Field(default=0, description="Child replies received")
    inbound_clicks: int = Field(default=0, description="Traffic clicks driven to site")
    leads_captured: int = Field(default=0, description="Qualified leads acquired")
    estimated_ad_savings_usd: float = Field(
        default=0.0,
        description="Displaced Google/Meta ad spend value",
    )


class DaemonStatusReport(BaseModel):
    """Health and iteration report for the background interceptor daemon."""

    is_running: bool = Field(default=False, description="Whether daemon polling loop is active")
    uptime_seconds: float = Field(default=0.0, description="Elapsed runtime in seconds")
    poll_interval_seconds: float = Field(default=60.0, description="Sleep duration between stream scans")
    autonomy_tier: AutonomyTier = Field(
        default=AutonomyTier.MANUAL_REVIEW,
        description="Active autonomous decision tier",
    )
    total_iterations: int = Field(default=0, description="Total poll iterations executed")
    total_opportunities_found: int = Field(default=0, description="Deduplicated buyer pain signals detected")
    total_dispatched: int = Field(default=0, description="Total replies dispatched to platforms")
    last_polled_at: Optional[str] = Field(default=None, description="ISO timestamp of last completed poll")

