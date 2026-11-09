"""FastAPI router for the 8-Vector Day-1 Launch Carpet Bombing Engine."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.analyzer.models import ProductProfile
from zerocac.crawler.scraper import URLScraper
from zerocac.engines.microtool import MicroToolEngine
from zerocac.launch.models import HardenedLaunchPackage, LaunchExecutionReport
from zerocac.launch.orchestrator import LaunchOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/launch", tags=["Day-1 Launch Engine"])


class PrepareLaunchApiRequest(BaseModel):
    """Payload to synthesize complete 8-Vector launch kit."""

    url: Optional[str] = Field(default=None, description="Product landing page URL")
    product_name: Optional[str] = Field(default="Product", description="Brand name")
    description: Optional[str] = Field(default=None, description="Direct product description")
    live_url: Optional[str] = Field(default=None, description="Deployed edge tool URL")
    dry_run: bool = Field(default=False, description="Simulate generation")


class ExecuteLaunchApiRequest(BaseModel):
    """Payload to execute multi-wave launch syndication."""

    package: HardenedLaunchPackage = Field(..., description="Compiled launch package")
    dry_run: bool = Field(default=False, description="Simulate execution without external network posts")


@router.post("/prepare", response_model=HardenedLaunchPackage, status_code=status.HTTP_200_OK)
async def prepare_launch(payload: PrepareLaunchApiRequest) -> HardenedLaunchPackage:
    """Synthesize complete 8-vector Day-1 launch assets for a product."""
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

    # Generate microtool if not provided
    microtool_engine = MicroToolEngine()
    tool_pkg = await microtool_engine.generate_tool(profile, dry_run=True)

    live_url = payload.live_url or f"https://{tool_pkg.concept.slug}.pages.dev"
    orchestrator = LaunchOrchestrator()

    return orchestrator.prepare_launch_kit(
        profile=profile,
        tool_html=tool_pkg.html_content,
        tool_slug=tool_pkg.concept.slug,
        live_url=live_url,
        tool_name=tool_pkg.concept.tool_name,
    )


@router.post("/execute", response_model=LaunchExecutionReport, status_code=status.HTTP_200_OK)
async def execute_launch(payload: ExecuteLaunchApiRequest) -> LaunchExecutionReport:
    """Dispatch multi-wave launch across all 8 independent vectors."""
    orchestrator = LaunchOrchestrator()
    return await orchestrator.execute_launch(package=payload.package, dry_run=payload.dry_run)
