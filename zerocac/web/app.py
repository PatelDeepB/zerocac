"""FastAPI web server exposing REST endpoints and serving the ZeroCAC dashboard."""

from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from zerocac import __version__
from zerocac.ai.router import AIRouter
from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.analyzer.models import ProductProfile
from zerocac.config import get_settings
from zerocac.crawler.scraper import URLScraper
from zerocac.engines.aeo import AEOEngine, AEOSchemaPackage
from zerocac.engines.directory import DirectoryEngine, DirectorySubmissionPackage
from zerocac.engines.geo_optimizer import GEOPackage, PrincetonGEOEngine
from zerocac.engines.microtool import MicroToolEngine, MicroToolPackage
from zerocac.engines.narrative import ViralCampaignPackage, ViralNarrativeEngine
from zerocac.engines.radar import LiveIntentRadarEngine, RadarReport
from zerocac.engines.sniper import IntentSniperEngine, SniperCampaign
from zerocac.engines.virality_loop import ViralityArtifactPackage, ViralityEngine
from zerocac.web.routers.deploy import router as deploy_router
from zerocac.web.routers.dispatch import router as dispatch_router
from zerocac.web.routers.launch import router as launch_router
from zerocac.web.routers.leads import router as leads_router
from zerocac.web.routers.pseo import router as pseo_router
from zerocac.web.routers.telemetry import router as telemetry_router

app = FastAPI(
    title="ZeroCAC API",
    description="Autonomous AI Marketing Agent that scales products to $0 CAC",
    version=__version__,
)

app.include_router(deploy_router)
app.include_router(dispatch_router)
app.include_router(launch_router)
app.include_router(leads_router)
app.include_router(pseo_router)
app.include_router(telemetry_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Request & Response Models
class AnalyzeRequest(BaseModel):
    """Payload for initiating product analysis."""

    url: Optional[str] = Field(default=None, description="Landing page URL to crawl")
    description: Optional[str] = Field(default=None, description="Direct product description")
    product_name: Optional[str] = Field(default="Product", description="Product title")
    provider: Optional[str] = Field(default=None, description="Optional target AI provider")
    model: Optional[str] = Field(default=None, description="Optional target model identifier")


class RadarApiRequest(BaseModel):
    """Payload for running live intent radar scan."""

    profile: Optional[ProductProfile] = None
    url: Optional[str] = None
    description: Optional[str] = None
    product_name: Optional[str] = "Product"
    keywords: Optional[List[str]] = None
    limit_per_source: int = 4
    dry_run: bool = False
    provider: Optional[str] = None


class MicroToolApiRequest(BaseModel):
    """Payload for generating standalone interactive micro-tools."""

    profile: Optional[ProductProfile] = None
    url: Optional[str] = None
    description: Optional[str] = None
    product_name: Optional[str] = "Product"
    dry_run: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None


class GeoApiRequest(BaseModel):
    """Payload for generating Princeton GEO citation packages."""

    profile: Optional[ProductProfile] = None
    url: Optional[str] = None
    description: Optional[str] = None
    product_name: Optional[str] = "Product"
    dry_run: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None


class ViralityApiRequest(BaseModel):
    """Payload for generating product-led virality loop assets."""

    profile: Optional[ProductProfile] = None
    url: Optional[str] = None
    description: Optional[str] = None
    product_name: Optional[str] = "Product"
    dry_run: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None


class GenerateRequest(BaseModel):
    """Payload for generating organic campaign assets from a ProductProfile."""

    profile: ProductProfile
    engines: List[str] = Field(
        default=["sniper", "aeo", "narrative", "directory"],
        description="List of engines to run",
    )
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)


class FullCampaignResponse(BaseModel):
    """Aggregated campaign results across all requested organic engines."""

    profile: ProductProfile
    sniper: Optional[SniperCampaign] = None
    aeo: Optional[AEOSchemaPackage] = None
    narrative: Optional[ViralCampaignPackage] = None
    directory: Optional[DirectorySubmissionPackage] = None
    radar: Optional[RadarReport] = None
    microtool: Optional[MicroToolPackage] = None
    geo: Optional[GEOPackage] = None
    virality: Optional[ViralityArtifactPackage] = None


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Lightweight unauthenticated system health check."""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.env,
        "default_provider": settings.default_ai_provider,
        "default_strategy_model": settings.default_strategy_model,
        "default_fast_model": settings.default_fast_model,
    }


@app.get("/", include_in_schema=False)
async def serve_dashboard() -> FileResponse:
    """Serve the static single-page control dashboard."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard UI not compiled"
        )
    return FileResponse(index_file)


@app.post("/api/v1/analyze", response_model=ProductProfile, tags=["Analysis"])
async def analyze_product(payload: AnalyzeRequest) -> ProductProfile:
    """Ingest URL or description and extract strategic positioning and buyer personas."""
    if not payload.url and not payload.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'url' or 'description' must be supplied.",
        )

    analyzer = ProductAnalyzer()

    if payload.url:
        scraper = URLScraper()
        try:
            raw_data = await scraper.crawl_url(payload.url)
            return await analyzer.analyze_raw_data(
                raw_data, provider_name=payload.provider, model=payload.model
            )
        except Exception:
            return await analyzer.analyze_text(
                description=f"Product at {payload.url}",
                product_name=payload.product_name or "Product",
                provider_name=payload.provider,
                model=payload.model,
            )

    return await analyzer.analyze_text(
        description=payload.description or "",
        product_name=payload.product_name or "Product",
        provider_name=payload.provider,
        model=payload.model,
    )


