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

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
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
        if pct == 0:
            return "0"
        return f"+{pct}" if value_dir > 0 else f"-{pct}"

    @property
    def extra_state_attributes(self):
        base = super().extra_state_attributes or {}
        attrs = dict(base)
        try:
            value_ind = int(self.parameter["value"])
            value_max = int(self.param_max["value"])
            value_dir = int(self.param_dir["value"])
            position = int(value_ind * 100 / value_max) if value_max > 0 else 0
        except Exception:
            value_ind = self.parameter.get("value")
            value_max = self.param_max.get("value")
            value_dir = self.param_dir.get("value")
            position = None

        if position is None:
            direction = "Unknown"
            grate_state = "Unknown"
        elif position <= 0:
            direction = "Stationary"
            grate_state = "Closed - ready to operate"
        elif position >= 100:
            direction = "Stationary"
            grate_state = "Open - cleaning"
        elif isinstance(value_dir, int) and value_dir > 0:
            direction = "Opening"
            grate_state = "Opening"
        else:
            direction = "Closing"
            grate_state = "Closing"

        attrs["Position percentage"] = position
        attrs["Direction"] = direction
        attrs["Grate state"] = grate_state
        attrs["Raw index"] = value_ind
        attrs["Raw maximum"] = value_max
        attrs["Raw direction"] = value_dir
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
                hass,
                device,
                ["", "mdi:grid", None, "Burner Grate Position"],
                param_ind,
                param_dir,
                param_max,
            )
        )
        return entities
