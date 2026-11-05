"""Data models for closed-loop telemetry analytics and self-healing optimization."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PerformanceTier(str, Enum):
    """Categorization of an organic asset based on conversion telemetry."""

    UNDERPERFORMING = "underperforming"
    HEALTHY = "healthy"
    OUTPERFORMING = "outperforming"


class OptimizationAction(str, Enum):
    """Action prescribed by the self-tuning growth engine."""

    REWRITE_HEADLINE = "rewrite_headline"
    SHARPEN_CTA = "sharpen_cta"
    EXPAND_CLUSTER = "expand_cluster"
    MAINTAIN = "maintain"


class AssetMetrics(BaseModel):
    """Telemetry report for a specific deployed micro-tool or GEO page."""

    slug: str = Field(..., description="Project slug or URL path")
    impressions: int = Field(default=0, ge=0, description="Total search or feed impressions")
    clicks: int = Field(default=0, ge=0, description="Total user clicks to the asset")
    ctr: float = Field(default=0.0, ge=0.0, description="Click-through rate percentage")
    leads_captured: int = Field(default=0, ge=0, description="Qualified prospect emails collected")
    conversion_rate: float = Field(default=0.0, ge=0.0, description="Lead capture conversion rate percentage")
    tier: PerformanceTier = Field(
        default=PerformanceTier.HEALTHY,
        description="Performance health status",
    )
    recommended_action: OptimizationAction = Field(
        default=OptimizationAction.MAINTAIN,
        description="Autonomous self-tuning action recommended",
    )


class TelemetryAuditReport(BaseModel):
    """Holistic ROI and closed-loop optimization audit across all organic assets."""

    total_assets: int = Field(..., description="Number of assets evaluated")
    total_impressions: int = Field(..., description="Aggregated organic impressions")
    total_clicks: int = Field(..., description="Aggregated organic clicks")
    total_leads_acquired: int = Field(..., description="Aggregated email leads acquired at $0 CAC")
    estimated_ad_savings_usd: float = Field(
        ...,
        description="Total ad dollars saved based on average $25 B2B CPL benchmark",
    )
    blended_conversion_rate: float = Field(..., description="Overall lead capture percentage")
    assets: List[AssetMetrics] = Field(default_factory=list, description="Detailed per-asset metrics")
    autonomous_actions_taken: List[str] = Field(
        default_factory=list,
        description="Self-healing optimizations executed automatically",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Audit timestamp in UTC ISO format",
    )
