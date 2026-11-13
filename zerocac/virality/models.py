"""Data models for product-led K-factor virality and milestone referral rewards."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class RewardTierId(str, Enum):
    """Configurable reward milestone unlock tiers."""

    GEO_PACKAGE_EXPORT = "geo_package_export"
    UNMETERED_INTERCEPTOR = "unmetered_interceptor"
    CUSTOM_DOMAIN_PROXY = "custom_domain_proxy"


class RewardTier(BaseModel):
    """Milestone reward unlocked by driving verified user referrals."""

    tier_id: RewardTierId = Field(..., description="Unique tier identifier")
    name: str = Field(..., description="Display title of the reward")
    required_referrals: int = Field(..., ge=1, description="Number of referrals required to unlock")
    description: str = Field(..., description="Detailed explanation of unlocked feature")
    is_unlocked: bool = Field(default=False, description="Whether user has unlocked this reward")


class ReferralStats(BaseModel):
    """Aggregate referral conversion metrics and active viral K-factor."""

    user_email: str = Field(..., description="Referrer email address")
    referral_code: str = Field(..., description="Unique tracking token")
    referral_url: str = Field(..., description="Shareable URL embedding tracking code")
    total_clicks: int = Field(default=0, description="Total link clicks received")
    total_conversions: int = Field(default=0, description="Total users converted from referrals")
    conversion_rate: float = Field(default=0.0, description="Conversion percentage (conversions / clicks)")
    k_factor: float = Field(default=0.0, description="Calculated K-factor (invites x conversion rate)")
    unlocked_rewards: List[RewardTier] = Field(default_factory=list, description="Unlocked reward tiers")
    next_milestone: Optional[RewardTier] = Field(default=None, description="Next achievable milestone tier")


class LeaderboardEntry(BaseModel):
    """Ranked user in the community leaderboard of organic growth champions."""

    rank: int = Field(..., ge=1, description="Leaderboard placement")
    user_handle: str = Field(..., description="Masked user handle or name")
    referrals_driven: int = Field(..., ge=0, description="Total verified referrals")
    ad_dollars_saved_usd: float = Field(..., ge=0.0, description="Equivalent ad spend saved at $35 CPC")
    badge_title: str = Field(..., description="Earned title e.g. Organic Grandmaster")


class TrackReferralPayload(BaseModel):
    """Payload to log a referral click or conversion."""

    referral_code: str = Field(..., description="Unique referral token")
    visitor_id: Optional[str] = Field(default=None, description="Visitor tracking cookie or IP hash")
    converted_email: Optional[EmailStr] = Field(default=None, description="Email if conversion event occurred")
