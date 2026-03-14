import logging
from typing import List, Dict, Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTime, PERCENTAGE
from homeassistant.core import HomeAssistant

from ..const import DOMAIN, WEB_BOILER_CLIENT, WEB_BOILER_SYSTEM
from ..common import format_name, format_time, create_device_info

from .generic_sensors_all import GENERIC_SENSORS_COMMON, get_generic_temperature_settings_sensors
from .generic_sensors_peltec import PELTEC_GENERIC_SENSORS
from .generic_sensors_compact import COMPACT_GENERIC_SENSORS
from .generic_sensors_cm_pelet_set import CM_PELET_SET_GENERIC_SENSORS
from .generic_sensors_biotec import BIOTEC_GENERIC_SENSORS
from .generic_sensors_biotec_plus import BIOTEC_PLUS_GENERIC_SENSORS

_LOGGER = logging.getLogger(__name__)


class WebBoilerGenericSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, device, sensor_data, parameter, disabled_by_default: bool = False) -> None:
        self.hass = hass
        self.web_boiler_client = hass.data[DOMAIN][device.username][WEB_BOILER_CLIENT]
        self.web_boiler_system = hass.data[DOMAIN][device.username][WEB_BOILER_SYSTEM]
        self.device = device
        self.parameter = parameter

        self._unit = sensor_data[0]
        self._icon = sensor_data[1]
        self._device_class = sensor_data[2]
        self._description = sensor_data[3]
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

    def __del__(self):
        if hasattr(self.parameter, "set_update_callback"):
            self.parameter.set_update_callback(None, self._callback_id)

    async def async_added_to_hass(self):
        self.added_to_hass = True
        self.async_schedule_update_ha_state(False)
        if hasattr(self.parameter, "set_update_callback"):
            self.parameter.set_update_callback(self.update_callback, self._callback_id)

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
        if self._device_class == SensorDeviceClass.TEMPERATURE:
            return SensorStateClass.MEASUREMENT
        if self._unit == PERCENTAGE and self._param_name in ("B_razP", "B_Oxy1", "B_signal", "B_misP"):
            return SensorStateClass.MEASUREMENT
        if self._param_name == "B_fan":
            return SensorStateClass.MEASUREMENT
        if self._unit == UnitOfTime.MINUTES and self._param_name.startswith("CNT_"):
            return SensorStateClass.TOTAL_INCREASING
        if self._param_name == "CNT_1":
            return SensorStateClass.TOTAL_INCREASING
        if self._param_name == "CNT_7":
            return SensorStateClass.TOTAL_INCREASING
        return None

    _YES_NO_PARAMS = {
        # Binary active/demand states — boiler-specific
        "B_fireS", "B_zahPa", "B_cm2k",
        "B_puz",          # pellet transporter active
        "B_PTV/GRI",      # DHW/heater active state
    }

    # ON/OFF states — consistent with pump/fan binary sensors
    _ON_OFF_PARAMS = {
        "B_P2", "B_P3", "B_P4",
        "B_Paku", "B_Pk1_k2",
        "B_VAC_STS", "B_VAC_TUR",
        "B_dop", "B_doz", "B_specG", "B_start",
        "B_PTV/GRI_SEL",
    }

    # Valve states
    _VALVE_PARAMS = {"B_Valve"}

    _TANK_LEVEL_STATES = {0: "Empty", 1: "Reserve", 2: "Full"}

    _SUP_TYPE_STATES = {0: "None", 1: "Pellet Screw", 2: "Vacuum"}

    @property
    def native_value(self) -> Any:
        value = self.parameter["value"]
        if self._param_name in WebBoilerGenericSensor._YES_NO_PARAMS:
            try:
                return "Yes" if int(str(value)) != 0 else "No"
            except (ValueError, TypeError):
                pass
        if self._param_name in WebBoilerGenericSensor._ON_OFF_PARAMS:
            try:
                return "ON" if int(str(value)) != 0 else "OFF"
            except (ValueError, TypeError):
                pass
        if self._param_name in WebBoilerGenericSensor._VALVE_PARAMS:
            try:
                return "Open" if int(str(value)) != 0 else "Closed"
            except (ValueError, TypeError):
                pass
        if self._param_name == "B_razina":
            try:
                return WebBoilerGenericSensor._TANK_LEVEL_STATES.get(int(str(value)), str(value))
            except (ValueError, TypeError):
                pass
        if self._param_name == "B_SUP_TYPE":
            try:
                return WebBoilerGenericSensor._SUP_TYPE_STATES.get(int(str(value)), str(value))
            except (ValueError, TypeError):
                pass
        return value

    @property
    def available(self) -> bool:
        return self.web_boiler_client.is_websocket_connected()

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {}
        if "timestamp" in self.parameter:
            try:
                attrs["Last updated"] = format_time(self.hass, int(self.parameter["timestamp"]))
            except Exception:
                pass
        attrs["Original name"] = self.parameter["name"]
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
        skip_params = {"B_CMD"}
        entities: List[SensorEntity] = []
        for param_id, sensor_data in GENERIC_SENSORS_COMMON.items():
            if param_id in skip_params:
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

        if device["type"] in ("peltec", "peltec2"):
            generic_map = PELTEC_GENERIC_SENSORS
            skip_params = {
                "B_CMD", "K1B_onOff", "K1B_P",
                "B_KONF",
                "B_resInd", "B_resDir", "B_resMax",
                "B_BRAND", "B_INST", "B_PRODNAME", "B_VER", "B_sng",
                "B_Time", "PING",
            }
            if device["type"] == "peltec2":
                skip_params.add("B_STATE")
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
        "PING", "B_Time",
        "CMD", "CMD_TIME",
        "SE00", "SE01", "SE02",
        "wf_req",
        # duplicates of named ON/OFF binary sensors
        "B_zahPpwm", "B_zahP1", "B_zahK1_K2", "B_zahValve", "B_PTV_PRI",
    }

    @staticmethod
    def create_unknown_entities(hass: HomeAssistant, device) -> List[SensorEntity]:
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
                    hass, device,
                    [None, "mdi:help-circle-outline", None, param_name],
                    parameter,
                    disabled_by_default=True,
                )
            )
        return entities
