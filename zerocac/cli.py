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
            "• OpenAI: GPT-6 Astra, GPT-6.1 Luna, gpt-oss-120b\n"
            "• Google: Gemini 4 Argon, Gemini 3.8 Flash\n"
            "• Anthropic: Claude Opus 5.5, Claude Sonnet 5.5\n"
            "• NVIDIA: Nemotron 3 Ultra (550B MoE), Nemotron 3.5 Super VL\n"
            "• DeepSeek: DeepSeek-V4.1-Flash, DeepSeek-R1",
            title="System Info",
            border_style="green",
        )
    )


@app.command()
def analyze(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
) -> None:
    """Analyze a product landing page and extract strategic positioning and ICP personas."""
    profile = asyncio.run(_run_analysis(url, description, provider))
    _print_profile_panel(profile)


@app.command()
def snipe(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
    count: int = typer.Option(3, "--count", "-c", help="Number of opportunities to generate"),
) -> None:
    """Generate high-intent social problem-solving opportunities across Reddit, HN, and X."""
    profile = asyncio.run(_run_analysis(url, description, provider))
    sniper_engine = IntentSniperEngine()
    campaign = asyncio.run(
        sniper_engine.generate_opportunities(profile, count=count, provider_name=provider)
    )

    console.print(f"\n[bold green]Intent Sniper Opportunities for {profile.product_name}:[/bold green]\n")
    for opp in campaign.opportunities:
        console.print(
            Panel(
                f"[bold cyan]Thread:[/bold cyan] {opp.thread_title}\n"
                f"[bold yellow]Platform:[/bold yellow] {opp.platform} ({opp.community}) | "
                f"[bold green]Intent Score:[/bold green] {opp.intent_score}%\n\n"
                f"[bold white]Drafted Solution:[/bold white]\n{opp.draft_response}",
                title=f"{opp.platform} Opportunity",
                border_style="cyan",
            )
        )


@app.command()
def aeo(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
) -> None:
    """Generate comparison pages and JSON-LD schema for Perplexity and SearchGPT."""
    profile = asyncio.run(_run_analysis(url, description, provider))
    aeo_engine = AEOEngine()
    package = asyncio.run(aeo_engine.generate_package(profile, provider_name=provider))

    console.print(f"\n[bold green]Generated {len(package.comparison_pages)} AEO Comparison Pages:[/bold green]\n")
    for page in package.comparison_pages:
        console.print(Panel(page.markdown_content[:600] + "\n...", title=page.title, border_style="magenta"))


@app.command()
def viral(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
) -> None:
    """Generate X build-in-public thread, LinkedIn carousel slides, and 60s video script."""
    profile = asyncio.run(_run_analysis(url, description, provider))
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
) -> None:
    """Output tailored submission packages for 30+ software directories."""
    profile = asyncio.run(_run_analysis(url, description, None))
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
def run(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    output_dir: Path = typer.Option(Path("dist_campaign"), "--out", "-o", help="Output directory"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Target AI provider"),
) -> None:
    """Execute all organic growth engines and export assets to disk."""
    profile = asyncio.run(_run_analysis(url, description, provider))
    console.print("[bold yellow]Executing all 4 organic distribution engines...[/bold yellow]")

    router = AIRouter()
    sniper_pkg = asyncio.run(IntentSniperEngine(router).generate_opportunities(profile, count=3, provider_name=provider))
    aeo_pkg = asyncio.run(AEOEngine(router).generate_package(profile, provider_name=provider))
    viral_pkg = asyncio.run(ViralNarrativeEngine(router).generate_campaign(profile, provider_name=provider))
    dir_pkg = DirectoryEngine().generate_package(profile)

    output_dir.mkdir(parents=True, exist_ok=True)
    _save_campaign_artifacts(output_dir, profile, sniper_pkg, aeo_pkg, viral_pkg, dir_pkg)
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
async def _run_analysis(url: Optional[str], desc: Optional[str], provider: Optional[str]) -> ProductProfile:
    """Orchestrate crawler and analyzer."""
    if not url and not desc:
        console.print("[bold red]Error: Either a URL or --desc must be provided.[/bold red]")
        raise typer.Exit(code=1)

    analyzer = ProductAnalyzer()
    if url:
        try:
            raw = await URLScraper().crawl_url(url)
            return await analyzer.analyze_raw_data(raw, provider_name=provider)
        except Exception:
            return await analyzer.analyze_text(description=f"Product at {url}", product_name="Product", provider_name=provider)
    return await analyzer.analyze_text(description=desc or "", product_name="Product", provider_name=provider)


def _print_profile_panel(profile: ProductProfile) -> None:
    """Render structured product profile to console."""
    personas_str = "\n".join(f"• {p.persona_name}: {p.core_pain_point}" for p in profile.personas)
    competitors_str = "\n".join(f"• vs {g.competitor_name}: {g.our_advantage}" for g in profile.competitor_gaps)
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
) -> None:
    """Write generated assets to organized files."""
    (out_dir / "profile.json").write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "sniper_campaign.json").write_text(sniper.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "viral_campaign.json").write_text(viral.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "directories.json").write_text(directory.model_dump_json(indent=2), encoding="utf-8")

    # Export AEO markdown pages
    aeo_dir = out_dir / "aeo_pages"
    aeo_dir.mkdir(exist_ok=True)
    for page in aeo.comparison_pages:
        (aeo_dir / f"{page.slug}.md").write_text(page.markdown_content, encoding="utf-8")
        (aeo_dir / f"{page.slug}_schema.json").write_text(page.faq_schema_json, encoding="utf-8")
