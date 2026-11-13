"""Typer-powered command-line interface for ZeroCAC autonomous marketing."""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
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
from zerocac.leads.dispatcher import ResendDispatcher
from zerocac.leads.models import LeadStatus
from zerocac.leads.nurture import NurtureEngine
from zerocac.leads.repository import LeadRepository
from zerocac.dispatchers.models import ApprovalStatus, DispatchChannel, DispatchItem
from zerocac.dispatchers.queue import DispatchQueue
from zerocac.interceptor.daemon import InterceptorDaemon
from zerocac.interceptor.engine import CommunityInterceptorEngine
from zerocac.interceptor.models import (
    AutonomyTier,
    IntentClassification,
    InterceptOpportunity,
    SocialPlatform,
    StealthMode,
)
from zerocac.launch.models import HardenedLaunchPackage
from zerocac.launch.orchestrator import LaunchOrchestrator
from zerocac.pseo.deployer import PSEOBatchDeployer
from zerocac.pseo.engine import PSEOMatrixEngine
from zerocac.pseo.models import PSEOMatrixPackage
from zerocac.telemetry.engine import TelemetryEngine
from zerocac.virality.tracker import ReferralTracker


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


@app.command(name="referral")
def referral_cmd(
    email: str = typer.Argument(..., help="User email address to query or create referral link"),
    base_url: str = typer.Option("https://zerocac.org", "--base-url", "-u", help="Base landing page URL"),
) -> None:
    """Generate or view tracked referral link, K-factor, and milestone rewards."""
    tracker = ReferralTracker()
    stats = asyncio.run(tracker.get_stats(email, base_url=base_url))

    rewards_text = "\n".join(
        f"  - [bold green]UNLOCKED:[/bold green] {r.name} ({r.description})"
        for r in stats.unlocked_rewards
    ) or "  - None yet (Drive 3 referrals to unlock Princeton GEO package)"

    next_text = f"{stats.next_milestone.name} (Requires {stats.next_milestone.required_referrals} referrals)" if stats.next_milestone else "All Milestones Achieved!"

    console.print(
        Panel(
            f"[bold cyan]Referral Share URL:[/bold cyan] {stats.referral_url}\n"
            f"[bold yellow]Referral Code:[/bold yellow] {stats.referral_code}\n\n"
            f"[bold green]Total Conversions:[/bold green] {stats.total_conversions} | [bold cyan]Clicks:[/bold cyan] {stats.total_clicks}\n"
            f"[bold magenta]Calculated K-Factor:[/bold magenta] {stats.k_factor} ({'Viral Growth' if stats.k_factor >= 1.0 else 'Compounding Sub-Viral'})\n\n"
            f"[bold green]Milestone Rewards:[/bold green]\n{rewards_text}\n\n"
            f"[bold yellow]Next Milestone Target:[/bold yellow] {next_text}",
            title="ZeroCAC Product-Led Referral Engine",
            border_style="green",
        )
    )


@app.command(name="leaderboard")
def leaderboard_cmd(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of champions to display"),
) -> None:
    """Display community leaderboard of top organic CAC killers."""
    tracker = ReferralTracker()
    entries = asyncio.run(tracker.get_leaderboard(limit=limit))

    table = Table(title="Leaderboard of Organic CAC Killers", border_style="green")
    table.add_column("Rank", justify="center", style="bold green")
    table.add_column("Champion", style="cyan")
    table.add_column("Referrals", justify="center", style="bold yellow")
    table.add_column("Ad Dollars Saved", justify="right", style="green")
    table.add_column("Honorary Title", style="magenta")

    for e in entries:
        table.add_row(
            f"#{e.rank}",
            e.user_handle,
            str(e.referrals_driven),
            f"${e.ad_dollars_saved_usd:,.0f}",
            e.badge_title,
        )

    console.print(table)




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


