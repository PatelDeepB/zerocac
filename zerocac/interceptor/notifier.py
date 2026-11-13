"""Instant push notification alerts for high-agony buyer signals."""

import logging
import os
from typing import Optional
import httpx

from zerocac.interceptor.models import InterceptOpportunity

logger = logging.getLogger(__name__)


class InterceptorNotifier:
    """Dispatches instant Telegram alerts with 1-click mobile action buttons."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        alert_threshold: int = 85,
    ) -> None:
        """Initialize Telegram notifier with credentials and threshold."""
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.alert_threshold = alert_threshold

    def format_alert_message(self, opp: InterceptOpportunity) -> str:
        """Format high-intent opportunity into an actionable Telegram card."""
        spend = opp.extracted_entities.get("monthly_spend")
        spend_str = f"${spend}/mo" if spend else "Unspecified"
        scale_str = opp.extracted_entities.get("scale_volume") or "Not stated"

        return (
            f"🚨 <b>HIGH BUYER AGONY DETECTED</b>\n\n"
            f"<b>Platform:</b> {opp.platform.value.upper()} (<code>{opp.subreddit_or_topic}</code>)\n"
            f"<b>Intent Score:</b> <b>{opp.intent_score}/100</b> ({opp.classification.value})\n"
            f"<b>Author:</b> u/{opp.author}\n"
            f"<b>Thread:</b> {opp.title}\n"
            f"<b>OP Spend & Scale:</b> {spend_str} | {scale_str}\n\n"
            f"<b>Synthesized Trojan Response ({opp.stealth_mode.value}):</b>\n"
            f"<code>{opp.synthesized_reply[:400]}...</code>\n\n"
            f"Tap below to approve instant distribution:"
        )

    def _build_inline_keyboard(self, opportunity_id: str) -> dict:
        """Build interactive Telegram callback buttons for mobile action."""
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "🚀 Approve & Post",
                        "callback_data": f"intercept_approve:{opportunity_id}",
                    },
                    {
                        "text": "❌ Dismiss",
                        "callback_data": f"intercept_reject:{opportunity_id}",
                    },
                ]
            ]
        }

    async def send_alert(
        self,
        opportunity: InterceptOpportunity,
        dry_run: bool = False,
    ) -> bool:
        """Send formatted alert card to Telegram if opportunity meets alert threshold."""
        if opportunity.intent_score < self.alert_threshold:
            return False

        if not self.bot_token or not self.chat_id or dry_run:
            logger.info(
                "Simulated Telegram push alert for %s (Score: %d/100)",
                opportunity.opportunity_id,
                opportunity.intent_score,
            )
            return True

        endpoint = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": self.format_alert_message(opportunity),
            "parse_mode": "HTML",
            "reply_markup": self._build_inline_keyboard(opportunity.opportunity_id),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(endpoint, json=payload)
                return res.status_code == 200
        except Exception as exc:
            logger.warning("Failed to dispatch Telegram alert for %s: %s", opportunity.opportunity_id, exc)
            return False
