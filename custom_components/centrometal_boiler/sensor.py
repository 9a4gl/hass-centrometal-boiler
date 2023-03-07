# -*- coding: utf-8 -*-
"""Support for Centrometal Boiler System sensors."""

from homeassistant.const import (
    CONF_EMAIL,
)
from homeassistant.core import HomeAssistant

import logging

from .sensors.WebBoilerDeviceTypeSensor import WebBoilerDeviceTypeSensor
from .sensors.WebBoilerGenericSensor import WebBoilerGenericSensor
from .sensors.WebBoilerConfigurationSensor import WebBoilerConfigurationSensor
from .sensors.WebBoilerWorkingTableSensor import WebBoilerWorkingTableSensor
from .sensors.WebBoilerPelletLevelSensor import WebBoilerPelletLevelSensor
from .sensors.WebBoilerCurrentTimeSensor import WebBoilerCurrentTimeSensor
from .sensors.WebBoilerFireGridSensor import WebBoilerFireGridSensor
from .sensors.WebBoilerHeatingCircuitSensor import WebBoilerHeatingCircuitSensor

from .const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Perform the setup for Centrometal boiler sensor devices."""
    entities = []

    unique_id = config_entry.data[CONF_EMAIL]
    web_boiler_client = hass.data[DOMAIN][unique_id][WEB_BOILER_CLIENT]
    for device in web_boiler_client.data.values():
        entities.extend(WebBoilerGenericSensor.create_common_entities(hass, device))
        entities.extend(WebBoilerConfigurationSensor.create_entities(hass, device))
        entities.extend(WebBoilerCurrentTimeSensor.create_entities(hass, device))
        entities.extend(WebBoilerWorkingTableSensor.create_entities(hass, device))
        entities.extend(WebBoilerDeviceTypeSensor.create_entities(hass, device))
        entities.extend(
            WebBoilerHeatingCircuitSensor.create_heating_circuits_entities(hass, device)
        )
        if device["type"] == "peltec" or device["type"] == "biopl":
            entities.extend(WebBoilerPelletLevelSensor.create_entities(hass, device))
        if device["type"] == "peltec":
            entities.extend(WebBoilerFireGridSensor.create_entities(hass, device))
        entities.extend(WebBoilerGenericSensor.create_conf_entities(hass, device))
        entities.extend(
            WebBoilerGenericSensor.create_temperatures_entities(hass, device)
        )
        entities.extend(WebBoilerGenericSensor.create_unknown_entities(hass, device))

    async_add_entities(entities, True)
