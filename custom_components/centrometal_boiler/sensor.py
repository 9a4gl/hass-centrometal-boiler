import logging

from homeassistant.const import CONF_EMAIL
from homeassistant.core import HomeAssistant

from .sensors.WebBoilerDeviceTypeSensor import WebBoilerDeviceTypeSensor
from .sensors.WebBoilerGenericSensor import WebBoilerGenericSensor
from .sensors.WebBoilerConfigurationSensor import WebBoilerConfigurationSensor
from .sensors.WebBoilerWorkingTableSensor import WebBoilerWorkingTableSensor
from .sensors.WebBoilerFireGridSensor import WebBoilerFireGridSensor
from .sensors.WebBoilerOperationStateSensor import WebBoilerOperationStateSensor
from .sensors.WebBoilerHeatingCircuitSensor import WebBoilerHeatingCircuitSensor
from .sensors.WebBoilerBinaryOnOffSensor import create_binary_state_entities

from .const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    all_entities = []

    username = config_entry.data[CONF_EMAIL]
    web_boiler_client = hass.data[DOMAIN][username][WEB_BOILER_CLIENT]

    for device in web_boiler_client.data.values():
        all_entities.extend(create_binary_state_entities(hass, device))
        all_entities.extend(WebBoilerGenericSensor.create_common_entities(hass, device))
        all_entities.extend(WebBoilerConfigurationSensor.create_entities(hass, device))
        all_entities.extend(WebBoilerWorkingTableSensor.create_entities(hass, device))
        all_entities.extend(WebBoilerDeviceTypeSensor.create_entities(hass, device))
        all_entities.extend(
            WebBoilerHeatingCircuitSensor.create_heating_circuits_entities(hass, device)
        )

        if device["type"] in ("peltec", "peltec2"):
            all_entities.extend(WebBoilerFireGridSensor.create_entities(hass, device))

        if device["type"] == "peltec2":
            all_entities.extend(WebBoilerOperationStateSensor.create_entities(hass, device))

        all_entities.extend(WebBoilerGenericSensor.create_conf_entities(hass, device))
        all_entities.extend(WebBoilerGenericSensor.create_temperatures_entities(hass, device))
        all_entities.extend(WebBoilerGenericSensor.create_unknown_entities(hass, device))

    deduped_entities = []
    seen_ids = set()
    for entity in all_entities:
        uid = getattr(entity, "unique_id", None)
        if uid is None:
            deduped_entities.append(entity)
            continue
        if uid in seen_ids:
            _LOGGER.debug(
                "Skipping duplicate entity with unique_id %s (%s)",
                uid,
                getattr(entity, "name", "<no name>"),
            )
            continue
        seen_ids.add(uid)
        deduped_entities.append(entity)

    async_add_entities(deduped_entities, True)
