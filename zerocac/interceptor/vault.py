"""Multi-account vault managing social credentials and safety rotation."""

import logging
from typing import Dict, List, Optional

from zerocac.interceptor.camouflage import CamouflageEngine
from zerocac.interceptor.models import AccountCredential, SocialPlatform

logger = logging.getLogger(__name__)


class AccountVault:
    """Manages credentials and selects optimal accounts based on karma and post ratio."""

    def __init__(self, camouflage: Optional[CamouflageEngine] = None) -> None:
        """Initialize vault with camouflage engine."""
        self.camouflage = camouflage or CamouflageEngine()
        self._accounts: Dict[str, AccountCredential] = {}
        self._seed_default_accounts()

    def register_account(self, account: AccountCredential) -> None:
        """Add or update an account in the vault."""
        self._accounts[account.account_id] = account

    def get_account(self, account_id: str) -> Optional[AccountCredential]:
        """Fetch account by ID."""
        return self._accounts.get(account_id)

    def select_safe_account(self, platform: SocialPlatform) -> Optional[AccountCredential]:
        """Pick the safest account on the platform with lowest promo ratio and highest karma."""
        candidates = [
            acc for acc in self._accounts.values()
            if acc.platform == platform and self.camouflage.is_account_safe(acc)
        ]
        if not candidates:
            # Fall back to any active account on that platform
            active = [acc for acc in self._accounts.values() if acc.platform == platform and acc.is_active]
            return active[0] if active else None

        # Sort by lowest promotional ratio then highest karma
        candidates.sort(key=lambda a: (a.promotional_ratio, -a.karma))
        return candidates[0]

    def list_accounts(self) -> List[AccountCredential]:
        """Return all registered accounts."""
        return list(self._accounts.values())

    def _seed_default_accounts(self) -> None:
        """Seed initial default developer accounts."""
        self.register_account(
            AccountCredential(
                platform=SocialPlatform.REDDIT,
                username="ZeroCAC_Architect",
                karma=650,
                account_age_days=320,
                non_promotional_count=18,
                promotional_count=1,
            )
        )
        self.register_account(
            AccountCredential(
                platform=SocialPlatform.X_TWITTER,
                username="zerocac_dev",
                karma=1200,
                account_age_days=450,
                non_promotional_count=25,
                promotional_count=2,
            )
        )
