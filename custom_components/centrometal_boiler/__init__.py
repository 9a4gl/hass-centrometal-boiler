"""Support for Centrometa Boiler devices."""

import logging
import datetime
import time

from centrometal_web_boiler import WebBoilerClient

from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PREFIX,
    EVENT_HOMEASSISTANT_STOP,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .const import (
    DOMAIN,
    WEB_BOILER_CLIENT,
    WEB_BOILER_SYSTEM,
    WEB_BOILER_LOGIN_RETRY_INTERVAL,
    WEB_BOILER_REFRESH_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch", "binary_sensor"]

# pylint: disable=missing-function-docstring
# pylint: disable=broad-except


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Centrometal Boiler System integration."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Setting up Centrometal Boiler System component")

    prefix = entry.data[CONF_PREFIX] if (CONF_PREFIX in entry.data) else ""
    web_boiler_system = WebBoilerSystem(
        hass,
        username=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        prefix=prefix,
    )

    unique_id = entry.data[CONF_EMAIL]
    hass.data[DOMAIN][unique_id] = {}
    hass.data[DOMAIN][unique_id][WEB_BOILER_SYSTEM] = web_boiler_system

    if not await web_boiler_system.start():
        _LOGGER.error(
            "Got Access Denied Error when setting up Centrometal Boiler System: %s",
            entry.data[CONF_EMAIL],
        )

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, web_boiler_system.stop())

    async def schedule_tick() -> None:
        async_call_later(hass, 1.0, fire_time_event)

    async def fire_time_event(target: float) -> None:
        await web_boiler_system.tick()
        await schedule_tick()

    await schedule_tick()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug(
        "Centrometal Boiler System component setup finished "
        + web_boiler_system.username
    )
    return True


class WebBoilerSystem:
    """A Centrometal Boiler System class."""

    def __init__(self, hass, *, username, password, prefix):
        """Initialize the Centrometal Boiler System."""
        self._hass = hass
        self.username = username
        self.password = password
        self.prefix = prefix.rstrip()
        if len(self.prefix) > 0:
            self.prefix = self.prefix + " "
        self.web_boiler_client = WebBoilerClient()
        self.web_boiler_client.set_connectivity_callback(self.update_callback)
        self.last_relogin_timestamp = datetime.datetime.timestamp(
            datetime.datetime.now()
        )
        self.last_refresh_timestamp = datetime.datetime.timestamp(
            datetime.datetime.now()
        )
    
    async def update_callback(self, status):
        _LOGGER.debug(f"update_callback called")
        if not self.web_boiler_client.websocket_connected:
            _LOGGER.debug(f"Trying relogin")
            await self.relogin()

    async def on_parameter_updated(self, device, param, create=False):
        action = "Create" if create else "update"
        serial = device["serial"]
        name = param["name"]
        value = param["value"]
        _LOGGER.info(
            "%s %s %s = %s (%s)",
            action,
            serial,
            name,
            value,
            self.web_boiler_client.username,
        )
        pass

    async def start(self):
        _LOGGER.debug(f"Starting Centrometal Boiler System {self.username}")
        self._hass.data[DOMAIN][self.username][WEB_BOILER_CLIENT] = (
            self.web_boiler_client
        )

        try:
            loggedIn = await self.web_boiler_client.login(self.username, self.password)
            if not loggedIn:
                raise Exception(
                    f"Cannot login to Centrometal web boiler server {self.username}"
                )
            gotConfiguration = await self.web_boiler_client.get_configuration()
            if not gotConfiguration:
                raise Exception(
                    f"Cannot get configuration from Centrometal server {self.username}"
                )
            if len(self.web_boiler_client.data) == 0:
                raise Exception(
                    f"No device found to Centrometal web boiler server {self.username}"
                )
            await self.web_boiler_client.start_websocket(self.on_parameter_updated)
            await self.web_boiler_client.refresh()
            return True
        except Exception as ex:
            _LOGGER.error("Authentication failed : %s", str(ex))
            return False

    async def stop(self):
        _LOGGER.debug(
            f"Stopping Centrometal WebBoilerSystem {self.web_boiler_client.username}"
        )
        return await self.web_boiler_client.close_websocket()

    async def tick(self):
        datenow = datetime.datetime.now()
        timestamp = datetime.datetime.timestamp(datenow)
        if not self.web_boiler_client.is_websocket_connected():
            if (
                timestamp - self.last_relogin_timestamp
                > WEB_BOILER_LOGIN_RETRY_INTERVAL
            ):
                _LOGGER.info(
                    f"Centrometal WebBoilerSystem::tick trying to relogin {self.web_boiler_client.username}"
                )
                await self.relogin()
        else:
            if timestamp - self.last_refresh_timestamp > WEB_BOILER_REFRESH_INTERVAL:
                self.last_refresh_timestamp = timestamp
                _LOGGER.info(
                    f"WebBoilerSystem::tick refresh data {self.web_boiler_client.username}"
                )
                refresh_successful = await self.web_boiler_client.refresh()
                if not refresh_successful:
                    await self.relogin()

    async def relogin(self):
        self.last_relogin_timestamp = time.time()
        await self.web_boiler_client.close_websocket()
        await self.web_boiler_client.http_client.close_session()
        relogin_successful = await self.web_boiler_client.relogin()
        if relogin_successful:
            await self.web_boiler_client.start_websocket(self.on_parameter_updated)
            await self.web_boiler_client.refresh()
        else:
            _LOGGER.warning(
                f"WebBoilerSystem::tick failed to relogin {self.web_boiler_client.username}"
            )
