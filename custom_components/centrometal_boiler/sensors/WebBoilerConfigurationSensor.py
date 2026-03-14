from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerConfigurationSensor(WebBoilerGenericSensor):
    @property
    def native_value(self):
        if self.device["type"] in ("peltec", "peltec2"):
            configurations = [
                "1. DHW", "2. DHC", "3. DHW || DHC", "4. BUF",
                "5. DHW || BUF", "6. BUF -- IHC", "7. DHW || BUF -- IHC",
                "8. BUF -- DHW", "9. BUF -- IHC || DHW", "10. CRO",
                "11. CRO / BUF", "12. DHC || DHW(2)", "13. DHC 2X",
                "14. BUF--IHCX2", "15. CRO -- DHW",
            ]
            try:
                idx = int(self.parameter["value"])
                if 0 <= idx < len(configurations):
                    return configurations[idx]
            except Exception:
                pass
        return self.parameter["value"]

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities: list[SensorEntity] = []
        if WebBoilerGenericSensor._device_has_parameter(device, "B_KONF"):
            parameter = device.get_parameter("B_KONF")
            if not parameter.get("used"):
                entities.append(
                    WebBoilerConfigurationSensor(
                        hass, device,
                        [None, "mdi:state-machine", None, "Configuration"],
                        parameter,
                    )
                )
        return entities
