"""Data models for inbound lead capture and behavioral nurture sequences."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class LeadStatus(str, Enum):
    """Lifecycle status of a captured organic prospect."""

    CAPTURED = "captured"
    ENRICHED = "enriched"
    NURTURED = "nurtured"
    CONVERTED = "converted"


class Lead(BaseModel):
    """Structured representation of a prospect captured via an organic asset."""

    lead_id: str = Field(
        default_factory=lambda: f"lead-{uuid.uuid4().hex[:10]}",
        description="Unique identifier for the captured lead",
    )
    email: EmailStr = Field(..., description="Email address submitted by the user")
    full_name: Optional[str] = Field(default=None, description="Prospect name if provided")
    company: Optional[str] = Field(default=None, description="Prospect company if provided")
    project_slug: str = Field(..., description="Slug of the microtool or GEO asset origin")
    tool_inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw metrics and parameters entered in the interactive tool",
    )
    intent_score: int = Field(
        default=75,
        ge=0,
        le=100,
        description="Estimated purchase intent score based on input velocity and values",
    )
    status: LeadStatus = Field(
        default=LeadStatus.CAPTURED,
        description="Current nurture lifecycle status",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of initial lead capture",
    )


class NurtureEmail(BaseModel):
    """Single stage in an automated behavioral nurture sequence."""

    step: int = Field(..., description="Stage number in the sequence (1 to N)")
    delay_hours: int = Field(..., description="Delay in hours relative to previous stage")
    subject: str = Field(..., description="Compelling, personalized subject line")
    body_markdown: str = Field(..., description="Markdown body copy")
    body_html: str = Field(..., description="Styled HTML email body for delivery")


class NurtureSequence(BaseModel):
    """Complete multi-stage nurture campaign tailored to a captured lead."""

    sequence_id: str = Field(
        default_factory=lambda: f"seq-{uuid.uuid4().hex[:10]}",
        description="Unique identifier for the nurture sequence",
    )
    lead_id: str = Field(..., description="Reference to the recipient lead")
    recipient_email: str = Field(..., description="Destination email address")
    product_name: str = Field(..., description="Brand or product driving the sequence")
    stages: List[NurtureEmail] = Field(
        default_factory=list,
        description="Chronological email stages",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of sequence synthesis",
    )


class LeadCaptureResponse(BaseModel):
    """API outcome response for lead submission."""

    success: bool = Field(..., description="Whether lead capture and intake succeeded")
    lead_id: str = Field(..., description="Assigned lead identifier")
    message: str = Field(..., description="Human-readable status summary")
    next_action: str = Field(..., description="Prompt or instructions for user frontend")
