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
        entities.extend(PelTecGenericSensor.create_common_entities(hass, device))
        entities.extend(PelTecConfigurationSensor.create_entities(hass, device))
        entities.extend(PelTecCurrentTimeSensor.create_entities(hass, device))
        confParameter = device.get_parameter("B_KONF")
        if confParameter is not None:
            conf = confParameter["value"]
            if conf == "3":  # "4. BUF"
                entities.extend(PelTecPelletLevelSensor.create_entities(hass, device))
                entities.extend(PelTecFireGridSensor.create_entities(hass, device))
            entities.extend(
                PelTecGenericSensor.create_conf_entities(hass, device, conf)
            )
            entities.extend(PelTecWorkingTableSensor.create_entities(hass, device))
            entities.extend(PelTecGenericSensor.create_unknown_entities(hass, device))

    async_add_entities(entities, True)
