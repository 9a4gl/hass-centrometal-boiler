from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
import logging

from .WebBoilerGenericSensor import WebBoilerGenericSensor

_LOGGER = logging.getLogger(__name__)


class WebBoilerFuelPercentageSensor(WebBoilerGenericSensor):
    """Fuel percentage sensor that handles late arrival of B_razP parameter."""

    async def async_added_to_hass(self):
        """Subscribe to events and check for real parameter."""
        # Try to get the real parameter now
        try:
            if self._device.has_parameter("B_razP"):
                self.parameter = self._device.get_parameter("B_razP")
                _LOGGER.debug(
                    "WebBoilerFuelPercentageSensor connected to real B_razP parameter"
                )
        except Exception:
            pass

        # Call parent to set up subscription
        await super().async_added_to_hass()

    @property
    def native_value(self):
        """Return the percentage value."""
        try:
            return int(self.parameter["value"])
        except (ValueError, TypeError, KeyError):
            return None

    @property
    def native_unit_of_measurement(self):
        return "%"

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        try:
            param = device.get_parameter("B_razP")
        except Exception:
            # Create with placeholder - will update when B_razP arrives
            param = {"name": "B_razP", "value": 0, "used": True}

        sensor = WebBoilerFuelPercentageSensor(
            hass,
            device,
            ["%", "mdi:percent", None, "Fuel level"],
            param,
        )
        # Store device reference for later parameter lookup
        sensor._device = device
        entities.append(sensor)
        return entities
