from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from .HttpClient import HttpClient, HttpClientAuthError, HttpClientConnectionError
from .HttpHelper import HttpHelper
from .WebBoilerDeviceCollection import WebBoilerDeviceCollection
from .WebBoilerWsClient import WebBoilerWsClient
from .logging_utils import redact_account


# Permissive but bounded set of "command accepted" markers the upstream
# Centrometal API has been observed to use. We intentionally do NOT do a
# recursive deep walk of arbitrary response shapes — that would accept a
# nested success marker even when the outer response indicates failure.
_SUCCESS_STATUS_VALUES = {"success", "ok", "done"}


def _response_is_success(response: Any) -> bool:
    """Decide whether a control-API response indicates success.

    Accepts ``True``, ``{"status": "success"|"ok"|"done"}``, ``{"success": True}``,
    ``{"ok": True}``, and the same shapes wrapped one level under a
    ``"result"`` / ``"data"`` envelope. Explicit top-level failure markers
    win over nested success markers so legitimate error envelopes are not
    silently swallowed.
    """
    if response is True:
        return True
    if not isinstance(response, dict):
        return False
    if response.get("success") is False or response.get("ok") is False:
        return False
    status = response.get("status")
    if isinstance(status, str):
        normalized_status = status.strip().lower()
        if normalized_status in _SUCCESS_STATUS_VALUES:
            return True
        return False
    if response.get("success") is True or response.get("ok") is True:
        return True
    inner = response.get("result") or response.get("data")
    if isinstance(inner, dict):
        if inner.get("success") is True or inner.get("ok") is True:
            return True
        inner_status = inner.get("status")
        if isinstance(inner_status, str) and inner_status.strip().lower() in _SUCCESS_STATUS_VALUES:
            return True
    return False


