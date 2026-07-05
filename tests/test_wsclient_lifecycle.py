from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

from centrometal_web_boiler.WebBoilerWsClient import WebBoilerWsClient  # noqa: E402


def _client() -> WebBoilerWsClient:
    async def noop(*args, **kwargs):
        return None

    return WebBoilerWsClient(None, noop, noop, noop, noop)


def test_ws_client_is_not_running_before_start() -> None:
    client = _client()
    assert client.is_running() is False


def test_ws_client_is_running_with_active_task() -> None:
    async def runner() -> None:
        client = _client()
        client._task = asyncio.create_task(asyncio.sleep(60))
        try:
            assert client.is_running() is True
        finally:
            client._task.cancel()
            try:
                await client._task
            except asyncio.CancelledError:
                pass

    asyncio.run(runner())


def test_ws_client_is_not_running_after_task_done() -> None:
    async def runner() -> None:
        client = _client()
        client._task = asyncio.create_task(asyncio.sleep(0))
        await client._task
        assert client.is_running() is False

    asyncio.run(runner())
