"""FastAPI router for closed-loop telemetry analytics and self-healing reports."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from zerocac.telemetry.engine import TelemetryEngine
from zerocac.telemetry.experiment import (
    ABExperiment,
    ExperimentEngine,
    ExperimentVariant,
)
from zerocac.telemetry.models import AssetMetrics, TelemetryAuditReport
from zerocac.telemetry.store import ExperimentStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry & Self-Tuning"])


class CreateExperimentPayload(BaseModel):
    """Payload to synthesize A/B testing variants."""

    slug: str = Field(..., description="Asset identifier or slug")
    title: str = Field(..., description="Base headline or tool name")
    category: str = Field(default="Developer Tool", description="Product category")


class LogExperimentEventPayload(BaseModel):
    """Payload to record an event against an experimental variant."""

    slug: str = Field(..., description="Asset identifier")
    variant_id: str = Field(..., description="Interacted variant ID")
    event_type: str = Field(..., description="Event: impression, click, or conversion")


class OptimizeExperimentPayload(BaseModel):
    """Payload to trigger multi-armed bandit re-allocation."""

    slug: str = Field(..., description="Asset identifier")


@router.post("/experiments/create", response_model=ABExperiment, status_code=status.HTTP_200_OK)
async def create_ab_experiment(payload: CreateExperimentPayload) -> ABExperiment:
    """Generate 3 distinct psychological variants (utilitarian, contrarian, quantitative)."""
    store = ExperimentStore()
    existing = await store.get_experiment(payload.slug)
    if existing:
        return existing

    exp = ExperimentEngine.generate_experiment(payload.slug, payload.title, payload.category)
    await store.save_experiment(exp)
    return exp


@router.get("/experiments/{slug}", response_model=ABExperiment, status_code=status.HTTP_200_OK)
async def get_ab_experiment(slug: str) -> ABExperiment:
    """Retrieve active experiment state and current traffic allocations."""
    store = ExperimentStore()
    exp = await store.get_experiment(slug)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment for '{slug}' not found",
        )
    return exp


@router.post("/experiments/event", response_model=ABExperiment, status_code=status.HTTP_200_OK)
async def log_experiment_event(payload: LogExperimentEventPayload) -> ABExperiment:
    """Record an impression, click, or conversion for a variant."""
    store = ExperimentStore()
    exp = await store.get_experiment(payload.slug)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    success = ExperimentEngine.record_event(exp, payload.variant_id, payload.event_type)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid variant or event type")

    await store.save_experiment(exp)
    return exp


@router.post("/experiments/optimize", status_code=status.HTTP_200_OK)
async def optimize_experiment_allocations(payload: OptimizeExperimentPayload) -> dict:
    """Run multi-armed bandit algorithm allocating 80% traffic to top converter."""
    store = ExperimentStore()
    exp = await store.get_experiment(payload.slug)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    actions = ExperimentEngine.optimize_allocations(exp)
    await store.save_experiment(exp)
    return {"experiment": exp, "actions_taken": actions}


@router.get("/roi", response_model=Dict[str, float], status_code=status.HTTP_200_OK)
async def get_empirical_roi_proof(
    visitors: int = Query(default=14280, ge=0, description="Organic visitor volume"),
    leads: int = Query(default=42, ge=0, description="Captured qualified leads"),
    cpc: float = Query(default=35.0, ge=0.0, description="Benchmark search CPC in USD"),
    cpl: float = Query(default=180.0, ge=0.0, description="Benchmark qualified CPL in USD"),
) -> Dict[str, float]:
    """Compute empirical formula proving displacement of Google/Meta paid advertising."""
    return ExperimentEngine.calculate_empirical_roi(visitors, leads, cpc, cpl)



class AuditApiRequest(BaseModel):
    """Optional payload specifying manual telemetry metrics to evaluate."""

    assets: Optional[List[AssetMetrics]] = Field(
        default=None,
        description="Explicit asset telemetry to audit",
    )
    dry_run: bool = Field(default=False, description="Simulate self-tuning adjustments")


@router.get("/report", response_model=TelemetryAuditReport, status_code=status.HTTP_200_OK)
async def get_telemetry_report() -> TelemetryAuditReport:
    """Retrieve holistic organic ROI, ad dollars saved, and self-tuning health audit."""
    engine = TelemetryEngine()
    return await engine.audit_assets()


@router.post("/audit", response_model=TelemetryAuditReport, status_code=status.HTTP_200_OK)
async def execute_telemetry_audit(payload: AuditApiRequest) -> TelemetryAuditReport:
    """Run self-healing audit on specified or historical telemetry."""
    engine = TelemetryEngine()
    return await engine.audit_assets(manual_metrics=payload.assets, dry_run=payload.dry_run)
