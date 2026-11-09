"""Data models for the 8-Vector Day-1 Launch Carpet Bombing Engine."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class LaunchVector(str, Enum):
    """The 8 independent distribution vectors executed during Day-1 launch."""

    GITHUB = "github"
    HACKER_NEWS = "hacker_news"
    PRODUCT_HUNT = "product_hunt"
    PEERLIST = "peerlist"
    MICROLAUNCH = "microlaunch"
    REDDIT = "reddit"
    TECH_PUBLISHING = "tech_publishing"
    SOCIAL_BLAST = "social_blast"
    DIRECTORIES = "directories"


class GitHubLaunchPackage(BaseModel):
    """Open-source repository package engineered for GitHub Explore and Trending."""

    repo_name: str = Field(..., description="Repository slug (e.g. socius-dealflow-calculator)")
    tagline: str = Field(..., description="Concise repo description under 120 chars")
    topics: List[str] = Field(default_factory=list, description="Target GitHub discovery tags")
    readme_markdown: str = Field(..., description="High-converting README with SVG badges and demo")
    license_type: str = Field(default="Apache-2.0", description="Open-source license type")


class ShowHNPackage(BaseModel):
    """Hacker News Show HN submission payload compliant with strict community rules."""

    title: str = Field(..., description="Show HN: [Name] - [Technical utility under 80 chars]")
    target_url: str = Field(..., description="URL pointing to live deployed microtool or repo")
    maker_comment: str = Field(..., description="In-depth technical genesis, architecture, and tradeoffs")
    suggested_utc_hour: int = Field(default=13, description="Optimal UTC submission hour for HN traffic")


class LaunchTrioItem(BaseModel):
    """Aggregator platform submission data."""

    platform_name: str = Field(..., description="Platform identifier (e.g. Product Hunt, Peerlist)")
    tagline: str = Field(..., description="Short benefit hook under 60 chars")
    description: str = Field(..., description="Summary under 260 chars")
    maker_first_comment: str = Field(..., description="Founder backstory and open discussion prompt")
    topic_tags: List[str] = Field(default_factory=list, description="Target platform taxonomy tags")


class SubredditPost(BaseModel):
    """Tailored organic post for a specific target subreddit."""

    subreddit: str = Field(..., description="Target subreddit name (e.g. r/SaaS, r/SideProject)")
    angle_type: str = Field(..., description="Cultural angle (build_in_public, teardown, technical)")
    title: str = Field(..., description="Non-promotional, high-curiosity headline")
    body_markdown: str = Field(..., description="Value-first body copy providing immediate insight")
    first_comment: Optional[str] = Field(
        default=None,
        description="First comment containing the open micro-tool link",
    )


class TechnicalArticle(BaseModel):
    """Syndicated technical article for Dev.to, Hashnode, or Medium."""

    platform: str = Field(..., description="Target publishing outlet (e.g. devto, hashnode)")
    title: str = Field(..., description="Compelling engineering case study title")
    markdown_content: str = Field(..., description="Complete long-form article body")
    canonical_url: str = Field(..., description="Canonical source URL pointing to deployed tool")
    tags: List[str] = Field(default_factory=list, description="Platform publication tags")


class SocialBlastPackage(BaseModel):
    """Viral social assets for X (Twitter) and LinkedIn."""

    x_thread: List[str] = Field(default_factory=list, description="5-tweet contrarian breakdown")
    video_script_60s: str = Field(..., description="60-second screen-demo script for Loom or video")
    linkedin_post: str = Field(..., description="Story-driven post formatting for LinkedIn feed")
    linkedin_first_comment: str = Field(..., description="First comment link to preserve post reach")


class DirectoryListing(BaseModel):
    """Directory submission record adapted to character limitations."""

    directory_name: str = Field(..., description="Directory name (e.g. SaaSHub, Toolify, BetaList)")
    submission_url: str = Field(..., description="Submission or intake URL")
    title: str = Field(..., description="Listing title under 50 chars")
    short_pitch: str = Field(..., description="One-sentence description under 140 chars")
    full_description: str = Field(..., description="Detailed profile under 700 chars")
    tags: List[str] = Field(default_factory=list, description="Classification tags")


class HardenedLaunchPackage(BaseModel):
    """Complete 8-Vector Day-1 Launch payload eliminating single-point-of-failure risk."""

    launch_id: str = Field(
        default_factory=lambda: f"launch-{uuid.uuid4().hex[:10]}",
        description="Unique launch campaign identifier",
    )
    product_name: str = Field(..., description="Product brand name")
    live_tool_url: str = Field(..., description="URL of deployed microtool")
    github_package: GitHubLaunchPackage = Field(..., description="Vector 1: Open source repository")
    show_hn: ShowHNPackage = Field(..., description="Vector 2: Hacker News Show HN")
    launch_trio: List[LaunchTrioItem] = Field(..., description="Vector 3: Product Hunt, Peerlist, MicroLaunch")
    reddit_posts: List[SubredditPost] = Field(..., description="Vector 4: 5x Culturally adapted subreddits")
    technical_articles: List[TechnicalArticle] = Field(..., description="Vector 5: Dev.to, Hashnode, Medium")
    social_blast: SocialBlastPackage = Field(..., description="Vector 6 & 7: X Thread & LinkedIn Carousel")
    directories: List[DirectoryListing] = Field(..., description="Vector 8: 15x High-DA startup catalogs")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of launch kit synthesis",
    )


class VectorExecutionStatus(BaseModel):
    """Status record for a single launch vector execution."""

    vector: LaunchVector = Field(..., description="Distribution vector identifier")
    destination: str = Field(..., description="Target platform or endpoint")
    success: bool = Field(..., description="Whether submission or syndication succeeded")
    live_post_url: Optional[str] = Field(default=None, description="Direct URL to published post")
    error_message: Optional[str] = Field(default=None, description="Failure details if rejected")


class LaunchExecutionReport(BaseModel):
    """Consolidated outcome report across the 8-Vector Day-1 Launch blast."""

    launch_id: str = Field(..., description="Launch identifier")
    product_name: str = Field(..., description="Target product")
    total_vectors_attempted: int = Field(..., description="Number of vectors executed")
    successful_vectors: int = Field(..., description="Number of vectors published successfully")
    estimated_day1_visitors_floor: int = Field(
        ...,
        description="Conservative aggregate visitor floor across successful vectors",
    )
    vector_results: List[VectorExecutionStatus] = Field(default_factory=list, description="Per-vector status")
    dispatched_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of execution completion",
    )
