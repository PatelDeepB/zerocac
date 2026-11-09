"""FastAPI router for the Programmatic SEO (pSEO) Matrix Engine."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.crawler.scraper import URLScraper
from zerocac.engines.microtool import MicroToolEngine
from zerocac.pseo.deployer import PSEOBatchDeployer
from zerocac.pseo.engine import PSEOMatrixEngine
from zerocac.pseo.models import PSEODeploymentReport, PSEOMatrixPackage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pseo", tags=["Programmatic SEO"])


class GeneratePSEOPayload(BaseModel):
    """Payload to synthesize multi-axis programmatic SEO matrix."""

    url: Optional[str] = Field(default=None, description="Product landing page URL")
    product_name: Optional[str] = Field(default="Product", description="Brand name")
    description: Optional[str] = Field(default=None, description="Direct product description")
    count: int = Field(default=15, ge=3, le=100, description="Number of programmatic pages to generate")
    dry_run: bool = Field(default=False, description="Simulate generation")


class DeployPSEOPayload(BaseModel):
    """Payload to deploy programmatic SEO cluster to edge."""

    package: PSEOMatrixPackage = Field(..., description="Compiled matrix package")
    dry_run: bool = Field(default=False, description="Simulate edge deployment and IndexNow")


@router.post("/generate", response_model=PSEOMatrixPackage, status_code=status.HTTP_200_OK)
async def generate_pseo_cluster(payload: GeneratePSEOPayload) -> PSEOMatrixPackage:
    """Synthesize validated multi-axis pSEO landing pages with Trojan Horse teardowns."""
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

    microtool_engine = MicroToolEngine()
    tool_pkg = await microtool_engine.generate_tool(profile, dry_run=True)

    engine = PSEOMatrixEngine()
    return await engine.generate_matrix(
        profile=profile,
        tool_html=tool_pkg.html_content,
        target_count=payload.count,
        dry_run=payload.dry_run,
    )


@router.post("/deploy", response_model=PSEODeploymentReport, status_code=status.HTTP_200_OK)
async def deploy_pseo_cluster(payload: DeployPSEOPayload) -> PSEODeploymentReport:
    """Deploy complete pSEO matrix to live edge and batch submit to IndexNow."""
    deployer = PSEOBatchDeployer()
    return await deployer.deploy_matrix(payload.package, dry_run=payload.dry_run)
