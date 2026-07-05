from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor


class WebBoilerErrorsSensor(WebBoilerGenericSensor):
    """Decoded event/error history from the portal's errors-list endpoint."""

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        base = super().extra_state_attributes or {}
        attrs = dict(base)
        events = self.device.get("errors") or []
        attrs["Event count"] = len(events)
        attrs["Events"] = events[-50:]
        if events:
            attrs["Latest event"] = events[-1]
        return attrs

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        if device.get("errors") is None:
            return []
        parameter = device.get_or_create_parameter("Errors_History")
        parameter["name"] = "Errors_History"
        if "value" not in parameter:
            events = device.get("errors") or []
            parameter["value"] = events[-1].get("description", "Event") if events else "No events"
        return [
            WebBoilerErrorsSensor(
                hass,
                device,
                [None, "mdi:alert-circle-outline", None, "Event History"],
                parameter,
            )
        ]
