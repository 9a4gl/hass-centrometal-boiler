from typing import List
from homeassistant.components.sensor import SensorEntity

from .PelTecGenericSensor import PelTecGenericSensor


class PelTecPelletLevelSensor(PelTecGenericSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        configurations = ["Empty", "Reserve", "Full"]
        return configurations[int(self.parameter["value"])]

    @staticmethod
    def create_entities(hass, device) -> List[SensorEntity]:
        entities = []
        entities.append(
            PelTecPelletLevelSensor(
                hass,
                device,
                ["", "mdi:bucket-outline", None, "Tank Level"],
                device.get_parameter("B_razina"),
            )
        )
        return entities
