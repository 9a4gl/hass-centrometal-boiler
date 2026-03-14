import logging
from homeassistant.const import CONF_EMAIL

from .switches.WebBoilerPowerSwitch import WebBoilerPowerSwitch
from .switches.WebBoilerCircuitSwitch import WebBoilerCircuitSwitch
from .const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = []
    unique_id = config_entry.data[CONF_EMAIL]
    web_boiler_client = hass.data[DOMAIN][unique_id][WEB_BOILER_CLIENT]

    for device in web_boiler_client.data.values():
        if device["type"] in ("peltec", "peltec2", "cmpelet", "biopl"):
            entities.append(WebBoilerPowerSwitch(hass, device))
        for circuit in device["circuits"].values():
            entities.append(
                WebBoilerCircuitSwitch(hass, device, circuit["naslov"], circuit["dbindex"])
            )

    _LOGGER.debug(
        "Adding boiler control as switch: %s (%s)", entities, web_boiler_client.username
    )

    if entities:
        async_add_entities(entities, True)
