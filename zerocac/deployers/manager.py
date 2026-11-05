"""Unified edge deployment manager orchestrating hosting and search indexing."""

import logging
from typing import Optional
from urllib.parse import urlparse

from zerocac.deployers.cloudflare import CloudflarePagesDeployer
from zerocac.deployers.indexer import IndexNowClient, SitemapPinger
from zerocac.deployers.models import (
    DeploymentArtifact,
    DeploymentProvider,
    DeploymentResult,
)

logger = logging.getLogger(__name__)


class EdgeDeploymentManager:
    """Coordinates edge deployment and automated immediate search indexation."""

    def __init__(
        self,
        cloudflare_deployer: Optional[CloudflarePagesDeployer] = None,
        indexnow_client: Optional[IndexNowClient] = None,
        sitemap_pinger: Optional[SitemapPinger] = None,
    ) -> None:
        """Initialize orchestrator with modular deployers and indexers."""
        self.cloudflare_deployer = cloudflare_deployer or CloudflarePagesDeployer()
        self.indexnow_client = indexnow_client or IndexNowClient()
        self.sitemap_pinger = sitemap_pinger or SitemapPinger()

    async def deploy_and_index(
        self,
        artifact: DeploymentArtifact,
        provider: DeploymentProvider = DeploymentProvider.CLOUDFLARE_PAGES,
        enable_indexing: bool = True,
        dry_run: bool = False,
    ) -> DeploymentResult:
        """Deploy web artifact and ping search engines immediately upon publication."""
        # 1. Execute edge deployment
        if provider == DeploymentProvider.CLOUDFLARE_PAGES:
            result = await self.cloudflare_deployer.deploy(artifact=artifact, dry_run=dry_run)
        else:
            result = await self.cloudflare_deployer.deploy(artifact=artifact, dry_run=True)

        if not result.success:
            logger.error("Deployment failed: %s", result.error_message)
            return result

        # 2. Trigger instant search indexation if enabled
        if enable_indexing and result.live_url:
            parsed = urlparse(result.live_url)
            host = parsed.netloc or f"{artifact.project_slug}.pages.dev"
            urls_to_index = [result.live_url]

            indexnow_ok = await self.indexnow_client.submit_urls(
                host=host,
                urls=urls_to_index,
                dry_run=dry_run,
            )
            result.indexnow_submitted = indexnow_ok
            if indexnow_ok:
                result.indexed_urls = urls_to_index

            # Ping sitemap if generated
            if artifact.sitemap_xml:
                sitemap_url = f"{result.live_url.rstrip('/')}/sitemap.xml"
                await self.sitemap_pinger.ping_search_engines(sitemap_url, dry_run=dry_run)

        return result
