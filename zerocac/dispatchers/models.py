"""Data models for multi-channel distribution and interactive approval queue."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field


class DispatchChannel(str, Enum):
    """Supported external syndication and distribution targets."""

    TELEGRAM = "telegram"
    SLACK = "slack"
    GHOST = "ghost"
    WEBFLOW = "webflow"
    WEBHOOK = "webhook"
    TWITTER = "twitter"
    REDDIT = "reddit"


class ApprovalStatus(str, Enum):
    """Workflow state of an asset queued for external publishing."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPATCHED = "dispatched"


class DispatchItem(BaseModel):
    """Asset queued for approval or automated publishing."""

    item_id: str = Field(
        default_factory=lambda: f"disp-{uuid.uuid4().hex[:10]}",
        description="Unique identifier for dispatch entry",
    )
    channel: DispatchChannel = Field(..., description="Target distribution channel")
    title: str = Field(..., description="Short title or headline of the post")
    content: str = Field(..., description="Full text or markdown content to publish")
    target_destination: Optional[str] = Field(
        default=None,
        description="Target webhook URL, thread link, or chat identifier",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Channel-specific attributes (e.g. tags, slug, canonical_url)",
    )
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING,
        description="Current approval workflow state",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO creation timestamp",
    )
    dispatched_at: Optional[str] = Field(
        default=None,
        description="UTC ISO timestamp when publishing succeeded",
    )


class DispatchResult(BaseModel):
    """Outcome report of a publishing or approval execution."""

    success: bool = Field(..., description="Whether distribution operation succeeded")
    item_id: str = Field(..., description="Dispatched item identifier")
    channel: DispatchChannel = Field(..., description="Target channel used")
    external_post_id: Optional[str] = Field(
        default=None,
        description="Identifier returned by external API if available",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if delivery failed",
    )
