from typing import List

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerBinaryOnOffSensor(WebBoilerGenericSensor):
    @property
    def native_value(self):
        raw = self.parameter["value"]
        if raw in (1, "1", "ON", "On", "on", True, "TRUE", "True", "true"):
            return "ON"
        if raw in (0, "0", "OFF", "Off", "off", False, "FALSE", "False", "false"):
            return "OFF"
        try:
            intval = int(str(raw))
            if intval == 1:
                return "ON"
            if intval == 0:
                return "OFF"
        except (ValueError, TypeError):
            pass
        return str(raw)

    @property
    def extra_state_attributes(self):
        base = super().extra_state_attributes or {}
        base["raw_value"] = self.parameter.get("value")
        return base


def create_binary_state_entities(hass: HomeAssistant, device) -> List[SensorEntity]:
    entities: List[SensorEntity] = []

    binary_map = {
        "B_CMD":    [None, "mdi:state-machine", None, "Command Active"],
        "B_Ppwm":   [None, "mdi:pump",          None, "PWM Pump"],
        "B_P1":     [None, "mdi:pump",          None, "Hot Water Flow"],
        "B_gri":    [None, "mdi:meter-electric", None, "Electric Heater"],
        "B_fan01":  [None, "mdi:fan",           None, "Fan Active"],
        "K1B_onOff":[None, "mdi:pump",          None, "DHW Pump Demand"],
        "K1B_P":    [None, "mdi:pump",          None, "DHW Pump State"],
    }

    params = device.get("parameters", {})

    for param_name, sensor_data in binary_map.items():
        if param_name not in params:
            continue
        parameter = device.get_parameter(param_name)
        if parameter.get("used"):
            continue
        parameter["used"] = True
        entities.append(WebBoilerBinaryOnOffSensor(hass, device, sensor_data, parameter))

    return entities
