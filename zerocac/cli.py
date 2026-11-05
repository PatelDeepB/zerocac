"""Typer-powered command-line interface for ZeroCAC autonomous marketing."""

import asyncio
import json
from pathlib import Path
from typing import Optional
import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from zerocac import __version__
from zerocac.ai.router import AIRouter
from zerocac.analyzer.engine import ProductAnalyzer
from zerocac.analyzer.models import ProductProfile
from zerocac.config import get_settings
from zerocac.crawler.scraper import URLScraper
from zerocac.engines.aeo import AEOEngine
from zerocac.engines.directory import DirectoryEngine
from zerocac.engines.geo_optimizer import PrincetonGEOEngine
from zerocac.engines.microtool import MicroToolEngine
from zerocac.engines.narrative import ViralNarrativeEngine
from zerocac.engines.radar import LiveIntentRadarEngine
from zerocac.engines.sniper import IntentSniperEngine
from zerocac.engines.virality_loop import ViralityEngine
from zerocac.deployers.manager import EdgeDeploymentManager
from zerocac.deployers.models import DeploymentArtifact, DeploymentProvider

app = typer.Typer(
    name="zerocac",
    help="ZeroCAC: Autonomous AI Marketing Agent ($0 Customer Acquisition Cost)",
    add_completion=False,
)
console = Console()


@app.command()
def version() -> None:
    """Display ZeroCAC version and supported frontier 2026 AI models."""
    console.print(
        Panel(
            f"[bold green]ZeroCAC v{__version__}[/bold green]\n"
            "Autonomous AI Marketing Agent that scales products to $0 CAC.\n\n"
            "[bold cyan]Supported Frontier AI Models (2026):[/bold cyan]\n"
            "- OpenAI: GPT-6 Astra, GPT-6.1 Luna, gpt-oss-120b\n"
            "- Google: Gemini 4 Argon, Gemini 3.8 Flash\n"
            "- Anthropic: Claude Opus 5.5, Claude Sonnet 5.5\n"
            "- NVIDIA: Nemotron 3 Ultra (550B MoE), Nemotron 3.5 Super VL\n"
            "- DeepSeek: DeepSeek-V4.1-Flash, DeepSeek-R1",
            title="System Info",
            border_style="green",
        )
    )


@app.command()
def analyze(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
) -> None:
    """Analyze a product landing page and extract strategic positioning and ICP personas."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    _print_profile_panel(profile)


@app.command()
def snipe(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    count: int = typer.Option(3, "--count", "-c", help="Number of opportunities to generate"),
) -> None:
    """Identify buyer pain queries on Reddit, Hacker News, and X and draft authentic responses."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    sniper_engine = IntentSniperEngine()
    campaign = asyncio.run(
        sniper_engine.generate_opportunities(profile, count=count, provider_name=provider)
    )

    table = Table(title=f"Intent Sniper Opportunities for {profile.product_name}")
    table.add_column("Platform", style="cyan", width=12)
    table.add_column("Community", style="green", width=15)
    table.add_column("Intent", justify="right", style="magenta", width=8)
    table.add_column("Question / Pain Statement", style="white", width=35)
    table.add_column("Drafted Authentic Response", style="dim", width=40)

    for opp in campaign.opportunities:
        table.add_row(
            opp.platform,
            opp.community,
            f"{opp.intent_score}/100",
            opp.thread_title,
            opp.draft_response,
        )
    console.print(table)


@app.command()
def aeo(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
) -> None:
    """Generate Answer Engine Optimization comparison pages and FAQ schema for AI crawlers."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    aeo_engine = AEOEngine()
    package = asyncio.run(aeo_engine.generate_package(profile, provider_name=provider))

    for page in package.comparison_pages:
        console.print(
            Panel(
                f"[bold cyan]Slug:[/bold cyan] {page.slug}\n"
                f"[bold green]Title:[/bold green] {page.page_title}\n\n"
                f"{page.markdown_content[:600]}...",
                title=f"AEO Target: vs {page.target_competitor}",
                border_style="blue",
            )
        )


@app.command()
def viral(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
) -> None:
    """Generate X build-in-public thread, LinkedIn carousel slides, and 60s video script."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    narrative_engine = ViralNarrativeEngine()
    campaign = asyncio.run(narrative_engine.generate_campaign(profile, provider_name=provider))

    console.print("\n[bold cyan]X Build-In-Public Thread:[/bold cyan]")
    for tweet in campaign.x_thread:
        console.print(f"[white]{tweet}[/white]\n")

    console.print("\n[bold magenta]60-Second Video Script:[/bold magenta]")
    console.print(Panel(campaign.video_script_60s, title="TikTok / Shorts Script", border_style="yellow"))


