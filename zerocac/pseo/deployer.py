"""Batch deployer publishing complete pSEO clusters and dispatching IndexNow."""

import logging
from typing import Optional
from urllib.parse import urlparse

from zerocac.deployers.cloudflare import CloudflarePagesDeployer
from zerocac.deployers.indexer import IndexNowClient
from zerocac.deployers.models import DeploymentArtifact, DeploymentProvider
from zerocac.pseo.models import PSEODeploymentReport, PSEOMatrixPackage

logger = logging.getLogger(__name__)


class PSEOBatchDeployer:
    """Publishes complete programmatic matrices to edge hosting and triggers IndexNow."""

    def __init__(
        self,
        cloudflare_deployer: Optional[CloudflarePagesDeployer] = None,
        indexnow_client: Optional[IndexNowClient] = None,
    ) -> None:
        """Initialize deployer with edge hosting and search indexing clients."""
        self.cloudflare_deployer = cloudflare_deployer or CloudflarePagesDeployer()
        self.indexnow_client = indexnow_client or IndexNowClient()

    async def deploy_matrix(
        self,
        package: PSEOMatrixPackage,
        provider: DeploymentProvider = DeploymentProvider.CLOUDFLARE_PAGES,
        dry_run: bool = False,
    ) -> PSEODeploymentReport:
        """Deploy all programmatic pages, hub index, and sitemap to edge."""
        project_slug = f"{package.product_name.lower().replace(' ', '-')}-pseo"
        extra_files = {"sitemap-pseo.xml": package.sitemap_xml}

        # Mount each page under /vs/{slug}/index.html
        for p in package.pages:
            extra_files[f"vs/{p.slug}/index.html"] = p.html_content

        artifact = DeploymentArtifact(
            project_slug=project_slug,
            title=f"{package.product_name} Programmatic Directory",
            html_content=package.hub_page_html,
            sitemap_xml=package.sitemap_xml,
            robots_txt="User-agent: *\nAllow: /\nSitemap: /sitemap-pseo.xml\n",
            extra_files=extra_files,
        )

        deploy_res = await self.cloudflare_deployer.deploy(artifact, dry_run=dry_run)
        live_base = deploy_res.live_url or f"https://{project_slug}.pages.dev"
        hub_url = f"{live_base.rstrip('/')}/vs/"

        # Collect all generated URLs for IndexNow batch submission
        urls_to_index = [hub_url] + [f"{live_base.rstrip('/')}/vs/{p.slug}" for p in package.pages]
        parsed = urlparse(live_base)
        host = parsed.netloc or f"{project_slug}.pages.dev"

        indexnow_ok = await self.indexnow_client.submit_urls(host, urls_to_index, dry_run=dry_run)

        return PSEODeploymentReport(
            matrix_id=package.matrix_id,
            product_name=package.product_name,
            total_pages_deployed=len(package.pages),
            hub_url=hub_url,
            indexnow_submitted=indexnow_ok,
            indexed_urls=urls_to_index,
            reverse_proxy_mounted=bool(package.reverse_proxy_config),
        )
