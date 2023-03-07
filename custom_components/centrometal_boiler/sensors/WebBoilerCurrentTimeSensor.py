from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import UTC

from .WebBoilerGenericSensor import WebBoilerGenericSensor
from ..common import format_time


class WebBoilerCurrentTimeSensor(WebBoilerGenericSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        if self.parameter["value"] == "?":
            return self.parameter["value"]
        value = int(self.parameter["value"], 16)
        return format_time(self.hass, value, UTC)

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        entities.append(
            WebBoilerCurrentTimeSensor(
                hass,
                device,
                [None, "mdi:clock-outline", None, "Clock"],
                device.get_parameter("B_Time"),
            )
        )
        return entities
