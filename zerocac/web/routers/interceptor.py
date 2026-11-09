"""FastAPI router for the Direct Social & Community Intent Interceptor."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.crawler.scraper import URLScraper
from zerocac.interceptor.engine import CommunityInterceptorEngine
from zerocac.interceptor.models import (
    InterceptDispatchResult,
    InterceptOpportunity,
    StealthMode,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intercept", tags=["Community Interceptor"])


class ScanInterceptPayload(BaseModel):
    """Payload to scan social streams for buyer pain points."""

    url: Optional[str] = Field(default=None, description="Product landing page URL")
    product_name: Optional[str] = Field(default="Product", description="Brand name")
    description: Optional[str] = Field(default=None, description="Direct product description")
    subreddits: Optional[List[str]] = Field(default=None, description="Custom subreddit names")
    min_score: int = Field(default=75, ge=0, le=100, description="Minimum qualifying intent score")
    stealth_mode: StealthMode = Field(default=StealthMode.ZERO_LINK_VALUE_TRAP, description="Linking mode")
    dry_run: bool = Field(default=False, description="Simulate feed scan")


class ReplyInterceptPayload(BaseModel):
    """Payload to dispatch an approved community response."""

    opportunity: InterceptOpportunity = Field(..., description="Target opportunity to answer")
    account_id: Optional[str] = Field(default=None, description="Target account ID to post from")
    dry_run: bool = Field(default=False, description="Simulate dispatch without live API call")


@router.post("/scan", response_model=List[InterceptOpportunity], status_code=status.HTTP_200_OK)
async def scan_buyer_opportunities(payload: ScanInterceptPayload) -> List[InterceptOpportunity]:
    """Scan Reddit, Hacker News, and X for qualified buyer purchase signals."""
    if not payload.url and not payload.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either url or description must be provided",
        )

    analyzer = ProductAnalyzer()
    if payload.url:
        try:
            raw = await URLScraper().crawl_url(payload.url)
            profile = await analyzer.analyze_raw_data(raw)
        except Exception:
            profile = await analyzer.analyze_text(
                description=f"Product at {payload.url}",
                product_name=payload.product_name or "Product",
            )
    else:
        profile = await analyzer.analyze_text(
            description=payload.description or "",
            product_name=payload.product_name or "Product",
        )

    engine = CommunityInterceptorEngine()
    return await engine.scan_opportunities(
        profile=profile,
        tool_url=payload.url or "https://yourproduct.com",
        subreddits=payload.subreddits,
        min_score=payload.min_score,
        stealth_mode=payload.stealth_mode,
        dry_run=payload.dry_run,
    )


@router.post("/reply", response_model=InterceptDispatchResult, status_code=status.HTTP_200_OK)
async def dispatch_community_reply(payload: ReplyInterceptPayload) -> InterceptDispatchResult:
    """Publish practitioner response to target thread."""
    engine = CommunityInterceptorEngine()
    return await engine.dispatch_reply(
        opportunity=payload.opportunity,
        account_id=payload.account_id,
        dry_run=payload.dry_run,
    )


@router.get("/telemetry", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_interceptor_telemetry() -> Dict[str, Any]:
    """Retrieve aggregated community interception metrics and ad savings."""
    engine = CommunityInterceptorEngine()
    return engine.get_telemetry_summary()
