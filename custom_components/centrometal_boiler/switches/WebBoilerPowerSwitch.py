from ..const import DOMAIN, WEB_BOILER_CLIENT, WEB_BOILER_SYSTEM
from ..common import create_device_info

from homeassistant.components.switch import SwitchEntity

import homeassistant.util.dt as dt_util
from datetime import datetime

import asyncio


class WebBoilerPowerSwitch(SwitchEntity):
    """Representation of a boiler Power Switch."""

    def __init__(self, hass, device):
        """Initialize the Boiler Power Switch."""
        self.hass = hass
        self.web_boiler_client = hass.data[DOMAIN][WEB_BOILER_CLIENT]
        self.web_boiler_system = hass.data[DOMAIN][WEB_BOILER_SYSTEM]
        self._device = device
        self._product = device["product"]
        self._name = f"{self.web_boiler_system.prefix} {self._product} Boiler Switch"
        self._unique_id = device["serial"]
        self._state = None
        self._error_message = ""
        self._param = device.get_parameter("B_STATE")

    def __del__(self):
        self._param.set_update_callback(None, "switch")

    async def async_added_to_hass(self):
        """Subscribe to events."""
        self.async_schedule_update_ha_state(False)
        self._param.set_update_callback(self.update_callback, "switch")

    @property
    def should_poll(self) -> bool:
        """No polling needed for a power socket."""
        return False

    async def update_callback(self, device):
        """Call update for Home Assistant when the device is updated."""
        self.async_write_ha_state()

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
        return self.web_boiler_client.is_websocket_connected()

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
        asyncio.run_coroutine_threadsafe(
            self.web_boiler_client.turn(self._device["serial"], True), self.hass.loop
        )

    def turn_off(self, **kwargs):
        asyncio.run_coroutine_threadsafe(
            self.web_boiler_client.turn(self._device["serial"], False), self.hass.loop
        )

    @property
    def device_info(self):
        return create_device_info(self._device)
