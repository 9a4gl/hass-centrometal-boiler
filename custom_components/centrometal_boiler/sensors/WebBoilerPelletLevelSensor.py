from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerPelletLevelSensor(WebBoilerGenericSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        configurations = ["Empty", "Reserve", "Full"]
        return configurations[int(self.parameter["value"])]

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        entities.append(
            WebBoilerPelletLevelSensor(
                hass,
                device,
                [None, "mdi:bucket-outline", None, "Tank Level"],
                device.get_parameter("B_razina"),
            )
        )
        return entities
