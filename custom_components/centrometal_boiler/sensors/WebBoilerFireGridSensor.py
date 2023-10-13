from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerFireGridSensor(WebBoilerGenericSensor):
    def __init__(
        self, hass: HomeAssistant, device, sensor_data, param_ind, param_dir, param_max
    ) -> None:
        super().__init__(hass, device, sensor_data, param_ind)
        self.param_dir = param_dir
        self.param_max = param_max
        self.param_dir["used"] = True
        self.param_max["used"] = True

    def __del__(self):
        self.param_dir.set_update_callback(None, "firegrid")
        self.param_max.set_update_callback(None, "firegrid")

    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        await super().async_added_to_hass()
        self.param_dir.set_update_callback(self.update_callback, "firegrid")
        self.param_max.set_update_callback(self.update_callback, "firegrid")

    @property
    def native_value(self):
        """Return the value of the sensor."""
        try:
            value_ind = int(self.parameter["value"])
            value_max = int(self.param_max["value"])
            value_dir = int(self.param_dir["value"])
        except Exception:
            return "0"
        if value_max < 0:
            return "0"
        text = str(int(value_ind * 100 / value_max))
        if value_dir > 0:
            return "+" + text
        return "-" + text

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = super().device_state_attributes
        attributes["Ind"] = self.parameter["value"]
        attributes["Max"] = self.param_max["value"]
        attributes["Dir"] = self.param_dir["value"]
        return attributes

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities = []
        entities.append(
            WebBoilerFireGridSensor(
                hass,
                device,
                ["", "mdi:grid", None, "Fire Grid Position"],
                device.get_parameter("B_resInd"),
                device.get_parameter("B_resDir"),
                device.get_parameter("B_resMax"),
            )
        )
        return entities
