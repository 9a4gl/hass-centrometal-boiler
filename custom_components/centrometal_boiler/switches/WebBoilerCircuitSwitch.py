import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError
import homeassistant.util.dt as dt_util

from ..common import create_device_info, format_name


class WebBoilerCircuitSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, device, naslov, dbindex) -> None:
        self.hass = hass
        self.web_boiler_client = device["__client"]
        self._system = device["__system"]
        self._device = device
        self._serial = device["serial"]
        self._name = format_name(hass, device, naslov)
        self._unique_id = f"{self._serial}_switch_{dbindex}"
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

    async def async_will_remove_from_hass(self) -> None:
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

    @staticmethod
    def _coerce_number(value):
        try:
            return float(str(value).strip().replace(",", "."))
        except (ValueError, TypeError, AttributeError):
            return None

    @staticmethod
    def _coerce_bool(value):
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in ("1", "on", "true", "yes", "active", "enabled"):
            return True
        if text in ("0", "off", "false", "no", "inactive", "disabled"):
            return False
        return None

    @property
    def is_on(self) -> bool | None:
        """Return circuit state from the live PVAL value.

        Some Centrometal circuit rows, especially DHW, do not report the live
        ON state as exactly PMAX. The command API still uses 1/0, while the
        parameter table may expose PMAX as a limit/option value instead of the
        current ON value. Treat anything different from PMIN/OFF as ON, and
        keep PMAX as a fallback for devices that do not expose PMIN.
        """
        try:
            state_raw = self._param_state["value"]
        except KeyError:
            return None

        state_bool = self._coerce_bool(state_raw)
        if state_bool is not None:
            return state_bool

        state_num = self._coerce_number(state_raw)
        if state_num is None:
            return None

        off_num = self._coerce_number(self._param_off.get("value"))
        if off_num is not None:
            return state_num != off_num

        on_num = self._coerce_number(self._param_on.get("value"))
        if on_num is not None:
            return state_num == on_num

        return state_num != 0

    @property
    def available(self) -> bool:
        return self.web_boiler_client.has_fresh_data()

    def _compute_last_updated_str(self) -> str:
        tzinfo = dt_util.get_time_zone(self.hass.config.time_zone)
        try:
            raw_ts = self._param_state["timestamp"]
            if raw_ts is not None:
                # Fixed: use timezone-aware fromtimestamp (Python 3.12+ deprecation)
                dt = datetime.datetime.fromtimestamp(int(raw_ts), tz=datetime.timezone.utc)
                return dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            pass
        return "?"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        # Diagnostics: surface the raw triplet that drives is_on so users
        # who report "HA shows Off but WebUI shows On" bugs can paste the
        # values directly into an issue.
        attrs: dict[str, Any] = {"Last updated": self._compute_last_updated_str()}
        try:
            attrs["PVAL"] = self._param_state.get("value")
            attrs["PMIN"] = self._param_off.get("value") if self._param_off else None
            attrs["PMAX"] = self._param_on.get("value") if self._param_on else None
        except Exception:
            pass
        return attrs

    async def turn_circuit_on_off(self, value: bool):
        ok = await self.web_boiler_client.turn_circuit(self._device["serial"], self._dbindex, value)
        if not ok:
            await self._system.relogin()
            raise HomeAssistantError("Failed to send the heating circuit command")
        refreshed = await self.web_boiler_client.refresh()
        if not refreshed:
            raise HomeAssistantError(
                "The heating circuit command was sent, but the integration could not refresh the latest state"
            )
        await self.web_boiler_client.data.notify_all_updated()

    async def async_turn_on(self, **kwargs) -> None:
        await self.turn_circuit_on_off(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.turn_circuit_on_off(False)

    @property
    def device_info(self) -> dict[str, Any]:
        return create_device_info(self._device)
