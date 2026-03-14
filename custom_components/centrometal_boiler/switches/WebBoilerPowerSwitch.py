from datetime import datetime
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity

from ..common import create_device_info, format_name
from ..const import DOMAIN, WEB_BOILER_CLIENT, WEB_BOILER_SYSTEM


def _value_is_on(v: Any) -> bool:
    if v in (1, "1", "ON", "On", "on", True, "TRUE", "True", "true"):
        return True
    if v in (0, "0", "OFF", "Off", "off", False, "FALSE", "False", "false"):
        return False
    try:
        intval = int(str(v))
        if intval == 1:
            return True
        if intval == 0:
            return False
    except (ValueError, TypeError):
        pass
    return str(v) != "OFF"


class WebBoilerPowerSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, device) -> None:
        self.hass = hass
        self.web_boiler_client = hass.data[DOMAIN][device.username][WEB_BOILER_CLIENT]
        self.web_boiler_system = hass.data[DOMAIN][device.username][WEB_BOILER_SYSTEM]
        self._device = device
        self._name = format_name(hass, device, f"{device['product']} Boiler Switch")
        self._unique_id = device["serial"]
        self._param_cmd   = device.get_parameter("B_CMD")
        self._param_state = device.get_parameter("B_STATE")

    def __del__(self):
        try:
            if self._param_cmd:
                self._param_cmd.set_update_callback(None, "switch")
        except Exception:
            pass
        try:
            if self._param_state:
                self._param_state.set_update_callback(None, "switch")
        except Exception:
            pass

    async def async_added_to_hass(self):
        self.async_schedule_update_ha_state(False)
        if self._param_cmd:
            self._param_cmd.set_update_callback(self.update_callback, "switch")
        if self._param_state:
            self._param_state.set_update_callback(self.update_callback, "switch")

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

    def _current_cmd_on(self) -> bool | None:
        if not self._param_cmd:
            return None
        try:
            return _value_is_on(self._param_cmd["value"])
        except Exception:
            return None

    def _current_state_on(self) -> bool:
        try:
            return self._param_state["value"] != "OFF"
        except Exception:
            return False

    @property
    def is_on(self) -> bool:
        cmd_val = self._current_cmd_on()
        if cmd_val is not None:
            return cmd_val
        return self._current_state_on()

    @property
    def available(self) -> bool:
        return self.web_boiler_client.is_websocket_connected()

    def _compute_last_updated_str(self) -> str:
        tzinfo = dt_util.get_time_zone(self.hass.config.time_zone)
        for param in (self._param_cmd, self._param_state):
            if not param:
                continue
            try:
                raw_ts = param.get("timestamp") if hasattr(param, "get") else param["timestamp"]
                return datetime.fromtimestamp(int(raw_ts)).astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")
            except Exception:
                continue
        return "?"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"Last updated": self._compute_last_updated_str()}
        try:
            attrs["Command Active (B_CMD)"] = self._param_cmd["value"] if self._param_cmd else "N/A"
        except Exception:
            attrs["Command Active (B_CMD)"] = "N/A"
        try:
            attrs["Boiler State (B_STATE)"] = self._param_state["value"] if self._param_state else "N/A"
        except Exception:
            attrs["Boiler State (B_STATE)"] = "N/A"
        return attrs

    async def _async_turn_and_refresh(self, power_on: bool) -> None:
        await self.web_boiler_client.turn(self._device["serial"], power_on)
        refreshed = await self.web_boiler_client.refresh()
        if refreshed:
            await self.web_boiler_client.data.notify_all_updated()

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_turn_and_refresh(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_turn_and_refresh(False)

    @property
    def device_info(self) -> dict[str, Any]:
        return create_device_info(self._device)
