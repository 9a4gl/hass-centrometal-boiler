import logging

from .switches.WebBoilerPowerSwitch import WebBoilerPowerSwitch
from .switches.WebBoilerCircuitSwitch import WebBoilerCircuitSwitch

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = []
    web_boiler_client = config_entry.runtime_data.client
    for device in web_boiler_client.data.values():
        if device["type"] in ("peltec", "peltec2", "cmpelet", "biopl"):
            entities.append(WebBoilerPowerSwitch(hass, device))
        for circuit in device["circuits"].values():
            entities.append(WebBoilerCircuitSwitch(hass, device, circuit["naslov"], circuit["dbindex"]))
    if entities:
        async_add_entities(entities, True)
