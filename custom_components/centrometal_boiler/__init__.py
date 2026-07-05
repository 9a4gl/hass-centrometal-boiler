from __future__ import annotations

import datetime
import hashlib
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_PREFIX, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from .centrometal_web_boiler import (
    HttpClientAuthError,
    HttpClientConnectionError,
    WebBoilerClient,
    next_retry_delay,
)
from .const import (
    CONF_REFRESH_INTERVAL,
    CONF_RETRY_BASE_INTERVAL,
    CONF_RETRY_MAX_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    DEFAULT_RETRY_BASE_INTERVAL,
    DEFAULT_RETRY_MAX_INTERVAL,
    DOMAIN,
)
from .runtime import CentrometalRuntimeData

_LOGGER = logging.getLogger(__name__)


def _redact_account(account: str) -> str:
    """Return a stable non-reversible account identifier for logs."""
    digest = hashlib.sha256(account.encode()).hexdigest()[:8]
    return f"account-{digest}"


PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.BINARY_SENSOR]
CentrometalConfigEntry = ConfigEntry[CentrometalRuntimeData]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CentrometalConfigEntry) -> bool:
    prefix = entry.data.get(CONF_PREFIX, "") or ""
    system = WebBoilerSystem(
        hass=hass,
        entry=entry,
        username=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        prefix=prefix,
    )
    stop_listener = None
    try:
        try:
            await system.start()
        except ConfigEntryAuthFailed:
            raise
        except HttpClientAuthError as err:
            raise ConfigEntryAuthFailed("Invalid Centrometal credentials") from err
        except (HttpClientConnectionError, ConnectionError) as err:
            raise ConfigEntryNotReady(f"Cannot connect to Centrometal web-boiler server: {err}") from err

        runtime = CentrometalRuntimeData(client=system.web_boiler_client, system=system)
        entry.runtime_data = runtime
        stop_listener = hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, system.stop)
        runtime.stop_listener = stop_listener
        entry.async_on_unload(entry.add_update_listener(_async_options_updated))

        system.start_tick()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception:
        system.cancel_tick()
        if stop_listener is not None:
            stop_listener()
        try:
            await system.stop()
        except Exception as err:
            _LOGGER.debug("Centrometal setup cleanup failed: %s", err)
        raise


async def _async_options_updated(hass: HomeAssistant, entry: CentrometalConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: CentrometalConfigEntry) -> bool:
    runtime = entry.runtime_data
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False
    runtime.system.cancel_tick()
    if runtime.stop_listener is not None:
        runtime.stop_listener()
        runtime.stop_listener = None
    await runtime.system.stop()
    return True


