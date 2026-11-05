"""Generic and Headless CMS webhook dispatcher for automated syndication."""

import logging
import os
from typing import Optional
import httpx

from zerocac.dispatchers.models import DispatchChannel, DispatchItem, DispatchResult

logger = logging.getLogger(__name__)


class CMSWebhookDispatcher:
    """Dispatches approved assets to Webhooks, Ghost, Webflow, or Slack."""

    def __init__(self, default_webhook_url: Optional[str] = None) -> None:
        """Initialize dispatcher with optional fallback webhook."""
        self.default_webhook_url = default_webhook_url or os.getenv("DISTRIBUTION_WEBHOOK_URL")

    async def dispatch(
        self,
        item: DispatchItem,
        webhook_url: Optional[str] = None,
        dry_run: bool = False,
    ) -> DispatchResult:
        """Deliver approved payload to external webhook or CMS endpoint."""
        target_url = webhook_url or item.target_destination or self.default_webhook_url

        if not target_url or dry_run:
            logger.info("Simulated webhook distribution for item %s to %s", item.item_id, item.channel.value)
            return DispatchResult(
                success=True,
                item_id=item.item_id,
                channel=item.channel,
                external_post_id=f"sim-wh-{item.item_id}",
            )

        payload = {
            "item_id": item.item_id,
            "channel": item.channel.value,
            "title": item.title,
            "content": item.content,
            "metadata": item.metadata,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(target_url, json=payload)
                if res.status_code in [200, 201, 202]:
                    return DispatchResult(
                        success=True,
                        item_id=item.item_id,
                        channel=item.channel,
                        external_post_id=f"wh-status-{res.status_code}",
                    )
                return DispatchResult(
                    success=False,
                    item_id=item.item_id,
                    channel=item.channel,
                    error_message=f"Webhook returned error {res.status_code}: {res.text}",
                )
        except httpx.HTTPError as exc:
            return DispatchResult(
                success=False,
                item_id=item.item_id,
                channel=item.channel,
                error_message=f"Network error during webhook delivery: {str(exc)}",
            )
