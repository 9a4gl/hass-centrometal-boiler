"""Support for Centrometa PelTec System devices."""
import logging

from peltec import PelTecClient

from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STOP,
    EVENT_TIME_CHANGED,
)

from homeassistant.core import HomeAssistant

from .const import DOMAIN, PELTEC_CLIENT, PELTEC_SYSTEM

_LOGGER = logging.getLogger(__name__)

# PLATFORMS = ("vacuum", "sensor", "switch", "binary_sensor")
PLATFORMS = ["sensor"]

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
        await hass.async_add_executor_job(peltec_system.start)
    except Exception as ex:
        _LOGGER.error(
            "Got Access Denied Error when setting up Centrometal PelTec System: %s", ex
        )
        return False

    hass.data[DOMAIN][PELTEC_SYSTEM] = peltec_system

    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, lambda event: peltec_system.stop()
    )

    hass.bus.async_listen(EVENT_TIME_CHANGED, peltec_system.tick)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    _LOGGER.debug("Centrometal PelTec System component setup finished")
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

    def on_parameter_updated(self, device, param, create=False):
        action = "Create" if create else "update"
        serial = device["serial"]
        name = param["name"]
        value = param["value"]
        _LOGGER.info("%s %s %s = %s", action, serial, name, value)

    def start(self):
        _LOGGER.debug("Starting Centrometal PelTec System")
        self._hass.data[DOMAIN][PELTEC_CLIENT] = self.peltec_client

        try:
            if not self.peltec_client.login(self.username, self.password):
                raise Exception("Cannot login to Centrometal PelTec server")
            if not self.peltec_client.get_configuration():
                raise Exception(
                    "Cannot get configuration from Centrometal PelTec server"
                )
            if len(self.peltec_client.data) == 0:
                raise Exception("No device found to Centrometal PelTec server")
            self.peltec_client.start_websocket(self.on_parameter_updated, False)
        except Exception as ex:
            _LOGGER.error("Authentication failed : %s", str(ex))

    def stop(self):
        _LOGGER.debug("Stopping CentrometalPelTecSystem")
        self.peltec_client.stop()

    def tick(self, now):
        _LOGGER.info("Tick CentrometalPelTecSystem " + str(now))
