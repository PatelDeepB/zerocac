"""FastAPI router for edge deployment and search indexing endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from zerocac.deployers.manager import EdgeDeploymentManager
from zerocac.deployers.models import (
    DeploymentArtifact,
    DeploymentProvider,
    DeploymentResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deploy", tags=["Deployment"])


class DeployApiRequest(BaseModel):
    """Payload to deploy an HTML tool or GEO asset to edge infrastructure."""

    project_slug: str = Field(..., description="Unique slug for edge project")
    title: str = Field(default="Edge Deployment", description="Asset display title")
    html_content: str = Field(..., description="Raw HTML content to host")
    robots_txt: Optional[str] = Field(default=None, description="Robots.txt contents")
    sitemap_xml: Optional[str] = Field(default=None, description="Sitemap.xml contents")
    provider: DeploymentProvider = Field(
        default=DeploymentProvider.CLOUDFLARE_PAGES,
        description="Target edge hosting provider",
    )
    enable_indexing: bool = Field(
        default=True,
        description="Whether to ping IndexNow on deployment",
    )
    dry_run: bool = Field(
        default=False,
        description="Simulate deployment without contacting remote APIs",
    )


@router.post("", response_model=DeploymentResult, status_code=status.HTTP_200_OK)
async def deploy_artifact(payload: DeployApiRequest) -> DeploymentResult:
    """Deploy HTML asset to edge hosting and notify search indexing networks."""
    if not payload.html_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HTML content cannot be empty",
        )

    artifact = DeploymentArtifact(
        project_slug=payload.project_slug,
        title=payload.title,
        html_content=payload.html_content,
        robots_txt=payload.robots_txt,
        sitemap_xml=payload.sitemap_xml,
    )

    manager = EdgeDeploymentManager()
    result = await manager.deploy_and_index(
        artifact=artifact,
        provider=payload.provider,
        enable_indexing=payload.enable_indexing,
        dry_run=payload.dry_run,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "Deployment failed",
        )

    return result