@app.post("/api/v1/radar", response_model=RadarReport, tags=["Radar"])
async def run_radar(payload: RadarApiRequest) -> RadarReport:
    """Execute live intent radar scan for real-time buyer pain discussions."""
    profile = payload.profile
    if not profile:
        if not payload.url and not payload.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'profile', 'url', or 'description' must be provided.",
            )
        analyzer = ProductAnalyzer()
        profile = await analyzer.analyze_text(
            description=payload.description or f"Product at {payload.url}",
            product_name=payload.product_name or "Product",
            provider_name=payload.provider,
        )

    radar_engine = LiveIntentRadarEngine(router=AIRouter())
    return await radar_engine.scan_live_feeds(
        profile=profile,
        keywords=payload.keywords,
        limit_per_source=payload.limit_per_source,
        dry_run=payload.dry_run,
    )


@app.post("/api/v1/microtool", response_model=MicroToolPackage, tags=["Micro-Tool"])
async def generate_microtool(payload: MicroToolApiRequest) -> MicroToolPackage:
    """Generate standalone interactive HTML/JS micro-tool for Engineering-as-Marketing."""
    profile = payload.profile
    if not profile:
        if not payload.url and not payload.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'profile', 'url', or 'description' must be provided.",
            )
        analyzer = ProductAnalyzer()
        profile = await analyzer.analyze_text(
            description=payload.description or f"Product at {payload.url}",
            product_name=payload.product_name or "Product",
            provider_name=payload.provider,
        )

    engine = MicroToolEngine(router=AIRouter())
    return await engine.generate_tool(
        profile=profile,
        provider_name=payload.provider,
        model=payload.model,
        dry_run=payload.dry_run,
    )


@app.post("/api/v1/geo", response_model=GEOPackage, tags=["GEO"])
async def generate_geo(payload: GeoApiRequest) -> GEOPackage:
    """Generate Princeton Generative Engine Optimization citation packages."""
    profile = payload.profile
    if not profile:
        if not payload.url and not payload.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'profile', 'url', or 'description' must be provided.",
            )
        analyzer = ProductAnalyzer()
        profile = await analyzer.analyze_text(
            description=payload.description or f"Product at {payload.url}",
            product_name=payload.product_name or "Product",
            provider_name=payload.provider,
        )

    engine = PrincetonGEOEngine(router=AIRouter())
    return await engine.generate_package(
        profile=profile,
        provider_name=payload.provider,
        model=payload.model,
        dry_run=payload.dry_run,
    )


@app.post("/api/v1/virality", response_model=ViralityArtifactPackage, tags=["Virality"])
async def generate_virality(payload: ViralityApiRequest) -> ViralityArtifactPackage:
    """Generate product-led virality loop assets and embeddable badges."""
    profile = payload.profile
    if not profile:
        if not payload.url and not payload.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'profile', 'url', or 'description' must be provided.",
            )
        analyzer = ProductAnalyzer()
        profile = await analyzer.analyze_text(
            description=payload.description or f"Product at {payload.url}",
            product_name=payload.product_name or "Product",
            provider_name=payload.provider,
        )

    engine = ViralityEngine(router=AIRouter())
    return await engine.generate_package(
        profile=profile,
        provider_name=payload.provider,
        model=payload.model,
        dry_run=payload.dry_run,
    )


@app.post("/api/v1/generate", response_model=FullCampaignResponse, tags=["Campaigns"])
async def generate_campaign(payload: GenerateRequest) -> FullCampaignResponse:
    """Execute requested organic growth engines and compile campaign package."""
    profile = payload.profile
    router = AIRouter()
    response = FullCampaignResponse(profile=profile)

    if "sniper" in payload.engines:
        sniper_engine = IntentSniperEngine(router=router)
        response.sniper = await sniper_engine.generate_opportunities(
            profile, count=3, provider_name=payload.provider, model=payload.model
        )

    if "aeo" in payload.engines:
        aeo_engine = AEOEngine(router=router)
        response.aeo = await aeo_engine.generate_package(
            profile, provider_name=payload.provider, model=payload.model
        )

    if "narrative" in payload.engines:
        narrative_engine = ViralNarrativeEngine(router=router)
        response.narrative = await narrative_engine.generate_campaign(
            profile, provider_name=payload.provider, model=payload.model
        )

    if "directory" in payload.engines:
        dir_engine = DirectoryEngine()
        response.directory = dir_engine.generate_package(profile)

    if "radar" in payload.engines:
        radar_engine = LiveIntentRadarEngine(router=router)
        response.radar = await radar_engine.scan_live_feeds(profile, dry_run=False)

    if "microtool" in payload.engines:
        tool_engine = MicroToolEngine(router=router)
        response.microtool = await tool_engine.generate_tool(profile, dry_run=False)

    if "geo" in payload.engines:
        geo_engine = PrincetonGEOEngine(router=router)
        response.geo = await geo_engine.generate_package(profile, dry_run=False)

    if "virality" in payload.engines:
        virality_engine = ViralityEngine(router=router)
        response.virality = await virality_engine.generate_package(profile, dry_run=False)

    return response
