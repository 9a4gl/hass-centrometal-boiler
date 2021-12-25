"""Support for Centrometa PelTec System devices."""
import logging
import datetime

from peltec import PelTecClient

from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STOP,
    EVENT_TIME_CHANGED,
)

from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    PELTEC_CLIENT,
    PELTEC_SYSTEM,
    PELTEC_LOGIN_RETRY_INTERVAL,
    PELTEC_REFRESH_INTERVAL,
)

from .services import setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch", "binary_sensor"]

# pylint: disable=missing-function-docstring
# pylint: disable=broad-except


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Centrometal PelTec System integration."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Setting up Centrometal PelTec System component")

    peltec_system = PelTecSystem(
        hass, username=entry.data[CONF_EMAIL], password=entry.data[CONF_PASSWORD]
    )

    try:
        await peltec_system.start()
    except Exception as ex:
        _LOGGER.error(
            "Got Access Denied Error when setting up Centrometal PelTec System: %s", ex
        )
        return False

    hass.data[DOMAIN][PELTEC_SYSTEM] = peltec_system

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, peltec_system.stop())

    hass.bus.async_listen(EVENT_TIME_CHANGED, peltec_system.tick)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    setup_services(hass)

    _LOGGER.debug(
        "Centrometal PelTec System component setup finished " + peltec_system.username
    )
    return True


class PelTecSystem:
    """A Centrometal PelTec System class."""

    def __init__(self, hass, *, username, password):
        """Initialize the Centrometal PelTec System."""
        self._hass = hass
        self.username = username
        self.password = password
        self.peltec_client = None
        self.peltec_client = PelTecClient()
        self.last_relogin_timestamp = datetime.datetime.timestamp(
            datetime.datetime.now()
        )
        self.last_refresh_timestamp = datetime.datetime.timestamp(
            datetime.datetime.now()
        )

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
            self.peltec_client.username,
        )
        pass

    async def start(self):
        _LOGGER.debug(f"Starting Centrometal PelTec System {self.username}")
        self._hass.data[DOMAIN][PELTEC_CLIENT] = self.peltec_client

        try:
            loggedIn = await self.peltec_client.login(self.username, self.password)
            if not loggedIn:
                raise Exception(
                    f"Cannot login to Centrometal PelTec server {self.username}"
                )
            gotConfiguration = await self.peltec_client.get_configuration()
            if not gotConfiguration:
                raise Exception(
                    f"Cannot get configuration from Centrometal server {self.username}"
                )
            if len(self.peltec_client.data) == 0:
                raise Exception(
                    f"No device found to Centrometal PelTec server {self.username}"
                )
            await self.peltec_client.start_websocket(self.on_parameter_updated)
        except Exception as ex:
            _LOGGER.error("Authentication failed : %s", str(ex))

    async def stop(self):
        _LOGGER.debug(f"Stopping CentrometalPelTecSystem {self.peltec_client.username}")
        await self.peltec_client.close_websocket()

    async def tick(self, now):
        timestamp = datetime.datetime.timestamp(now.time_fired)
        if not self.peltec_client.is_websocket_connected():
            if timestamp - self.last_relogin_timestamp > PELTEC_LOGIN_RETRY_INTERVAL:
                _LOGGER.info(
                    f"CentrometalPelTecSystem::tick trying to relogin {self.peltec_client.username}"
                )
                self.last_relogin_timestamp = timestamp
                await self.peltec_client.close_websocket()
                reloginSuccessful = await self.peltec_client.relogin()
                if reloginSuccessful:
                    await self.peltec_client.start_websocket(self.on_parameter_updated)
                else:
                    _LOGGER.warning(
                        f"CentrometalPelTecSystem::tick failed to relogin {self.peltec_client.username}"
                    )
        else:
            if timestamp - self.last_refresh_timestamp > PELTEC_REFRESH_INTERVAL:
                self.last_refresh_timestamp = timestamp
                _LOGGER.info(
                    f"CentrometalPelTecSystem::tick refresh data {self.peltec_client.username}"
                )
                await self.peltec_client.refresh()
