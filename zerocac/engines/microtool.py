"""Autonomous Micro-Tool Architect (Engineering-as-Marketing Engine)."""

import logging
from pathlib import Path
import re
from typing import Optional
from pydantic import BaseModel, Field

from zerocac.ai.base import LLMMessage
from zerocac.ai.router import AIRouter
from zerocac.analyzer.models import ProductProfile
from zerocac.leads.injector import LeadCaptureInjector

logger = logging.getLogger(__name__)


class MicroToolConcept(BaseModel):
    """Architectural specification for a standalone lead-generation micro-tool."""

    tool_name: str = Field(description="Display title of the free micro-tool")
    slug: str = Field(description="URL-friendly directory or file slug")
    headline: str = Field(description="Catchy value hook for the tool header")
    core_functionality: str = Field(description="What interactive problem the tool solves locally")
    target_icp: str = Field(description="Specific persona this tool is engineered to attract")
    virality_hook: str = Field(description="Why users will share this or bookmark it on GitHub/HN")


class MicroToolPackage(BaseModel):
    """Complete deployment payload for a standalone interactive tool."""

    concept: MicroToolConcept
    html_content: str = Field(description="Complete standalone HTML/CSS/JS single-file application")
    deployment_instructions: str = Field(description="Quickstart steps to host on GitHub Pages or Vercel")


