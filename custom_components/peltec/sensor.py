# -*- coding: utf-8 -*-

"""Support for Centrometal PelTec System sensors."""
import logging

import homeassistant.util.dt as dt_util
from datetime import datetime

import peltec

from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TIME_MINUTES,
)

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import DOMAIN, PELTEC_CLIENT

_LOGGER = logging.getLogger(__name__)

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
        "Flue gas",
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
}

PELTEC_SENSOR_SETTINGS = {
    "PVAL_66_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer tank temperature",
        {"PDEF_66_0": "Default", "PMIN_66_0": "Min", "PMAX_66_0": "Max"},
    ],
    "PVAL_67_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Differential of buffer tank temperature",
        {"PDEF_67_0": "Default", "PMIN_67_0": "Min", "PMAX_67_0": "Max"},
    ],
    "PVAL_69_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Minimal buffer tank temperature",
        {"PDEF_69_0": "Default", "PMIN_69_0": "Min", "PMAX_69_0": "Max"},
    ],
    "PVAL_70_0": [
        "",
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Minimal buffer tank temperature-off",
        {"PDEF_70_0": "Default", "PMIN_70_0": "Min", "PMAX_70_0": "Max"},
    ],
}

PELTEC_SENSOR_TYPES = {
    **PELTEC_SENSOR_TEMPERATURES,
    **PELTEC_SENSOR_COUNTERS,
    **PELTEC_SENSOR_SETTINGS,
    **PELTEC_SENSOR_MISC,
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Perform the setup for Centrometal PelTec sensor devices."""
    entities = []

    peltec_client = hass.data[DOMAIN][PELTEC_CLIENT]
    for device in peltec_client.data.values():
        parameters = device["parameters"]
        for param_id, sensor_data in PELTEC_SENSOR_TYPES.items():
            if param_id in parameters.keys():
                parameter = parameters[param_id]
                entities.append(PelTecSensor(hass, device, sensor_data, parameter))
        entities.append(
            PelTecConfigurationSensor(
                hass,
                device,
                ["", "mdi:state-machine", None, "Configuration"],
                parameters["B_KONF"],
            )
        )
        entities.append(
            PelTecTableSensor(
                hass,
                device,
                ["", "mdi:state-machine", None, "Working table"],
                parameters["PVAL_222_0"],
            )
        )

    async_add_entities(entities, True)


class PelTecSensor(SensorEntity):
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
        if self._parameter_name in PELTEC_SENSOR_TYPES:
            return self._device_class
        return None

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
        tzinfo = dt_util.get_time_zone(self.hass.config.time_zone)
        last_updated_dt = datetime.fromtimestamp(int(self.parameter["timestamp"]))
        last_updated = last_updated_dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")
        attributes = {}
        for key, description in self.attributes.items():
            attributes[description] = self.device["parameters"][key]["value"] or "?"
        attributes["Last updated"] = last_updated
        return attributes

    @property
    def device_info(self):
        power = self.device["parameters"]["B_sng"]["value"] or "?"
        firmware_ver = self.device["parameters"]["B_VER"]["value"] or "?"
        wifi_ver = self.device["parameters"]["B_WifiVER"]["value"] or "?"
        name = "PelTec"
        model = self.device["product"] + " " + power
        sw_version = firmware_ver + " Wifi:" + wifi_ver
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._serial)
            },
            "name": name,
            "manufacturer": "Centrometal",
            "model": model,
            "sw_version": sw_version,
        }


class PelTecConfigurationSensor(PelTecSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        configurations = [
            "1. DHW",
            "2. DHC",
            "3. DHW || DHC",
            "4. BUF",
            "5. DHW || BUF",
            "6. BUF -- IHC",
            "7. DHW || BUF -- IHC",
            "8. BUF -- DHW",
            "9. BUF -- IHC || DHW",
            "10. CRO",
            "11. CRO / BUF",
            "12. DHC || DHW(2)",
            "13. DHC 2X",
            "14. BUF--IHCX2",
            "15. CRO -- DHW",
        ]
        return configurations[int(self.parameter["value"])]


# TIHOTODO 223 is table 1 ? 224 is table 2? where is table 3?
# TIHOTODO how to refresh specific table?
# TIHOTODO doees 222_0 clear tables?


class PelTecTableSensor(PelTecSensor):
    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        await super().async_added_to_hass()
        for tableIndex in range(1, 4):
            for i in range(0, 42):
                param = "PVAL_" + str(222 + tableIndex) + "_" + str(i)
                self.device["parameters"][param].set_update_callback(
                    self.update_callback
                )

    def getValue(self, tableIndex, dayIndex, i):
        param = "PVAL_" + str(222 + tableIndex) + "_" + str(dayIndex * 6 + i)
        value = self.device["parameters"][param]["value"]
        return int(value)

    def formatTime(self, val):
        return "%02d:%02d" % (int(val / 60), val % 60)

    def getRange(self, tableIndex, dayIndex, i, j):
        val1 = self.getValue(tableIndex, dayIndex, i)
        val2 = self.getValue(tableIndex, dayIndex, j)
        if val1 == 1440 and val2 == 1440:
            return " - "
        return self.formatTime(val1) + "-" + self.formatTime(val2)

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = super().device_state_attributes
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        tables = [1, 2, 3]
        for tableIndex in tables:
            for i in range(0, 7):
                day = days[i]
                texts = [
                    self.getRange(tableIndex, i, 0, 1),
                    self.getRange(tableIndex, i, 2, 3),
                    self.getRange(tableIndex, i, 4, 5),
                ]
                key = "Table" + str(tableIndex) + " " + day
                attributes[key] = " / ".join(texts)
        return attributes
