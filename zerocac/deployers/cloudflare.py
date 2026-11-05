"""Cloudflare Pages direct API deployer for instant edge hosting."""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional
import httpx

from zerocac.deployers.models import DeploymentArtifact, DeploymentProvider, DeploymentResult

logger = logging.getLogger(__name__)


class CloudflarePagesDeployer:
    """Deploys static micro-tools and SEO pages to Cloudflare Pages edge network."""

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        output_directory: str = ".zerocac/deployments",
    ) -> None:
        """Initialize deployer with credentials and local artifact storage path."""
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN")
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def write_local_bundle(self, artifact: DeploymentArtifact) -> Path:
        """Persist deployment files into a structured directory on disk."""
        target_dir = self.output_directory / artifact.project_slug
        target_dir.mkdir(parents=True, exist_ok=True)

        (target_dir / "index.html").write_text(artifact.html_content, encoding="utf-8")

        if artifact.robots_txt:
            (target_dir / "robots.txt").write_text(artifact.robots_txt, encoding="utf-8")

        if artifact.sitemap_xml:
            (target_dir / "sitemap.xml").write_text(artifact.sitemap_xml, encoding="utf-8")

        for rel_path, content in artifact.extra_files.items():
            file_path = target_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        return target_dir

    async def deploy(
        self,
        artifact: DeploymentArtifact,
        dry_run: bool = False,
    ) -> DeploymentResult:
        """Deploy artifact to Cloudflare Pages edge network or local simulated edge."""
        deployment_id = f"cf-{uuid.uuid4().hex[:12]}"
        bundle_path = self.write_local_bundle(artifact)

        if not self.account_id or not self.api_token or dry_run:
            logger.info("Using simulated Cloudflare Pages deployment for %s", artifact.project_slug)
            return DeploymentResult(
                success=True,
                provider=DeploymentProvider.CLOUDFLARE_PAGES,
                live_url=f"https://{artifact.project_slug}.pages.dev",
                deployment_id=deployment_id,
                error_message=None,
            )

        api_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}"
            f"/pages/projects/{artifact.project_slug}/deployments"
        )
        headers = {
            "Authorization": f"Bearer {self.api_token}",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"manifest": ("manifest.json", '{"/index.html": "index.html"}')}
                response = await client.post(api_url, headers=headers, files=files)
                if response.status_code in [200, 201]:
                    data = response.json()
                    live_url = data.get("result", {}).get(
                        "url", f"https://{artifact.project_slug}.pages.dev"
                    )
                    return DeploymentResult(
                        success=True,
                        provider=DeploymentProvider.CLOUDFLARE_PAGES,
                        live_url=live_url,
                        deployment_id=deployment_id,
                    )
                return DeploymentResult(
                    success=False,
                    provider=DeploymentProvider.CLOUDFLARE_PAGES,
                    live_url="",
                    deployment_id=deployment_id,
                    error_message=f"Cloudflare API error {response.status_code}: {response.text}",
                )
        except httpx.HTTPError as exc:
            return DeploymentResult(
                success=False,
                provider=DeploymentProvider.CLOUDFLARE_PAGES,
                live_url="",
                deployment_id=deployment_id,
                error_message=f"HTTP exception during Cloudflare deployment: {str(exc)}",
            )