@app.command(name="leads")
def list_leads(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project slug"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum leads to return"),
) -> None:
    """List captured inbound leads and their nurture status."""
    repo = LeadRepository()
    leads = asyncio.run(repo.list_leads(project_slug=project, limit=limit))

    if not leads:
        console.print("[yellow]No leads captured yet. Deploy micro-tools to acquire leads.[/yellow]")
        return

    table = Table(title="Inbound Lead Pipeline ($0 CAC)", border_style="cyan")
    table.add_column("Lead ID", style="dim")
    table.add_column("Email", style="bold green")
    table.add_column("Name", style="white")
    table.add_column("Project", style="cyan")
    table.add_column("Intent", style="bold yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Captured At", style="dim")

    for lead in leads:
        table.add_row(
            lead.lead_id,
            str(lead.email),
            lead.full_name or "-",
            lead.project_slug,
            str(lead.intent_score),
            lead.status.value.upper(),
            lead.created_at[:10],
        )
    console.print(table)


@app.command(name="nurture")
def execute_nurture(
    lead_id: str = typer.Argument(..., help="Lead identifier to nurture"),
    product: str = typer.Option("ZeroCAC", "--product", "-p", help="Product brand name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate email sending"),
) -> None:
    """Generate and dispatch personalized behavioral nurture sequence for a lead."""
    repo = LeadRepository()
    lead = asyncio.run(repo.get_lead(lead_id))
    if not lead:
        console.print(f"[bold red]Error: Lead '{lead_id}' not found.[/bold red]")
        raise typer.Exit(code=1)

    profile = ProductProfile(
        product_name=product,
        category="Growth Engine",
        one_liner="Scale to $0 CAC without ad burn",
        core_problem="Paid ad fatigue",
        solution_mechanism="Autonomous micro-tools and GEO assets",
        unique_value_proposition="Compounding zero-cost distribution",
        key_features=["Micro-tools", "Live Radar"],
    )

    engine = NurtureEngine()
    sequence = engine.build_default_sequence(lead, profile)
    dispatcher = ResendDispatcher()

    console.print(f"[bold cyan]Synthesized 3-Stage Nurture Sequence for {lead.email}...[/bold cyan]")
    for stage in sequence.stages:
        console.print(f"  - Stage {stage.step} (+{stage.delay_hours}h): [bold green]{stage.subject}[/bold green]")

    res = asyncio.run(dispatcher.dispatch_stage(sequence.stages[0], str(lead.email), dry_run=dry_run))
    if res.get("success"):
        asyncio.run(repo.update_status(lead.lead_id, LeadStatus.NURTURED))
        console.print(f"[bold green]Successfully dispatched Stage 1 to {lead.email}![/bold green] (ID: {res.get('id')})")
    else:
        console.print(f"[bold red]Dispatch failed:[/bold red] {res.get('error')}")


dispatch_app = typer.Typer(name="dispatch", help="Multi-channel approval queue and syndication commands")
app.add_typer(dispatch_app, name="dispatch")


@dispatch_app.command(name="queue")
def list_dispatch_queue(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (pending, approved, dispatched)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max items to list"),
) -> None:
    """List assets awaiting approval or recently dispatched."""
    queue = DispatchQueue()
    status_filter = ApprovalStatus(status.lower()) if status else None
    items = asyncio.run(queue.list_queue(status=status_filter, limit=limit))

    if not items:
        console.print("[yellow]Dispatch queue is currently empty.[/yellow]")
        return

    table = Table(title="Outbound Distribution Approval Queue", border_style="magenta")
    table.add_column("Item ID", style="dim")
    table.add_column("Channel", style="bold cyan")
    table.add_column("Headline", style="white")
    table.add_column("Status", style="bold yellow")
    table.add_column("Created At", style="dim")

    for it in items:
        table.add_row(
            it.item_id,
            it.channel.value.upper(),
            it.title[:40],
            it.status.value.upper(),
            it.created_at[:16].replace("T", " "),
        )
    console.print(table)


