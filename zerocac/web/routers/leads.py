"""FastAPI router for inbound lead capture and behavioral email nurturing."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from zerocac.analyzer.models import ProductProfile
from zerocac.leads.dispatcher import ResendDispatcher
from zerocac.leads.models import Lead, LeadCaptureResponse, LeadStatus, NurtureSequence
from zerocac.leads.nurture import NurtureEngine
from zerocac.leads.repository import LeadRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/leads", tags=["Leads & Nurturing"])


class CaptureLeadApiRequest(BaseModel):
    """Payload submitted when a user enters their email into a microtool."""

    email: EmailStr = Field(..., description="Prospect email address")
    full_name: Optional[str] = Field(default=None, description="Prospect name")
    company: Optional[str] = Field(default=None, description="Prospect organization")
    project_slug: str = Field(..., description="Slug of the microtool where email was entered")
    tool_inputs: Dict[str, Any] = Field(default_factory=dict, description="Active calculator parameters")
    dry_run: bool = Field(default=False, description="Simulate dispatch without sending real email")


@router.post("/capture", response_model=LeadCaptureResponse, status_code=status.HTTP_201_CREATED)
async def capture_lead(payload: CaptureLeadApiRequest) -> LeadCaptureResponse:
    """Capture prospect email from interactive tool and trigger nurture sequence."""
    repo = LeadRepository()
    lead = Lead(
        email=payload.email,
        full_name=payload.full_name,
        company=payload.company,
        project_slug=payload.project_slug,
        tool_inputs=payload.tool_inputs,
        intent_score=85 if payload.tool_inputs else 70,
    )
    await repo.save_lead(lead)

    # Initialize behavioral nurture sequence
    profile = ProductProfile(
        product_name=payload.project_slug.replace("-", " ").title(),
        category="Organic Growth Engine",
        one_liner="Scale without paid ads",
        core_problem="Paid ads are expensive and burn cash",
        solution_mechanism="Autonomous micro-tools and GEO assets",
        unique_value_proposition="Scale to $0 CAC with permanent equity",
        key_features=["Micro-tools", "Live Radar", "AEO Comparison Pages"],
    )

    engine = NurtureEngine()
    sequence = engine.build_default_sequence(lead, profile)
    dispatcher = ResendDispatcher()

    # Dispatch Stage 1 immediately
    if sequence.stages:
        await dispatcher.dispatch_stage(
            stage=sequence.stages[0],
            recipient=str(lead.email),
            dry_run=payload.dry_run,
        )
        await repo.update_status(lead.lead_id, LeadStatus.NURTURED)

    return LeadCaptureResponse(
        success=True,
        lead_id=lead.lead_id,
        message="Prospect captured and Stage 1 diagnostic email dispatched.",
        next_action="Check inbox for full analytical breakdown.",
    )


@router.get("", response_model=List[Lead], status_code=status.HTTP_200_OK)
async def list_captured_leads(
    project_slug: Optional[str] = Query(default=None, description="Filter leads by project slug"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum leads to return"),
) -> List[Lead]:
    """Retrieve captured leads with optional project filter."""
    repo = LeadRepository()
    return await repo.list_leads(project_slug=project_slug, limit=limit)


@router.post("/{lead_id}/nurture", response_model=NurtureSequence, status_code=status.HTTP_200_OK)
async def generate_and_dispatch_nurture(
    lead_id: str,
    product_name: str = Query(default="ZeroCAC", description="Product brand name"),
    dry_run: bool = Query(default=True, description="Whether to simulate email delivery"),
) -> NurtureSequence:
    """Generate complete 3-stage nurture sequence and dispatch Stage 1."""
    repo = LeadRepository()
    lead = await repo.get_lead(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found",
        )

    profile = ProductProfile(
        product_name=product_name,
        category="Growth Engine",
        one_liner="Scale to $0 CAC",
        core_problem="Paid ad fatigue",
        solution_mechanism="Autonomous organic marketing",
        unique_value_proposition="Compounding $0 CAC assets",
        key_features=["Calculators", "GEO Pages"],
    )

    engine = NurtureEngine()
    sequence = engine.build_default_sequence(lead, profile)
    dispatcher = ResendDispatcher()

    if sequence.stages:
        await dispatcher.dispatch_stage(
            stage=sequence.stages[0],
            recipient=str(lead.email),
            dry_run=dry_run,
        )
        await repo.update_status(lead.lead_id, LeadStatus.NURTURED)

    return sequence
