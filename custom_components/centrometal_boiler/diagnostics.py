from __future__ import annotations

from typing import Any
import hashlib

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

TO_REDACT = {CONF_EMAIL, CONF_PASSWORD, "country", "address", "place", "city", "serial", "id", "label"}


def _hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:8]


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry) -> dict[str, Any]:
    runtime = entry.runtime_data
    data = runtime.client.data
    devices: dict[str, Any] = {}
    for index, (serial, device) in enumerate(data.items(), start=1):
        device_key = f"device_{index}_{_hash_identifier(str(serial))}"
        devices[device_key] = {
            k: v for k, v in device.items() if k not in {"parameters", "widgets", "__client", "__system"}
        }
        devices[device_key]["parameters"] = {
            name: {
                "value": param.get("value"),
                "timestamp": param.get("timestamp"),
            }
            for name, param in device.get("parameters", {}).items()
        }
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "websocket_connected": runtime.client.is_websocket_connected(),
        "devices": async_redact_data(devices, TO_REDACT),
    }
