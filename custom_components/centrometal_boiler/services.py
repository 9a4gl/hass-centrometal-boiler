from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    WEB_BOILER_SYSTEM,
)

from homeassistant.const import (
    CONF_EMAIL,
)

ATTR_SERIAL = "serial"
ATTR_VALUE = "value"


def setup_services(hass: HomeAssistant, entry: ConfigEntry):
    async def handle_turn(call):
        """Handle the service call."""
        unique_id = entry.data[CONF_EMAIL]
        web_boiler_system = hass.data[DOMAIN][unique_id][WEB_BOILER_SYSTEM]
        if web_boiler_system.web_boiler_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            value = call.data.get(ATTR_VALUE, False)
            if serial != "":
                if not await web_boiler_system.web_boiler_client.turn(serial, value):
                    web_boiler_system.relogin()

    async def handle_turn_on(call):
        """Handle the service call."""
        unique_id = entry.data[CONF_EMAIL]
        web_boiler_system = hass.data[DOMAIN][unique_id][WEB_BOILER_SYSTEM]
        if web_boiler_system.web_boiler_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            if serial != "":
                if not await web_boiler_system.web_boiler_client.turn(serial, True):
                    web_boiler_system.relogin()

    async def handle_turn_off(call):
        """Handle the service call."""
        unique_id = entry.data[CONF_EMAIL]
        web_boiler_system = hass.data[DOMAIN][unique_id][WEB_BOILER_SYSTEM]
        if web_boiler_system.web_boiler_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            if serial != "":
                if not await web_boiler_system.web_boiler_client.turn(serial, True):
                    web_boiler_system.relogin()

    async def handle_turn_toggle(call):
        """Handle the service call."""
        unique_id = entry.data[CONF_EMAIL]
        web_boiler_system = hass.data[DOMAIN][unique_id][WEB_BOILER_SYSTEM]
        if web_boiler_system.web_boiler_client.is_websocket_connected():
            serial = call.data.get(ATTR_SERIAL, "")
            if serial != "":
                device = web_boiler_system.web_boiler_client.data[serial]
                if "B_STATE" in device["parameters"]:
                    param = device["parameters"]["B_STATE"]
                    newvalue = param["value"] == "OFF"
                    if not await web_boiler_system.web_boiler_client.turn(
                        serial, newvalue
                    ):
                        web_boiler_system.relogin()

    hass.services.async_register(DOMAIN, "turn", handle_turn)
    hass.services.async_register(DOMAIN, "turn_on", handle_turn_on)
    hass.services.async_register(DOMAIN, "turn_off", handle_turn_off)
    hass.services.async_register(DOMAIN, "turn_toggle", handle_turn_toggle)
