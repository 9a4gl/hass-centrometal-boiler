import logging
import datetime
import time
from typing import Optional, Callable

from centrometal_web_boiler import WebBoilerClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PREFIX,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    WEB_BOILER_CLIENT,
    WEB_BOILER_SYSTEM,
    WEB_BOILER_LOGIN_RETRY_INTERVAL,
    WEB_BOILER_REFRESH_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Setting up Centrometal Boiler System component")

    prefix = entry.data.get(CONF_PREFIX, "") or ""

    web_boiler_system = WebBoilerSystem(
        hass=hass,
        username=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        prefix=prefix,
    )

    unique_id = entry.data[CONF_EMAIL]
    hass.data[DOMAIN][unique_id] = {}
    hass.data[DOMAIN][unique_id][WEB_BOILER_SYSTEM] = web_boiler_system
    hass.data[DOMAIN][unique_id][WEB_BOILER_CLIENT] = web_boiler_system.web_boiler_client

    ok = await web_boiler_system.start()
    if not ok:
        _LOGGER.error(
            "Got Access Denied Error when setting up Centrometal Boiler System: %s",
            entry.data[CONF_EMAIL],
        )

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, web_boiler_system.stop)

    web_boiler_system.start_tick()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug(
        "Centrometal Boiler System component setup finished %s",
        web_boiler_system.username,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unique_id = entry.data[CONF_EMAIL]
    store = hass.data.get(DOMAIN, {}).get(unique_id)
    system: Optional["WebBoilerSystem"] = None
    if store:
        system = store.get(WEB_BOILER_SYSTEM)

    if system:
        try:
            system.cancel_tick()
        except Exception:
            pass
        try:
            await system.stop()
        except Exception:
            pass

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    try:
        hass.data[DOMAIN].pop(unique_id, None)
    except Exception:
        pass

    return unload_ok


class WebBoilerSystem:
    def __init__(self, hass: HomeAssistant, *, username: str, password: str, prefix: str) -> None:
        self._hass = hass
        self.username = username
        self.password = password
        prefix = prefix.rstrip()
        self.prefix = (prefix + " ") if prefix else ""
        self.web_boiler_client = WebBoilerClient()
        now_ts = datetime.datetime.now().timestamp()
        self.last_relogin_timestamp = now_ts
        self.last_refresh_timestamp = now_ts
        self._tick_unsub: Optional[Callable[[], None]] = None

    async def on_parameter_updated(self, device, param, create: bool = False):
        action = "Create" if create else "update"
        _LOGGER.debug(
            "%s %s %s = %s (%s)",
            action,
            device["serial"],
            param["name"],
            param["value"],
            self.web_boiler_client.username,
        )

    async def start(self) -> bool:
        _LOGGER.debug("Starting Centrometal Boiler System %s", self.username)
        try:
            logged_in = await self.web_boiler_client.login(self.username, self.password)
            if not logged_in:
                raise Exception(f"Cannot login to Centrometal web boiler server {self.username}")
            got_configuration = await self.web_boiler_client.get_configuration()
            if not got_configuration:
                raise Exception(f"Cannot get configuration from Centrometal server {self.username}")
            if len(self.web_boiler_client.data) == 0:
                raise Exception(f"No device found to Centrometal web boiler server {self.username}")
            await self.web_boiler_client.start_websocket(self.on_parameter_updated)
            await self.web_boiler_client.refresh()
            self.last_refresh_timestamp = time.time()
            return True
        except Exception as ex:
            _LOGGER.error("Authentication failed : %s", str(ex))
            return False

    def start_tick(self) -> None:
        self.cancel_tick()

        async def _on_interval(_now) -> None:
            try:
                await self.tick()
            except Exception as ex:
                _LOGGER.warning("WebBoilerSystem.tick raised: %s", ex)

        self._tick_unsub = async_track_time_interval(
            self._hass, _on_interval, datetime.timedelta(seconds=1)
        )

    def cancel_tick(self) -> None:
        if self._tick_unsub:
            try:
                self._tick_unsub()
            except Exception:
                pass
            self._tick_unsub = None

    async def stop(self, event=None):
        _LOGGER.debug("Stopping Centrometal WebBoilerSystem %s", self.web_boiler_client.username)
        return await self.web_boiler_client.close_websocket()

    async def tick(self):
        now = datetime.datetime.now().timestamp()
        try:
            connected = self.web_boiler_client.is_websocket_connected()
        except Exception:
            connected = False

        if not connected:
            if now - self.last_relogin_timestamp > WEB_BOILER_LOGIN_RETRY_INTERVAL:
                _LOGGER.info(
                    "Centrometal WebBoilerSystem::tick trying to relogin %s",
                    self.web_boiler_client.username,
                )
                await self.relogin()
            return

        if now - self.last_refresh_timestamp > WEB_BOILER_REFRESH_INTERVAL:
            self.last_refresh_timestamp = now
            _LOGGER.info(
                "WebBoilerSystem::tick refresh data %s",
                self.web_boiler_client.username,
            )
            refresh_successful = await self.web_boiler_client.refresh()
            if not refresh_successful:
                await self.relogin()

    async def relogin(self):
        self.last_relogin_timestamp = time.time()
        try:
            await self.web_boiler_client.close_websocket()
        except Exception:
            pass
        try:
            await self.web_boiler_client.http_client.close_session()
        except Exception:
            pass
        relogin_successful = await self.web_boiler_client.relogin()
        if relogin_successful:
            await self.web_boiler_client.start_websocket(self.on_parameter_updated)
            ok = await self.web_boiler_client.refresh()
            if ok:
                self.last_refresh_timestamp = time.time()
        else:
            _LOGGER.warning(
                "WebBoilerSystem::tick failed to relogin %s",
                self.web_boiler_client.username,
            )
