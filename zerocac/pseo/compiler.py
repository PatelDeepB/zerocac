"""Anti-thin-content page compiler rendering conversion-optimized HTML and GEO schema."""

import json
import logging
from typing import List, Optional
from zerocac.analyzer.models import ProductProfile
from zerocac.leads.injector import LeadCaptureInjector
from zerocac.pseo.generator import MatrixCandidate
from zerocac.pseo.models import PSEOPage

logger = logging.getLogger(__name__)


class PSEOPageCompiler:
    """Compiles validated blueprints into responsive HTML with Princeton GEO optimization."""

    def __init__(self, injector: Optional[LeadCaptureInjector] = None) -> None:
        """Initialize compiler with lead capture form injector."""
        self.injector = injector or LeadCaptureInjector()

    def compile_page(
        self,
        candidate: MatrixCandidate,
        profile: ProductProfile,
        tool_html: str,
        parent_hub_url: str = "/alternatives/",
        sibling_links: Optional[List[str]] = None,
    ) -> PSEOPage:
        """Compile complete standalone HTML document with schema, teardown, and live tool."""
        siblings = sibling_links or []
        answer_first = self._generate_answer_first(candidate, profile)
        json_schema = self._build_json_ld_schema(candidate, profile, answer_first)
        html = self._render_full_html(candidate, profile, answer_first, json_schema, tool_html, siblings, parent_hub_url)
        html_with_lead_gate = self.injector.inject_lead_form(html)

        demand_score = int(candidate.unique_metrics.get("demand_score", 75))
        est_visits = int(candidate.unique_metrics.get("estimated_monthly_visits", 120))

        return PSEOPage(
            slug=candidate.slug,
            axis=candidate.axis,
            target_query=candidate.query,
            h1_title=candidate.h1,
            demand_score=demand_score,
            estimated_monthly_visits=est_visits,
            answer_first_summary=answer_first,
            trojan_horse_teardown=candidate.teardown,
            unique_metrics=candidate.unique_metrics,
            comparison_table_markdown=candidate.comparison_md,
            html_content=html_with_lead_gate,
            json_ld_schema=json_schema,
            sibling_links=siblings,
            parent_hub_url=parent_hub_url,
            verified_as_of="Q1 2026",
        )

    def _generate_answer_first(self, candidate: MatrixCandidate, profile: ProductProfile) -> str:
        """Generate 40-60 word authoritative answer for Perplexity and Google SGE citation."""
        return (
            f"When evaluating {candidate.query}, practitioners prioritize unit efficiency and time-to-value. "
            f"{profile.product_name} provides a standalone, edge-deployed utility operating at $0 customer "
            f"acquisition cost, delivering 75% faster diagnostics and zero software dependency overhead "
            f"compared to traditional alternative offerings in 2026."
        )

    def _build_json_ld_schema(self, candidate: MatrixCandidate, profile: ProductProfile, answer_first: str) -> str:
        """Generate valid FAQPage and SoftwareApplication JSON-LD."""
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "SoftwareApplication",
                    "name": profile.product_name,
                    "applicationCategory": "BusinessApplication",
                    "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                },
                {
                    "@type": "FAQPage",
                    "mainEntity": [
                        {
                            "@type": "Question",
                            "name": f"How does {profile.product_name} compare on {candidate.query}?",
                            "acceptedAnswer": {"@type": "Answer", "text": answer_first},
                        }
                    ],
                },
            ],
        }
        return json.dumps(schema, indent=2)

    def _render_head(self, candidate: MatrixCandidate, profile: ProductProfile, answer_first: str, json_schema: str) -> str:
        """Render HTML head including styles, metadata, and JSON-LD structured schema."""
        return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{candidate.h1} | {profile.product_name}</title>
  <meta name="description" content="{answer_first[:155]}">
  <script type="application/ld+json">
{json_schema}
  </script>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #111827; background: #f9fafb; margin: 0; padding: 0; }}
    .container {{ max-width: 860px; margin: 2rem auto; padding: 2rem; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; }}
    .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; margin-bottom: 1rem; }}
    .geo-answer {{ background: #eff6ff; border-left: 4px solid #2563eb; padding: 1rem 1.25rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0; font-size: 1.05rem; }}
    .table-wrap {{ overflow-x: auto; margin: 2rem 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 0.75rem 1rem; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .mesh-links {{ margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #e5e7eb; font-size: 0.9rem; }}
  </style>
</head>"""

    def _render_full_html(
        self,
        candidate: MatrixCandidate,
        profile: ProductProfile,
        answer_first: str,
        json_schema: str,
        tool_html: str,
        siblings: List[str],
        parent_hub_url: str,
    ) -> str:
        """Assemble semantic, accessible HTML document."""
        sibling_items = "".join(f'<li><a href="{s}" style="color: #2563eb;">{s.split("/")[-1].replace("-", " ").title()}</a></li>' for s in siblings)
        table_html = self._markdown_table_to_html(candidate.comparison_md)
        head_html = self._render_head(candidate, profile, answer_first, json_schema)

        return f"""<!DOCTYPE html>
<html lang="en">
{head_html}
<body>
  <div class="container">
    <nav style="font-size: 0.85rem; color: #6b7280; margin-bottom: 1.5rem;">
      <a href="{parent_hub_url}" style="color: #6b7280; text-decoration: none;">&larr; Comparisons Index</a>
    </nav>
    <span class="badge">Verified for Q1 2026</span>
    <h1>{candidate.h1}</h1>
    
    <div class="geo-answer">
      <strong>Answer-First Executive Synthesis:</strong><br/>
      {answer_first}
    </div>

    <h2>1. Objective Market Analysis</h2>
    <p>{candidate.teardown}</p>

    <h2>2. Technical & Economic Comparison Matrix</h2>
    <div class="table-wrap">
      {table_html}
    </div>

    <h2>3. Interactive Diagnostic & ROI Evaluator</h2>
    <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.5rem; background: #fafafa;">
      <p style="margin-top: 0; color: #4b5563;">Use the live model below to calculate exact returns for your team:</p>
      {tool_html}
    </div>

    <div class="mesh-links">
      <h3>Related Comparison Clusters</h3>
      <ul>{sibling_items or "<li><a href='" + parent_hub_url + "'>Browse All Comparisons</a></li>"}</ul>
    </div>
  </div>
</body>
</html>"""

    def _markdown_table_to_html(self, md_table: str) -> str:
        """Convert standard markdown table to clean HTML table."""
        lines = [line.strip() for line in md_table.strip().split("\n") if line.strip()]
        if len(lines) < 3:
            return "<p>Comparison table loading...</p>"

        header_cols = [c.strip() for c in lines[0].split("|")[1:-1]]
        headers = "".join(f"<th>{h}</th>" for h in header_cols)

        rows = []
        for line in lines[2:]:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            row_html = "".join(f"<td>{c}</td>" for c in cols)
            rows.append(f"<tr>{row_html}</tr>")

        return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
