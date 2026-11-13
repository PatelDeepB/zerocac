"""Persistent SQLite store for A/B experiments and multi-armed bandit state."""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import List, Optional

from zerocac.telemetry.experiment import ABExperiment

logger = logging.getLogger(__name__)


class ExperimentStore:
    """Async-compatible SQLite repository for saving and retrieving A/B experiments."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize database connection and create tables."""
        self.db_path = db_path or str(Path.cwd() / "zerocac_experiments.db")
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with row factories."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Create experiments table if missing."""
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS experiments (
                        asset_slug TEXT PRIMARY KEY,
                        experiment_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        winner_variant_id TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
        finally:
            conn.close()

    async def save_experiment(self, experiment: ABExperiment) -> None:
        """Persist or update an active experiment."""
        now_utc = datetime.now(timezone.utc).isoformat()
        payload = experiment.model_dump_json()

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO experiments (
                        asset_slug, experiment_id, status, winner_variant_id,
                        created_at, updated_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        experiment.asset_slug,
                        experiment.experiment_id,
                        experiment.status,
                        experiment.winner_variant_id,
                        experiment.created_at or now_utc,
                        experiment.updated_at or now_utc,
                        payload,
                    ),
                )
        finally:
            conn.close()

    async def get_experiment(self, asset_slug: str) -> Optional[ABExperiment]:
        """Retrieve an experiment for a given asset slug."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT payload_json FROM experiments WHERE asset_slug = ?",
                (asset_slug,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            data = json.loads(row["payload_json"])
            return ABExperiment(**data)
        finally:
            conn.close()

    async def list_experiments(self) -> List[ABExperiment]:
        """List all experiments stored in the repository."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT payload_json FROM experiments ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                try:
                    data = json.loads(row["payload_json"])
                    results.append(ABExperiment(**data))
                except (json.JSONDecodeError, ValueError):
                    continue
            return results
        finally:
            conn.close()
