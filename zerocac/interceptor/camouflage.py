"""Enforces the Reddit 9:1 anti-ban ratio and generates altruistic karma-building replies."""

import logging
from zerocac.interceptor.models import AccountCredential

logger = logging.getLogger(__name__)


class CamouflageEngine:
    """Guards account reputation and prevents automated spam blacklisting."""

    def __init__(self, max_promotional_ratio: float = 0.12, min_karma: int = 30) -> None:
        """Initialize engine with safety thresholds."""
        self.max_promotional_ratio = max_promotional_ratio
        self.min_karma = min_karma

    def is_account_safe(self, account: AccountCredential) -> bool:
        """Check whether account can safely dispatch a promotional comment."""
        if not account.is_active:
            return False
        if account.karma < self.min_karma:
            return False
        if account.account_age_days < 14:
            return False
        return account.promotional_ratio <= self.max_promotional_ratio

    def record_activity(self, account: AccountCredential, is_promotional: bool) -> AccountCredential:
        """Update account activity counters after dispatch."""
        if is_promotional:
            account.promotional_count += 1
        else:
            account.non_promotional_count += 1
        return account

    def generate_altruistic_reply(self, question: str, technical_domain: str = "DevOps") -> str:
        """Draft a 100% helpful, zero-pitch technical response to maintain karma ratios."""
        return (
            f"From my experience dealing with {technical_domain.lower()} architectures, "
            f"the primary bottleneck here usually comes down to asynchronous queue contention "
            f"and unindexed telemetry queries. A good first step before replacing components "
            f"is running an isolated profile against your staging ingress. Inspect your p99 "
            f"latency graphs and verify memory limits on your worker pods."
        )
