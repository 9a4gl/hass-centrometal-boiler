from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity
import homeassistant.util.dt as dt_util

from ..const import DOMAIN, WEB_BOILER_CLIENT
from ..common import create_device_info, format_name


class WebBoilerCircuitSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, device, naslov, dbindex) -> None:
        self.hass = hass
        self.web_boiler_client = hass.data[DOMAIN][device.username][WEB_BOILER_CLIENT]
        self._device = device
        self._serial = device["serial"]
        self._name = format_name(hass, device, naslov)
        self._unique_id = f"{self._serial}_switch_{dbindex}"
        self._dbindex = dbindex
        self._table_key = f"table_{dbindex}_switch"
        self._param_name_def   = f"PDEF_{dbindex}_0"
        self._param_name_state = f"PVAL_{dbindex}_0"
        self._param_name_off   = f"PMIN_{dbindex}_0"
        self._param_name_on    = f"PMAX_{dbindex}_0"
        self._param_def   = self._device.get_parameter(self._param_name_def)
        self._param_state = self._device.get_parameter(self._param_name_state)
        self._param_off   = self._device.get_parameter(self._param_name_off)
        self._param_on    = self._device.get_parameter(self._param_name_on)
        self._param_def["used"]   = True
        self._param_state["used"] = True
        self._param_off["used"]   = True
        self._param_on["used"]    = True

    def __del__(self):
        try:
            self._param_def.set_update_callback(None, self._table_key)
            self._param_state.set_update_callback(None, self._table_key)
            self._param_off.set_update_callback(None, self._table_key)
            self._param_on.set_update_callback(None, self._table_key)
        except Exception:
            pass

    async def async_added_to_hass(self):
        self.async_schedule_update_ha_state(False)
        self._param_def.set_update_callback(self.update_callback, self._table_key)
        self._param_state.set_update_callback(self.update_callback, self._table_key)
        self._param_off.set_update_callback(self.update_callback, self._table_key)
        self._param_on.set_update_callback(self.update_callback, self._table_key)

    @property
    def should_poll(self) -> bool:
        return False

    async def update_callback(self, _device):
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool:
        try:
            return int(self._param_state["value"]) == int(self._param_on["value"])
        except (ValueError, KeyError, TypeError):
            return False

    @property
    def available(self) -> bool:
        return self.web_boiler_client.is_websocket_connected()

    def _compute_last_updated_str(self) -> str:
        tzinfo = dt_util.get_time_zone(self.hass.config.time_zone)
        try:
            raw_ts = self._param_state["timestamp"]
            if raw_ts is not None:
                return datetime.fromtimestamp(int(raw_ts)).astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            pass
        return "?"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"Last updated": self._compute_last_updated_str()}

    async def turn_circuit_on_off(self, value: bool):
        ok = await self.web_boiler_client.turn_circuit(self._device["serial"], self._dbindex, value)
        if not ok:
            self.web_boiler_client.relogin()

    async def async_turn_on(self, **kwargs) -> None:
        await self.turn_circuit_on_off(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.turn_circuit_on_off(False)

    @property
    def device_info(self) -> dict[str, Any]:
        return create_device_info(self._device)
