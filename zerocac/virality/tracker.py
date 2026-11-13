"""SQLite referral tracking engine and milestone reward unlock coordinator."""

from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
import sqlite3
from typing import List, Optional, Tuple

from zerocac.virality.models import (
    LeaderboardEntry,
    ReferralStats,
    RewardTier,
    RewardTierId,
)

logger = logging.getLogger(__name__)

STANDARD_REWARDS = [
    RewardTier(
        tier_id=RewardTierId.GEO_PACKAGE_EXPORT,
        name="Princeton GEO Full Export",
        required_referrals=3,
        description="Unlock full export of Princeton GEO 40-60 word Answer-First definitions & JSON-LD schemas.",
    ),
    RewardTier(
        tier_id=RewardTierId.UNMETERED_INTERCEPTOR,
        name="Unmetered Interceptor Radar",
        required_referrals=10,
        description="Unlock unmetered 24/7 background social stream interception across Reddit, HN, and X.",
    ),
    RewardTier(
        tier_id=RewardTierId.CUSTOM_DOMAIN_PROXY,
        name="Custom Domain Edge Proxy",
        required_referrals=25,
        description="Unlock automated Cloudflare Worker custom domain edge routing for all pSEO clusters.",
    ),
]


class ReferralTracker:
    """Tracks referral visits, conversions, calculates viral K-factor, and manages rewards."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize referral store and ensure database tables exist."""
        self.db_path = db_path or str(Path.cwd() / "zerocac_virality.db")
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with row factories enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Create tables for referral accounts and tracked events."""
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS referral_accounts (
                        user_email TEXT PRIMARY KEY,
                        referral_code TEXT UNIQUE NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS referral_events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        referral_code TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        visitor_id TEXT,
                        referred_email TEXT,
                        created_at TEXT NOT NULL
                    )
                    """
                )
        finally:
            conn.close()

    def _generate_referral_code(self, email: str) -> str:
        """Derive a consistent deterministic short code from user email."""
        h = hashlib.sha256(email.lower().strip().encode("utf-8")).hexdigest()
        return f"ref-{h[:8]}"

    async def get_or_create_referral_code(self, user_email: str) -> str:
        """Fetch existing referral code or register a new user in the referral engine."""
        email = user_email.lower().strip()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT referral_code FROM referral_accounts WHERE user_email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return row["referral_code"]

            ref_code = self._generate_referral_code(email)
            now_utc = datetime.now(timezone.utc).isoformat()
            with conn:
                cursor.execute(
                    "INSERT INTO referral_accounts (user_email, referral_code, created_at) VALUES (?, ?, ?)",
                    (email, ref_code, now_utc),
                )
            return ref_code
        finally:
            conn.close()

    async def record_click(self, ref_code: str, visitor_id: Optional[str] = None) -> bool:
        """Log a click arrival event for a given referral link."""
        now_utc = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO referral_events (referral_code, event_type, visitor_id, created_at) VALUES (?, 'click', ?, ?)",
                    (ref_code, visitor_id or "anon", now_utc),
                )
                return True
        finally:
            conn.close()

    async def record_conversion(self, ref_code: str, referred_email: str) -> bool:
        """Log a signup or lead capture event driven by a referrer."""
        now_utc = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO referral_events (referral_code, event_type, referred_email, created_at)
                    VALUES (?, 'conversion', ?, ?)
                    """,
                    (ref_code, referred_email.lower().strip(), now_utc),
                )
                return True
        finally:
            conn.close()

    async def get_stats(self, identifier: str, base_url: str = "https://zerocac.org") -> ReferralStats:
        """Compute live K-factor, conversions, and milestone rewards for a user."""
        email, ref_code = await self._resolve_account(identifier)
        clicks, conversions = self._count_events(ref_code)

        conversion_rate = (conversions / clicks) if clicks > 0 else 0.0
        # K-factor = invites sent x conversion rate (assuming 3 invites per user)
        k_factor = round(3.5 * conversion_rate, 2)

        unlocked, next_tier = self._calculate_milestone_tiers(conversions)
        referral_url = f"{base_url.rstrip('/')}?ref={ref_code}"

        return ReferralStats(
            user_email=email,
            referral_code=ref_code,
            referral_url=referral_url,
            total_clicks=clicks,
            total_conversions=conversions,
            conversion_rate=round(conversion_rate, 4),
            k_factor=k_factor,
            unlocked_rewards=unlocked,
            next_milestone=next_tier,
        )

    async def _resolve_account(self, identifier: str) -> Tuple[str, str]:
        """Resolve either email or referral code to a full (email, code) pair."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if "@" in identifier:
                email = identifier.lower().strip()
                ref_code = await self.get_or_create_referral_code(email)
                return email, ref_code

            cursor.execute("SELECT user_email, referral_code FROM referral_accounts WHERE referral_code = ?", (identifier,))
            row = cursor.fetchone()
            if row:
                return row["user_email"], row["referral_code"]
            return f"{identifier}@referral.user", identifier
        finally:
            conn.close()

    def _count_events(self, ref_code: str) -> Tuple[int, int]:
        """Count total clicks and conversions for a referral code."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) AS c FROM referral_events WHERE referral_code = ? AND event_type = 'click'",
                (ref_code,),
            )
            clicks = cursor.fetchone()["c"]

            cursor.execute(
                "SELECT COUNT(*) AS c FROM referral_events WHERE referral_code = ? AND event_type = 'conversion'",
                (ref_code,),
            )
            conversions = cursor.fetchone()["c"]
            return clicks, conversions
        finally:
            conn.close()

    def _calculate_milestone_tiers(self, conversions: int) -> Tuple[List[RewardTier], Optional[RewardTier]]:
        """Determine which milestone rewards are unlocked and the next target."""
        unlocked: List[RewardTier] = []
        next_tier: Optional[RewardTier] = None

        for tier in STANDARD_REWARDS:
            is_unlocked = conversions >= tier.required_referrals
            tier_copy = tier.model_copy(update={"is_unlocked": is_unlocked})
            if is_unlocked:
                unlocked.append(tier_copy)
            elif next_tier is None:
                next_tier = tier_copy

        return unlocked, next_tier

    async def get_leaderboard(self, limit: int = 10) -> List[LeaderboardEntry]:
        """Generate ranked leaderboard of users with highest referrals and ad savings."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.user_email, COUNT(e.event_id) AS total_referrals
                FROM referral_accounts a
                LEFT JOIN referral_events e ON a.referral_code = e.referral_code AND e.event_type = 'conversion'
                GROUP BY a.user_email
                ORDER BY total_referrals DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            entries: List[LeaderboardEntry] = []

            for idx, row in enumerate(rows, start=1):
                email = row["user_email"]
                conversions = row["total_referrals"]
                handle = f"{email[:3]}***@{email.split('@')[-1]}" if "@" in email else email
                savings = conversions * 18 * 35.0  # 18 visits/lead @ $35 CPC

                title = "Organic Novice"
                if conversions >= 25:
                    title = "CAC Exterminator Grandmaster"
                elif conversions >= 10:
                    title = "Growth Architect"
                elif conversions >= 3:
                    title = "Organic Vanguard"

                entries.append(
                    LeaderboardEntry(
                        rank=idx,
                        user_handle=handle,
                        referrals_driven=conversions,
                        ad_dollars_saved_usd=savings,
                        badge_title=title,
                    )
                )

            return entries
        finally:
            conn.close()
