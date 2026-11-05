"""Email delivery client supporting Resend API with dry-run simulation."""

import logging
import os
from typing import Any, Dict, Optional
import httpx

from zerocac.leads.models import NurtureEmail

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_FROM_SENDER = "ZeroCAC Growth <onboarding@resend.dev>"


class ResendDispatcher:
    """Dispatches nurture emails via Resend transactional email API."""

    def __init__(self, api_key: Optional[str] = None, from_sender: Optional[str] = None) -> None:
        """Initialize dispatcher with API key and verified sender address."""
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.from_sender = from_sender or os.getenv("RESEND_FROM_EMAIL") or DEFAULT_FROM_SENDER

    async def dispatch_stage(
        self,
        stage: NurtureEmail,
        recipient: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Send a single stage email to prospect."""
        if not self.api_key or dry_run:
            logger.info("Simulated nurture email dispatch (Step %d) to %s", stage.step, recipient)
            return {
                "success": True,
                "id": f"sim-re-{stage.step}-{recipient.split('@')[0]}",
                "recipient": recipient,
                "step": stage.step,
                "dry_run": True,
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": self.from_sender,
            "to": [recipient],
            "subject": stage.subject,
            "html": stage.body_html,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(RESEND_API_URL, headers=headers, json=payload)
                if res.status_code in [200, 201]:
                    data = res.json()
                    logger.info("Sent nurture email step %d to %s: %s", stage.step, recipient, data.get("id"))
                    return {
                        "success": True,
                        "id": data.get("id"),
                        "recipient": recipient,
                        "step": stage.step,
                        "dry_run": False,
                    }
                logger.error("Resend API rejected email (%d): %s", res.status_code, res.text)
                return {
                    "success": False,
                    "error": f"Resend error {res.status_code}: {res.text}",
                    "recipient": recipient,
                    "step": stage.step,
                }
        except httpx.HTTPError as exc:
            logger.error("Network error contacting Resend API: %s", str(exc))
            return {
                "success": False,
                "error": str(exc),
                "recipient": recipient,
                "step": stage.step,
            }
