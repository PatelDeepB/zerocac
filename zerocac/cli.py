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
from zerocac.engines.narrative import ViralNarrativeEngine
from zerocac.engines.radar import LiveIntentRadarEngine
from zerocac.engines.sniper import IntentSniperEngine

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
def run(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    output_dir: Path = typer.Option(Path("dist_campaign"), "--out", "-o", help="Output directory"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    velocity: bool = typer.Option(False, "--velocity", "-v", help="Include real-time Live Intent Radar scanning"),
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
    if velocity:
        console.print("[bold cyan]Scanning live feeds via Live Intent Radar...[/bold cyan]")
        radar_engine = LiveIntentRadarEngine(router)
        radar_pkg = asyncio.run(radar_engine.scan_live_feeds(profile, dry_run=False))

    output_dir.mkdir(parents=True, exist_ok=True)
    _save_campaign_artifacts(output_dir, profile, sniper_pkg, aeo_pkg, viral_pkg, dir_pkg, radar_pkg)
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
) -> None:
    """Write generated assets to organized files."""
    (out_dir / "profile.json").write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "sniper_campaign.json").write_text(sniper.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "viral_campaign.json").write_text(viral.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "directories.json").write_text(directory.model_dump_json(indent=2), encoding="utf-8")

    if radar:
        (out_dir / "radar_signals.json").write_text(radar.model_dump_json(indent=2), encoding="utf-8")

    # Export AEO markdown pages
    aeo_dir = out_dir / "aeo_pages"
    aeo_dir.mkdir(exist_ok=True)
    for page in aeo.comparison_pages:
        (aeo_dir / f"{page.slug}.md").write_text(page.markdown_content, encoding="utf-8")
        (aeo_dir / f"{page.slug}_schema.json").write_text(page.faq_schema_json, encoding="utf-8")


if __name__ == "__main__":
    app()