class WebBoilerSystem:
    def __init__(
        self, hass: HomeAssistant, *, entry: CentrometalConfigEntry, username: str, password: str, prefix: str
    ) -> None:
        self._hass = hass
        self._entry = entry
        self.username = username
        self.password = password
        self._log_account = _redact_account(username)
        prefix = prefix.rstrip()
        self.prefix = (prefix + " ") if prefix else ""
        self.web_boiler_client = WebBoilerClient(hass)
        self.refresh_interval = entry.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
        self.retry_base_interval = entry.options.get(CONF_RETRY_BASE_INTERVAL, DEFAULT_RETRY_BASE_INTERVAL)
        self.retry_max_interval = entry.options.get(CONF_RETRY_MAX_INTERVAL, DEFAULT_RETRY_MAX_INTERVAL)
        # Counts consecutive failed relogin attempts so retries back off
        # instead of hammering the server on a fixed cadence during a
        # prolonged outage. Reset to 0 on the next fully successful login.
        self._relogin_attempt = 0
        now_ts = time.monotonic()
        self.last_relogin_timestamp = now_ts
        self.last_refresh_timestamp = now_ts
        self._tick_unsub = None

    async def on_parameter_updated(self, device, param, create: bool = False):
        action = "Create" if create else "update"
        _LOGGER.debug(
            "%s %s %s = %s (%s)",
            action,
            device["serial"],
            param["name"],
            param["value"],
            self._log_account,
        )

    def _annotate_devices(self) -> None:
        devices = list(self.web_boiler_client.data.values())
        multi = len(devices) > 1
        for device in devices:
            device["__client"] = self.web_boiler_client
            device["__system"] = self
            device["__prefix"] = self.prefix
            device["__multi_device"] = multi

    async def start(self) -> None:
        _LOGGER.debug("Starting Centrometal Boiler System %s", self._log_account)
        try:
            logged_in = await self.web_boiler_client.login(self.username, self.password)
        except HttpClientAuthError as err:
            raise ConfigEntryAuthFailed("Invalid Centrometal credentials") from err
        except HttpClientConnectionError as err:
            raise ConfigEntryNotReady(str(err)) from err

        if not logged_in:
            raise ConfigEntryNotReady("Cannot login to Centrometal server")

        got_configuration = await self.web_boiler_client.get_configuration()
        if not got_configuration:
            raise ConfigEntryNotReady("Cannot get configuration from Centrometal server")
        if len(self.web_boiler_client.data) == 0:
            raise ConfigEntryNotReady("No device found on Centrometal boiler server")
        self._annotate_devices()
        await self.web_boiler_client.start_websocket(self.on_parameter_updated)
        try:
            refresh_ok = await self.web_boiler_client.refresh()
        except HttpClientAuthError:
            _LOGGER.info(
                "WebBoilerSystem initial refresh got login page after successful login; "
                "attempting one fresh HTTP relogin %s",
                self._log_account,
            )
            try:
                await self.web_boiler_client.http_client.reinitialize_session()
                await self.web_boiler_client.http_client.login()
            except HttpClientAuthError as err:
                raise ConfigEntryAuthFailed("Invalid Centrometal credentials") from err
            except HttpClientConnectionError as err:
                raise ConfigEntryNotReady(str(err)) from err
            try:
                refresh_ok = await self.web_boiler_client.refresh()
            except HttpClientAuthError:
                _LOGGER.warning(
                    "WebBoilerSystem initial refresh got login page again right after successful "
                    "relogin — treating as transient startup issue %s",
                    self._log_account,
                )
                refresh_ok = False
            except HttpClientConnectionError as err:
                raise ConfigEntryNotReady(str(err)) from err
        except HttpClientConnectionError as err:
            raise ConfigEntryNotReady(str(err)) from err
        if not refresh_ok:
            raise ConfigEntryNotReady("Initial refresh failed")
        self.last_refresh_timestamp = time.monotonic()

    def start_tick(self) -> None:
        self.cancel_tick()

        async def _on_interval(_now) -> None:
            try:
                await self.tick()
            except Exception as ex:
                _LOGGER.warning("WebBoilerSystem.tick raised: %s", ex)

        self._tick_unsub = async_track_time_interval(self._hass, _on_interval, datetime.timedelta(seconds=60))

    def cancel_tick(self) -> None:
        if self._tick_unsub:
            self._tick_unsub()
            self._tick_unsub = None

    async def stop(self, event=None):
        _LOGGER.debug("Stopping Centrometal WebBoilerSystem %s", self._log_account)
        await self.web_boiler_client.close()

    def _current_retry_delay(self) -> float:
        """Seconds to wait before the next relogin attempt.

        Backs off exponentially (capped at ``retry_max_interval``) with each
        consecutive failure, and resets to ``retry_base_interval`` as soon as
        a relogin succeeds, so a brief blip recovers quickly while a
        prolonged outage is not retried on a fixed cadence forever.
        """
        return next_retry_delay(self._relogin_attempt, base=self.retry_base_interval, cap=self.retry_max_interval)

    async def tick(self):
        now = time.monotonic()
        connected = self.web_boiler_client.is_websocket_connected()
        websocket_running = self.web_boiler_client.is_websocket_running()

        if not connected:
            disconnected_for = self.web_boiler_client.websocket_disconnected_for()
            # Tolerance: keep using the existing reconnect loop for up to 3x
            # the *base* relogin retry interval (not the backed-off value, so
            # this window doesn't grow along with the backoff). While we
            # wait, keep refreshing state via HTTP so HA entities don't go
            # stale.
            if websocket_running and disconnected_for < (self.retry_base_interval * 3):
                _LOGGER.debug(
                    "Centrometal websocket disconnected for %.0fs but reconnect loop is active (%s)",
                    disconnected_for,
                    self._log_account,
                )
                if now - self.last_refresh_timestamp > self.refresh_interval:
                    self.last_refresh_timestamp = now
                    try:
                        await self.web_boiler_client.refresh()
                    except HttpClientAuthError:
                        await self._silent_http_relogin()
                    except HttpClientConnectionError:
                        pass
                return
            if now - self.last_relogin_timestamp > self._current_retry_delay():
                _LOGGER.info(
                    "Centrometal WebBoilerSystem::tick websocket unavailable for %.0fs; trying relogin %s",
                    disconnected_for,
                    self._log_account,
                )
                await self.relogin()
            return

        if now - self.last_refresh_timestamp > self.refresh_interval:
            self.last_refresh_timestamp = now
            _LOGGER.info("WebBoilerSystem::tick refresh data %s", self._log_account)
            try:
                refresh_successful = await self.web_boiler_client.refresh()
            except HttpClientAuthError:
                _LOGGER.info(
                    "WebBoilerSystem::tick HTTP session expired during refresh, attempting silent relogin %s",
                    self._log_account,
                )
                await self._silent_http_relogin()
                return
            except HttpClientConnectionError:
                refresh_successful = False
            if not refresh_successful:
                await self.relogin()

    async def _silent_http_relogin(self):
        """Re-establish the HTTP session silently after session/cookie expiration.

        Only triggers a full reauth flow if the credentials themselves are rejected.
        The websocket connection is left untouched since it operates independently.
        """
        try:
            await self.web_boiler_client.http_client.reinitialize_session()
            await self.web_boiler_client.http_client.login()
        except HttpClientAuthError:
            _LOGGER.warning(
                "WebBoilerSystem silent HTTP relogin failed: credentials rejected %s",
                self._log_account,
            )
            self._entry.async_start_reauth(self._hass)
            return
        except HttpClientConnectionError as err:
            _LOGGER.warning(
                "WebBoilerSystem silent HTTP relogin failed: connection error %s (%s)",
                err,
                self._log_account,
            )
            return

        _LOGGER.info(
            "WebBoilerSystem silent HTTP relogin succeeded %s",
            self._log_account,
        )
        # Retry the refresh now that we have a fresh session
        try:
            ok = await self.web_boiler_client.refresh()
        except HttpClientAuthError:
            # Login just succeeded seconds ago, so credentials are valid.
            # The server returned the login page again for some other reason
            # (session race, load balancer, rate limit). Do NOT trigger reauth.
            _LOGGER.warning(
                "WebBoilerSystem refresh got login page again right after successful "
                "relogin — treating as transient server issue, not invalid credentials %s",
                self._log_account,
            )
            return
        except HttpClientConnectionError:
            ok = False
        if ok:
            self.last_refresh_timestamp = time.monotonic()

    def _record_relogin_success(self) -> None:
        self._relogin_attempt = 0

    def _record_relogin_failure(self) -> None:
        # Bounded so the exponential backoff calculation stays cheap even
        # after a very long outage; next_retry_delay() already clamps the
        # resulting delay to retry_max_interval regardless.
        self._relogin_attempt = min(self._relogin_attempt + 1, 32)

    async def relogin(self):
        self.last_relogin_timestamp = time.monotonic()
        try:
            await self.web_boiler_client.close_websocket()
        except Exception:
            pass

        try:
            relogin_successful = await self.web_boiler_client.relogin()
        except HttpClientAuthError:
            self._record_relogin_failure()
            _LOGGER.warning("WebBoilerSystem relogin failed due to invalid credentials %s", self._log_account)
            self._entry.async_start_reauth(self._hass)
            return
        except HttpClientConnectionError as err:
            self._record_relogin_failure()
            _LOGGER.warning("WebBoilerSystem relogin failed due to connection error %s (%s)", err, self._log_account)
            return

        if relogin_successful:
            self._record_relogin_success()
            self._annotate_devices()
            await self.web_boiler_client.start_websocket(self.on_parameter_updated)
            try:
                ok = await self.web_boiler_client.refresh()
            except HttpClientAuthError:
                # Relogin just succeeded, so credentials are valid.
                # Treat this as a transient server-side issue.
                _LOGGER.warning(
                    "WebBoilerSystem refresh got login page right after successful "
                    "relogin — treating as transient, not triggering reauth %s",
                    self._log_account,
                )
                ok = False
            except HttpClientConnectionError:
                ok = False
            if ok:
                self.last_refresh_timestamp = time.monotonic()
            return

        self._record_relogin_failure()
        _LOGGER.warning("WebBoilerSystem::tick failed to relogin %s", self._log_account)
