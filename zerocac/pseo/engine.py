"""Master Programmatic SEO Matrix Engine coordinating the multi-axis pipeline."""

import logging
from typing import Optional
from zerocac.analyzer.models import ProductProfile
from zerocac.pseo.compiler import PSEOPageCompiler
from zerocac.pseo.generator import PSEOMatrixGenerator
from zerocac.pseo.mesh import InternalLinkingMesh
from zerocac.pseo.models import PSEOMatrixPackage

logger = logging.getLogger(__name__)


class PSEOMatrixEngine:
    """End-to-end engine synthesizing multi-axis programmatic landing page clusters."""

    def __init__(
        self,
        generator: Optional[PSEOMatrixGenerator] = None,
        compiler: Optional[PSEOPageCompiler] = None,
        mesh: Optional[InternalLinkingMesh] = None,
    ) -> None:
        """Initialize engine with modular generators and compilers."""
        self.generator = generator or PSEOMatrixGenerator()
        self.compiler = compiler or PSEOPageCompiler()
        self.mesh = mesh or InternalLinkingMesh()

    async def generate_matrix(
        self,
        profile: ProductProfile,
        tool_html: str,
        target_count: int = 15,
        base_url: str = "https://yourdomain.com",
        dry_run: bool = False,
    ) -> PSEOMatrixPackage:
        """Execute full pSEO synthesis: candidates, compilation, linking mesh, and sitemaps."""
        candidates = await self.generator.generate_candidates(profile, target_count=target_count, dry_run=dry_run)
        compiled_pages = [
            self.compiler.compile_page(c, profile, tool_html, parent_hub_url=f"{base_url.rstrip('/')}/vs/")
            for c in candidates
        ]

        # Build bidirectional internal link mesh
        meshed_pages = self.mesh.build_mesh(compiled_pages, base_url=base_url)
        hub_html = self.mesh.generate_hub_page(meshed_pages, profile.product_name)
        sitemap_xml = self.mesh.generate_sitemap_xml(meshed_pages, base_url=base_url)
        subdomain = f"{profile.product_name.lower().replace(' ', '-')}-pseo"
        reverse_proxy_cfg = self.mesh.generate_reverse_proxy_config(subdomain)

        return PSEOMatrixPackage(
            product_name=profile.product_name,
            pages=meshed_pages,
            hub_page_html=hub_html,
            sitemap_xml=sitemap_xml,
            reverse_proxy_config=reverse_proxy_cfg,
        )
