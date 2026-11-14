"""Manage live measurements and authenticated HTTP snapshots."""

import asyncio
import logging
import ssl
from datetime import UTC, datetime
from json import JSONDecodeError
from math import isfinite
from time import monotonic

from centrometal_web_boiler import WebBoilerClient
from centrometal_web_boiler.const import WEB_BOILER_STOMP_URL
from centrometal_web_boiler.HttpClient import HttpClient
from centrometal_web_boiler.HttpHelper import HttpHelper
from centrometal_web_boiler.WebBoilerDeviceCollection import WebBoilerDeviceCollection

from .const import WEB_BOILER_LOGIN_RETRY_INTERVAL, WEB_BOILER_REFRESH_INTERVAL

_LOGGER = logging.getLogger(__name__)
# The library logs request bodies, response bodies and identifiers. Its loggers
# are instance attributes, so redact by keeping those instances silent.
_LIBRARY_LOGGER = logging.getLogger(f"{__name__}.private")
_LIBRARY_LOGGER.disabled = True

POLL_INTERVAL = 60
MAX_BACKOFF = 300
DATA_EXPIRY = 180
REQUEST_TIMEOUT = 15


def _valid_value(value):
    if isinstance(value, str):
        return bool(value.strip()) and value != "?"
    return isinstance(value, (int, float)) and isfinite(value)


