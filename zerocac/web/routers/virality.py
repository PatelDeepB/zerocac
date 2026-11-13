"""FastAPI router for product-led K-factor virality and referral rewards."""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, EmailStr, Field

from zerocac.virality.models import (
    LeaderboardEntry,
    ReferralStats,
    TrackReferralPayload,
)
from zerocac.virality.tracker import ReferralTracker
from zerocac.virality.widget import ViralWidgetRenderer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/virality", tags=["Viral Loops & Referrals"])


class CreateReferralPayload(BaseModel):
    """Payload to generate a tracked referral link."""

    email: EmailStr = Field(..., description="User email to register for referral incentives")
    base_url: str = Field(default="https://zerocac.org", description="Base landing page URL")


@router.post("/referral/create", response_model=ReferralStats, status_code=status.HTTP_200_OK)
async def create_referral_link(payload: CreateReferralPayload) -> ReferralStats:
    """Generate tracked referral link and return active milestone status."""
    tracker = ReferralTracker()
    return await tracker.get_stats(payload.email, base_url=payload.base_url)


@router.post("/referral/track", status_code=status.HTTP_200_OK)
async def track_referral_event(payload: TrackReferralPayload) -> dict:
    """Record a referral arrival click or user conversion event."""
    tracker = ReferralTracker()
    if payload.converted_email:
        await tracker.record_conversion(payload.referral_code, str(payload.converted_email))
        return {"success": True, "event": "conversion", "referral_code": payload.referral_code}

    await tracker.record_click(payload.referral_code, visitor_id=payload.visitor_id)
    return {"success": True, "event": "click", "referral_code": payload.referral_code}


@router.get("/referral/{identifier}", response_model=ReferralStats, status_code=status.HTTP_200_OK)
async def get_referral_stats(
    identifier: str,
    base_url: str = Query(default="https://zerocac.org", description="Base landing page URL"),
) -> ReferralStats:
    """Retrieve live referral metrics, K-factor, and milestone tier unlocks."""
    tracker = ReferralTracker()
    return await tracker.get_stats(identifier, base_url=base_url)


@router.get("/leaderboard", response_model=List[LeaderboardEntry], status_code=status.HTTP_200_OK)
async def get_viral_leaderboard(
    limit: int = Query(default=10, ge=1, le=100, description="Max leaderboard entries"),
) -> List[LeaderboardEntry]:
    """Retrieve community leaderboard of top organic distribution champions."""
    tracker = ReferralTracker()
    return await tracker.get_leaderboard(limit=limit)


@router.get("/badge", response_class=Response, status_code=status.HTTP_200_OK)
async def get_dynamic_savings_badge(
    product_name: str = Query(default="ZeroCAC", description="Brand name on badge"),
    savings: float = Query(default=15400.0, description="Ad dollars displaced"),
) -> Response:
    """Render dynamic SVG counter badge highlighting displaced ad spend."""
    renderer = ViralWidgetRenderer()
    svg_content = renderer.render_svg_counter_badge(product_name, savings)
    return Response(content=svg_content, media_type="image/svg+xml")
