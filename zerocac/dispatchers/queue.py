"""Persistent approval queue coordinating outbound syndication."""

import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import List, Optional

from zerocac.dispatchers.cms import CMSWebhookDispatcher
from zerocac.dispatchers.models import (
    ApprovalStatus,
    DispatchChannel,
    DispatchItem,
    DispatchResult,
)
from zerocac.dispatchers.telegram import TelegramApprovalBot

logger = logging.getLogger(__name__)

DEFAULT_QUEUE_DB = ".zerocac/dispatch.db"


class DispatchQueue:
    """Coordinates items awaiting user approval and triggers downstream dispatchers."""

    def __init__(self, db_path: str = DEFAULT_QUEUE_DB) -> None:
        """Initialize queue database schema."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db_sync()

    def _init_db_sync(self) -> None:
        """Create SQLite schema if not already initialized."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dispatch_queue (
                    item_id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    target_destination TEXT,
                    metadata TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    dispatched_at TEXT
                )
                """
            )
            conn.commit()

    async def enqueue(self, item: DispatchItem) -> DispatchItem:
        """Add an asset to the approval queue."""
        return await asyncio.to_thread(self._enqueue_sync, item)

    def _enqueue_sync(self, item: DispatchItem) -> DispatchItem:
        """Synchronous insert into dispatch_queue table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO dispatch_queue
                (item_id, channel, title, content, target_destination, metadata, status, created_at, dispatched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.item_id,
                    item.channel.value,
                    item.title,
                    item.content,
                    item.target_destination,
                    json.dumps(item.metadata),
                    item.status.value,
                    item.created_at,
                    item.dispatched_at,
                ),
            )
            conn.commit()
        return item

    async def get_item(self, item_id: str) -> Optional[DispatchItem]:
        """Fetch queue item by identifier."""
        return await asyncio.to_thread(self._get_item_sync, item_id)

    def _get_item_sync(self, item_id: str) -> Optional[DispatchItem]:
        """Synchronous select query."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM dispatch_queue WHERE item_id = ?", (item_id,)).fetchone()
            if not row:
                return None
            return self._row_to_item(row)

    async def list_queue(
        self, status: Optional[ApprovalStatus] = None, limit: int = 50
    ) -> List[DispatchItem]:
        """List queue items with optional status filtering."""
        return await asyncio.to_thread(self._list_queue_sync, status, limit)

    def _list_queue_sync(self, status: Optional[ApprovalStatus], limit: int) -> List[DispatchItem]:
        """Synchronous query for queued items."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM dispatch_queue WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM dispatch_queue ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_item(r) for r in rows]

    async def approve_and_dispatch(self, item_id: str, dry_run: bool = False) -> DispatchResult:
        """Mark an item as approved and immediately fire channel dispatcher."""
        item = await self.get_item(item_id)
        if not item:
            return DispatchResult(
                success=False,
                item_id=item_id,
                channel=DispatchChannel.WEBHOOK,
                error_message=f"Item '{item_id}' not found",
            )

        if item.channel == DispatchChannel.TELEGRAM:
            bot = TelegramApprovalBot()
            result = await bot.send_approval_request(item, dry_run=dry_run)
        else:
            cms = CMSWebhookDispatcher()
            result = await cms.dispatch(item, dry_run=dry_run)

        if result.success:
            await self._update_status(item_id, ApprovalStatus.DISPATCHED)
        return result

    async def reject(self, item_id: str) -> bool:
        """Mark item as rejected to prevent dispatch."""
        return await self._update_status(item_id, ApprovalStatus.REJECTED)

    async def _update_status(self, item_id: str, status: ApprovalStatus) -> bool:
        """Update approval status asynchronously."""
        now = datetime.now(timezone.utc).isoformat() if status == ApprovalStatus.DISPATCHED else None
        return await asyncio.to_thread(self._update_status_sync, item_id, status, now)

    def _update_status_sync(self, item_id: str, status: ApprovalStatus, dispatched_at: Optional[str]) -> bool:
        """Synchronous status update."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE dispatch_queue SET status = ?, dispatched_at = COALESCE(?, dispatched_at) WHERE item_id = ?",
                (status.value, dispatched_at, item_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def _row_to_item(self, row: sqlite3.Row) -> DispatchItem:
        """Map SQLite row to DispatchItem model."""
        return DispatchItem(
            item_id=row["item_id"],
            channel=DispatchChannel(row["channel"]),
            title=row["title"],
            content=row["content"],
            target_destination=row["target_destination"],
            metadata=json.loads(row["metadata"] or "{}"),
            status=ApprovalStatus(row["status"]),
            created_at=row["created_at"],
            dispatched_at=row["dispatched_at"],
        )
