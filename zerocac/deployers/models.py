"""Data models for autonomous edge deployment and search indexation."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DeploymentProvider(str, Enum):
    """Supported edge deployment hosting targets."""

    CLOUDFLARE_PAGES = "cloudflare_pages"
    VERCEL = "vercel"
    LOCAL_PREVIEW = "local_preview"


class DeploymentArtifact(BaseModel):
    """Bundle containing compiled HTML and search assets ready for edge deployment."""

    project_slug: str = Field(..., description="Unique URL-safe identifier for project")
    title: str = Field(..., description="Title for deployment meta")
    html_content: str = Field(..., description="Compiled standalone HTML document")
    robots_txt: Optional[str] = Field(
        default=None,
        description="Search crawler directive file content",
    )
    sitemap_xml: Optional[str] = Field(
        default=None,
        description="XML sitemap for crawler discovery",
    )
    extra_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Supplementary file path to content mapping",
    )


class IndexNowPayload(BaseModel):
    """Payload schema for Bing and Yandex IndexNow API submission."""

    host: str = Field(..., description="Root domain of the host")
    key: str = Field(..., description="IndexNow verification key")
    key_location: Optional[str] = Field(
        default=None,
        description="Full URL location of key text file",
    )
    url_list: List[str] = Field(..., description="List of published URLs to index")


class DeploymentResult(BaseModel):
    """Outcome report for an edge deployment and indexation task."""

    success: bool = Field(..., description="Whether deployment finished successfully")
    provider: DeploymentProvider = Field(..., description="Edge host provider used")
    live_url: str = Field(..., description="Publicly accessible edge URL")
    deployment_id: str = Field(..., description="Unique identifier of edge deployment")
    indexnow_submitted: bool = Field(
        default=False,
        description="Whether URLs were submitted to search indexing APIs",
    )
    indexed_urls: List[str] = Field(
        default_factory=list,
        description="URLs successfully dispatched to search engines",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of deployment completion",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if deployment failed",
    )
