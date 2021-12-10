from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    PELTEC_SYSTEM,
)

ATTR_SERIAL = "serial"
ATTR_VALUE = "value"


def setup_services(hass: HomeAssistant):
    async def handle_turn(call):
        """Handle the service call."""
        peltec_system = hass.data[DOMAIN][PELTEC_SYSTEM]
        if peltec_system.peltec_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            value = call.data.get(ATTR_VALUE, False)
            if serial != "":
                await peltec_system.peltec_client.turn(serial, value)

    async def handle_turn_on(call):
        """Handle the service call."""
        peltec_system = hass.data[DOMAIN][PELTEC_SYSTEM]
        if peltec_system.peltec_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            if serial != "":
                await peltec_system.peltec_client.turn(serial, True)

    async def handle_turn_off(call):
        """Handle the service call."""
        peltec_system = hass.data[DOMAIN][PELTEC_SYSTEM]
        if peltec_system.peltec_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            if serial != "":
                await peltec_system.peltec_client.turn(serial, True)

    async def handle_turn_toggle(call):
        """Handle the service call."""
        peltec_system = hass.data[DOMAIN][PELTEC_SYSTEM]
        if peltec_system.peltec_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            if serial != "":
                device = peltec_system.peltec_client.data[serial]
                if "B_STATE" in device["parameters"]:
                    param = device["parameters"]["B_STATE"]
                    newvalue = param["value"] == "OFF"
                    await peltec_system.peltec_client.turn(serial, newvalue)

    hass.services.async_register(DOMAIN, "turn", handle_turn)
    hass.services.async_register(DOMAIN, "turn_on", handle_turn_on)
    hass.services.async_register(DOMAIN, "turn_off", handle_turn_off)
    hass.services.async_register(DOMAIN, "turn_toggle", handle_turn_toggle)
