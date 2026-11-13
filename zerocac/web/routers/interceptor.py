"""FastAPI router for the Direct Social & Community Intent Interceptor."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.crawler.scraper import URLScraper
from zerocac.interceptor.daemon import InterceptorDaemon
from zerocac.interceptor.engine import CommunityInterceptorEngine
from zerocac.interceptor.models import (
    AutonomyTier,
    DaemonStatusReport,
    InterceptDispatchResult,
    InterceptOpportunity,
    StealthMode,
)
from zerocac.interceptor.store import InterceptorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intercept", tags=["Community Interceptor"])

_active_daemon: Optional[InterceptorDaemon] = None
_daemon_task: Optional[asyncio.Task] = None



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


class StartDaemonPayload(BaseModel):
    """Payload to start continuous background interception daemon."""

    poll_interval: float = Field(default=60.0, ge=5.0, le=3600.0, description="Seconds between stream polls")
    autonomy_tier: AutonomyTier = Field(
        default=AutonomyTier.MANUAL_REVIEW,
        description="Autonomous dispatch policy",
    )
    min_score: int = Field(default=75, ge=0, le=100, description="Minimum qualifying intent score")
    subreddits: Optional[List[str]] = Field(default=None, description="Target subreddit list")
    dry_run: bool = Field(default=True, description="Simulate feed scan and posting")


@router.get("/opportunities", response_model=List[InterceptOpportunity], status_code=status.HTTP_200_OK)
async def list_stored_opportunities(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items to return"),
) -> List[InterceptOpportunity]:
    """Retrieve deduplicated buyer opportunities from SQLite storage."""
    store = InterceptorStore()
    return await store.list_opportunities(status=status_filter, limit=limit)


@router.get("/daemon/status", response_model=DaemonStatusReport, status_code=status.HTTP_200_OK)
async def get_daemon_status() -> DaemonStatusReport:
    """Retrieve current background daemon running state and metrics."""
    global _active_daemon
    if _active_daemon:
        return _active_daemon.get_status()
    return DaemonStatusReport(is_running=False)


@router.post("/daemon/start", response_model=DaemonStatusReport, status_code=status.HTTP_200_OK)
async def start_interceptor_daemon(payload: StartDaemonPayload) -> DaemonStatusReport:
    """Launch the 24/7 background social interception loop."""
    global _active_daemon, _daemon_task

    if _active_daemon and _active_daemon.get_status().is_running:
        return _active_daemon.get_status()

    _active_daemon = InterceptorDaemon(
        poll_interval=payload.poll_interval,
        autonomy_tier=payload.autonomy_tier,
        min_score=payload.min_score,
        subreddits=payload.subreddits,
        dry_run=payload.dry_run,
    )
    _active_daemon.mark_started()
    _daemon_task = asyncio.create_task(_active_daemon.start())
    return _active_daemon.get_status()


@router.post("/daemon/stop", response_model=DaemonStatusReport, status_code=status.HTTP_200_OK)
async def stop_interceptor_daemon() -> DaemonStatusReport:
    """Terminate the 24/7 background social interception loop."""
    global _active_daemon, _daemon_task

    if not _active_daemon:
        return DaemonStatusReport(is_running=False)

    _active_daemon.stop()
    if _daemon_task and not _daemon_task.done():
        _daemon_task.cancel()

    status_report = _active_daemon.get_status()
    _active_daemon = None
    _daemon_task = None
    return status_report