class WebBoilerClient:
    def __init__(self, hass=None):
        self.hass = hass
        self.logger = logging.getLogger(__name__)
        self.websocket_connected = False
        self.connectivity_callbacks: dict[str, Callable[[bool], Awaitable[None]]] = {}
        self.ws_client = WebBoilerWsClient(
            hass,
            self.ws_connected_callback,
            self.ws_disconnected_callback,
            self.ws_error_callback,
            self.ws_data_callback,
        )
        self.on_parameter_updated_callback = None
        self.log_account = "account-unknown"
        # Telemetry timestamps used by the entity-availability calculation
        # and by the orchestrator's tick(). All are monotonic seconds.
        self.last_successful_http_refresh: float | None = None
        self.last_metadata_refresh: float | None = None
        self.last_websocket_message: float | None = None
        self.disconnected_since: float | None = time.monotonic()

    async def login(self, username, password):
        self.logger.info("WebBoilerClient - Logging in... (%s)", redact_account(username))
        self.username = username
        self.log_account = redact_account(username)
        self.password = password
        self.http_client = HttpClient(self.username, self.password)
        self.http_helper = HttpHelper(self.http_client)
        self.data = WebBoilerDeviceCollection(username)
        return await self.http_client.login()

    async def get_configuration(self) -> bool:
        await self.http_client.get_installations()
        if self.http_helper.get_device_count() == 0:
            self.logger.warning("WebBoilerClient - there is no installed device (%s)", self.log_account)
            return False
        self.data.parse_installations(self.http_client.installations)
        tasks = [
            self.http_client.get_installation_status_all(self.http_helper.get_all_devices_ids()),
        ]
        for serial in self.http_helper.get_all_devices_serials():
            tasks.append(self.http_client.get_parameter_list(serial))
        await asyncio.gather(*tasks)
        await self.data.parse_installation_statuses(self.http_client.installation_status_all)
        self.data.parse_parameter_lists(self.http_client.parameter_list)

        # Event history is useful metadata, not a prerequisite for loading
        # the boiler. Older accounts/firmware may reject this endpoint, so a
        # failure here must not prevent the integration from starting.
        try:
            await asyncio.gather(
                *(self.http_client.get_errors_list(id_) for id_ in self.http_helper.get_all_devices_ids())
            )
            self.data.parse_errors_lists(self.http_client.errors_list)
        except HttpClientAuthError:
            raise
        except HttpClientConnectionError as err:
            self.logger.warning(
                "Could not load Centrometal event history: %s (%s)",
                err,
                self.log_account,
            )

        now = time.monotonic()
        self.last_successful_http_refresh = now
        self.last_metadata_refresh = now
        return True

    async def close_websocket(self) -> bool:
        try:
            await self.ws_client.close()
            return True
        except Exception as e:
            self.logger.error(
                "WebBoilerClient::close_websocket failed %s (%s)",
                str(e),
                getattr(self, "log_account", "account-unknown"),
            )
            return False

    async def close(self) -> None:
        await self.close_websocket()
        http_client = getattr(self, "http_client", None)
        if http_client is not None:
            await http_client.close_session()

    async def start_websocket(self, on_parameter_updated_callback):
        self.logger.info("WebBoilerClient - Starting websocket... (%s)", self.log_account)
        self.on_parameter_updated_callback = on_parameter_updated_callback
        await self.ws_client.start(self.username)

    async def refresh(self, delay: float = 1.0) -> bool:
        """Refresh boiler state over HTTP and update the local parameter cache.

        The previous implementation only sent REFRESH/RSTAT control commands and
        relied on the websocket to deliver the resulting state updates. That
        meant if the websocket was lagging, disconnected, or had dropped a
        frame, Home Assistant kept showing stale values. We now follow up with
        a direct ``/wdata/data/installation-status-all`` read so the local
        cache is refreshed from HTTP regardless of websocket health, and the
        on-update callbacks fire so HA entities re-render.
        """
        try:
            ids = self.http_helper.get_all_devices_ids()
            for id_ in ids:
                await self.http_client.refresh_device(id_)
                await asyncio.sleep(delay)
                await self.http_client.rstat_all_device(id_)
                await asyncio.sleep(delay)
            statuses = await self.http_client.get_installation_status_all(ids)
            await self.data.parse_installation_statuses(statuses)
            metadata_parameters = []
            now = time.monotonic()

            # Event history is supplemental. A temporary failure of this
            # endpoint must not invalidate a successful boiler-state refresh.
            try:
                await asyncio.gather(*(self.http_client.get_errors_list(id_) for id_ in ids))
                metadata_parameters.extend(self.data.parse_errors_lists(self.http_client.errors_list))
            except HttpClientAuthError:
                raise
            except HttpClientConnectionError as err:
                self.logger.warning(
                    "Could not refresh Centrometal event history: %s (%s)",
                    err,
                    self.log_account,
                )

            # Editable-setting and circuit metadata come from parameter-list
            # and are refreshed hourly. Non-entity groups are discarded.
            if self.last_metadata_refresh is None or now - self.last_metadata_refresh >= 3600:
                try:
                    serials = self.http_helper.get_all_devices_serials()
                    await asyncio.gather(*(self.http_client.get_parameter_list(serial) for serial in serials))
                    metadata_parameters.extend(self.data.parse_parameter_lists(self.http_client.parameter_list))
                    self.last_metadata_refresh = now
                except HttpClientAuthError:
                    raise
                except HttpClientConnectionError as err:
                    self.logger.warning(
                        "Could not refresh Centrometal metadata: %s (%s)",
                        err,
                        self.log_account,
                    )

            for parameter in metadata_parameters:
                await parameter.notify_updated()

            self.last_successful_http_refresh = now
            return True
        except HttpClientAuthError:
            raise
        except HttpClientConnectionError as e:
            self.logger.warning("WebBoilerClient::refresh failed: %s (%s)", e, self.log_account)
            return False
        except Exception:
            # Last-resort guard — log with traceback so we can diagnose, but
            # do not let a stray bug in parsing kill the orchestrator tick.
            self.logger.exception("WebBoilerClient::refresh unexpected failure (%s)", self.log_account)
            return False

    async def _notify_connectivity(self):
        for callback in list(self.connectivity_callbacks.values()):
            await callback(self.websocket_connected)

    async def ws_connected_callback(self, ws, frame):
        self.logger.info("WebBoilerClient - connected (%s)", self.log_account)
        self.websocket_connected = True
        self.disconnected_since = None
        self.last_websocket_message = time.monotonic()
        await self._notify_connectivity()
        for serial in self.http_helper.get_all_devices_serials():
            device = self.data.get_device_by_serial(serial)
            await self.ws_client.subscribe_to_installation(ws, device)
        self.data.set_on_update_callback(self.on_parameter_updated_callback)
        await self.data.notify_all_updated()

    async def ws_disconnected_callback(self, ws, close_status_code, close_msg):
        self.websocket_connected = False
        if self.disconnected_since is None:
            self.disconnected_since = time.monotonic()
        await self._notify_connectivity()
        await self.data.notify_all_updated()
        log_level = logging.INFO
        if close_status_code not in (None, 1000, 1001):
            log_level = logging.WARNING
        self.logger.log(
            log_level,
            "WebBoilerClient - disconnected close_status_code:%s close_msg:%s (%s)",
            close_status_code,
            close_msg,
            self.log_account,
        )

    async def ws_error_callback(self, ws, err):
        self.logger.error("WebBoilerClient - error err:%s (%s)", err, self.log_account)

    async def ws_data_callback(self, ws, stomp_frame):
        self.last_websocket_message = time.monotonic()
        await self.data.parse_real_time_frame(stomp_frame)

    def is_websocket_connected(self) -> bool:
        return self.websocket_connected

    def is_websocket_running(self) -> bool:
        return self.ws_client.is_running()

    def has_recent_http_refresh(self, max_age: float = 300.0) -> bool:
        """True when an HTTP refresh has succeeded within ``max_age`` seconds."""
        if self.last_successful_http_refresh is None:
            return False
        return (time.monotonic() - self.last_successful_http_refresh) <= max_age

    def websocket_disconnected_for(self) -> float:
        """Seconds since the websocket last went down (0 while connected)."""
        if self.websocket_connected or self.disconnected_since is None:
            return 0.0
        return time.monotonic() - self.disconnected_since

    def has_fresh_data(self, max_age: float = 300.0) -> bool:
        """Availability signal for entities.

        Per HA guidance (integration-quality-scale: entity-unavailable):
        an entity should report unavailable when we cannot fetch data, not
        keep showing the last-known value indefinitely. We treat the entity
        as available when *either* the websocket is currently connected
        *or* an HTTP refresh has succeeded recently — so transient WS gaps
        do not cause UI flapping while a stale-for-hours integration *does*
        eventually go unavailable.
        """
        return self.websocket_connected or self.has_recent_http_refresh(max_age)

    async def relogin(self):
        await self.http_client.close_session()
        await self.http_client.reinitialize_session()
        return await self.http_client.login()

    async def turn(self, serial, on):
        try:
            device = self.data.get_device_by_serial(serial)
        except LookupError as err:
            self.logger.error(
                "WebBoilerClient::turn unknown serial %s: %s (%s)",
                serial,
                err,
                self.log_account,
            )
            return False
        try:
            response = await self.http_client.turn_device_by_id(device["id"], on)
        except HttpClientAuthError:
            raise
        except HttpClientConnectionError as e:
            self.logger.warning("WebBoilerClient::turn failed: %s (%s)", e, self.log_account)
            return False
        ok = _response_is_success(response)
        if not ok:
            self.logger.warning("WebBoilerClient::turn rejected response %s (%s)", response, self.log_account)
        return ok

    async def turn_circuit(self, serial, circuit, on):
        try:
            device = self.data.get_device_by_serial(serial)
        except LookupError as err:
            self.logger.error(
                "WebBoilerClient::turn_circuit unknown serial %s: %s (%s)",
                serial,
                err,
                self.log_account,
            )
            return False
        try:
            response = await self.http_client.turn_device_circuit(device["id"], circuit, on)
        except HttpClientAuthError:
            raise
        except HttpClientConnectionError as e:
            self.logger.warning("WebBoilerClient::turn_circuit failed: %s (%s)", e, self.log_account)
            return False
        ok = _response_is_success(response)
        if not ok:
            self.logger.warning(
                "WebBoilerClient::turn_circuit rejected response %s (%s)",
                response,
                self.log_account,
            )
        return ok

    def set_connectivity_callback(self, connectivity_callback, update_key="default"):
        if connectivity_callback is None:
            self.connectivity_callbacks.pop(update_key, None)
        else:
            self.connectivity_callbacks[update_key] = connectivity_callback
