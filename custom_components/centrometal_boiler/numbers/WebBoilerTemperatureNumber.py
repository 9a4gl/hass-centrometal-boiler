"""Writable temperature setting (e.g. day/night room temperature of a circuit)."""

import logging

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

# pylint: disable=relative-beyond-top-level
from ..common import create_device_info, format_name
from ..const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


class WebBoilerTemperatureNumber(NumberEntity):
    """Temperature set point stored in boiler parameter PVAL_<dbindex>_0.

    The value is written the same way the Centrometal web portal does it:
    POST /api/inst/control/multiple  {"messages": {<id>: {"PWR <dbindex>": <value>}}}
    """

    _attr_should_poll = False
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_icon = "mdi:thermometer-lines"

    def __init__(self, hass: HomeAssistant, device, naslov, dbindex) -> None:
        self.hass = hass
        self.web_boiler_client = hass.data[DOMAIN][device.username][WEB_BOILER_CLIENT]
        self._device = device
        self._dbindex = dbindex
        self._attr_name = format_name(hass, device, naslov)
        self._attr_unique_id = f"{device['serial']}_number_{dbindex}"
        self._callback_key = f"number_{dbindex}"
        self._params = []
        for prefix in ("PVAL", "PMIN", "PMAX", "PDEF"):
            name = f"{prefix}_{dbindex}_0"
            param = device.get_parameter(name) if device.has_parameter(name) else None
            setattr(self, f"_param_{prefix.lower()}", param)
            if param is not None:
                param["used"] = True
                self._params.append(param)

    async def async_added_to_hass(self):
        for param in self._params:
            param.set_update_callback(self.update_callback, self._callback_key)

    async def async_will_remove_from_hass(self):
        for param in self._params:
            param.set_update_callback(None, self._callback_key)

    async def update_callback(self, device):
        self.async_write_ha_state()

    @staticmethod
    def _as_float(param, fallback):
        try:
            return float(param["value"])
        except (TypeError, KeyError, ValueError):
            return fallback

    @property
    def native_value(self):
        return self._as_float(self._param_pval, None)

    @property
    def native_min_value(self):
        return self._as_float(self._param_pmin, 0.0)

    @property
    def native_max_value(self):
        return self._as_float(self._param_pmax, 100.0)

    @property
    def available(self):
        return self.web_boiler_client.is_websocket_connected()

    @property
    def extra_state_attributes(self):
        return {
            "dbindex": self._dbindex,
            "default": self._as_float(self._param_pdef, None),
        }

    @property
    def device_info(self):
        return create_device_info(self._device)

    async def async_set_native_value(self, value: float) -> None:
        if not self.native_min_value <= value <= self.native_max_value:
            raise HomeAssistantError(
                f"{value} is outside {self.native_min_value}-{self.native_max_value}"
            )
        new_value = int(round(value))
        client = self.web_boiler_client
        serial = self._device["serial"]
        if hasattr(client, "set_parameter"):
            ok = await client.set_parameter(serial, self._dbindex, new_value)
        else:  # library without set_parameter (<= 0.0.58)
            data = {"messages": {str(self._device["id"]): {f"PWR {self._dbindex}": new_value}}}
            try:
                response = await client.http_client._control_multiple(data)
                ok = response.get("status") == "success"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.warning("Setting PWR %s failed: %s", self._dbindex, err)
                ok = False
        if not ok:
            await client.relogin()
            raise HomeAssistantError(f"Boiler did not accept PWR {self._dbindex}={new_value}")
        _LOGGER.info("Set PWR %s = %s (%s)", self._dbindex, new_value, serial)
