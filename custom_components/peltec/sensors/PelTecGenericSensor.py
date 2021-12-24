from typing import List
import logging

from homeassistant.components.sensor import SensorEntity


from ..const import DOMAIN, PELTEC_CLIENT
from ..common import formatTime, create_device_info

from .generic_all import PELTEC_SENSOR_GENERIC_COMMON
from .generic_4buf import PELTEC_4BUF_SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


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
        self._attributes = sensor_data[4] if len(sensor_data) == 5 else {}
        self._serial = device["serial"]
        self._parameter_name = parameter["name"]
        self._name = f"PelTec {self._description}"
        self._unique_id = f"{self._serial}-{self._parameter_name}"
        #
        self.added_to_hass = False
        self.parameter["used"] = True
        for attribute in self._attributes:
            attribute_parameter = self.device.getPelTecParameter(attribute)
            attribute_parameter["used"] = True

    def __del__(self):
        self.parameter.set_update_callback(None, "generic")

    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        self.added_to_hass = True
        self.async_schedule_update_ha_state(False)
        self.parameter.set_update_callback(self.update_callback, "generic")

    @property
    def should_poll(self) -> bool:
        """No polling needed for a sensor."""
        return False

    async def update_callback(self, parameter):
        """Call update for Home Assistant when the parameter is updated."""
        self.async_write_ha_state()

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
        attributes = {}
        if "timestamp" in self.parameter:
            last_updated = formatTime(self.hass, int(self.parameter["timestamp"]))
            for key, description in self._attributes.items():
                parameter = self.device.getPelTecParameter(key)
                attributes[description] = parameter["value"] or "?"
            attributes["Last updated"] = last_updated
        return attributes

    @property
    def device_info(self):
        return create_device_info(self.device)

    @staticmethod
    def createCommonEntities(hass, device) -> List[SensorEntity]:
        entities = []
        for param_id, sensor_data in PELTEC_SENSOR_GENERIC_COMMON.items():
            parameter = device.getPelTecParameter(param_id)
            entities.append(PelTecGenericSensor(hass, device, sensor_data, parameter))
        return entities

    @staticmethod
    def createConfEntities(hass, device, conf) -> List[SensorEntity]:
        entities = []
        if conf == "3":  # "4. BUF":
            for param_id, sensor_data in PELTEC_4BUF_SENSOR_TYPES.items():
                parameter = device.getPelTecParameter(param_id)
                entities.append(
                    PelTecGenericSensor(hass, device, sensor_data, parameter)
                )
        return entities

    @staticmethod
    def createUnknownEntities(hass, device) -> List[SensorEntity]:
        entities = []
        for param_key, param in device["parameters"].items():
            if "used" in param.keys():
                continue
            _LOGGER.info("Creating unknown entry for " + param_key)
            sensor_data = ["", "mdi:help", None, "{?} " + param_key, {}]
            entities.append(PelTecGenericSensor(hass, device, sensor_data, param))
        return entities
