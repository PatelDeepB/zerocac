"""Telegram notification client with inline 1-click approval buttons."""

import logging
import os
from typing import Optional
import httpx

from zerocac.dispatchers.models import DispatchChannel, DispatchItem, DispatchResult

logger = logging.getLogger(__name__)


class TelegramApprovalBot:
    """Dispatches distribution drafts to Telegram with interactive approve/reject callbacks."""

    def __init__(self, bot_token: Optional[str] = None, default_chat_id: Optional[str] = None) -> None:
        """Initialize bot with credentials."""
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.default_chat_id = default_chat_id or os.getenv("TELEGRAM_CHAT_ID")

    async def send_approval_request(
        self,
        item: DispatchItem,
        chat_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> DispatchResult:
        """Send formatted card to Telegram with inline approval buttons."""
        target_chat = chat_id or self.default_chat_id or "default-chat"

        if not self.bot_token or dry_run:
            logger.info("Simulated Telegram approval card dispatched for %s (%s)", item.item_id, item.channel.value)
            return DispatchResult(
                success=True,
                item_id=item.item_id,
                channel=DispatchChannel.TELEGRAM,
                external_post_id=f"sim-tg-{item.item_id}",
            )

        endpoint = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        message_text = (
            f"<b>ZeroCAC Growth Radar: Action Required</b>\n\n"
            f"<b>Target:</b> {item.channel.value.upper()}\n"
            f"<b>Headline:</b> {item.title}\n\n"
            f"<code>{item.content[:800]}</code>\n\n"
            f"Tap below to approve instant distribution:"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "Approve & Post",
                        "callback_data": f"approve:{item.item_id}",
                    },
                    {
                        "text": "Discard",
                        "callback_data": f"reject:{item.item_id}",
                    },
                ]
            ]
        }

        payload = {
            "chat_id": target_chat,
            "text": message_text,
            "parse_mode": "HTML",
            "reply_markup": inline_keyboard,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    msg_id = str(data.get("result", {}).get("message_id", "tg-ok"))
                    return DispatchResult(
                        success=True,
                        item_id=item.item_id,
                        channel=DispatchChannel.TELEGRAM,
                        external_post_id=msg_id,
                    )
                return DispatchResult(
                    success=False,
                    item_id=item.item_id,
                    channel=DispatchChannel.TELEGRAM,
                    error_message=f"Telegram API error {res.status_code}: {res.text}",
                )
        except httpx.HTTPError as exc:
            return DispatchResult(
                success=False,
                item_id=item.item_id,
                channel=DispatchChannel.TELEGRAM,
                error_message=f"Network error: {str(exc)}",
            )