@dispatch_app.command(name="approve")
def approve_dispatch_item(
    item_id: str = typer.Argument(..., help="Item identifier to approve and publish"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate publishing"),
) -> None:
    """Approve queued item and fire destination channel webhook."""
    queue = DispatchQueue()
    console.print(f"[bold cyan]Approving and dispatching {item_id}...[/bold cyan]")
    res = asyncio.run(queue.approve_and_dispatch(item_id, dry_run=dry_run))

    if res.success:
        console.print(f"[bold green]Successfully published to {res.channel.value}![/bold green] (Post ID: {res.external_post_id})")
    else:
        console.print(f"[bold red]Dispatch failed:[/bold red] {res.error_message}")
        raise typer.Exit(code=1)


@dispatch_app.command(name="reject")
def reject_dispatch_item(
    item_id: str = typer.Argument(..., help="Item identifier to reject"),
) -> None:
    """Reject queued distribution draft."""
    queue = DispatchQueue()
    ok = asyncio.run(queue.reject(item_id))
    if ok:
        console.print(f"[bold yellow]Rejected item {item_id}.[/bold yellow]")
    else:
        console.print(f"[bold red]Item {item_id} not found.[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="telemetry")
def view_telemetry() -> None:
    """View closed-loop telemetry analytics, $0 CAC ad savings, and self-tuning health."""
    engine = TelemetryEngine()
    report = asyncio.run(engine.audit_assets())

    console.print(
        Panel(
            f"[bold green]Total Leads Acquired ($0 CAC):[/bold green] {report.total_leads_acquired}\n"
            f"[bold yellow]Estimated Ad Budget Saved:[/bold yellow] ${report.estimated_ad_savings_usd:,.2f} USD\n"
            f"[bold cyan]Blended Conversion Rate:[/bold cyan] {report.blended_conversion_rate}%\n"
            f"[bold white]Monitored Organic Assets:[/bold white] {report.total_assets}\n"
            f"[bold dim]Total Clicks / Impressions:[/bold dim] {report.total_clicks} / {report.total_impressions}",
            title="Closed-Loop Telemetry & Organic ROI Report",
            border_style="green",
        )
    )

    if report.assets:
        table = Table(title="Organic Asset Health & Self-Healing Actions", border_style="cyan")
        table.add_column("Asset Slug", style="bold white")
        table.add_column("Clicks / Imp", style="dim")
        table.add_column("CTR", style="cyan")
        table.add_column("Leads", style="bold green")
        table.add_column("Conv %", style="yellow")
        table.add_column("Health Status", style="magenta")
        table.add_column("Prescribed Action", style="blue")

        for a in report.assets:
            table.add_row(
                a.slug[:28],
                f"{a.clicks}/{a.impressions}",
                f"{a.ctr:.1f}%",
                str(a.leads_captured),
                f"{a.conversion_rate:.1f}%",
                a.tier.value.upper(),
                a.recommended_action.value.replace("_", " ").title(),
            )
        console.print(table)


launch_app = typer.Typer(name="launch", help="Autonomous 8-Vector Day-1 Launch Carpet Bombing commands")
app.add_typer(launch_app, name="launch")


@launch_app.command(name="prepare")
def prepare_launch_cmd(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    output_dir: Path = typer.Option(Path("dist_launch"), "--out", "-o", help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate synthesis"),
) -> None:
    """Synthesize complete 8-vector Day-1 launch package."""
    profile = asyncio.run(_run_analysis(url, description, provider=None, name=name))
    console.print(f"[bold cyan]Compiling 8-Vector Day-1 Launch Machine for {profile.product_name}...[/bold cyan]")

    engine = MicroToolEngine()
    tool_pkg = asyncio.run(engine.generate_tool(profile, dry_run=True))
    live_url = f"https://{tool_pkg.concept.slug}.pages.dev"

    orchestrator = LaunchOrchestrator()
    package = orchestrator.prepare_launch_kit(
        profile=profile,
        tool_html=tool_pkg.html_content,
        tool_slug=tool_pkg.concept.slug,
        live_url=live_url,
        tool_name=tool_pkg.concept.tool_name,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    pkg_path = output_dir / "launch_package.json"
    pkg_path.write_text(package.model_dump_json(indent=2), encoding="utf-8")

    orchestrator.github_packager.export_repository(package.github_package, tool_pkg.html_content, output_dir)

    table = Table(title=f"8-Vector Day-1 Launch Package: {profile.product_name}", border_style="green")
    table.add_column("Vector", style="bold cyan")
    table.add_column("Target Destination", style="white")
    table.add_column("Artifact Headline", style="green")

    table.add_row("Vector 1: GitHub Open Source", package.github_package.repo_name, package.github_package.tagline)
    table.add_row("Vector 2: Hacker News", "Hacker News (Show HN)", package.show_hn.title)
    table.add_row("Vector 3: Launch Trio", "Product Hunt + Peerlist + MicroLaunch", f"{len(package.launch_trio)} Aggregator Payloads")
    table.add_row("Vector 4: Subreddit Value", "5x Target Subreddits", ", ".join(p.subreddit for p in package.reddit_posts))
    table.add_row("Vector 5: Tech Publishing", "Dev.to + Hashnode", package.technical_articles[0].title[:35])
    table.add_row("Vector 6: X Thread", "X / Twitter Algorithmic Thread", f"{len(package.social_blast.x_thread)} Tweets + Video Script")
    table.add_row("Vector 7: LinkedIn Story", "LinkedIn Founder Post", "Narrative Post + 1st Comment Link")
    table.add_row("Vector 8: Startup Directories", "15x High-DA Directories", f"{len(package.directories)} Directory Payloads")

    console.print(table)
    console.print(f"[bold green]Launch kit successfully exported to: {pkg_path.resolve()}[/bold green]")


@launch_app.command(name="execute")
def execute_launch_cmd(
    package_file: Path = typer.Argument(..., help="Path to launch_package.json"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate dispatch without live API calls"),
) -> None:
    """Dispatch multi-wave launch across all 8 vectors."""
    if not package_file.exists():
        console.print(f"[bold red]Error: Package file '{package_file}' not found.[/bold red]")
        raise typer.Exit(code=1)

    data = json.loads(package_file.read_text(encoding="utf-8"))
    package = HardenedLaunchPackage(**data)

    console.print(f"[bold yellow]Executing 8-Vector Day-1 Carpet Bombing for {package.product_name}...[/bold yellow]")
    orchestrator = LaunchOrchestrator()
    report = asyncio.run(orchestrator.execute_launch(package, dry_run=dry_run))

    table = Table(title="Day-1 Multi-Wave Execution Report", border_style="magenta")
    table.add_column("Vector", style="bold cyan")
    table.add_column("Destination", style="white")
    table.add_column("Status", style="bold green")
    table.add_column("Live URL", style="dim")

    for v in report.vector_results:
        table.add_row(
            v.vector.value.upper(),
            v.destination,
            "[bold green]DISPATCHED[/bold green]" if v.success else "[bold red]FAILED[/bold red]",
            v.live_post_url or "-",
        )
    console.print(table)
    console.print(
        Panel(
            f"[bold green]Total Vectors Dispatched:[/bold green] {report.successful_vectors} / {report.total_vectors_attempted}\n"
            f"[bold yellow]Guaranteed Day-1 Visitor Floor:[/bold yellow] ~{report.estimated_day1_visitors_floor} Visitors\n"
            f"[bold cyan]Estimated Day-1 Lead Yield (12%):[/bold cyan] ~{int(report.estimated_day1_visitors_floor * 0.12)} Qualified Leads\n"
            f"[bold green]Equivalent Ad Budget Saved:[/bold green] ${int(report.estimated_day1_visitors_floor * 0.12) * 25:,.2f} USD ($0 CAC)",
            title="Day-1 Launch Impact Projection",
            border_style="green",
        )
    )


pseo_app = typer.Typer(name="pseo", help="Autonomous Programmatic SEO Matrix Engine commands")
app.add_typer(pseo_app, name="pseo")


def _export_pseo_artifacts(package: PSEOMatrixPackage, output_dir: Path) -> Path:
    """Save pSEO package, index hub, sitemap, and subpage HTML assets to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pkg_path = output_dir / "pseo_package.json"
    pkg_path.write_text(package.model_dump_json(indent=2), encoding="utf-8")

    pages_dir = output_dir / "vs"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(package.hub_page_html, encoding="utf-8")
    (output_dir / "sitemap-pseo.xml").write_text(package.sitemap_xml, encoding="utf-8")

    for page in package.pages:
        page_dir = pages_dir / page.slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(page.html_content, encoding="utf-8")

    return pkg_path


def _render_pseo_summary(package: PSEOMatrixPackage, pkg_path: Path) -> None:
    """Render rich console table and impact projection panel for pSEO matrix."""
    table = Table(
        title=f"Programmatic SEO Matrix: {package.product_name} ({len(package.pages)} Pages)",
        border_style="green",
    )
    table.add_column("Axis", style="bold cyan")
    table.add_column("Target Query", style="white")
    table.add_column("Demand Score", style="yellow")
    table.add_column("Est Traffic/mo", style="bold green")
    table.add_column("Slug", style="dim")

    for p in package.pages:
        table.add_row(
            p.axis.value.replace("_", " ").title(),
            p.target_query,
            f"{p.demand_score}/100",
            f"~{p.estimated_monthly_visits} visits",
            f"/vs/{p.slug}",
        )
    console.print(table)

    total_est_clicks = sum(p.estimated_monthly_visits for p in package.pages)
    console.print(
        Panel(
            f"[bold green]Total Programmatic Landing Pages Generated:[/bold green] {len(package.pages)}\n"
            f"[bold yellow]Total Projected Organic Search Traffic:[/bold yellow] ~{total_est_clicks:,} Clicks/Month ($0 CAC)\n"
            f"[bold cyan]Equivalent Google Ads Spend Value:[/bold cyan] ${total_est_clicks * 15:,.2f} USD / Month\n"
            f"[bold white]Internal Links Formed:[/bold white] Bidirectional Hub-and-Spoke Mesh (0 Orphan Pages)\n"
            f"[bold magenta]Package Artifact:[/bold magenta] {pkg_path.resolve()}",
            title="Programmatic Matrix Impact Projection",
            border_style="green",
        )
    )


@pseo_app.command(name="generate")
def generate_pseo_cmd(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    count: int = typer.Option(9, "--count", "-c", help="Number of matrix pages to generate"),
    output_dir: Path = typer.Option(Path("dist_pseo"), "--out", "-o", help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate generation"),
) -> None:
    """Synthesize validated multi-axis pSEO matrix cluster."""
    profile = asyncio.run(_run_analysis(url, description, provider=None, name=name))
    console.print(f"[bold cyan]Compiling Programmatic SEO Matrix for {profile.product_name}...[/bold cyan]")

    engine = MicroToolEngine()
    tool_pkg = asyncio.run(engine.generate_tool(profile, dry_run=True))

    pseo_engine = PSEOMatrixEngine()
    package = asyncio.run(
        pseo_engine.generate_matrix(
            profile=profile,
            tool_html=tool_pkg.html_content,
            target_count=count,
            dry_run=dry_run,
        )
    )

    pkg_path = _export_pseo_artifacts(package, output_dir)
    _render_pseo_summary(package, pkg_path)


@pseo_app.command(name="deploy")
def deploy_pseo_cmd(
    package_file: Path = typer.Argument(..., help="Path to pseo_package.json"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate dispatch without live API calls"),
) -> None:
    """Deploy programmatic matrix to edge hosting and ping IndexNow."""
    if not package_file.exists():
        console.print(f"[bold red]Error: Package file '{package_file}' not found.[/bold red]")
        raise typer.Exit(code=1)

    data = json.loads(package_file.read_text(encoding="utf-8"))
    package = PSEOMatrixPackage(**data)

    console.print(f"[bold yellow]Deploying Programmatic SEO Matrix for {package.product_name}...[/bold yellow]")
    deployer = PSEOBatchDeployer()
    report = asyncio.run(deployer.deploy_matrix(package, dry_run=dry_run))

    table = Table(title="Programmatic SEO Deployment Report", border_style="magenta")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Status / Value", style="white")

    table.add_row("Pages Deployed", str(report.total_pages_deployed))
    table.add_row("Live Directory Hub URL", report.hub_url)
    idx_status = "[bold green]SUBMITTED (Bing, Yandex, Seznam)[/bold green]" if report.indexnow_submitted else "[bold red]FAILED[/bold red]"
    table.add_row("IndexNow Search Submission", idx_status)
    proxy_status = "[bold green]Active (/vs/* mounted)[/bold green]" if report.reverse_proxy_mounted else "Inactive"
    table.add_row("Reverse Proxy Route Config", proxy_status)
    table.add_row("URLs Indexed in Batch", f"{len(report.indexed_urls)} URLs")

    console.print(table)


intercept_app = typer.Typer(name="intercept", help="Direct Social & Community Intent Interceptor commands")
app.add_typer(intercept_app, name="intercept")


def _render_intercept_scan_table(opportunities: List[InterceptOpportunity]) -> None:
    """Render rich console table of detected buyer opportunities."""
    table = Table(title=f"Detected High-Intent Buyer Opportunities ({len(opportunities)})", border_style="green")
    table.add_column("Opportunity ID", style="bold cyan")
    table.add_column("Platform / Topic", style="white")
    table.add_column("Score", style="yellow")
    table.add_column("Intent Category", style="magenta")
    table.add_column("Competitor", style="bold red")
    table.add_column("Thread Title", style="white")

    for opp in opportunities:
        table.add_row(
            opp.opportunity_id,
            f"{opp.platform.value} ({opp.subreddit_or_topic})",
            f"{opp.intent_score}/100",
            opp.classification.value.replace("_", " ").title(),
            opp.detected_competitor or "-",
            opp.title[:38],
        )
    console.print(table)

    if opportunities:
        top = opportunities[0]
        console.print(
            Panel(
                f"[bold cyan]Target Post:[/bold cyan] {top.title}\n"
                f"[bold yellow]Author:[/bold yellow] u/{top.author} | [bold green]Score:[/bold green] {top.intent_score}/100\n"
                f"[bold magenta]Stealth Strategy:[/bold magenta] {top.stealth_mode.value}\n\n"
                f"[bold white]Drafted Practitioner Response:[/bold white]\n{top.synthesized_reply}",
                title=f"Top Priority Intercept Draft [{top.opportunity_id}]",
                border_style="cyan",
            )
        )


@intercept_app.command(name="scan")
def scan_intercept_cmd(
    url: Optional[str] = typer.Argument(None, help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Product brand name"),
    subreddits: Optional[str] = typer.Option(None, "--subs", "-s", help="Comma-separated target subreddits"),
    min_score: int = typer.Option(75, "--min-score", "-m", help="Minimum qualifying intent score"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate feed scan"),
) -> None:
    """Scan live social feeds for qualified buyer purchase signals."""
    profile = asyncio.run(_run_analysis(url, description, provider=None, name=name))
    console.print(f"[bold cyan]Scanning live social streams for {profile.product_name}...[/bold cyan]")

    subs_list = [s.strip() for s in subreddits.split(",")] if subreddits else None
    engine = CommunityInterceptorEngine()
    opportunities = asyncio.run(
        engine.scan_opportunities(
            profile=profile,
            tool_url=url or f"https://{profile.product_name.lower().replace(' ', '-')}.pages.dev",
            subreddits=subs_list,
            min_score=min_score,
            dry_run=dry_run,
        )
    )

    _render_intercept_scan_table(opportunities)


@intercept_app.command(name="reply")
def reply_intercept_cmd(
    opportunity_id: str = typer.Argument(..., help="Opportunity identifier"),
    url: str = typer.Option(..., "--url", "-u", help="Direct URL of the target thread"),
    text: str = typer.Option(..., "--text", "-t", help="Reply text to dispatch"),
    platform: str = typer.Option("reddit", "--platform", "-p", help="Target platform"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate dispatch without live API call"),
) -> None:
    """Dispatch practitioner response to live platform thread."""
    plat_enum = SocialPlatform(platform.lower())
    opp = InterceptOpportunity(
        opportunity_id=opportunity_id,
        platform=plat_enum,
        post_id=opportunity_id,
        post_url=url,
        subreddit_or_topic="general",
        author="target_user",
        title="Target buyer thread",
        body_text="Looking for alternative",
        created_at_utc="2026-11-09T10:00:00Z",
        intent_score=85,
        classification=IntentClassification.IMMEDIATE_MIGRATION,
        synthesized_reply=text,
    )

    engine = CommunityInterceptorEngine()
    console.print(f"[bold yellow]Dispatching reply to {plat_enum.value} ({opportunity_id})...[/bold yellow]")
    res = asyncio.run(engine.dispatch_reply(opp, dry_run=dry_run))

    if res.success:
        console.print(f"[bold green]Successfully dispatched to {res.platform.value}![/bold green] (URL: {res.live_comment_url})")
    else:
        console.print(f"[bold red]Dispatch failed:[/bold red] {res.error_message}")
        raise typer.Exit(code=1)


@intercept_app.command(name="telemetry")
def intercept_telemetry_cmd() -> None:
    """View community interception conversions and displaced Google Ads spend."""
    engine = CommunityInterceptorEngine()
    summary = engine.get_telemetry_summary()

    console.print(
        Panel(
            f"[bold green]Total Opportunities Detected:[/bold green] {summary['total_opportunities_detected']}\n"
            f"[bold yellow]Total Responses Dispatched:[/bold yellow] {summary['total_dispatched']}\n"
            f"[bold cyan]Estimated Inbound Organic Clicks:[/bold cyan] ~{summary['estimated_inbound_clicks']:,}\n"
            f"[bold green]Qualified Leads Acquired ($0 CAC):[/bold green] ~{summary['estimated_leads_acquired']:,}\n"
            f"[bold magenta]Equivalent Ad Spend Displaced:[/bold magenta] ${summary['estimated_ad_savings_usd']:,.2f} USD",
            title="Community Interceptor Impact & Ad Displacement",
            border_style="green",
        )
    )


@intercept_app.command(name="daemon")
def intercept_daemon_cmd(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Product landing page URL"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Direct product description"),
    name: Optional[str] = typer.Option("Product", "--name", "-n", help="Product brand name"),
    subreddits: Optional[str] = typer.Option(None, "--subreddits", "-s", help="Comma-separated subreddits"),
    min_score: int = typer.Option(75, "--min-score", "-m", help="Minimum qualifying intent score"),
    alert_threshold: int = typer.Option(85, "--alert-threshold", "-t", help="Telegram push alert threshold"),
    interval: float = typer.Option(60.0, "--interval", "-i", help="Poll interval in seconds"),
    autonomy: str = typer.Option("manual_review", "--autonomy", "-a", help="Autonomy tier"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Simulate network posts"),
    once: bool = typer.Option(False, "--once", help="Run a single scan iteration and exit"),
) -> None:
    """Run persistent 24/7 background social intent interception daemon."""
    subs = [s.strip() for s in subreddits.split(",")] if subreddits else None
    tier = AutonomyTier(autonomy) if autonomy in AutonomyTier._value2member_map_ else AutonomyTier.MANUAL_REVIEW

    daemon = InterceptorDaemon(
        tool_url=url or "https://zerocac.org",
        subreddits=subs,
        min_score=min_score,
        alert_threshold=alert_threshold,
        autonomy_tier=tier,
        poll_interval=interval,
        dry_run=dry_run,
    )

    if once:
        opps = asyncio.run(daemon.run_once())
        console.print(f"[bold green]Poll pass complete:[/bold green] Found {len(opps)} new qualified opportunities.")
        _render_intercept_scan_table(opps)
        return

    console.print(
        Panel(
            f"[bold green]24/7 Interceptor Daemon Active[/bold green]\n"
            f"[bold cyan]Poll Interval:[/bold cyan] {interval}s | [bold yellow]Autonomy Tier:[/bold yellow] {tier.value}\n"
            f"[bold magenta]Min Intent Score:[/bold magenta] {min_score} | [bold green]Alert Threshold:[/bold green] {alert_threshold}\n"
            f"[dim]Press Ctrl+C to halt daemon gracefully.[/dim]",
            title="ZeroCAC Continuous Growth Radar",
            border_style="green",
        )
    )

    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        daemon.stop()
        console.print("[yellow]Interceptor daemon halted gracefully.[/yellow]")



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
