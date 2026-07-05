import logging
from typing import List, Dict, Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower, UnitOfTime, PERCENTAGE
from homeassistant.core import HomeAssistant

from ..common import format_name, format_time, create_device_info

from .generic_sensors_all import GENERIC_SENSORS_COMMON, get_generic_temperature_settings_sensors
from .generic_sensors_peltec import PELTEC2_GENERIC_SENSORS, PELTEC_GENERIC_SENSORS
from .generic_sensors_compact import COMPACT_GENERIC_SENSORS
from .generic_sensors_cm_pelet_set import CM_PELET_SET_GENERIC_SENSORS
from .generic_sensors_biotec import BIOTEC_GENERIC_SENSORS
from .generic_sensors_biotec_plus import BIOTEC_PLUS_GENERIC_SENSORS
from ..peltec2 import (
    configuration_has_buffer,
    configuration_has_dhw,
    decode_internet_access,
    decode_start_transition,
    decode_status_mark,
    decode_status_mark_details,
    decode_tank_level,
    portal_hex_bit_is_set,
    valid_lambda,
    valid_nonnegative_measurement,
    valid_percentage,
    valid_signal_db,
    valid_temperature,
)

_LOGGER = logging.getLogger(__name__)


class WebBoilerGenericSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, device, sensor_data, parameter, disabled_by_default: bool = False) -> None:
        self.hass = hass
        self.web_boiler_client = device["__client"]
        self.web_boiler_system = device["__system"]
        self.device = device
        self.parameter = parameter

        self._unit = sensor_data[0]
        self._icon = sensor_data[1]
        self._device_class = sensor_data[2]
        self._description = sensor_data[3]
        if device.get("type") == "peltec2":
            self._description = {
                "B_VER": "Software Version",
                "B_sng": "Rated Boiler Power",
            }.get(parameter["name"], self._description)
            if parameter["name"] == "B_sng":
                self._unit = UnitOfPower.KILO_WATT
        self._attributes_map = sensor_data[4] if len(sensor_data) == 5 else {}

        self._serial = device["serial"]
        self._param_name = parameter["name"]
        self._product = device["product"]
        if disabled_by_default:
            self._attr_entity_registry_enabled_default = False
            self._attr_entity_registry_visible_default = False
        self._name = format_name(hass, device, f"{self._product} {self._description}")
        self._unique_id = f"{self._serial}-{self._param_name}"
        self._callback_id = f"{self._unique_id}-generic"
        self.added_to_hass = False

        self.parameter["used"] = True
        for attr_param_name in self._attributes_map:
            attr_param = self.device.get_parameter(attr_param_name)
            attr_param["used"] = True

    async def async_will_remove_from_hass(self) -> None:
        if hasattr(self.parameter, "set_update_callback"):
            self.parameter.set_update_callback(None, self._callback_id)
        if self._param_name == "B_start" and self.device.has_parameter("B_STATE"):
            self.device.get_parameter("B_STATE").set_update_callback(None, f"{self._callback_id}-state")
        if self._param_name == "B_Oxy1":
            if self.device.has_parameter("B_STATE"):
                self.device.get_parameter("B_STATE").set_update_callback(None, f"{self._callback_id}-state")
            if self.device.has_parameter("B_fireS"):
                self.device.get_parameter("B_fireS").set_update_callback(None, f"{self._callback_id}-flame")
        if self._param_name == "B_razP" and self.device.has_parameter("B_addConf"):
            self.device.get_parameter("B_addConf").set_update_callback(None, f"{self._callback_id}-accessory")

    async def async_added_to_hass(self):
        self.added_to_hass = True
        self.async_schedule_update_ha_state(False)
        if hasattr(self.parameter, "set_update_callback"):
            self.parameter.set_update_callback(self.update_callback, self._callback_id)
        if self._param_name == "B_start" and self.device.has_parameter("B_STATE"):
            self.device.get_parameter("B_STATE").set_update_callback(self.update_callback, f"{self._callback_id}-state")
        if self._param_name == "B_Oxy1":
            if self.device.has_parameter("B_STATE"):
                self.device.get_parameter("B_STATE").set_update_callback(
                    self.update_callback, f"{self._callback_id}-state"
                )
            if self.device.has_parameter("B_fireS"):
                self.device.get_parameter("B_fireS").set_update_callback(
                    self.update_callback, f"{self._callback_id}-flame"
                )
        if self._param_name == "B_razP" and self.device.has_parameter("B_addConf"):
            self.device.get_parameter("B_addConf").set_update_callback(
                self.update_callback, f"{self._callback_id}-accessory"
            )

    @property
    def should_poll(self) -> bool:
        return False

    async def update_callback(self, _param) -> None:
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def icon(self) -> str | None:
        return self._icon

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    @property
    def device_class(self) -> str | None:
        return self._device_class

    @property
    def state_class(self) -> str | None:
        # Set temperatures are configuration targets, not measurements. Keep
        # their Celsius device class and unit conversion, but do not generate
        # long-term min/max/mean statistics for them.
        if self.device.get("type") == "peltec2" and self._param_name.endswith(("_Tpol", "_Tsob")):
            return None
        # RSSI is diagnostic and changes unit from the erroneous percentage
        # mapping used in 0.2.0.10. Do not create long-term statistics for it,
        # which also avoids a percentage-to-dB statistics migration conflict.
        if self.device.get("type") == "peltec2" and self._param_name == "B_signal":
            return None
        if self._device_class == SensorDeviceClass.TEMPERATURE:
            return SensorStateClass.MEASUREMENT
        # Any percentage or rpm-unit parameter is a plain numeric reading —
        # covers every current one (air flow, lambda probe, pellet level,
        # wifi signal, mixing valve, fan/motor speed, power modulation) and
        # any future one, instead of a hand-maintained per-code allowlist
        # that's easy to forget to update when adding a new sensor.
        if self._unit in (PERCENTAGE, "rpm", "dB"):
            return SensorStateClass.MEASUREMENT
        if self._unit == UnitOfTime.MINUTES and self._param_name.startswith("CNT_"):
            return SensorStateClass.TOTAL_INCREASING
        if self._param_name == "CNT_1":
            return SensorStateClass.TOTAL_INCREASING
        if self._param_name == "CNT_7":
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def suggested_display_precision(self) -> int | None:
        """Return the suggested number of decimals for numeric sensors.

        Home Assistant treats ANY entity with this set as "must be numeric"
        and raises ValueError on the next state update if native_value isn't
        coercible to a number (verified directly against Home Assistant's
        own sensor entity source: setting this — independent of unit or
        state_class — flips _numeric_state_expected() to True). So every
        text-returning parameter (Yes/No, On/Off, Open/Closed, the tank
        level and supply type enums) is excluded explicitly here, rather
        than relying on none of them currently having a unit/state_class
        set — that's true today (checked across every device table) but
        isn't an invariant a future edit is guaranteed to preserve.
        """
        text_returning_params = (
            WebBoilerGenericSensor._YES_NO_PARAMS
            | WebBoilerGenericSensor._ON_OFF_PARAMS
            | WebBoilerGenericSensor._VALVE_PARAMS
            | {"B_razina", "B_SUP_TYPE", "B_specG", "B_start", "B_Inp1", "B_addConf"}
        )
        if self._param_name in text_returning_params:
            return None

        # All CNT_ counters are whole numbers, whether they count events
        # (ignition starts) or minutes of runtime -- never show decimals.
        if self._param_name.startswith("CNT_"):
            return 0
        if self.device.get("type") == "peltec2":
            if self._device_class == SensorDeviceClass.TEMPERATURE:
                return 1
            if self._param_name in {"B_Oxy1", "B_misP"}:
                return 1
            if self._param_name in {"B_signal", "B_cm2k", "B_razP", "B_FotV", "B_fan", "B_sng"}:
                return 0

        # Any other sensor with a state class or a real unit is a plain
        # numeric reading (temperatures, percentages, rpm, etc.).
        if self.state_class is not None or bool(self._unit):
            return 2

        # Status/enum/firmware/configuration and other text sensors: no
        # precision, so Home Assistant doesn't expect a numeric value.
        return None

    _YES_NO_PARAMS = {
        "B_puz",
        "B_PTV/GRI",
        "B_REC",
        "B_vanjS",
        "B_bup",
    }

    # Confirmed active-state values. PelTec II only creates entries from its
    # strict portal allowlist, so legacy codes in this set cannot leak into
    # the PelTec II device page.
    _ON_OFF_PARAMS = {
        "B_fireS",  # Flame State
        "B_zahPa",
        "B_P1",
        "B_P2",
        "B_P3",
        "B_P4",
        "B_Pk",
        "B_zahP1",
        "B_zahP2",
        "B_zahP3",
        "B_Paku",
        "B_Pk1_k2",
        "B_VAC_STS",
        "B_VAC_TUR",
        "B_dop",
        "B_doz",
        "B_gri",
        "B_REO",  # PelTec II Lambda: DHW recirculation pump
        "B_tur",  # PelTec II Lambda: turbulator motor
        "B_Out1",  # PelTec II Lambda: auxiliary output/input 1
        "B_ashC",
        "B_zahPpwm",
        "B_zahK1_K2",
        "B_zahValve",
        "B_PTV_PRI",
    }

    # Valve states
    _VALVE_PARAMS = {"B_Valve"}

    @property
    def native_value(self) -> Any:
        value = self.parameter["value"]
        if self.device.get("type") == "peltec2" and self._device_class == SensorDeviceClass.TEMPERATURE:
            return valid_temperature(self._param_name, value)
        if self.device.get("type") == "peltec2" and self._param_name == "B_Oxy1":
            return valid_lambda(value)
        if self.device.get("type") == "peltec2" and self._param_name == "B_signal":
            return valid_signal_db(value)
        if self.device.get("type") == "peltec2" and self._param_name in {"B_razP", "B_misP"}:
            return valid_percentage(value)
        if self.device.get("type") == "peltec2" and self._param_name == "B_FotV":
            return valid_nonnegative_measurement(value, maximum=1001)
        if self.device.get("type") == "peltec2" and self._param_name == "B_fan":
            return valid_nonnegative_measurement(value, maximum=10000)
        if self.device.get("type") == "peltec2" and self._param_name == "B_sng":
            return valid_nonnegative_measurement(value, maximum=1000)
        if self.device.get("type") == "peltec2" and self._param_name == "B_specG":
            return decode_status_mark(value)
        if self.device.get("type") == "peltec2" and self._param_name == "B_start":
            state = self.device.get_parameter("B_STATE").get("value")
            return decode_start_transition(value, state)
        if self.device.get("type") == "peltec2" and self._param_name in {
            "B_PTV_PRI",
            "B_bup",
            "B_REC",
            "B_REO",
        }:
            try:
                return "On" if int(str(value)) != 0 else "Off"
            except (ValueError, TypeError):
                pass
        if self.device.get("type") == "peltec2" and self._param_name == "B_puz":
            try:
                return "On" if int(str(value)) != 0 else "Off"
            except (ValueError, TypeError):
                pass
        if self._param_name in WebBoilerGenericSensor._YES_NO_PARAMS:
            try:
                return "Yes" if int(str(value)) != 0 else "No"
            except (ValueError, TypeError):
                pass
        if self._param_name in WebBoilerGenericSensor._ON_OFF_PARAMS:
            try:
                return "On" if int(str(value)) != 0 else "Off"
            except (ValueError, TypeError):
                pass
        if self._param_name in WebBoilerGenericSensor._VALVE_PARAMS:
            try:
                return "Open" if int(str(value)) != 0 else "Closed"
            except (ValueError, TypeError):
                pass
        if self._param_name == "B_razina":
            return decode_tank_level(value)
        if self._param_name == "B_SUP_TYPE":
            return decode_internet_access(value)
        return value

    @property
    def available(self) -> bool:
        if not self.web_boiler_client.has_fresh_data():
            return False
        if self.device.get("type") != "peltec2":
            return True

        value = self.parameter.get("value")
        if self._device_class == SensorDeviceClass.TEMPERATURE:
            return valid_temperature(self._param_name, value) is not None
        if self._param_name == "B_Oxy1":
            return valid_lambda(value) is not None
        if self._param_name == "B_signal":
            return valid_signal_db(value) is not None
        if self._param_name == "B_misP":
            return valid_percentage(value) is not None
        if self._param_name == "B_FotV":
            return valid_nonnegative_measurement(value, maximum=1001) is not None
        if self._param_name == "B_fan":
            return valid_nonnegative_measurement(value, maximum=10000) is not None
        if self._param_name == "B_sng":
            return valid_nonnegative_measurement(value, maximum=1000) is not None
        if self._param_name == "B_razP":
            if valid_percentage(value) is None:
                return False
            if not self.device.has_parameter("B_addConf"):
                return False
            enabled = portal_hex_bit_is_set(self.device.get_parameter("B_addConf").get("value"), 3)
            return enabled is True
        return True

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {}
        if "timestamp" in self.parameter:
            try:
                attrs["Last updated"] = format_time(self.hass, int(self.parameter["timestamp"]))
            except Exception:
                pass
        attrs["Original name"] = self.parameter["name"]
        if self.device.get("type") == "peltec2" and self._param_name == "B_start":
            attrs["Boiler state"] = self.device.get_parameter("B_STATE").get("value")
        if self.device.get("type") == "peltec2" and self._param_name == "B_specG":
            details = decode_status_mark_details(self.parameter.get("value"))
            attrs["Raw value"] = details["raw_value"]
            attrs["Meaning"] = details["meaning"]
            attrs["Category"] = details["category"]
            attrs["Temporary shutdown"] = details["temporary_shutdown"]
            attrs["Documentation"] = details["documentation"]
        if self.device.get("type") == "peltec2" and self._param_name == "B_Oxy1":
            numeric = valid_lambda(self.parameter.get("value"))
            state = (
                self.device.get_parameter("B_STATE").get("value")
                if self.device.has_parameter("B_STATE")
                else None
            )
            flame_raw = (
                self.device.get_parameter("B_fireS").get("value")
                if self.device.has_parameter("B_fireS")
                else None
            )
            try:
                flame_detected = int(str(flame_raw)) != 0
            except (TypeError, ValueError):
                flame_detected = None
            attrs["Raw value"] = self.parameter.get("value")
            attrs["Measurement active"] = bool(numeric is not None and flame_detected is True)
            attrs["Boiler state"] = state
            attrs["Flame detected"] = flame_detected
        if self.device.get("type") == "peltec2" and self._param_name == "B_signal":
            connected_fn = getattr(self.web_boiler_client, "is_websocket_connected", None)
            numeric = valid_signal_db(self.parameter.get("value"))
            attrs["Raw value"] = self.parameter.get("value")
            attrs["Signal reported by controller"] = numeric is not None
            attrs["Portal connected"] = bool(connected_fn()) if callable(connected_fn) else None
            attrs["Controller display when missing"] = "---dB"
        if self.device.get("type") == "peltec2" and self._param_name == "B_FotV":
            numeric = valid_nonnegative_measurement(self.parameter.get("value"), maximum=1001)
            attrs["Over range"] = numeric == 1001
            if numeric == 1001:
                attrs["Controller display"] = ">1000 kΩ"
            elif numeric is not None:
                attrs["Controller display"] = f"{numeric:g} kΩ"
            else:
                attrs["Controller display"] = None
        if self.device.get("type") == "peltec2" and self._param_name == "B_misP":
            numeric = valid_percentage(self.parameter.get("value"))
            if numeric is not None:
                attrs["Valve state"] = "Closed" if numeric == 0 else "Open" if numeric == 100 else "Partially open"
        if self.device.get("type") == "peltec2" and self._param_name in {
            "B_PTV_PRI",
            "B_bup",
            "B_REC",
            "B_REO",
        }:
            attrs["Raw value"] = self.parameter.get("value")
        for key_param_name, nice_label in self._attributes_map.items():
            p = self.device.get_parameter(key_param_name)
            attrs[nice_label] = p["value"] or "None"
        return attrs

    @property
    def device_info(self):
        return create_device_info(self.device)

    @staticmethod
    def _device_has_parameter(device, param_name: str) -> bool:
        params = device.get("parameters", {})
        return param_name in params

    @staticmethod
    def create_common_entities(hass: HomeAssistant, device) -> List[SensorEntity]:
        # PelTec II exposes only the three portal-visible information fields.
        # Brand, installation type and Wi-Fi box version are internal or
        # duplicate metadata and are not created as entities.
        allowed_peltec2 = {"B_PRODNAME", "B_VER", "B_sng"}
        entities: List[SensorEntity] = []
        for param_id, sensor_data in GENERIC_SENSORS_COMMON.items():
            if param_id == "B_CMD":
                continue
            if device.get("type") == "peltec2" and param_id not in allowed_peltec2:
                continue
            if not WebBoilerGenericSensor._device_has_parameter(device, param_id):
                continue
            parameter = device.get_parameter(param_id)
            if parameter.get("used"):
                continue
            entities.append(WebBoilerGenericSensor(hass, device, sensor_data, parameter))
        return entities

    @staticmethod
    def create_temperatures_entities(hass: HomeAssistant, device) -> List[SensorEntity]:
        entities: List[SensorEntity] = []
        temp_sensors = get_generic_temperature_settings_sensors(device)
        for param_id, sensor_data in temp_sensors.items():
            if not WebBoilerGenericSensor._device_has_parameter(device, param_id):
                continue
            parameter = device.get_parameter(param_id)
            if parameter.get("used"):
                continue
            entities.append(WebBoilerGenericSensor(hass, device, sensor_data, parameter))
        return entities

    @staticmethod
    def create_conf_entities(hass: HomeAssistant, device) -> List[SensorEntity]:
        entities: List[SensorEntity] = []

        if device["type"] == "peltec2":
            # Keep the Lambda entity present even when the controller omits the
            # value while the boiler is not firing. The existing parameter
            # object receives future HTTP/WebSocket updates, so the entity
            # becomes available immediately when a valid reading returns.
            if not device.has_parameter("B_Oxy1"):
                device.create_parameter("B_Oxy1", None)
            generic_map = PELTEC2_GENERIC_SENSORS
            skip_params = {
                "B_CMD",
                "K1B_onOff",
                "K1B_P",
                "B_KONF",
                "B_STATE",
                "B_BRAND",
                "B_INST",
                "B_PRODNAME",
                "B_VER",
                "B_sng",
                "B_Time",
                "PING",
            }
        elif device["type"] == "peltec":
            generic_map = PELTEC_GENERIC_SENSORS
            skip_params = {
                "B_CMD",
                "K1B_onOff",
                "K1B_P",
                "B_KONF",
                "B_resInd",
                "B_resDir",
                "B_resMax",
                "B_BRAND",
                "B_INST",
                "B_PRODNAME",
                "B_VER",
                "B_sng",
                "B_Time",
                "PING",
            }
        elif device["type"] == "compact":
            generic_map = COMPACT_GENERIC_SENSORS
            skip_params = {"B_CMD"}
        elif device["type"] == "cmpelet":
            generic_map = CM_PELET_SET_GENERIC_SENSORS
            skip_params = {"B_CMD"}
        elif device["type"] == "biotec":
            generic_map = BIOTEC_GENERIC_SENSORS
            skip_params = {"B_CMD"}
        elif device["type"] == "biopl":
            generic_map = BIOTEC_PLUS_GENERIC_SENSORS
            skip_params = {"B_CMD"}
        else:
            generic_map = {}
            skip_params = set()

        for param_id, sensor_data in generic_map.items():
            if param_id in skip_params:
                continue
            if device.get("type") == "peltec2" and param_id == "B_razP":
                if not device.has_parameter("B_addConf"):
                    continue
                if portal_hex_bit_is_set(device.get_parameter("B_addConf").get("value"), 3) is not True:
                    continue
            if device.get("type") == "peltec2" and param_id in {
                "B_PTV_PRI",
                "B_bup",
                "B_REC",
                "B_REO",
            }:
                if not device.has_parameter("B_KONF"):
                    continue
                configuration = device.get_parameter("B_KONF").get("value")
                if param_id == "B_bup" and not configuration_has_buffer(configuration):
                    continue
                if param_id in {"B_PTV_PRI", "B_REC", "B_REO"} and not configuration_has_dhw(configuration):
                    continue
            if not WebBoilerGenericSensor._device_has_parameter(device, param_id):
                continue
            parameter = device.get_parameter(param_id)
            if parameter.get("used"):
                continue
            entities.append(WebBoilerGenericSensor(hass, device, sensor_data, parameter))

        return entities

    # Parameters to never expose as sensors — internal protocol noise
    _SKIP_UNKNOWN = {
        # internal protocol / timing noise
        "PING",
        "B_Time",
        "CMD",
        "CMD_TIME",
        "SE00",
        "SE01",
        "SE02",
        "wf_req",
        # Raw encoded event markers. The decoded event history comes from
        # /wdata/data/multi/errors-list/{id} and is exposed separately.
        "IW1-1",
        "IW1-2",
    }

    @staticmethod
    def create_unknown_entities(hass: HomeAssistant, device) -> List[SensorEntity]:
        if device.get("type") == "peltec2":
            return []
        entities: List[SensorEntity] = []
        for param_name, parameter in device.get("parameters", {}).items():
            if parameter.get("used"):
                continue
            # Skip PVAL/PDEF/PMIN/PMAX slots — handled by temperatures or circuit switches
            if param_name.startswith(("PVAL_", "PDEF_", "PMIN_", "PMAX_")):
                continue
            if param_name in WebBoilerGenericSensor._SKIP_UNKNOWN:
                continue
            _LOGGER.debug("create_unknown_entities: exposing unclaimed parameter %s", param_name)
            entities.append(
                WebBoilerGenericSensor(
                    hass,
                    device,
                    [None, "mdi:help-circle-outline", None, param_name],
                    parameter,
                    disabled_by_default=True,
                )
            )
        return entities
