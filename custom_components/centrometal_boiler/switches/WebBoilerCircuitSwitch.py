from ..const import DOMAIN, WEB_BOILER_CLIENT
from ..common import create_device_info, format_name

from homeassistant.components.switch import SwitchEntity

import homeassistant.util.dt as dt_util
from datetime import datetime

import asyncio


class WebBoilerCircuitSwitch(SwitchEntity):
    """Representation of a boiler Power Switch."""

    def __init__(self, hass, device, naslov, dbindex):
        """Initialize the Boiler Power Switch."""
        self.hass = hass
        self.web_boiler_client = hass.data[DOMAIN][device.username][WEB_BOILER_CLIENT]
        self._device = device
        self._product = device["product"]
        self._serial = device["serial"]
        self._name = format_name(hass, device, naslov)
        self._unique_id = device["serial"] + "_switch_" + str(dbindex)
        self._state = None
        self._error_message = ""
        self._dbindex = dbindex
        self._table_key = f"table_{dbindex}_switch"
        self._param_name_def = f"PDEF_{dbindex}_0"
        self._param_name_state = f"PVAL_{dbindex}_0"
        self._param_name_off = f"PMIN_{dbindex}_0"
        self._param_name_on = f"PMAX_{dbindex}_0"
        self._param_def = self._device.get_parameter(self._param_name_def)
        self._param_state = self._device.get_parameter(self._param_name_state)
        self._param_off = self._device.get_parameter(self._param_name_off)
        self._param_on = self._device.get_parameter(self._param_name_on)
        self._param_def["used"] = True
        self._param_state["used"] = True
        self._param_off["used"] = True
        self._param_on["used"] = True

    def __del__(self):
        self._param_def.set_update_callback(None, self._table_key)
        self._param_state.set_update_callback(None, self._table_key)
        self._param_off.set_update_callback(None, self._table_key)
        self._param_on.set_update_callback(None, self._table_key)

    async def async_added_to_hass(self):
        """Subscribe to events."""
        self.async_schedule_update_ha_state(False)
        self._param_def.set_update_callback(self.update_callback, self._table_key)
        self._param_state.set_update_callback(self.update_callback, self._table_key)
        self._param_off.set_update_callback(self.update_callback, self._table_key)
        self._param_on.set_update_callback(self.update_callback, self._table_key)

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
        try:
            return int(self._param_state["value"]) == int(self._param_on["value"])
        except ValueError:
            return False

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
        last_updated = "?"
        if "timestamp" in self._param_state.keys():
            last_updated_dt = datetime.fromtimestamp(
                int(self._param_state["timestamp"])
            )
            last_updated = last_updated_dt.astimezone(tzinfo).strftime(
                "%d.%m.%Y %H:%M:%S"
            )
        attributes = {}
        attributes["Last updated"] = last_updated
        return attributes

    async def turn_circuit_on_off(self, value):
        if not await self.web_boiler_client.turn_circuit(
            self._device["serial"], self._dbindex, value
        ):
            self.web_boiler_client.relogin()

    async def turn_circuit_off(self):
        await self.web_boiler_client.turn_circuit(
            self._device["serial"], self._dbindex, False
        )

    def turn_on(self, **kwargs):
        asyncio.run_coroutine_threadsafe(
            self.turn_circuit_on_off(True),
            self.hass.loop,
        )

    def turn_off(self, **kwargs):
        asyncio.run_coroutine_threadsafe(
            self.turn_circuit_on_off(False),
            self.hass.loop,
        )

    @property
    def device_info(self):
        return create_device_info(self._device)
