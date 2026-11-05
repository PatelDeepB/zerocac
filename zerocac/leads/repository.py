"""Thread-safe SQLite repository for managing captured organic leads."""

import asyncio
import json
import logging
from pathlib import Path
import sqlite3
from typing import List, Optional

from zerocac.leads.models import Lead, LeadStatus

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = ".zerocac/leads.db"


class LeadRepository:
    """Async repository managing persistent SQLite storage of inbound leads."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """Initialize repository and ensure schema is ready."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db_sync()

    def _init_db_sync(self) -> None:
        """Create SQLite schema if tables do not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    full_name TEXT,
                    company TEXT,
                    project_slug TEXT NOT NULL,
                    tool_inputs TEXT,
                    intent_score INTEGER DEFAULT 75,
                    status TEXT DEFAULT 'captured',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    async def save_lead(self, lead: Lead) -> Lead:
        """Save a new or updated lead asynchronously."""
        return await asyncio.to_thread(self._save_lead_sync, lead)

    def _save_lead_sync(self, lead: Lead) -> Lead:
        """Synchronous SQLite insert or replace operation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO leads
                (lead_id, email, full_name, company, project_slug, tool_inputs, intent_score, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead.lead_id,
                    str(lead.email),
                    lead.full_name,
                    lead.company,
                    lead.project_slug,
                    json.dumps(lead.tool_inputs),
                    lead.intent_score,
                    lead.status.value,
                    lead.created_at,
                ),
            )
            conn.commit()
        logger.info("Saved lead %s (%s) for %s", lead.lead_id, lead.email, lead.project_slug)
        return lead

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Fetch a specific lead by unique identifier."""
        return await asyncio.to_thread(self._get_lead_sync, lead_id)

    def _get_lead_sync(self, lead_id: str) -> Optional[Lead]:
        """Synchronous query for single lead."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Lead(
                lead_id=row["lead_id"],
                email=row["email"],
                full_name=row["full_name"],
                company=row["company"],
                project_slug=row["project_slug"],
                tool_inputs=json.loads(row["tool_inputs"] or "{}"),
                intent_score=row["intent_score"],
                status=LeadStatus(row["status"]),
                created_at=row["created_at"],
            )

    async def list_leads(
        self, project_slug: Optional[str] = None, limit: int = 50
    ) -> List[Lead]:
        """Retrieve recent leads with optional project slug filter."""
        return await asyncio.to_thread(self._list_leads_sync, project_slug, limit)

    def _list_leads_sync(self, project_slug: Optional[str], limit: int) -> List[Lead]:
        """Synchronous query for recent leads."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if project_slug:
                cursor = conn.execute(
                    "SELECT * FROM leads WHERE project_slug = ? ORDER BY created_at DESC LIMIT ?",
                    (project_slug, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [
                Lead(
                    lead_id=r["lead_id"],
                    email=r["email"],
                    full_name=r["full_name"],
                    company=r["company"],
                    project_slug=r["project_slug"],
                    tool_inputs=json.loads(r["tool_inputs"] or "{}"),
                    intent_score=r["intent_score"],
                    status=LeadStatus(r["status"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    async def update_status(self, lead_id: str, status: LeadStatus) -> bool:
        """Update lifecycle status of a lead."""
        return await asyncio.to_thread(self._update_status_sync, lead_id, status)

    def _update_status_sync(self, lead_id: str, status: LeadStatus) -> bool:
        """Synchronous SQLite update for status field."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE leads SET status = ? WHERE lead_id = ?",
                (status.value, lead_id),
            )
            conn.commit()
            return cursor.rowcount > 0
