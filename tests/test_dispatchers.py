"""Unit tests for Phase 3 Autonomous Webhook and Multi-Channel Dispatcher."""

from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from zerocac.cli import app as cli_app
from zerocac.dispatchers.cms import CMSWebhookDispatcher
from zerocac.dispatchers.models import (
    ApprovalStatus,
    DispatchChannel,
    DispatchItem,
)
from zerocac.dispatchers.queue import DispatchQueue
from zerocac.dispatchers.telegram import TelegramApprovalBot
from zerocac.web.app import app as fastapi_app

runner = CliRunner()
client = TestClient(fastapi_app)


@pytest.fixture
def temp_queue(tmp_path: Path) -> DispatchQueue:
    """Fixture providing isolated temporary SQLite dispatch queue."""
    db_file = tmp_path / "test_dispatch.db"
    return DispatchQueue(db_path=str(db_file))


@pytest.fixture
def sample_item() -> DispatchItem:
    """Fixture providing a sample queued distribution item."""
    return DispatchItem(
        channel=DispatchChannel.TELEGRAM,
        title="Contrarian SaaS Growth Thread",
        content="Most founders burn $10k on ads before getting their first 100 users.",
        target_destination="founder-chat-id",
        metadata={"tags": ["saas", "zero-cac"]},
    )


@pytest.mark.asyncio
async def test_telegram_bot_dry_run(sample_item: DispatchItem) -> None:
    """Ensure Telegram bot dry run succeeds without network calls."""
    # Arrange
    bot = TelegramApprovalBot()

    # Act
    res = await bot.send_approval_request(sample_item, dry_run=True)

    # Assert
    assert res.success is True
    assert res.channel == DispatchChannel.TELEGRAM
    assert "sim-tg-" in (res.external_post_id or "")


@pytest.mark.asyncio
async def test_cms_dispatcher_dry_run(sample_item: DispatchItem) -> None:
    """Ensure CMS webhook dispatcher dry run succeeds without remote endpoint."""
    # Arrange
    cms = CMSWebhookDispatcher()

    # Act
    res = await cms.dispatch(sample_item, dry_run=True)

    # Assert
    assert res.success is True
    assert "sim-wh-" in (res.external_post_id or "")


@pytest.mark.asyncio
async def test_dispatch_queue_workflow(temp_queue: DispatchQueue, sample_item: DispatchItem) -> None:
    """Ensure item can be enqueued, listed, and approved."""
    # Act 1: Enqueue
    enqueued = await temp_queue.enqueue(sample_item)
    assert enqueued.status == ApprovalStatus.PENDING

    # Act 2: List
    pending_items = await temp_queue.list_queue(status=ApprovalStatus.PENDING)
    assert len(pending_items) == 1
    assert pending_items[0].title == "Contrarian SaaS Growth Thread"

    # Act 3: Approve and dispatch
    result = await temp_queue.approve_and_dispatch(enqueued.item_id, dry_run=True)
    assert result.success is True

    # Act 4: Verify status updated
    updated_item = await temp_queue.get_item(enqueued.item_id)
    assert updated_item is not None
    assert updated_item.status == ApprovalStatus.DISPATCHED
    assert updated_item.dispatched_at is not None


@pytest.mark.asyncio
async def test_dispatch_queue_reject(temp_queue: DispatchQueue, sample_item: DispatchItem) -> None:
    """Ensure item rejection transitions status to REJECTED."""
    # Arrange
    await temp_queue.enqueue(sample_item)

    # Act
    rejected = await temp_queue.reject(sample_item.item_id)
    item = await temp_queue.get_item(sample_item.item_id)

    # Assert
    assert rejected is True
    assert item is not None
    assert item.status == ApprovalStatus.REJECTED


def test_api_dispatch_endpoints(tmp_path: Path) -> None:
    """Ensure FastAPI endpoints for enqueue and approval operate properly."""
    db_path = str(tmp_path / "api_dispatch.db")

    with patch("zerocac.web.routers.dispatch.DispatchQueue", return_value=DispatchQueue(db_path=db_path)):
        # 1. Enqueue
        req = {
            "channel": "webhook",
            "title": "Blog Post Teardown",
            "content": "# Why Paid Ads Burn Money\n\nOrganic compounding wins.",
            "target_destination": "https://example.com/webhook",
        }
        res_post = client.post("/api/v1/dispatch/enqueue", json=req)
        assert res_post.status_code == 201
        item_id = res_post.json()["item_id"]

        # 2. List queue
        res_get = client.get("/api/v1/dispatch/queue")
        assert res_get.status_code == 200
        assert len(res_get.json()) >= 1

        # 3. Approve
        res_approve = client.post(f"/api/v1/dispatch/{item_id}/approve?dry_run=true")
        assert res_approve.status_code == 200
        assert res_approve.json()["success"] is True


def test_cli_dispatch_commands(tmp_path: Path, sample_item: DispatchItem) -> None:
    """Ensure Typer CLI dispatch subcommands execute cleanly."""
    queue = DispatchQueue(db_path=str(tmp_path / "cli_dispatch.db"))

    with patch("zerocac.cli.DispatchQueue", return_value=queue):
        import asyncio
        asyncio.run(queue.enqueue(sample_item))

        # Test queue listing
        res_list = runner.invoke(cli_app, ["dispatch", "queue"])
        assert res_list.exit_code == 0
        assert "Contrarian" in res_list.output
        assert "TELEGRAM" in res_list.output

        # Test approval
        res_app = runner.invoke(cli_app, ["dispatch", "approve", sample_item.item_id, "--dry-run"])
        assert res_app.exit_code == 0
        assert "Successfully published" in res_app.output
