from __future__ import annotations

import asyncio
import logging
from typing import Optional

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from . import stomp
from .logging_utils import redact_account
from .HttpClient import build_verified_ssl_context
from .const import (
    WEB_BOILER_STOMP_DEVICE_TOPIC,
    WEB_BOILER_STOMP_LOGIN_PASSCODE,
    WEB_BOILER_STOMP_LOGIN_USERNAME,
    WEB_BOILER_STOMP_URL,
)


class WebBoilerWsClient:
    def __init__(self, hass, connected_callback, disconnected_callback, error_callback, data_callback):
        self.logger = logging.getLogger(__name__)
        self.hass = hass
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
        self.error_callback = error_callback
        self.data_callback = data_callback
        self.username = ""
        self.log_account = "account-unknown"
        self.subscription_index = 0
        self._ws = None
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._connected_event = asyncio.Event()
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def _create_ssl_context(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, build_verified_ssl_context)

    async def _heartbeat_loop(self, ws) -> None:
        # We wait on the stop event with a 30-second timeout instead of
        # ``asyncio.sleep(30)`` so that shutdown interrupts the loop
        # immediately rather than after the next tick.
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=30)
                # Stop event triggered — exit cleanly.
                return
            except asyncio.TimeoutError:
                pass
            try:
                await ws.send("\n")
            except asyncio.CancelledError:
                raise
            except Exception:
                # Heartbeat failure means the websocket is gone; the main
                # ``async for ws in connect(...)`` loop will reconnect. We
                # log at DEBUG with traceback so the cause isn't silently
                # lost (the previous ``except Exception: return`` swallowed
                # everything).
                self.logger.debug(
                    "WebBoilerWsClient heartbeat send failed (%s)",
                    self.log_account,
                    exc_info=True,
                )
                return

    async def _handle_connection(self, ws):
        self._ws = ws
        # New websocket -> new STOMP session -> subscription IDs start fresh.
        # Without this reset they grew unbounded across reconnects within a
        # single ``start()`` call.
        self.subscription_index = 0
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
        try:
            await ws.send(
                stomp.connect(
                    WEB_BOILER_STOMP_LOGIN_USERNAME,
                    WEB_BOILER_STOMP_LOGIN_PASSCODE,
                    "/",
                    (90000, 60000),
                )
            )
            frame_buffer = ""
            async for data in ws:
                if isinstance(data, bytes):
                    data = data.decode("utf-8", errors="ignore")
                frames, frame_buffer = stomp.extract_complete_frames(data, frame_buffer)
                for frame in frames:
                    try:
                        if frame["cmd"] == "HEARTBEAT":
                            continue
                        if frame["cmd"] == "ERROR":
                            await self.error_callback(ws, frame)
                            continue
                        if frame["cmd"] == "CONNECTED":
                            self._connected_event.set()
                            await self.connected_callback(ws, frame)
                            continue
                        await self.data_callback(ws, frame)
                    except asyncio.CancelledError:
                        raise
                    except Exception as err:
                        self.logger.exception(
                            "WebBoilerWsClient frame handler error (%s)",
                            self.log_account,
                        )
                        await self.error_callback(ws, err)
            if frame_buffer.strip("\n"):
                self.logger.debug(
                    "WebBoilerWsClient dropped incomplete frame buffer on socket close (%s): %r",
                    self.log_account,
                    frame_buffer[-200:],
                )
        finally:
            if self._heartbeat_task is not None:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_task = None
            self._ws = None
            self._connected_event.clear()

    async def _run(self):
        while not self._stop_event.is_set():
            ssl_ctx = await self._create_ssl_context()
            try:
                async for ws in connect(
                    WEB_BOILER_STOMP_URL,
                    ssl=ssl_ctx,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                ):
                    if self._stop_event.is_set():
                        break
                    close_code = None
                    close_reason = None
                    try:
                        await self._handle_connection(ws)
                    except ConnectionClosed as exc:
                        close_code = getattr(exc, "code", None)
                        close_reason = getattr(exc, "reason", None)
                        self.logger.warning(
                            "WebBoilerWsClient connection closed %s %s (%s)",
                            close_code,
                            close_reason,
                            self.log_account,
                        )
                    except asyncio.CancelledError:
                        raise
                    except Exception as err:
                        self.logger.exception("WebBoilerWsClient error (%s)", self.log_account)
                        await self.error_callback(ws, err)
                    finally:
                        if close_code is None:
                            close_code = getattr(ws, "close_code", None)
                        if close_reason is None:
                            close_reason = getattr(ws, "close_reason", None)
                        await self.disconnected_callback(ws, close_code, close_reason)
                break
            except asyncio.CancelledError:
                raise
            except Exception as err:
                self.logger.exception("WebBoilerWsClient connect loop failed (%s)", self.log_account)
                await self.error_callback(None, err)
                break

    def is_running(self) -> bool:
        """Return True when the websocket background task is active."""
        task = self._task
        return task is not None and not task.done()

    async def start(self, username: str) -> None:
        self.username = username
        self.log_account = redact_account(username)
        self.subscription_index = 0
        self._stop_event.clear()
        self._connected_event.clear()
        if self.is_running():
            return
        if self.hass is not None:
            self._task = self.hass.async_create_background_task(self._run(), f"{__name__}-{self.log_account}")
        else:
            self._task = asyncio.create_task(self._run())
        try:
            await asyncio.wait_for(self._connected_event.wait(), timeout=20)
        except asyncio.TimeoutError as err:
            await self.close()
            raise ConnectionError(f"Timed out waiting for websocket CONNECTED frame ({self.log_account})") from err

    async def close(self):
        self._stop_event.set()
        if self._ws is not None:
            try:
                await self._ws.close(code=1000, reason="client_stop_requested")
            except Exception:
                pass
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._connected_event.clear()
        self._ws = None

    async def subscribe_to_installation(self, ws, device):
        device_type = device["type"]
        serial = device["serial"]
        topic = WEB_BOILER_STOMP_DEVICE_TOPIC + device_type + "." + serial
        self.subscription_index += 1
        await ws.send(stomp.subscribe(topic, f"sub-{self.subscription_index}", "auto"))
