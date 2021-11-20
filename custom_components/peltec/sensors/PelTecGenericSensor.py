from typing import List

from homeassistant.components.sensor import SensorEntity

from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TIME_MINUTES,
    PERCENTAGE,
)

from ..const import DOMAIN, PELTEC_CLIENT
from ..common import formatTime, create_device_info

PELTEC_SENSOR_TEMPERATURES = {
    "B_Tak1_1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Temparature Up",
    ],
    "B_Tak2_1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Temparature Down",
    ],
    "B_Tdpl1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Flue Gas",
    ],
    "B_Tpov1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Mixer Temperature",
    ],
    "B_Tk1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Boiler Temperature",
    ],
}

PELTEC_SENSOR_COUNTERS = {
    "CNT_0": [TIME_MINUTES, "mdi:timer", None, "Burner work"],
    "CNT_1": [
        "",
        "mdi:counter",
        None,
        "Number of Burner Start",
    ],
    "CNT_2": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Feeder Screw Work",
    ],
    "CNT_3": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Flame Duration",
    ],
    "CNT_4": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Fan Working Time",
    ],
    "CNT_5": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Electric Heater Working Time",
    ],
    "CNT_6": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Vacuum Turbine Working Time",
    ],
    "CNT_7": [
        "",
        "mdi:counter",
        None,
        "Vacuum Turbine Cycles Number",
    ],
    "CNT_8": [TIME_MINUTES, "mdi:timer", None, "Time on D6"],
    "CNT_9": [TIME_MINUTES, "mdi:timer", None, "Time on D5"],
    "CNT_10": [TIME_MINUTES, "mdi:timer", None, "Time on D4"],
    "CNT_11": [TIME_MINUTES, "mdi:timer", None, "Time on D3"],
    "CNT_12": [TIME_MINUTES, "mdi:timer", None, "Time on D2"],
    "CNT_13": [TIME_MINUTES, "mdi:timer", None, "Time on D1"],
    "CNT_14": [TIME_MINUTES, "mdi:timer", None, "Time on D0"],
    "CNT_15": ["", "mdi:counter", None, "Reserve Counter"],
}

PELTEC_SENSOR_MISC = {
    "B_STATE": ["", "mdi:state-machine", None, "State"],
    "B_fan": ["rpm", "mdi:fan", None, "Fan"],
    "B_fanB": ["rpm", "mdi:fan", None, "Fan B"],
    "B_Oxy1": ["% O2", "mdi:gas-cylinder", None, "Lambda Sensor"],
    "B_FotV": ["kOhm", "mdi:fire", None, "Fire Sensor"],
    "B_vanjS": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Outdoor Temperature",
    ],
    "B_cm2k": ["", "mdi:state-machine", None, "CM2K Status"],
    "B_misP": [PERCENTAGE, "mdi-pipe-valve", None, "Mixing Valve"],
}

PELTEC_SENSOR_SETTINGS = {
    "PVAL_66_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Setting Buffer Tank Temperatures",
        {"PDEF_66_0": "Default", "PMIN_66_0": "Min", "PMAX_66_0": "Max"},
    ],
    "PVAL_67_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Setting Differential of Buffer Tank Temperature",
        {"PDEF_67_0": "Default", "PMIN_67_0": "Min", "PMAX_67_0": "Max"},
    ],
    "PVAL_69_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Setting Minimal Buffer Tank Temperature",
        {"PDEF_69_0": "Default", "PMIN_69_0": "Min", "PMAX_69_0": "Max"},
    ],
    "PVAL_70_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Setting Minimal Buffer Tank Temperature-off",
        {"PDEF_70_0": "Default", "PMIN_70_0": "Min", "PMAX_70_0": "Max"},
    ],
}

PELTEC_SENSOR_TYPES = {
    **PELTEC_SENSOR_TEMPERATURES,
    **PELTEC_SENSOR_COUNTERS,
    **PELTEC_SENSOR_SETTINGS,
    **PELTEC_SENSOR_MISC,
}


class PelTecGenericSensor(SensorEntity):
    """Representation of a Centrometal PelTec Sensor."""

    def __init__(self, hass, device, sensor_data, parameter):
        """Initialize the Centrometarl PelTec Sensor."""
        self.hass = hass
        self.peltec_client = hass.data[DOMAIN][PELTEC_CLIENT]
        self.parameter = parameter
        self.device = device
        #
        self._unit = sensor_data[0]
        self._icon = sensor_data[1]
        self._device_class = sensor_data[2]
        self._description = sensor_data[3]
        self.attributes = sensor_data[4] if len(sensor_data) == 5 else {}
        self._serial = device["serial"]
        self._parameter_name = parameter["name"]
        self._name = f"PelTec {self._description}"
        self._unique_id = f"{self._serial}-{self._parameter_name}"
        #
        self.added_to_hass = False

    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        self.added_to_hass = True
        self.schedule_update_ha_state(True)
        self.parameter.set_update_callback(self.update_callback)

    @property
    def should_poll(self) -> bool:
        """No polling needed for a sensor."""
        return False

    def update_callback(self, parameter):
        """Call update for Home Assistant when the parameter is updated."""
        self.schedule_update_ha_state(True)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return self._device_class

    @property
    def native_value(self):
        """Return the value of the sensor."""
        return self.parameter["value"]

    @property
    def available(self):
        """Return the availablity of the sensor."""
        return self.peltec_client.is_websocket_connected()

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        last_updated = formatTime(self.hass, int(self.parameter["timestamp"]))
        attributes = {}
        for key, description in self.attributes.items():
            attributes[description] = self.device["parameters"][key]["value"] or "?"
        attributes["Last updated"] = last_updated
        return attributes

    @property
    def device_info(self):
        return create_device_info(self.device)

    @staticmethod
    def createEntities(parameters, hass, device) -> List[SensorEntity]:
        entities = []
        for param_id, sensor_data in PELTEC_SENSOR_TYPES.items():
            if param_id in parameters.keys():
                parameter = parameters[param_id]
                entities.append(
                    PelTecGenericSensor(hass, device, sensor_data, parameter)
                )
        return entities
