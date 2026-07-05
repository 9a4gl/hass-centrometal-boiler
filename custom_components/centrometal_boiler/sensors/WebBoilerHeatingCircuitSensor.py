import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerHeatingCircuitBinarySensor(WebBoilerGenericSensor):
    """Sensor that displays On/Off for heating circuit binary params."""

    @property
    def native_value(self):
        value = self.parameter["value"]
        try:
            return "On" if int(str(value)) != 0 else "Off"
        except (ValueError, TypeError):
            return str(value)


class WebBoilerHeatingCircuitDayNightSensor(WebBoilerGenericSensor):
    """Sensor that displays Day/Night/Program for _dayNight params."""

    _DAY_NIGHT_MAP = {0: "Day", 1: "Night", 2: "Program"}

    @property
    def native_value(self):
        value = self.parameter["value"]
        try:
            return self._DAY_NIGHT_MAP.get(int(str(value)), str(value))
        except (ValueError, TypeError):
            return str(value)


_LOGGER = logging.getLogger(__name__)


class WebBoilerHeatingCircuitSensor:
    @staticmethod
    def create_heating_circuits_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities: list[SensorEntity] = []
        for i in range(1, 5):
            prefix = f"C{i}B"
            if WebBoilerHeatingCircuitSensor.device_has_prefix(device, prefix):
                entities.extend(
                    WebBoilerHeatingCircuitSensor.create_heating_circuit_entities(hass, device, prefix, f"Circuit {i}")
                )
        for i in range(1, 5):
            prefix = f"K{i}B"
            if WebBoilerHeatingCircuitSensor.device_has_prefix(device, prefix):
                entities.extend(
                    WebBoilerHeatingCircuitSensor.create_heating_circuit_entities(hass, device, prefix, f"K{i} Circuit")
                )
        return entities

    @staticmethod
    def device_has_prefix(device, prefix):
        for param in device["parameters"].keys():
            if param.startswith(prefix):
                return True
        return False

    @staticmethod
    def create_heating_circuit_entities(hass, device, prefix, name) -> list[SensorEntity]:
        entities: list[SensorEntity] = []
        items: dict[str, list] = {
            prefix + "_CircType": [None, "mdi:view-list", None, name + " Heating Type"],
            prefix + "_dayNight": [None, "mdi:view-list", None, name + " Day Night Mode"],
            prefix + "_kor": [
                UnitOfTemperature.CELSIUS,
                "mdi:thermometer",
                SensorDeviceClass.TEMPERATURE,
                name + " Room Target Correction",
            ],
            prefix + "_korN": [
                UnitOfTemperature.CELSIUS,
                "mdi:thermometer-plus",
                SensorDeviceClass.TEMPERATURE,
                name + " Night Correction",
            ],
            prefix + "_korType": [None, "mdi:view-list", None, name + " Correction Type"],
            prefix + "_onOff": [None, "mdi:radiator", None, name + " Heating Circuit Enabled"],
            prefix + "_P": [None, "mdi:pump", None, name + " Pump"],
            prefix + "_Prec": [None, "mdi:reload", None, name + " Recirculation"],
            prefix + "_Tpol": [
                UnitOfTemperature.CELSIUS,
                "mdi:thermometer",
                SensorDeviceClass.TEMPERATURE,
                name + " Flow Target Temperature",
            ],
            prefix + "_Tpol1": [
                UnitOfTemperature.CELSIUS,
                "mdi:thermometer",
                SensorDeviceClass.TEMPERATURE,
                name + " Flow Measured Temperature",
            ],
            prefix + "_Tsob": [
                UnitOfTemperature.CELSIUS,
                "mdi:thermometer",
                SensorDeviceClass.TEMPERATURE,
                name + " Room Target Temperature",
            ],
            prefix + "_Tsob1": [
                UnitOfTemperature.CELSIUS,
                "mdi:thermometer",
                SensorDeviceClass.TEMPERATURE,
                name + " Room Measured Temperature",
            ],
            prefix + "_zahP": [None, "mdi:pump", None, name + " Pump Demand"],
            prefix + "_misC": [None, "mdi:pipe-valve", None, name + " Valve Closing"],
            prefix + "_misO": [None, "mdi:pipe-valve", None, name + " Valve Opening"],
        }
        # Portal-confirmed PelTec II fields. Other circuit telemetry is not
        # created at all; exposing raw or guessed values only clutters the
        # device and can mislead users.
        confirmed_peltec2_suffixes = {"_onOff", "_P", "_Tpol", "_Tpol1", "_Tsob", "_Tsob1", "_zahP"}
        binary_suffixes = {"_onOff", "_P", "_zahP", "_misC", "_misO"}
        daynight_suffixes = {"_dayNight"}

        for param_id, sensor_data in items.items():
            if not WebBoilerGenericSensor._device_has_parameter(device, param_id):
                continue
            parameter = device.get_parameter(param_id)
            if parameter.get("used"):
                continue
            if device.get("type") == "peltec2" and not any(
                param_id.endswith(suffix) for suffix in confirmed_peltec2_suffixes
            ):
                continue
            if any(param_id.endswith(s) for s in binary_suffixes):
                entities.append(WebBoilerHeatingCircuitBinarySensor(hass, device, sensor_data, parameter))
            elif any(param_id.endswith(s) for s in daynight_suffixes):
                entities.append(WebBoilerHeatingCircuitDayNightSensor(hass, device, sensor_data, parameter))
            else:
                entities.append(WebBoilerGenericSensor(hass, device, sensor_data, parameter))
        return entities