class WebBoilerSystem(WebBoilerClient):
    """Keep one device collection and one HTTP session per config entry."""

    def __init__(self, username, password, prefix, product_prefix):
        super().__init__()
        self.username = username
        self.password = password
        self.prefix = f"{prefix.rstrip()} " if prefix.rstrip() else ""
        self.product_prefix = product_prefix
        self.logger = self.ws_client.logger = _LIBRARY_LOGGER
        # 0.0.58 (shipped with integration 0.0.54) dispatches ERROR to
        # error_callback but stores the constructor argument as close_callback.
        self.ws_client.error_callback = self.ws_error_callback
        self.http_client = None
        self._monitor = None
        self._socket_task = None
        self._update_lock = asyncio.Lock()
        self._tick_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()
        self._ids = {}
        self._started = 0
        self._live = {}
        self._last_data = {}
        self._available = set()
        self._last_live = None
        self._last_http = None
        self._http_error = None
        self._subscription = "connecting"
        self._fallback = False
        self._next_poll = 0
        self._next_probe = 0
        self._next_refresh = float("inf")
        self._poll_delay = POLL_INTERVAL
        self._probe_delay = WEB_BOILER_LOGIN_RETRY_INTERVAL
        self._needs_login = False

    async def load_configuration(self):
        # Initialize the same objects as WebBoilerClient.login with safe logging
        # before the first authenticated request.
        self.http_client = HttpClient(self.username, self.password)
        self.http_client.logger = _LIBRARY_LOGGER
        self.http_helper = HttpHelper(self.http_client)
        self.data = WebBoilerDeviceCollection(self.username, self._parameter_received)
        self.data.logger = _LIBRARY_LOGGER
        try:
            async with asyncio.timeout(60):
                if (
                    not await self.http_client.login()
                    or not await self.get_configuration()
                ):
                    return False
        except Exception as error:  # noqa: BLE001
            _LOGGER.debug("Centrometal configuration failed (%s)", type(error).__name__)
            return False
        self._ids = {str(device["id"]): device for device in self.data.values()}
        now = monotonic()
        for device_id, device in self._ids.items():
            device.logger = _LIBRARY_LOGGER
            if device["parameters"]:
                self._last_data[device_id] = now
                self._available.add(device_id)
        return bool(self._ids)

    def start_monitoring(self):
        """Start the single transport loop after the platforms are loaded."""
        if self._monitor is None:
            self._started = self._next_probe = monotonic()
            self._monitor = asyncio.create_task(self._run())

    async def _run(self):
        while not asyncio.current_task().cancelling():
            await self.tick()
            if not asyncio.current_task().cancelling():
                await asyncio.sleep(1)

    async def pause(self):
        """Quiesce both transports before Home Assistant unloads entities."""
        async with self._shutdown_lock:
            await self._pause()

    async def _pause(self):
        if self._monitor is not None:
            self._monitor.cancel()
            await asyncio.gather(self._monitor, return_exceptions=True)
            self._monitor = None
        await self._close_socket()

    async def stop(self):
        """Stop background work and release the authenticated session."""
        async with self._shutdown_lock:
            await self._pause()
            if self.http_client is not None:
                await self.http_client.close_session()
                self.http_client = None

    async def _close_socket(self):
        if self._socket_task is not None:
            self._socket_task.cancel()
            await asyncio.gather(self._socket_task, return_exceptions=True)
            self._socket_task = None
        socket = self.ws_client.client
        if socket.connection is not None:
            await socket.close()
            socket.connection = None

    async def _run_socket(self):
        try:
            context = await asyncio.to_thread(ssl.create_default_context)
            # The pinned library starts this coroutine in an untracked task.
            # Own the task so unload can also cancel an in-progress handshake.
            await self.ws_client.client._ClientSocket__main(
                WEB_BOILER_STOMP_URL,
                ssl=context,
                open_timeout=REQUEST_TIMEOUT,
                logger=_LIBRARY_LOGGER,
            )
        except Exception as error:  # noqa: BLE001
            _LOGGER.debug(
                "Centrometal WebSocket attempt failed (%s)", type(error).__name__
            )
        finally:
            await self.ws_disconnected_callback(None, None, None)

    async def ws_connected_callback(self, ws, frame):
        """Send subscriptions. A CONNECTED frame only confirms the handshake."""
        self.websocket_connected = True
        await self.ws_client.subscribe_to_notifications(ws)
        for device in self.data.values():
            await self.ws_client.subscribe_to_installation(ws, device)
        self._subscription = "awaiting data"
        self._next_refresh = monotonic()
        if self.connectivity_callback is not None:
            await self.connectivity_callback(True)

    async def ws_disconnected_callback(self, ws, close_status_code, close_msg):
        self.websocket_connected, was_connected = False, self.websocket_connected
        if self._subscription != "rejected":
            self._subscription = "disconnected"
        if was_connected and self.connectivity_callback is not None:
            await self.connectivity_callback(False)

    async def ws_error_callback(self, ws, error):
        """Handle a broker ERROR without logging its raw frame."""
        self._subscription = "rejected"
        self._live.clear()
        was_connected = self.websocket_connected
        self.websocket_connected = False
        if was_connected and self.connectivity_callback is not None:
            await self.connectivity_callback(False)
        if not self._fallback:
            self._set_fallback(True)
        self._log_transport("broker rejected the STOMP session")

    async def ws_data_callback(self, ws, frame):
        """Parse live frames in the same collection used by HTTP snapshots."""
        if frame.get("cmd") != "MESSAGE" or self._subscription == "rejected":
            return
        async with self._update_lock:
            try:
                await self.data.parse_real_time_frame(frame)
            except Exception as error:  # noqa: BLE001
                _LOGGER.debug(
                    "Discarded Centrometal live frame (%s)", type(error).__name__
                )

    async def _parameter_received(self, device, parameter, create=False):
        # The library calls this after parsing an actual live parameter.
        # Its HTTP parser only invokes the parameter's entity callbacks.
        if create or not _valid_value(parameter["value"]):
            return
        device_id = str(device["id"])
        self._live[device_id] = self._last_data[device_id] = monotonic()
        self._last_live = datetime.now(UTC)
        if self._subscription != "receiving data":
            self._subscription = "receiving data"
            self._log_transport("live data received")
        await self._set_available(device_id, True)
        if self._fallback and not self._stale_devices(monotonic()):
            self._set_fallback(False)

    def is_device_data_available(self, device_id):
        """Report availability independently of the WebSocket status sensor."""
        return str(device_id) in self._available

    async def _set_available(self, device_id, available):
        if self.is_device_data_available(device_id) == available:
            return
        if available:
            self._available.add(device_id)
        else:
            self._available.discard(device_id)
        for parameter in self._ids[device_id]["parameters"].values():
            await parameter.notify_updated()

    def _stale_devices(self, now):
        return {
            device_id
            for device_id in self._ids
            if now - self._live.get(device_id, self._started) >= POLL_INTERVAL
            or (self._fallback and device_id not in self._live)
        }

    def _set_fallback(self, active):
        self._fallback = active
        if active:
            self._next_poll = monotonic()
        else:
            self._poll_delay = POLL_INTERVAL
            self._probe_delay = WEB_BOILER_LOGIN_RETRY_INTERVAL
        _LOGGER.info(
            "Centrometal transport mode is %s",
            "HTTP fallback" if active else "WebSocket",
        )
        self._log_transport("transport changed")

    def _log_transport(self, event):
        _LOGGER.debug(
            "Centrometal %s | mode=%s subscription=%s last_live=%s last_http=%s http_error=%s",
            event,
            "HTTP fallback" if self._fallback else "WebSocket",
            self._subscription,
            self._last_live,
            self._last_http,
            self._http_error,
        )

    async def tick(self):
        """Check freshness, poll if needed and attempt WebSocket recovery."""
        if self._tick_lock.locked():
            return
        async with self._tick_lock:
            now = monotonic()
            stale = self._stale_devices(now)
            if stale and not self._fallback:
                self._set_fallback(True)
            if self._fallback and now >= self._next_poll:
                await self._poll()
            if asyncio.current_task().cancelling():
                return
            async with self._update_lock:
                for device_id in self._available.copy():
                    if monotonic() - self._last_data[device_id] >= DATA_EXPIRY:
                        await self._set_available(device_id, False)
            now = monotonic()
            if now >= self._next_probe and (
                self._fallback or self._socket_task is None
            ):
                await self._close_socket()
                self._subscription = "connecting"
                self._log_transport("starting WebSocket recovery attempt")
                self._socket_task = asyncio.create_task(self._run_socket())
                self._next_probe = now + self._probe_delay
                if self._fallback:
                    self._probe_delay = min(self._probe_delay * 2, MAX_BACKOFF)
            if self.websocket_connected and now >= self._next_refresh:
                self._next_refresh = now + WEB_BOILER_REFRESH_INTERVAL
                await self._refresh_live()

    async def _refresh_live(self):
        # The library sends two requests and waits four seconds per installation.
        try:
            if self._needs_login:
                await self._reauthenticate()
            async with asyncio.timeout((2 * REQUEST_TIMEOUT + 4) * len(self._ids)):
                if not await self.refresh():
                    self._needs_login = True
                    self._next_refresh = monotonic() + POLL_INTERVAL
                    self._log_transport("live refresh command failed")
        except (TimeoutError, PermissionError) as error:
            self._log_transport(f"live refresh failed ({type(error).__name__})")

    async def _fetch_snapshot(self):
        async with asyncio.timeout(REQUEST_TIMEOUT):
            await self.http_client.get_installation_status_all(
                self.http_helper.get_all_devices_ids()
            )
        return self.http_client.installation_status_all

    async def _reauthenticate(self):
        self._log_transport("renewing the HTTP session")
        async with asyncio.timeout(REQUEST_TIMEOUT):
            self._needs_login = not await self.relogin()
        if self._needs_login:
            raise PermissionError

    async def _authenticated_snapshot(self):
        if self._needs_login:
            await self._reauthenticate()
            return await self._fetch_snapshot()
        try:
            return await self._fetch_snapshot()
        except Exception as error:
            if asyncio.current_task().cancelling():
                raise asyncio.CancelledError from None
            # These are the pinned client's representations of an auth status
            # or a JSON endpoint redirected to the HTML login page.
            if not self._is_expired_session(error):
                raise
            self._needs_login = True
        await self._reauthenticate()
        return await self._fetch_snapshot()

    @staticmethod
    def _is_expired_session(error):
        return str(error).endswith(("http code: 401", "http code: 403")) or isinstance(
            error.__context__, JSONDecodeError
        )

    async def _poll(self):
        try:
            snapshot = await self._authenticated_snapshot()
            async with self._update_lock:
                if self._fallback:
                    if not await self._apply_snapshot(snapshot):
                        raise ValueError("No usable HTTP measurements")
                    self._last_http = datetime.now(UTC)
            self._http_error = None
            self._poll_delay = POLL_INTERVAL
            self._next_poll = monotonic() + POLL_INTERVAL
            self._log_transport("HTTP polling cycle completed")
        except Exception as error:  # noqa: BLE001
            # The library's response reader can wrap cancellation in Exception.
            if asyncio.current_task().cancelling():
                raise asyncio.CancelledError from None
            self._needs_login |= self._is_expired_session(error)
            self._http_error = (
                "authentication" if self._needs_login else type(error).__name__
            )
            self._poll_delay = min(self._poll_delay * 2, MAX_BACKOFF)
            self._next_poll = monotonic() + self._poll_delay
            self._log_transport("HTTP poll failed; retry scheduled")

    async def _apply_snapshot(self, snapshot):
        """Publish only stale installations through the existing parameter parser."""
        now = monotonic()
        recent = datetime.now(UTC).timestamp() - DATA_EXPIRY
        stale = self._stale_devices(now)
        received = set()
        for device_id in stale:
            device = self._ids[device_id]
            installation = snapshot.get(device_id)
            if not isinstance(installation, dict):
                continue
            readings = installation.get("params", {})
            if not isinstance(readings, dict):
                continue
            changed = {}
            valid = False
            for name, reading in readings.items():
                parameter = device["parameters"].get(name)
                if parameter is None or not isinstance(reading, dict):
                    continue
                value = reading.get("v")
                if not _valid_value(value):
                    continue
                if "ut" in reading and reading["ut"] is None:
                    # The library supports undated readings. Treat a changed
                    # value as usable, without renewing unchanged cached data.
                    if value != parameter["value"]:
                        changed[name] = reading
                        valid = True
                    continue
                try:
                    timestamp = datetime.strptime(reading["ut"], "%Y-%m-%d %H:%M:%S")
                except (KeyError, TypeError, ValueError):
                    continue
                timestamp = int(timestamp.replace(tzinfo=UTC).timestamp())
                previous = parameter.get("timestamp") or 0
                if timestamp < previous:
                    continue
                valid |= timestamp >= recent
                if timestamp > previous or value != parameter["value"]:
                    changed[name] = reading
                    valid = True
            if valid:
                received.add(device_id)
                self._last_data[device_id] = now
                # Set availability before any parameter callback writes HA state.
                became_available = device_id not in self._available
                self._available.add(device_id)
                if changed:
                    await self.data.parse_installation_statuses(
                        {device_id: {"params": changed}}
                    )
                if became_available:
                    for name, parameter in device["parameters"].items():
                        if name not in changed:
                            await parameter.notify_updated()
        return received