@app.command()
def directories(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
) -> None:
    """Output tailored submission packages for 30+ software directories."""
    profile = asyncio.run(_run_analysis(url, description, None, name))
    dir_engine = DirectoryEngine()
    package = dir_engine.generate_package(profile)

    table = Table(title=f"Directory Submissions for {profile.product_name}")
    table.add_column("Directory", style="cyan")
    table.add_column("DA", justify="right", style="green")
    table.add_column("Tagline (<= 60 chars)", style="white")
    table.add_column("Submission URL", style="blue")

    for item in package.listings:
        table.add_row(item.directory_name, str(item.domain_authority), item.tagline, item.submission_url)
    console.print(table)


@app.command()
def radar(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    keywords: Optional[str] = typer.Option(None, "--keywords", "-k", help="Comma-separated custom search terms"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with deterministic simulated feeds"),
) -> None:
    """Scan real-time Reddit, Hacker News, and GitHub streams for high-intent pain points."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    kw_list = [k.strip() for k in keywords.split(",")] if keywords else None

    console.print(f"[bold cyan]Scanning live intent radar for {profile.product_name}...[/bold cyan]")
    engine = LiveIntentRadarEngine()
    report = asyncio.run(engine.scan_live_feeds(profile, keywords=kw_list, dry_run=dry_run))

    table = Table(title=f"Live Intent Radar Signals ({report.signals_found} Found)")
    table.add_column("Source", style="bold yellow")
    table.add_column("Score", style="bold green", justify="center")
    table.add_column("Discussion / Post", style="white")
    table.add_column("Pain Category", style="magenta")
    table.add_column("Recommended Authentic Reply", style="dim")

    for sig in report.high_intent_signals:
        table.add_row(
            sig.source.value,
            str(sig.intent_score),
            f"{sig.title}\n[link={sig.url}]{sig.url}[/link]",
            sig.pain_category,
            sig.recommended_reply,
        )

    console.print(table)
    console.print(Panel(report.action_plan, title="Radar Action Protocol", border_style="green"))


@app.command()
def microtool(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    output_dir: Path = typer.Option(Path("dist_tools"), "--out", "-o", help="Target output folder"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with built-in instant templates"),
) -> None:
    """Generate interactive single-file micro-tools (Engineering-as-Marketing)."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    console.print(f"[bold cyan]Engineering interactive micro-tool for {profile.product_name}...[/bold cyan]")

    engine = MicroToolEngine()
    package = asyncio.run(engine.generate_tool(profile, provider_name=provider, dry_run=dry_run))
    exported_dir = engine.export_tool(package, output_dir)

    console.print(
        Panel(
            f"[bold green]Tool Generated:[/bold green] {package.concept.tool_name}\n"
            f"[bold cyan]Headline:[/bold cyan] {package.concept.headline}\n"
            f"[bold yellow]Core Utility:[/bold yellow] {package.concept.core_functionality}\n"
            f"[bold magenta]Virality Hook:[/bold magenta] {package.concept.virality_hook}\n\n"
            f"[bold white]Saved To:[/bold white] {exported_dir.resolve()}\n\n"
            f"[bold blue]Deployment Guide:[/bold blue]\n{package.deployment_instructions}",
            title="Engineering-as-Marketing Asset Ready",
            border_style="green",
        )
    )


@app.command()
def geo(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with deterministic benchmarks"),
) -> None:
    """Generate Princeton GEO citation copy and robots.txt rules for AI search engines."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    console.print(f"[bold cyan]Engineering Princeton GEO assets for {profile.product_name}...[/bold cyan]")

    engine = PrincetonGEOEngine()
    package = asyncio.run(engine.generate_package(profile, provider_name=provider, dry_run=dry_run))

    for idx, asset in enumerate(package.assets, start=1):
        stats_formatted = "\n".join(f"- {s}" for s in asset.statistical_evidence)
        prompts_formatted = "\n".join(f"- {p}" for p in asset.citation_verification_prompts)
        console.print(
            Panel(
                f"[bold cyan]Target Query:[/bold cyan] {asset.target_query}\n\n"
                f"[bold green]Answer-First ({asset.word_count} words):[/bold green]\n{asset.answer_first_definition}\n\n"
                f"[bold yellow]Statistical Evidence:[/bold yellow]\n{stats_formatted}\n\n"
                f"[bold magenta]Verification Prompts for Perplexity & SearchGPT:[/bold magenta]\n{prompts_formatted}",
                title=f"GEO Citation Asset #{idx}",
                border_style="cyan",
            )
        )
    console.print(Panel(package.robots_txt_rules, title="Permissive robots.txt for AI Crawlers", border_style="green"))
    console.print(Panel(package.bing_webmaster_guidelines, title="Bing / ChatGPT Search Action Plan", border_style="yellow"))


@app.command()
def virality(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with deterministic loop specifications"),
) -> None:
    """Generate product-led viral loops, embeddable badges, and social artifacts."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    console.print(f"[bold cyan]Engineering product-led virality for {profile.product_name}...[/bold cyan]")

    engine = ViralityEngine()
    package = asyncio.run(engine.generate_package(profile, provider_name=provider, dry_run=dry_run))

    console.print(
        Panel(
            f"[bold cyan]K-Factor Strategy:[/bold cyan]\n{package.k_factor_strategy}\n\n"
            f"[bold green]Viral Loop Mechanics:[/bold green]\n" + "\n".join(package.viral_loop_mechanics) + "\n\n"
            f"[bold yellow]Markdown Badge (for GitHub README):[/bold yellow]\n{package.markdown_badge}\n\n"
            f"[bold magenta]HTML Footer Snippet:[/bold magenta]\n{package.html_badge_snippet}",
            title="Product-Led Virality & Distribution Assets",
            border_style="green",
        )
    )



@app.command()
def deploy(
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="Path to standalone HTML tool to deploy"),
    slug: Optional[str] = typer.Option(None, "--slug", "-s", help="Unique project slug"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Deployment display title"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Product URL to generate and deploy micro-tool for"),
    provider: str = typer.Option("cloudflare_pages", "--provider", "-p", help="Provider: cloudflare_pages or local_preview"),
    no_index: bool = typer.Option(False, "--no-index", help="Skip IndexNow instant search indexing"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run in simulated dry-run mode"),
) -> None:
    """Deploy a generated micro-tool or GEO page to live edge hosting with instant search indexing."""
    html_content = ""
    project_slug = slug or "zerocac-asset"
    display_title = title or project_slug.replace("-", " ").title()

    if file_path:
        path_obj = Path(file_path)
        if not path_obj.exists():
            console.print(f"[bold red]Error: File not found at {file_path}[/bold red]")
            raise typer.Exit(code=1)
        html_content = path_obj.read_text(encoding="utf-8")
        if not slug:
            project_slug = path_obj.stem
            display_title = title or project_slug.replace("-", " ").title()
    elif url:
        console.print(f"[bold cyan]Generating micro-tool for {url} to deploy...[/bold cyan]")
        profile = asyncio.run(_run_analysis(url=url, desc=None, provider=None))
        engine = MicroToolEngine()
        pkg = asyncio.run(engine.generate_tool(profile, dry_run=dry_run))
        html_content = pkg.standalone_html
        project_slug = slug or pkg.slug
        display_title = title or pkg.tool_title
    else:
        console.print("[bold red]Error: Either --file or --url must be provided.[/bold red]")
        raise typer.Exit(code=1)

    artifact = DeploymentArtifact(
        project_slug=project_slug,
        title=display_title,
        html_content=html_content,
        robots_txt="User-agent: *\nAllow: /\n",
        sitemap_xml=f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>https://{project_slug}.pages.dev/</loc></url>\n</urlset>',
    )

    console.print(f"[bold yellow]Deploying {project_slug} to edge ({provider})...[/bold yellow]")
    manager = EdgeDeploymentManager()
    target_provider = (
        DeploymentProvider.CLOUDFLARE_PAGES
        if provider == "cloudflare_pages"
        else DeploymentProvider.LOCAL_PREVIEW
    )
    result = asyncio.run(
        manager.deploy_and_index(
            artifact=artifact,
            provider=target_provider,
            enable_indexing=not no_index,
            dry_run=dry_run,
        )
    )

    if not result.success:
        console.print(f"[bold red]Deployment failed:[/bold red] {result.error_message}")
        raise typer.Exit(code=1)

    table = Table(title="Autonomous Edge Deployment Summary", border_style="green")
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="green")
    table.add_row("Deployment ID", result.deployment_id)
    table.add_row("Live Edge URL", result.live_url)
    table.add_row("Hosting Target", result.provider.value)
    table.add_row(
        "IndexNow Search Ping",
        "[bold green]Dispatched[/bold green]" if result.indexnow_submitted else "[dim]Skipped[/dim]",
    )
    table.add_row("Indexed URLs", ", ".join(result.indexed_urls) or "None")
    console.print(table)


