from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor
from centrometal_web_boiler.WebBoilerDeviceCollection import WebBoilerParameter


class WebBoilerDeviceTypeSensor(WebBoilerGenericSensor):
    @property
    def available(self):
        """Return the availablity of the sensor."""
        return True

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        parameter = WebBoilerParameter()
        parameter["name"] = "Device_Type"
        parameter["value"] = device["type"]
        entities = []
        entities.append(
            WebBoilerDeviceTypeSensor(
                hass,
                device,
                [None, "mdi:star-circle", None, "Device Type"],
                parameter,
            )
        )
        return entities
