import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from ..const import DOMAIN, WEB_BOILER_CLIENT, WEB_BOILER_SYSTEM
from ..common import format_name, format_time, create_device_info

from .generic_sensors_all import (
    GENERIC_SENSORS_COMMON,
    get_generic_temperature_settings_sensors,
)
from .generic_sensors_peltec import PELTEC_GENERIC_SENSORS
from .generic_sensors_compact import COMPACT_GENERIC_SENSORS
from .generic_sensors_cm_pelet_set import CM_PELET_SET_GENERIC_SENSORS
from .generic_sensors_biotec import BIOTEC_GENERIC_SENSORS
from .generic_sensors_biotec_plus import BIOTEC_PLUS_GENERIC_SENSORS

_LOGGER = logging.getLogger(__name__)


class WebBoilerGenericSensor(SensorEntity):
    """Representation of a Centrometal Boiler Sensor."""

    def __init__(self, hass: HomeAssistant, device, sensor_data, parameter, disabled_by_default=False) -> None:
        """Initialize the Centrometarl Boiler Sensor."""
        self.hass = hass
        self.web_boiler_client = hass.data[DOMAIN][device.username][WEB_BOILER_CLIENT]
        self.web_boiler_system = hass.data[DOMAIN][device.username][WEB_BOILER_SYSTEM]
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
        self._product = device["product"]
        self._name = format_name(hass, device, f"{self._product} {self._description}")
        self._unique_id = f"{self._serial}-{self._parameter_name}"
        if disabled_by_default:
          self._attr_entity_registry_enabled_default = False
          self._attr_entity_registry_visible_default = False
        #
        self.added_to_hass = False
        self.parameter["used"] = True
        for attribute in self._attributes:
            attribute_parameter = self.device.get_parameter(attribute)
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
    def native_unit_of_measurement(self):
        """Return the unit this state is expressed in."""
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
        return self.web_boiler_client.is_websocket_connected()

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = {}
        if "timestamp" in self.parameter:
            last_updated = format_time(self.hass, int(self.parameter["timestamp"]))
            for key, description in self._attributes.items():
                parameter = self.device.get_parameter(key)
                attributes[description] = parameter["value"] or "?"
            attributes["Last updated"] = last_updated
            attributes["Original name"] = self.parameter["name"]
        return attributes

    @property
    def device_info(self):
        return create_device_info(self.device)

    @staticmethod
    def create_common_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        for param_id, sensor_data in GENERIC_SENSORS_COMMON.items():
            parameter = device.get_parameter(param_id)
            entities.append(
                WebBoilerGenericSensor(hass, device, sensor_data, parameter)
            )
        return entities

    @staticmethod
    def create_temperatures_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        for param_id, sensor_data in get_generic_temperature_settings_sensors(
            device
        ).items():
            parameter = device.get_parameter(param_id)
            entities.append(
                WebBoilerGenericSensor(hass, device, sensor_data, parameter)
            )
        return entities

    @staticmethod
    def create_conf_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        generic_sensors = dict()
        if device["type"] in ["peltec"]:
            generic_sensors = PELTEC_GENERIC_SENSORS
        elif device["type"] == "compact":
            generic_sensors = COMPACT_GENERIC_SENSORS
        elif device["type"] == "cmpelet":
            generic_sensors = CM_PELET_SET_GENERIC_SENSORS
        elif device["type"] == "biotec":
            generic_sensors = BIOTEC_GENERIC_SENSORS
        elif device["type"] == "biopl":
            generic_sensors = BIOTEC_PLUS_GENERIC_SENSORS
        for param_id, sensor_data in generic_sensors.items():
            parameter = device.get_parameter(param_id)
            entities.append(
                WebBoilerGenericSensor(hass, device, sensor_data, parameter)
            )
        return entities

    @staticmethod
    def create_unknown_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        for param_key, param in device["parameters"].items():
            if "used" in param.keys():
                continue
            _LOGGER.info("Creating unknown entry for %s", param_key)
            sensor_data = [None, "mdi:help", None, "{?} " + param_key, {}]
            entities.append(WebBoilerGenericSensor(hass, device, sensor_data, param, True))
        return entities
