from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS

from typing import List
import logging

from homeassistant.components.sensor import SensorEntity

from .WebBoilerGenericSensor import WebBoilerGenericSensor

from ..const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


class WebBoilerHeatingCircuitSensor:
    """Representation of a Centrometal Boiler Sensor."""

    @staticmethod
    def create_heating_circuits_entities(hass, device) -> List[SensorEntity]:
        entities = []
        for i in range(1, 5):
            prefix = f"C{i}B"
            name = f"Circuit {i}"
            if WebBoilerHeatingCircuitSensor.device_has_prefix(device, prefix):
                entities.extend(
                    WebBoilerHeatingCircuitSensor.create_heating_circuit_entities(
                        hass, device, prefix, name
                    )
                )
        for i in range(1, 5):
            prefix = f"K{i}B"
            name = f"Circuit {i}K"
            if WebBoilerHeatingCircuitSensor.device_has_prefix(device, prefix):
                entities.extend(
                    WebBoilerHeatingCircuitSensor.create_heating_circuit_entities(
                        hass, device, prefix, name
                    )
                )
        return entities

    @staticmethod
    def device_has_prefix(device, prefix):
        for param in device["parameters"].keys():
            if param.startswith(prefix):
                return True
        return False

    @staticmethod
    def create_heating_circuit_entities(
        hass, device, prefix, name
    ) -> List[SensorEntity]:
        entities = []
        items = {}
        items[prefix + "_CircType"] = [
            None,
            "mdi:view-list",
            None,
            name + " Heating Type",
        ]
        items[prefix + "_dayNight"] = [
            None,
            "mdi:view-list",
            None,
            name + " Day Night Mode",
        ]
        items[prefix + "_kor"] = [
            TEMP_CELSIUS,
            "mdi:thermometer",
            DEVICE_CLASS_TEMPERATURE,
            name + " Room Target Correction",
        ]
        items[prefix + "_korType"] = [
            None,
            "mdi:view-list",
            None,
            name + " Correction Type",
        ]
        items[prefix + "_onOff"] = [None, "mdi:pump", None, name + " Pump Demand"]
        items[prefix + "_P"] = [None, "mdi:pump", None, name + " Pump"]
        items[prefix + "_Tpol"] = [
            TEMP_CELSIUS,
            "mdi:thermometer",
            DEVICE_CLASS_TEMPERATURE,
            name + " Flow Target Temperature",
        ]
        items[prefix + "_Tpol1"] = [
            TEMP_CELSIUS,
            "mdi:thermometer",
            DEVICE_CLASS_TEMPERATURE,
            name + " Flow Measured Temperature",
        ]
        items[prefix + "_Tsob"] = [
            TEMP_CELSIUS,
            "mdi:thermometer",
            DEVICE_CLASS_TEMPERATURE,
            name + " Room Target Temperature",
        ]
        items[prefix + "_Tsob1"] = [
            TEMP_CELSIUS,
            "mdi:thermometer",
            DEVICE_CLASS_TEMPERATURE,
            name + " Room Measured Temperature",
        ]
        items[prefix + "_misC"] = [
            None,
            "mdi:pipe-valve",
            None,
            name + " Valve Closing",
        ]
        items[prefix + "_misO"] = [
            None,
            "mdi:pipe-valve",
            None,
            name + " Valve Opening",
        ]
        for param_id, sensor_data in items.items():
            parameter = device.get_parameter(param_id)
            entities.append(
                WebBoilerGenericSensor(hass, device, sensor_data, parameter)
            )
        return entities
