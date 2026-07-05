import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .sensors.WebBoilerBinaryOnOffSensor import create_binary_state_entities
from .sensors.WebBoilerConfigurationSensor import WebBoilerConfigurationSensor
from .sensors.WebBoilerDeviceTypeSensor import WebBoilerDeviceTypeSensor
from .sensors.WebBoilerErrorsSensor import WebBoilerErrorsSensor
from .sensors.WebBoilerFireGridSensor import WebBoilerFireGridSensor
from .sensors.WebBoilerGenericSensor import WebBoilerGenericSensor
from .sensors.WebBoilerHeatingCircuitSensor import WebBoilerHeatingCircuitSensor
from .sensors.WebBoilerOperationStateSensor import WebBoilerOperationStateSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    all_entities = []
    web_boiler_client = config_entry.runtime_data.client
    devices = list(web_boiler_client.data.values())

    for device in devices:
        all_entities.extend(create_binary_state_entities(hass, device))
        all_entities.extend(WebBoilerGenericSensor.create_common_entities(hass, device))
        all_entities.extend(WebBoilerConfigurationSensor.create_entities(hass, device))

        # The synthetic device-type sensor is redundant for PelTec II because
        # the actual product is already exposed and is part of device metadata.
        if device.get("type") != "peltec2":
            all_entities.extend(WebBoilerDeviceTypeSensor.create_entities(hass, device))

        all_entities.extend(WebBoilerHeatingCircuitSensor.create_heating_circuits_entities(hass, device))

        # The controller manual exposes burner-grate position and movement.
        # Keep the existing entity implementation and unique ID for both
        # PelTec generations.
        if device.get("type") in {"peltec", "peltec2"}:
            all_entities.extend(WebBoilerFireGridSensor.create_entities(hass, device))

        if device.get("type") == "peltec2":
            all_entities.extend(WebBoilerOperationStateSensor.create_entities(hass, device))

        all_entities.extend(WebBoilerGenericSensor.create_conf_entities(hass, device))
        all_entities.extend(WebBoilerGenericSensor.create_temperatures_entities(hass, device))
        all_entities.extend(WebBoilerErrorsSensor.create_entities(hass, device))

        # Unknown raw entities are intentionally not created for PelTec II.
        # Other boiler families retain the previous diagnostic fallback.
        all_entities.extend(WebBoilerGenericSensor.create_unknown_entities(hass, device))

    deduped_entities = []
    seen_ids = set()
    for entity in all_entities:
        uid = getattr(entity, "unique_id", None)
        if uid is None or uid not in seen_ids:
            if uid is not None:
                seen_ids.add(uid)
            deduped_entities.append(entity)
        else:
            _LOGGER.debug(
                "Skipping duplicate entity with unique_id %s (%s)",
                uid,
                getattr(entity, "name", "<no name>"),
            )

    # Remove obsolete sensor registry entries from earlier builds. This makes
    # the device page match the current strict PelTec II entity allowlist.
    registry = er.async_get(hass)
    current_unique_ids = {
        entity.unique_id for entity in deduped_entities if getattr(entity, "unique_id", None) is not None
    }
    for registry_entry in er.async_entries_for_config_entry(registry, config_entry.entry_id):
        if not registry_entry.entity_id.startswith("sensor."):
            continue
        if registry_entry.unique_id in current_unique_ids:
            continue
        _LOGGER.debug(
            "Removing obsolete Centrometal sensor registry entry %s (%s)",
            registry_entry.entity_id,
            registry_entry.unique_id,
        )
        registry.async_remove(registry_entry.entity_id)

    async_add_entities(deduped_entities, True)
