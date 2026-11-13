"""Persistent SQLite storage engine for interceptor deduplication and queue state."""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from zerocac.interceptor.models import InterceptOpportunity

logger = logging.getLogger(__name__)


class InterceptorStore:
    """Async-compatible SQLite repository for stream deduplication and opportunity tracking."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize SQLite store and run migration schema."""
        self.db_path = db_path or str(Path.cwd() / "zerocac_interceptor.db")
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Create required tables for stream deduplication and opportunity tracking."""
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS seen_posts (
                        post_id TEXT PRIMARY KEY,
                        platform TEXT NOT NULL,
                        first_seen_at TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS intercept_opportunities (
                        opportunity_id TEXT PRIMARY KEY,
                        post_id TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        subreddit_or_topic TEXT NOT NULL,
                        intent_score INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
        finally:
            conn.close()

    async def is_seen(self, post_id: str) -> bool:
        """Check if an external post or comment has already been inspected."""
        if not post_id:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM seen_posts WHERE post_id = ?", (post_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    async def mark_seen(self, post_id: str, platform: str) -> None:
        """Record an external post ID into seen index to prevent re-processing."""
        if not post_id:
            return
        now_utc = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO seen_posts (post_id, platform, first_seen_at)
                    VALUES (?, ?, ?)
                    """,
                    (post_id, platform, now_utc),
                )
        finally:
            conn.close()

    async def save_opportunity(self, opportunity: InterceptOpportunity) -> None:
        """Persist a qualified buyer opportunity to the database."""
        now_utc = datetime.now(timezone.utc).isoformat()
        payload = opportunity.model_dump_json()

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO intercept_opportunities (
                        opportunity_id, post_id, platform, subreddit_or_topic,
                        intent_score, status, created_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        opportunity.opportunity_id,
                        opportunity.post_id,
                        opportunity.platform.value,
                        opportunity.subreddit_or_topic,
                        opportunity.intent_score,
                        opportunity.status,
                        now_utc,
                        payload,
                    ),
                )
        finally:
            conn.close()

    async def get_opportunity(self, opportunity_id: str) -> Optional[InterceptOpportunity]:
        """Retrieve a single opportunity by its unique identifier."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT payload_json FROM intercept_opportunities WHERE opportunity_id = ?",
                (opportunity_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            data = json.loads(row["payload_json"])
            return InterceptOpportunity(**data)
        finally:
            conn.close()

    async def list_opportunities(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[InterceptOpportunity]:
        """List persisted opportunities with optional status filter."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    """
                    SELECT payload_json FROM intercept_opportunities
                    WHERE status = ?
                    ORDER BY intent_score DESC, created_at DESC
                    LIMIT ?
                    """,
                    (status, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT payload_json FROM intercept_opportunities
                    ORDER BY intent_score DESC, created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()
            results: List[InterceptOpportunity] = []
            for row in rows:
                try:
                    data = json.loads(row["payload_json"])
                    results.append(InterceptOpportunity(**data))
                except (json.JSONDecodeError, ValueError):
                    continue
            return results
        finally:
            conn.close()

    async def update_opportunity_status(self, opportunity_id: str, new_status: str) -> bool:
        """Update the workflow state of a stored opportunity."""
        opp = await self.get_opportunity(opportunity_id)
        if not opp:
            return False

        opp.status = new_status
        payload = opp.model_dump_json()

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE intercept_opportunities
                    SET status = ?, payload_json = ?
                    WHERE opportunity_id = ?
                    """,
                    (new_status, payload, opportunity_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()
