"""Support for PelTec switch (Power control)."""

import logging

from homeassistant.core import callback
from homeassistant.components.switch import SwitchEntity

import homeassistant.util.dt as dt_util
from datetime import datetime

import peltec
from .const import DOMAIN, PELTEC_CLIENT, create_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the switches platform."""
    entities = []
    peltec_client = hass.data[DOMAIN][PELTEC_CLIENT]
    for device in peltec_client.data.values():
        entities.append(PelTectPowerSwitch(hass, device))
    _LOGGER.debug("Adding PelTec control as switch: %s", entities)
    async_add_entities(entities, True)


class PelTectPowerSwitch(SwitchEntity):
    """Representation of a PelTec Power Switch."""

    def __init__(self, hass, device):
        """Initialize the PelTec Power Switch."""
        self.hass = hass
        self.peltec_client = hass.data[DOMAIN][PELTEC_CLIENT]
        self._device = device
        self._name = "PelTec Boiler"
        self._unique_id = device["serial"]
        self._state = None
        self._error_message = ""
        self._param = device["parameters"]["B_STATE"]

    async def async_added_to_hass(self):
        """Subscribe to events."""
        self.schedule_update_ha_state(True)
        self._param.set_update_callback(self.update_callback)

    @property
    def should_poll(self) -> bool:
        """No polling needed for a power socket."""
        return False

    def update_callback(self, device):
        """Call update for Home Assistant when the device is updated."""
        self.schedule_update_ha_state(True)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if it is on."""
        return self._param["value"] != "OFF"

    @property
    def available(self):
        """Return True if the device is available."""
        return self.peltec_client.is_websocket_connected()

    def error(self):
        """Return the error message."""
        return self._error_message

    @property
    def device_state_attributes(self):
        """Return the state attributes of the power switch."""
        tzinfo = dt_util.get_time_zone(self.hass.config.time_zone)
        last_updated_dt = datetime.fromtimestamp(int(self._param["timestamp"]))
        last_updated = last_updated_dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")
        attributes = {}
        attributes["Last updated"] = last_updated
        return attributes

    def turn_on(self, **kwargs):
        self.peltec_client.turn(self._device["serial"], True)

    def turn_off(self, **kwargs):
        self.peltec_client.turn(self._device["serial"], False)

    @property
    def device_info(self):
        return create_device_info(self._device)
