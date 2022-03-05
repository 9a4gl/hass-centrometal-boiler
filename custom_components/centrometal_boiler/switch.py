"""Support for boiler switch (Power control)."""

from homeassistant.const import (
    CONF_EMAIL,
)

import logging

from .switches.WebBoilerPowerSwitch import WebBoilerPowerSwitch
from .switches.WebBoilerCircuitSwitch import WebBoilerCircuitSwitch

from .const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the switches platform."""
    entities = []
    unique_id = config_entry.data[CONF_EMAIL]
    web_boiler_client = hass.data[DOMAIN][unique_id][WEB_BOILER_CLIENT]
    for device in web_boiler_client.data.values():
        if (
            device["type"] == "peltec"
            or device["type"] == "cmpelet"
            or device["type"] == "biopl"
        ):
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
