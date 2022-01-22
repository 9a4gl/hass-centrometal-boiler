"""Support for boiler switch (Power control)."""

import logging

from .switches.WebBoilerPowerSwitch import WebBoilerPowerSwitch
from .switches.WebBoilerCircuitSwitch import WebBoilerCircuitSwitch

from .const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the switches platform."""
    entities = []
    web_boiler_client = hass.data[DOMAIN][WEB_BOILER_CLIENT]
    for device in web_boiler_client.data.values():
        if device["type"] == "peltec" or device["type"] == "cmpelet":
            entities.append(WebBoilerPowerSwitch(hass, device))
        for circuit in device["circuits"].values():
            entities.append(
                WebBoilerCircuitSwitch(
                    hass, device, circuit["naslov"], circuit["dbindex"]
                )
            )

    _LOGGER.debug(
        "Adding boiler control as switch: %s (%s)", entities, web_boiler_client.username
    )
    if len(entities) > 0:
        async_add_entities(entities, True)
