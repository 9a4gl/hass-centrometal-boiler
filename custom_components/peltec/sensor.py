# -*- coding: utf-8 -*-

"""Support for Centrometal PelTec System sensors."""
import logging

from .sensors.PelTecGenericSensor import PelTecGenericSensor
from .sensors.PelTecConfigurationSensor import PelTecConfigurationSensor
from .sensors.PelTecWorkingTableSensor import PelTecWorkingTableSensor

from .const import DOMAIN, PELTEC_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Perform the setup for Centrometal PelTec sensor devices."""
    entities = []

    peltec_client = hass.data[DOMAIN][PELTEC_CLIENT]
    for device in peltec_client.data.values():
        parameters = device["parameters"]
        entities.extend(PelTecGenericSensor.createEntities(parameters, hass, device))
        entities.extend(
            PelTecConfigurationSensor.createEntities(parameters, hass, device)
        )
        entities.extend(
            PelTecWorkingTableSensor.createEntities(parameters, hass, device)
        )

    async_add_entities(entities, True)
