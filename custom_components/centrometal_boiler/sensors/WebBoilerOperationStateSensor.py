from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor

_B_STATE_MAP: dict[str, str] = {
    "OFF":  "OFF: Switched off",
    "S0":   "S0: Fan blowing / grate check",
    "S1":   "S1: Not used",
    "S2":   "S2: Initial pellet filling",
    "S3":   "S3: Waiting for flame",
    "S4":   "S4: Electric heater igniting",
    "S5":   "S5: Flame developing",
    "SP1":  "SP1: Stabilising 1",
    "SP2":  "SP2: Stabilising 2",
    "SP3":  "SP3: Stabilising 3",
    "SP4":  "SP4: Stabilising 4",
    "SP5":  "SP5: Stabilising 5",
    "S6":   "S6: Additional flame development",
    "D0":   "D0: Power D0 (min)",
    "D1":   "D1: Power D1",
    "D2":   "D2: Power D2",
    "D3":   "D3: Power D3",
    "D4":   "D4: Power D4",
    "D5":   "D5: Power D5",
    "D6":   "D6: Power D6 (max)",
    "S7-1": "S7-1: Shutting down",
    "S7-2": "S7-2: Final fan blowing",
    "S7-3": "S7-3: Standby",
    "PF0":  "PF0: Power failure — heater starting",
    "PF1":  "PF1: Power failure — heater off",
    "PF2":  "PF2: Power failure — flame developing",
    "PF3":  "PF3: Power failure — waiting for flame off",
    "PF4":  "PF4: Power failure — final blowing",
    "C0":   "C0: Grate cleaning",
}


class WebBoilerOperationStateSensor(WebBoilerGenericSensor):
    @property
    def native_value(self) -> str:
        raw = self.parameter.get("value")
        if raw is None:
            return "Unknown"
        key = str(raw).strip()
        return _B_STATE_MAP.get(key, f"Unknown ({key})")

    @property
    def extra_state_attributes(self) -> dict:
        base = super().extra_state_attributes or {}
        attrs = dict(base)
        attrs["Raw stage code"] = self.parameter.get("value")
        return attrs

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        entities: list[SensorEntity] = []
        if not WebBoilerGenericSensor._device_has_parameter(device, "B_STATE"):
            return entities
        parameter = device.get_parameter("B_STATE")
        if parameter.get("used"):
            return entities
        entities.append(
            WebBoilerOperationStateSensor(
                hass,
                device,
                [None, "mdi:state-machine", None, "Boiler State"],
                parameter,
            )
        )
        return entities
