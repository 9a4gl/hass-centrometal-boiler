from typing import List
from .PelTecGenericSensor import PelTecGenericSensor
from homeassistant.components.sensor import SensorEntity


class PelTecPeletLevelSensor(PelTecGenericSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        configurations = ["Empty", "Reserve", "Full"]
        return configurations[int(self.parameter["value"])]

    @staticmethod
    def createEntities(parameters, hass, device) -> List[SensorEntity]:
        entities = []
        entities.append(
            PelTecPeletLevelSensor(
                hass,
                device,
                ["", "mdi:bucket-outline", None, "Tank Level"],
                parameters["B_razina"],
            )
        )
        return entities
