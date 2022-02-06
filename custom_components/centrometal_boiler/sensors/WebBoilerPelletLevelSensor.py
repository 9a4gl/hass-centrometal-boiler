from typing import List
from homeassistant.components.sensor import SensorEntity

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerPelletLevelSensor(WebBoilerGenericSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        configurations = ["Empty", "Reserve", "Full"]
        return configurations[int(self.parameter["value"])]

    @staticmethod
    def create_entities(hass, device) -> List[SensorEntity]:
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
