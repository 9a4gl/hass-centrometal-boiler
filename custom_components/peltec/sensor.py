# -*- coding: utf-8 -*-

"""Support for Centrometal PelTec System sensors."""
import logging

from .sensors.PelTecGenericSensor import PelTecGenericSensor
from .sensors.PelTecConfigurationSensor import PelTecConfigurationSensor
from .sensors.PelTecWorkingTableSensor import PelTecWorkingTableSensor
from .sensors.PelTecPelletLevelSensor import PelTecPelletLevelSensor
from .sensors.PelTecCurrentTimeSensor import PelTecCurrentTimeSensor
from .sensors.PelTecFireGridSensor import PelTecFireGridSensor

from .const import DOMAIN, PELTEC_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Perform the setup for Centrometal PelTec sensor devices."""
    entities = []

    peltec_client = hass.data[DOMAIN][PELTEC_CLIENT]
    for device in peltec_client.data.values():
        entities.extend(PelTecGenericSensor.createCommonEntities(hass, device))
        entities.extend(PelTecConfigurationSensor.createEntities(hass, device))
        confParameter = device.getPelTecParameter("B_KONF")
        if confParameter is not None:
            conf = confParameter["value"]
            if conf == "3":  # "4. BUF"
                entities.extend(PelTecPelletLevelSensor.createEntities(hass, device))
                entities.extend(PelTecCurrentTimeSensor.createEntities(hass, device))
                entities.extend(PelTecFireGridSensor.createEntities(hass, device))
            entities.extend(PelTecGenericSensor.createConfEntities(hass, device, conf))
            entities.extend(PelTecWorkingTableSensor.createEntities(hass, device))
            entities.extend(PelTecGenericSensor.createUnknownEntities(hass, device))

    async_add_entities(entities, True)
