from typing import List
from homeassistant.components.sensor import SensorEntity
from homeassistant.util.dt import UTC

from .PelTecGenericSensor import PelTecGenericSensor
from ..common import formatTime


class PelTecCurrentTimeSensor(PelTecGenericSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        value = int(self.parameter["value"], 16)
        return formatTime(self.hass, value, UTC)

    @staticmethod
    def createEntities(hass, device) -> List[SensorEntity]:
        entities = []
        entities.append(
            PelTecCurrentTimeSensor(
                hass,
                device,
                ["", "mdi:clock-outline", None, "Clock"],
                device.getOrCreatePelTecParameter("B_Time"),
            )
        )
        return entities
