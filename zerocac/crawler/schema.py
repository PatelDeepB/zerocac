"""Domain models and exceptions for web scraping."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CrawlerError(Exception):
    """Raised when web page fetching or parsing fails."""

    def __init__(self, message: str, url: str, status_code: Optional[int] = None) -> None:
        super().__init__(f"Failed to crawl {url}: {message}")
        self.url = url
        self.status_code = status_code


class ProductRawData(BaseModel):
    """Raw extracted DOM and content signals from a target product page."""

    url: str = Field(description="Target URL fetched")
    title: str = Field(default="", description="HTML title tag content")
    meta_description: str = Field(default="", description="Meta description tag content")
    og_title: str = Field(default="", description="OpenGraph title")
    og_description: str = Field(default="", description="OpenGraph description")
    headers: List[str] = Field(default_factory=list, description="H1, H2, and H3 headers")
    body_paragraphs: List[str] = Field(default_factory=list, description="Key paragraph text")
    bullet_points: List[str] = Field(default_factory=list, description="List items and features")
    calls_to_action: List[str] = Field(default_factory=list, description="CTA button and link texts")
    pricing_hints: List[str] = Field(default_factory=list, description="Extracted pricing signals")

    def to_condensed_text(self, max_chars: int = 4000) -> str:
        """Combine raw DOM extractions into a concise summary for LLM context."""
        parts = [
            f"URL: {self.url}",
            f"Title: {self.title or self.og_title}",
            f"Description: {self.meta_description or self.og_description}",
        ]
        if self.headers:
            parts.append(f"Key Headers: {' | '.join(self.headers[:8])}")
        if self.bullet_points:
            parts.append("Key Points:\n" + "\n".join(f"- {pt}" for pt in self.bullet_points[:10]))
        if self.calls_to_action:
            parts.append(f"CTAs: {', '.join(self.calls_to_action[:6])}")
        if self.body_paragraphs:
            parts.append("Content Snippet:\n" + "\n".join(self.body_paragraphs[:5]))

        condensed = "\n\n".join(parts)
        return condensed[:max_chars]
