"""Support for Centrometal PelTec System."""

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)

from .const import DOMAIN, PELTEC_CLIENT


async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = []

    peltec_client = hass.data[DOMAIN][PELTEC_CLIENT]
    for device in peltec_client.data.values():
        entities.append(PelTecWebsocketStatus(hass, peltec_client, device))
    async_add_entities(entities, True)


class PelTecWebsocketStatus(BinarySensorEntity):
    """Representation of Centrometal PelTec System websocket connection status."""

    def __init__(self, hass, peltec_client, device) -> None:
        """Initialize the binary sensor."""
        super().__init__()
        self.hass = hass
        self.peltec_client = peltec_client
        self.device = device
        self._serial = device["serial"]
        self._unique_id = self._serial + "_peltec_websocket_status"
        self._name = "Centrometal PelTec System connection"

    async def async_added_to_hass(self):
        """Subscribe to events."""
        self.peltec_client.set_connectivity_callback(self.update_callback)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def is_on(self) -> bool:
        """Return the status of the sensor."""
        return self.peltec_client.is_websocket_connected()

    @property
    def should_poll(self) -> bool:
        """No polling needed for a sensor."""
        return False

    def update_callback(self, status):
        """Call update for Home Assistant when the device is updated."""
        self.schedule_update_ha_state(True)

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY
