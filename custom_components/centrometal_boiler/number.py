"""Support for writable boiler temperature settings (Number entities)."""

import logging

from homeassistant.const import CONF_EMAIL

from .const import DOMAIN, WEB_BOILER_CLIENT
from .numbers.WebBoilerTemperatureNumber import WebBoilerTemperatureNumber

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the number platform (temperature set points)."""
    entities = []
    unique_id = config_entry.data[CONF_EMAIL]
    web_boiler_client = hass.data[DOMAIN][unique_id][WEB_BOILER_CLIENT]
    for device in web_boiler_client.data.values():
        try:
            temperatures = device["temperatures"]
        except (KeyError, TypeError):
            continue
        for value in temperatures.values():
            dbindex = value["dbindex"]
            if device.has_parameter(f"PVAL_{dbindex}_0"):
                entities.append(
                    WebBoilerTemperatureNumber(hass, device, value["naslov"], dbindex)
                )

    _LOGGER.debug(
        "Adding temperature settings as number: %s (%s)",
        entities,
        web_boiler_client.username,
    )
    if len(entities) > 0:
        async_add_entities(entities, True)
