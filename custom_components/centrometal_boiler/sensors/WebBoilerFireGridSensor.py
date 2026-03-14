from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerFireGridSensor(WebBoilerGenericSensor):
    def __init__(self, hass, device, sensor_data, param_ind, param_dir, param_max) -> None:
        super().__init__(hass, device, sensor_data, param_ind)
        self.param_dir = param_dir
        self.param_max = param_max
        self.param_dir["used"] = True
        self.param_max["used"] = True

    def __del__(self):
        super().__del__()
        try:
            self.param_dir.set_update_callback(None, "firegrid")
        except Exception:
            pass
        try:
            self.param_max.set_update_callback(None, "firegrid")
        except Exception:
            pass

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.param_dir.set_update_callback(self.update_callback, "firegrid")
        self.param_max.set_update_callback(self.update_callback, "firegrid")

    @property
    def native_value(self):
        try:
            value_ind = int(self.parameter["value"])
            value_max = int(self.param_max["value"])
            value_dir = int(self.param_dir["value"])
        except Exception:
            return "0"
        if value_max <= 0:
            return "0"
        pct = int(value_ind * 100 / value_max)
        return f"+{pct}" if value_dir > 0 else f"-{pct}"

    @property
    def extra_state_attributes(self):
        base = super().extra_state_attributes or {}
        attrs = dict(base)
        attrs["Ind"] = self.parameter["value"]
        attrs["Max"] = self.param_max["value"]
        attrs["Dir"] = self.param_dir["value"]
        return attrs

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities: list[SensorEntity] = []
        required = ["B_resInd", "B_resDir", "B_resMax"]
        for param_name in required:
            if not WebBoilerGenericSensor._device_has_parameter(device, param_name):
                return entities
        param_ind = device.get_parameter("B_resInd")
        param_dir = device.get_parameter("B_resDir")
        param_max = device.get_parameter("B_resMax")
        if param_ind.get("used") and param_dir.get("used") and param_max.get("used"):
            return entities
        entities.append(
            WebBoilerFireGridSensor(
                hass, device,
                ["", "mdi:grid", None, "Fire Grid Position"],
                param_ind, param_dir, param_max,
            )
        )
        return entities