class MicroToolEngine:
    """Discovers, designs, and compiles standalone interactive web utilities."""

    def __init__(self, router: Optional[AIRouter] = None) -> None:
        """Initialize engine with multi-provider AI router."""
        self.router = router or AIRouter()

    async def generate_tool(
        self,
        profile: ProductProfile,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        dry_run: bool = False,
    ) -> MicroToolPackage:
        """Analyze product and generate a production-ready single-file web application."""
        if dry_run:
            return self._generate_dry_run_tool(profile)

        concept = await self._discover_concept(profile, provider_name, model)
        raw_html = await self._compile_html_application(profile, concept, provider_name, model)
        html_content = LeadCaptureInjector().inject_lead_form(raw_html)

        return MicroToolPackage(
            concept=concept,
            html_content=html_content,
            deployment_instructions=self._get_deployment_instructions(concept.slug),
        )

    async def _discover_concept(
        self, profile: ProductProfile, provider_name: Optional[str], model: Optional[str]
    ) -> MicroToolConcept:
        """Determine the most viral and high-conversion micro-tool concept for this product."""
        prompt = (
            f"Analyze this product and design an Engineering-as-Marketing free utility.\n"
            f"Product: {profile.product_name}\n"
            f"One-Liner: {profile.one_liner}\n"
            f"Core Problem: {profile.core_problem}\n"
            f"Target Audience: {profile.personas[0].persona_name if profile.personas else 'Founders'}\n\n"
            "Design a standalone interactive calculator, checker, or generator that solves one acute pain in 30 seconds for free.\n"
            "Return valid JSON matching:\n"
            "{\n"
            '  "tool_name": "<Catchy Tool Title>",\n'
            '  "slug": "<kebab-case-slug>",\n'
            '  "headline": "<Direct Benefit Hook>",\n'
            '  "core_functionality": "<What user inputs and what outputs calculate>",\n'
            '  "target_icp": "<Target Persona>",\n'
            '  "virality_hook": "<Reason users share on Hacker News / Reddit>"\n'
            "}"
        )
        messages = [
            LLMMessage(role="system", content="You are a principal growth engineer specializing in Engineering-as-Marketing. Design practical, zero-friction tools like HubSpot Website Grader or Canva Palette Generator."),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self.router.generate_text(messages=messages, provider_name=provider_name, model=model, temperature=0.3)
            data = self._parse_json_dict(resp.content)
            return MicroToolConcept(**data)
        except Exception as exc:
            logger.warning(f"Concept generation failed ({exc}), falling back to default CAC calculator.")
            return self._build_default_concept(profile)

    async def _compile_html_application(
        self,
        profile: ProductProfile,
        concept: MicroToolConcept,
        provider_name: Optional[str],
        model: Optional[str],
    ) -> str:
        """Generate a complete standalone, responsive HTML/CSS/JS file."""
        prompt = (
            f"Generate a single-file interactive HTML/CSS/JS web application for:\n"
            f"Tool Name: {concept.tool_name}\n"
            f"Headline: {concept.headline}\n"
            f"Functionality: {concept.core_functionality}\n"
            f"Parent Product: {profile.product_name} ({profile.one_liner})\n\n"
            "Requirements:\n"
            "1. Single file HTML with inline CSS in <style> and client-side JavaScript in <script>.\n"
            "2. Modern dark-mode responsive design (slate/zinc palette, accessible contrast, mobile-friendly).\n"
            "3. Interactive form with inputs (sliders, numbers, or textareas) and immediate dynamic output display upon user action.\n"
            "4. Zero external runtime dependencies (pure vanilla HTML5, CSS3, JS).\n"
            f"5. A high-converting footer card recommending {profile.product_name} with link to product site.\n"
            "Return ONLY the complete <!DOCTYPE html> document without conversational preamble."
        )
        messages = [
            LLMMessage(role="system", content="You are an expert frontend engineer. You build clean, accessible, zero-dependency HTML/JS utilities that run instantly in any browser."),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self.router.generate_text(messages=messages, provider_name=provider_name, model=model, temperature=0.2, max_tokens=3500)
            cleaned = self._clean_html_code(resp.content)
            if "<!DOCTYPE html>" in cleaned and "<script>" in cleaned:
                return cleaned
        except Exception as exc:
            logger.warning(f"HTML generation failed ({exc}), serving built-in template.")

        return self._generate_fallback_html(profile, concept)

    def export_tool(self, package: MicroToolPackage, destination_dir: Path) -> Path:
        """Save HTML tool to disk in a deployment-ready directory structure."""
        tool_dir = destination_dir / package.concept.slug
        tool_dir.mkdir(parents=True, exist_ok=True)

        html_file = tool_dir / "index.html"
        html_file.write_text(package.html_content, encoding="utf-8")

        readme_file = tool_dir / "README.md"
        readme_file.write_text(
            f"# {package.concept.tool_name}\n\n"
            f"> {package.concept.headline}\n\n"
            f"## Deployment\n{package.deployment_instructions}\n\n"
            f"Engineered with ZeroCAC for {package.concept.target_icp}.\n",
            encoding="utf-8",
        )
        return tool_dir

    def _clean_html_code(self, text: str) -> str:
        """Strip markdown code fence markers from generated HTML."""
        cleaned = re.sub(r"^```(?:html)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        return cleaned.strip()

    def _parse_json_dict(self, text: str) -> dict:
        """Parse JSON dictionary from model response."""
        import json

        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)

    def _build_default_concept(self, profile: ProductProfile) -> MicroToolConcept:
        """Default high-converting concept when dynamic discovery is unavailable."""
        return MicroToolConcept(
            tool_name=f"{profile.product_name} Ad Spend vs Organic CAC Calculator",
            slug="ad-spend-vs-organic-cac-calculator",
            headline="Calculate how much cash you lose every month to Google and Meta ad auctions.",
            core_functionality="Input current ad spend, CPC, and conversion rate to see exact true CAC and 12-month savings using organic distribution.",
            target_icp="Growth marketers and bootstrapped SaaS founders",
            virality_hook="Exposes the hidden financial bleed of paid ads with a 1-click shareable savings certificate.",
        )

    def _generate_dry_run_tool(self, profile: ProductProfile) -> MicroToolPackage:
        """Deterministic tool package for test suites and offline verification."""
        concept = self._build_default_concept(profile)
        raw_html = self._generate_fallback_html(profile, concept)
        html_content = LeadCaptureInjector().inject_lead_form(raw_html)
        return MicroToolPackage(
            concept=concept,
            html_content=html_content,
            deployment_instructions=self._get_deployment_instructions(concept.slug),
        )

    def _get_deployment_instructions(self, slug: str) -> str:
        """Produce 1-minute hosting instructions."""
        return (
            f"Quick Deployment Guide:\n"
            f"1. Vercel: Run `npx vercel deploy dist/tools/{slug}`\n"
            f"2. GitHub Pages: Push `dist/tools/{slug}/index.html` to a repository `gh-pages` branch.\n"
            f"3. Website Subfolder: Copy `index.html` into your public `public/tools/{slug}/` directory."
        )

    def _generate_fallback_html(
        self, profile: ProductProfile, concept: MicroToolConcept
    ) -> str:
        """Self-contained, accessible, responsive single-file calculator template."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{concept.tool_name}</title>
  <meta name="description" content="{concept.headline}">
  <style>
    :root {{
      --bg: #0b0f17;
      --card-bg: #131a29;
      --border: #1f2c42;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #10b981;
      --accent-glow: rgba(16, 185, 129, 0.2);
      --danger: #ef4444;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font);
      background-color: var(--bg);
      color: var(--text-main);
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 2rem 1rem;
    }}
    main {{
      width: 100%;
      max-width: 680px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    header {{ text-align: center; margin-bottom: 2rem; }}
    h1 {{ font-size: 1.6rem; color: #fff; margin-bottom: 0.5rem; }}
    p.lead {{ color: var(--text-muted); font-size: 0.95rem; line-height: 1.5; }}
    .form-group {{ margin-bottom: 1.25rem; }}
    label {{ display: block; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.4rem; }}
    input[type="number"], input[type="range"] {{
      width: 100%;
      background: #0d131f;
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 0.75rem 1rem;
      border-radius: 8px;
      font-size: 1rem;
      outline: none;
    }}
    input[type="number"]:focus {{ border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }}
    .results-card {{
      margin-top: 1.5rem;
      background: #0d131f;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.5rem;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      text-align: center;
    }}
    .stat-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }}
    .stat-val {{ font-size: 1.75rem; font-weight: 700; margin-top: 0.25rem; }}
    .val-danger {{ color: var(--danger); }}
    .val-success {{ color: var(--accent); }}
    .footer-bridge {{
      margin-top: 2rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      text-align: center;
    }}
    .footer-bridge p {{ font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem; }}
    .cta-btn {{
      display: inline-block;
      background: var(--accent);
      color: #042f22;
      font-weight: 700;
      text-decoration: none;
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      transition: transform 0.15s ease;
    }}
    .cta-btn:hover {{ transform: scale(1.02); }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{concept.tool_name}</h1>
      <p class="lead">{concept.headline}</p>
    </header>

    <section aria-label="Calculator Inputs">
      <div class="form-group">
        <label for="monthlySpend">Monthly Ad Budget (USD)</label>
        <input type="number" id="monthlySpend" value="3000" min="100" step="100">
      </div>
      <div class="form-group">
        <label for="costPerClick">Average Cost Per Click / CPC (USD)</label>
        <input type="number" id="costPerClick" value="3.50" min="0.10" step="0.10">
      </div>
      <div class="form-group">
        <label for="convRate">Landing Page Conversion Rate (%)</label>
        <input type="number" id="convRate" value="2.5" min="0.1" max="100" step="0.1">
      </div>
    </section>

    <section class="results-card" aria-label="Calculation Results">
      <div>
        <div class="stat-label">Your Current True CAC</div>
        <div class="stat-val val-danger" id="currentCac">$140.00</div>
      </div>
      <div>
        <div class="stat-label">12-Month Paid Ad Burn</div>
        <div class="stat-val val-danger" id="annualBurn">$36,000</div>
      </div>
      <div style="grid-column: span 2; border-top: 1px solid var(--border); padding-top: 1rem;">
        <div class="stat-label">Potential Savings with {profile.product_name}</div>
        <div class="stat-val val-success" id="organicSavings">$36,000 / yr</div>
      </div>
    </section>

    <footer class="footer-bridge">
      <p>Tired of paying the paid ad tax? <strong>{profile.product_name}</strong> provides {profile.one_liner}</p>
      <a href="https://github.com/PatelDeepB/zerocac" class="cta-btn" target="_blank" rel="noopener">Explore {profile.product_name} ($0 CAC)</a>
    </footer>
  </main>

  <script>
    function recalculate() {{
      const spend = parseFloat(document.getElementById('monthlySpend').value) || 0;
      const cpc = parseFloat(document.getElementById('costPerClick').value) || 0.1;
      const cr = (parseFloat(document.getElementById('convRate').value) || 1) / 100;

      const clicks = spend / cpc;
      const customers = clicks * cr;
      const cac = customers > 0 ? (spend / customers) : 0;
      const annual = spend * 12;

      document.getElementById('currentCac').innerText = '$' + cac.toFixed(2);
      document.getElementById('annualBurn').innerText = '$' + annual.toLocaleString();
      document.getElementById('organicSavings').innerText = '$' + annual.toLocaleString() + ' / yr';
    }}

    document.querySelectorAll('input').forEach(input => {{
      input.addEventListener('input', recalculate);
    }});
    recalculate();
  </script>
</body>
</html>
"""
