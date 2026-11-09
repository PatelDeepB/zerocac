"""Data models for the Programmatic SEO (pSEO) Matrix Engine."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class PSEOAxis(str, Enum):
    """The 3 strategic axes of programmatic search expansion."""

    COMPETITOR_ALTERNATIVE = "competitor_alternative"
    REGIONAL_ECOSYSTEM = "regional_ecosystem"
    CALCULATOR_SLICE = "calculator_slice"


class DemandSignal(BaseModel):
    """Validated search volume and query intent signal."""

    query: str = Field(..., description="Target search query")
    search_frequency_score: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Search demand velocity score (0-100)",
    )
    intent_type: str = Field(
        default="commercial_investigation",
        description="Search intent classification",
    )
    verified: bool = Field(default=True, description="Whether query was verified by search suggest")


class PSEOPage(BaseModel):
    """Specification for a single high-intent programmatic landing page."""

    slug: str = Field(..., description="URL-friendly slug (e.g. socius-vs-soho-house)")
    axis: PSEOAxis = Field(..., description="Strategic axis")
    target_query: str = Field(..., description="Target search query")
    h1_title: str = Field(..., description="Page H1 title")
    demand_score: int = Field(
        default=75,
        ge=0,
        le=100,
        description="Search demand score (0-100)",
    )
    estimated_monthly_visits: int = Field(
        default=120,
        ge=0,
        description="Estimated monthly organic search visits",
    )
    answer_first_summary: str = Field(
        ...,
        description="40-60 word Answer-First summary for Princeton GEO extraction",
    )
    trojan_horse_teardown: str = Field(
        ...,
        description="Objective competitor breakdown delivering immediate value to eliminate bounce",
    )
    unique_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Empirical quantitative data points fulfilling the Data-Model Gate",
    )
    comparison_table_markdown: str = Field(..., description="Feature/pricing markdown matrix")
    html_content: str = Field(..., description="Complete standalone responsive HTML")
    json_ld_schema: str = Field(..., description="Valid FAQPage & SoftwareApplication JSON-LD schema")
    sibling_links: List[str] = Field(
        default_factory=list,
        description="URLs of 3-4 adjacent cluster pages in the hub-and-spoke graph",
    )
    parent_hub_url: str = Field(..., description="URL of the master hub/pillar index")
    verified_as_of: str = Field(
        default="Q1 2026",
        description="Freshness tag preventing ranking decay",
    )


class PSEOMatrixPackage(BaseModel):
    """Complete multi-axis programmatic SEO cluster bundle ready for edge deployment."""

    matrix_id: str = Field(
        default_factory=lambda: f"pseo-{uuid.uuid4().hex[:10]}",
        description="Unique matrix bundle identifier",
    )
    product_name: str = Field(..., description="Product brand name")
    pages: List[PSEOPage] = Field(..., description="Collection of unique programmatic landing pages")
    hub_page_html: str = Field(..., description="Master hub index page HTML")
    sitemap_xml: str = Field(..., description="Segmented XML sitemap (sitemap-pseo.xml)")
    reverse_proxy_config: Dict[str, str] = Field(
        default_factory=dict,
        description="Reverse proxy route definitions for Cloudflare Workers / Next.js",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC creation timestamp",
    )


class PSEODeploymentReport(BaseModel):
    """Outcome report for programmatic SEO cluster deployment."""

    matrix_id: str = Field(..., description="Cluster identifier")
    product_name: str = Field(..., description="Product brand name")
    total_pages_deployed: int = Field(..., description="Number of unique pages published")
    hub_url: str = Field(..., description="Master hub index URL")
    indexnow_submitted: bool = Field(default=False, description="Whether batch IndexNow ping succeeded")
    indexed_urls: List[str] = Field(default_factory=list, description="List of submitted URLs")
    reverse_proxy_mounted: bool = Field(default=False, description="Whether reverse proxy config was exported")
    deployed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC deployment timestamp",
    )
