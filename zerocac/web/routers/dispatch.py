"""FastAPI router for distribution approval queue and multi-channel publishing."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from zerocac.dispatchers.models import (
    ApprovalStatus,
    DispatchChannel,
    DispatchItem,
    DispatchResult,
)
from zerocac.dispatchers.queue import DispatchQueue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dispatch", tags=["Distribution Dispatcher"])


class EnqueueApiRequest(BaseModel):
    """Payload to add content or draft into the approval queue."""

    channel: DispatchChannel = Field(..., description="Target distribution channel")
    title: str = Field(..., description="Post title or subject")
    content: str = Field(..., description="Full message body or article markdown")
    target_destination: Optional[str] = Field(default=None, description="Webhook URL or chat ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata parameters")


@router.post("/enqueue", response_model=DispatchItem, status_code=status.HTTP_201_CREATED)
async def enqueue_dispatch_item(payload: EnqueueApiRequest) -> DispatchItem:
    """Queue an asset for approval prior to external distribution."""
    queue = DispatchQueue()
    item = DispatchItem(
        channel=payload.channel,
        title=payload.title,
        content=payload.content,
        target_destination=payload.target_destination,
        metadata=payload.metadata,
    )
    return await queue.enqueue(item)


@router.get("/queue", response_model=List[DispatchItem], status_code=status.HTTP_200_OK)
async def list_dispatch_queue(
    status_filter: Optional[ApprovalStatus] = Query(default=None, alias="status", description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=500, description="Max items to retrieve"),
) -> List[DispatchItem]:
    """Retrieve items from the distribution queue."""
    queue = DispatchQueue()
    return await queue.list_queue(status=status_filter, limit=limit)


@router.post("/{item_id}/approve", response_model=DispatchResult, status_code=status.HTTP_200_OK)
async def approve_and_send(
    item_id: str,
    dry_run: bool = Query(default=False, description="Simulate delivery without contacting remote API"),
) -> DispatchResult:
    """Approve queued item and fire external channel dispatcher."""
    queue = DispatchQueue()
    result = await queue.approve_and_dispatch(item_id=item_id, dry_run=dry_run)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "Distribution failed",
        )
    return result


@router.post("/{item_id}/reject", status_code=status.HTTP_200_OK)
async def reject_dispatch_item(item_id: str) -> Dict[str, Any]:
    """Mark item as rejected to prevent external publishing."""
    queue = DispatchQueue()
    ok = await queue.reject(item_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{item_id}' not found",
        )
    return {"success": True, "item_id": item_id, "status": "rejected"}
