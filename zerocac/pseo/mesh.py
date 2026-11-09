"""Hub-and-spoke internal linking graph, segmented sitemaps, and reverse proxy routes."""

from datetime import datetime, timezone
import logging
from typing import Dict, List
from zerocac.pseo.models import PSEOPage

logger = logging.getLogger(__name__)


class InternalLinkingMesh:
    """Builds crawler-optimized bidirectional internal links and segmented XML sitemaps."""

    def build_mesh(
        self,
        pages: List[PSEOPage],
        base_url: str = "https://yourdomain.com",
    ) -> List[PSEOPage]:
        """Compute sibling links for every page to eliminate orphaned nodes."""
        all_slugs = [p.slug for p in pages]
        count = len(pages)

        for i, page in enumerate(pages):
            # Select 3 nearest circular neighbors
            siblings = []
            for offset in [1, 2, 3]:
                idx = (i + offset) % count
                if all_slugs[idx] != page.slug:
                    siblings.append(f"{base_url.rstrip('/')}/vs/{all_slugs[idx]}")
            page.sibling_links = siblings

            # Inject actual sibling HTML links into the page HTML
            sibling_items = "".join(
                f'<li><a href="{s}" style="color: #2563eb;">{s.split("/")[-1].replace("-", " ").title()}</a></li>'
                for s in siblings
            )
            mesh_nav = f'<nav class="internal-mesh" style="margin-top: 1rem;"><ul>{sibling_items}</ul></nav>'
            placeholder = f"<ul><li><a href='{page.parent_hub_url}'>Browse All Comparisons</a></li></ul>"
            if placeholder in page.html_content:
                page.html_content = page.html_content.replace(placeholder, mesh_nav)
            elif '<div class="mesh-links">' in page.html_content:
                page.html_content = page.html_content.replace(
                    '<div class="mesh-links">',
                    f'<div class="mesh-links">\n{mesh_nav}',
                )

        return pages

    def generate_hub_page(self, pages: List[PSEOPage], product_name: str) -> str:
        """Render master index pillar page linking to every programmatic asset."""
        cards = []
        for p in pages:
            cards.append(
                f'<div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; background: #ffffff;">'
                f'<h3 style="margin-top: 0;"><a href="/vs/{p.slug}" style="color: #2563eb; text-decoration: none;">{p.h1_title}</a></h3>'
                f'<p style="color: #4b5563; font-size: 0.9rem;">{p.answer_first_summary[:140]}...</p>'
                f'<span style="font-size: 0.75rem; background: #f3f4f6; padding: 0.2rem 0.5rem; border-radius: 4px;">{p.axis.value}</span>'
                f'</div>'
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{product_name} | Master Comparisons & Alternatives Index</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f9fafb; color: #111827; padding: 2rem; }}
    .container {{ max-width: 860px; margin: 0 auto; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{product_name} Solutions & Alternatives Directory</h1>
    <p>Comprehensive objective teardowns, regional guides, and interactive calculators.</p>
    <div style="margin-top: 2rem;">
      {''.join(cards)}
    </div>
  </div>
</body>
</html>"""

    def generate_sitemap_xml(self, pages: List[PSEOPage], base_url: str) -> str:
        """Compile search-engine-ready XML sitemap with lastmod timestamps."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        urls = [
            f"  <url>\n    <loc>{base_url.rstrip('/')}/vs/</loc>\n    <lastmod>{now}</lastmod>\n    <changefreq>weekly</changefreq>\n  </url>"
        ]
        for p in pages:
            full_url = f"{base_url.rstrip('/')}/vs/{p.slug}"
            urls.append(
                f"  <url>\n    <loc>{full_url}</loc>\n    <lastmod>{now}</lastmod>\n    <changefreq>weekly</changefreq>\n  </url>"
            )

        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls)
            + "\n</urlset>"
        )

    def generate_reverse_proxy_config(self, base_subdomain: str) -> Dict[str, str]:
        """Generate Cloudflare Worker and Next.js reverse proxy snippets."""
        worker_code = (
            f"export default {{\n"
            f"  async fetch(request) {{\n"
            f"    const url = new URL(request.url);\n"
            f"    if (url.pathname.startsWith('/vs/')) {{\n"
            f"      return fetch('https://{base_subdomain}.pages.dev' + url.pathname, request);\n"
            f"    }}\n"
            f"    return fetch(request);\n"
            f"  }}\n"
            f"}};\n"
        )
        return {
            "cloudflare_worker_js": worker_code,
            "next_config_rewrites": f"async rewrites() {{ return [{{ source: '/vs/:path*', destination: 'https://{base_subdomain}.pages.dev/vs/:path*' }}]; }}",
        }