@app.command()
def run(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    output_dir: Path = typer.Option(Path("dist_campaign"), "--out", "-o", help="Output directory"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    velocity: bool = typer.Option(False, "--velocity", "-v", help="Include real-time Live Radar, Micro-Tools, GEO, and Virality"),
) -> None:
    """Execute all organic growth engines and export assets to disk."""
    profile = asyncio.run(_run_analysis(url, description, provider, name))
    console.print(f"[bold yellow]Executing organic distribution engines for {profile.product_name}...[/bold yellow]")

    router = AIRouter()
    sniper_pkg = asyncio.run(IntentSniperEngine(router).generate_opportunities(profile, count=3, provider_name=provider))
    aeo_pkg = asyncio.run(AEOEngine(router).generate_package(profile, provider_name=provider))
    viral_pkg = asyncio.run(ViralNarrativeEngine(router).generate_campaign(profile, provider_name=provider))
    dir_pkg = DirectoryEngine().generate_package(profile)

    radar_pkg = None
    tool_pkg = None
    geo_pkg = None
    virality_pkg = None
    if velocity:
        console.print("[bold cyan]Scanning live feeds via Live Intent Radar...[/bold cyan]")
        radar_engine = LiveIntentRadarEngine(router)
        radar_pkg = asyncio.run(radar_engine.scan_live_feeds(profile, dry_run=False))

        console.print("[bold cyan]Compiling interactive micro-tool application...[/bold cyan]")
        tool_engine = MicroToolEngine(router)
        tool_pkg = asyncio.run(tool_engine.generate_tool(profile, provider_name=provider, dry_run=False))

        console.print("[bold cyan]Generating Princeton GEO citation assets...[/bold cyan]")
        geo_engine = PrincetonGEOEngine(router)
        geo_pkg = asyncio.run(geo_engine.generate_package(profile, provider_name=provider, dry_run=False))

        console.print("[bold cyan]Synthesizing product-led virality loop...[/bold cyan]")
        virality_engine = ViralityEngine(router)
        virality_pkg = asyncio.run(virality_engine.generate_package(profile, provider_name=provider, dry_run=False))

    output_dir.mkdir(parents=True, exist_ok=True)
    _save_campaign_artifacts(output_dir, profile, sniper_pkg, aeo_pkg, viral_pkg, dir_pkg, radar_pkg, tool_pkg, geo_pkg, virality_pkg)
    console.print(f"[bold green]Successfully exported complete campaign to: {output_dir.resolve()}[/bold green]")


@app.command()
def serve(
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Bind host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Bind port"),
) -> None:
    """Launch the ZeroCAC local FastAPI web control dashboard."""
    settings = get_settings()
    target_host = host or settings.host
    target_port = port or settings.port
    console.print(f"[bold green]Starting ZeroCAC Dashboard at http://{target_host}:{target_port}[/bold green]")
    uvicorn.run("zerocac.web.app:app", host=target_host, port=target_port, reload=False)


# Helpers
def _infer_product_name(url: Optional[str], desc: Optional[str], name: Optional[str]) -> str:
    """Infer or clean the product title."""
    if name and name.strip():
        return name.strip()
    if desc:
        candidate = desc.split("-")[0].split(":")[0].strip()
        if candidate and 1 < len(candidate) < 30:
            return candidate
    if url:
        clean_url = url.replace("https://", "").replace("http://", "").split("/")[0]
        domain_parts = clean_url.split(".")
        if len(domain_parts) >= 2:
            base = domain_parts[1] if domain_parts[0] in ("www", "app") else domain_parts[0]
            if base:
                return base.capitalize()
    return "Product"


async def _run_analysis(
    url: Optional[str],
    desc: Optional[str],
    provider: Optional[str],
    name: Optional[str] = None,
) -> ProductProfile:
    """Orchestrate crawler and analyzer."""
    if not url and not desc:
        console.print("[bold red]Error: Either a URL or --desc must be provided.[/bold red]")
        raise typer.Exit(code=1)

    inferred_name = _infer_product_name(url, desc, name)
    analyzer = ProductAnalyzer()
    if url:
        try:
            raw = await URLScraper().crawl_url(url)
            return await analyzer.analyze_raw_data(raw, provider_name=provider)
        except Exception:
            return await analyzer.analyze_text(
                description=f"Product at {url}",
                product_name=inferred_name,
                provider_name=provider,
            )
    return await analyzer.analyze_text(
        description=desc or "",
        product_name=inferred_name,
        provider_name=provider,
    )


def _print_profile_panel(profile: ProductProfile) -> None:
    """Render structured product profile to console."""
    personas_str = "\n".join(f"- {p.persona_name}: {p.core_pain_point}" for p in profile.personas)
    competitors_str = "\n".join(f"- vs {g.competitor_name}: {g.our_advantage}" for g in profile.competitor_gaps)
    console.print(
        Panel(
            f"[bold cyan]Product:[/bold cyan] {profile.product_name} ({profile.category})\n"
            f"[bold green]One-Liner:[/bold green] {profile.one_liner}\n\n"
            f"[bold yellow]Unique Value Proposition:[/bold yellow]\n{profile.unique_value_proposition}\n\n"
            f"[bold magenta]Target Personas:[/bold magenta]\n{personas_str}\n\n"
            f"[bold blue]Competitor Exploitation Angles:[/bold blue]\n{competitors_str}",
            title="Strategic Intelligence Profile",
            border_style="green",
        )
    )


def _save_campaign_artifacts(
    out_dir: Path,
    profile: ProductProfile,
    sniper: any,
    aeo: any,
    viral: any,
    directory: any,
    radar: any = None,
    tool: any = None,
    geo: any = None,
    virality: any = None,
) -> None:
    """Write generated assets to organized files."""
    (out_dir / "profile.json").write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "sniper_campaign.json").write_text(sniper.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "viral_campaign.json").write_text(viral.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "directories.json").write_text(directory.model_dump_json(indent=2), encoding="utf-8")

    if radar:
        (out_dir / "radar_signals.json").write_text(radar.model_dump_json(indent=2), encoding="utf-8")

    if tool:
        tools_dir = out_dir / "micro_tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        MicroToolEngine().export_tool(tool, tools_dir)

    if geo:
        geo_dir = out_dir / "geo_assets"
        geo_dir.mkdir(parents=True, exist_ok=True)
        (geo_dir / "robots.txt").write_text(geo.robots_txt_rules, encoding="utf-8")
        (geo_dir / "geo_package.json").write_text(geo.model_dump_json(indent=2), encoding="utf-8")

    if virality:
        v_dir = out_dir / "virality"
        v_dir.mkdir(parents=True, exist_ok=True)
        (v_dir / "badge.svg").write_text(virality.svg_badge, encoding="utf-8")
        (v_dir / "virality_package.json").write_text(virality.model_dump_json(indent=2), encoding="utf-8")

    # Export AEO markdown pages
    aeo_dir = out_dir / "aeo_pages"
    aeo_dir.mkdir(exist_ok=True)
    for page in aeo.comparison_pages:
        (aeo_dir / f"{page.slug}.md").write_text(page.markdown_content, encoding="utf-8")
        (aeo_dir / f"{page.slug}_schema.json").write_text(page.faq_schema_json, encoding="utf-8")


if __name__ == "__main__":
    app()
