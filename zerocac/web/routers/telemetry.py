"""FastAPI router for closed-loop telemetry analytics and self-healing reports."""

import logging
from typing import List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from zerocac.telemetry.engine import TelemetryEngine
from zerocac.telemetry.models import AssetMetrics, TelemetryAuditReport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry & Self-Tuning"])


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
