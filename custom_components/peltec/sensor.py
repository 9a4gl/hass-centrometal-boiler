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
    CONF_COUNT,
)
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import DOMAIN, PELTEC_CLIENT

_LOGGER = logging.getLogger(__name__)

PELTEC_SENSOR_TEMPERATURES = {
    "B_Tak1_1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Temperatura Gornja",
    ],
    "B_Tak2_1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Temperatura Donja",
    ],
    "B_Tdpl1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Temperatura u dimovodu",
    ],
    "B_Tpov1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Temperatura mjesaca",
    ],
    "B_Tk1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Temperatura u kotlu",
    ],
}

PELTEC_SENSOR_COUNTERS = {
    "CNT_0": [TIME_MINUTES, "mdi:timer", None, "Burner work"],
    "CNT_1": [
        CONF_COUNT,
        "mdi:counter",
        None,
        "Number of burner start",
    ],
    "CNT_2": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Feeder screw work",
    ],
    "CNT_3": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Flame duration",
    ],
    "CNT_4": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Fan working time",
    ],
    "CNT_5": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Electric heater working time",
    ],
    "CNT_6": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Vacuum turbine working time",
    ],
    "CNT_7": [
        CONF_COUNT,
        "mdi:counter",
        None,
        "Vacuum turbine cycles number",
    ],
    "CNT_8": [TIME_MINUTES, "mdi:timer", None, "Time on D6"],
    "CNT_9": [TIME_MINUTES, "mdi:timer", None, "Time on D5"],
    "CNT_10": [TIME_MINUTES, "mdi:timer", None, "Time on D4"],
    "CNT_11": [TIME_MINUTES, "mdi:timer", None, "Time on D3"],
    "CNT_12": [TIME_MINUTES, "mdi:timer", None, "Time on D2"],
    "CNT_13": [TIME_MINUTES, "mdi:timer", None, "Time on D1"],
    "CNT_14": [TIME_MINUTES, "mdi:timer", None, "Time on D0"],
    "CNT_15": [CONF_COUNT, "mdi:counter", None, "Reserve counter"],
}

PELTEC_SENSOR_MISC = {
    "B_STATE": ["state", "mdi:state-machine", None, "State"],
    "B_fan": ["rpm", "mdi:fan", None, "Fan"],
    "B_fanB": ["rpm", "mdi:fan", None, "Fan B"],
    "B_Oxy1": ["% O2", "mdi:gas-cylinder", None, "Lambda Sensor"],
    "B_FotV": ["kOhm", "mdi:fire", None, "Fire"],
}

PELTEC_SENSOR_TYPES = {
    **PELTEC_SENSOR_TEMPERATURES,
    **PELTEC_SENSOR_COUNTERS,
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

    async_add_entities(entities, True)


class PelTecSensor(Entity):
    """Representation of a Centrometal PelTec Sensor."""

    def __init__(self, hass, device, sensor_data, parameter):
        """Initialize the Centrometarl PelTec Sensor."""
        self.hass = hass
        self.sensor_data = sensor_data
        self.device = device
        self.parameter = parameter
        #
        self.serial = device["serial"]
        self.parameter_name = parameter["name"]
        self._name = sensor_data[3]
        self._unique_id = f"{self.parameter_name}_{self.serial}"

    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        # self.device.add_callback(self.update_callback) # TIHOTODO subscribe to parameter change

    @property
    def should_poll(self) -> bool:
        """No polling needed for a sensor."""
        return False

    def update_callback(self, device):
        """Call update for Home Assistant when the device is updated."""
        self.schedule_update_ha_state(True)

    @property
    def name(self):
        """Return the name of the device."""
        # return self._name
        return self._unique_id

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self.sensor_data[1]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self.sensor_data[0]

    @property
    def device_class(self):
        """Return the device class of this entity."""
        if self.parameter_name in PELTEC_SENSOR_TYPES:
            return self.sensor_data[2]
        return None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.parameter["value"]

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        tzinfo = dt_util.get_time_zone(self.hass.config.time_zone)
        last_updated_dt = datetime.fromtimestamp(int(self.parameter["timestamp"]))
        last_updated = last_updated_dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")
        return {"Last updated:": last_updated}

    @property
    def device_info(self):
        power = self.device["parameters"]["B_sng"]["value"] or "?"
        firmware_ver = self.device["parameters"]["B_VER"]["value"] or "?"
        wifi_ver = self.device["parameters"]["B_WifiVER"]["value"] or "?"
        name = self.device["product"] + " " + power
        model = self.device["product"] + " " + power
        sw_version = firmware_ver + " Wifi:" + wifi_ver
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.serial)
            },
            "name": name,
            "manufacturer": "Centrometal",
            "model": model,
            "sw_version": sw_version,
        }
