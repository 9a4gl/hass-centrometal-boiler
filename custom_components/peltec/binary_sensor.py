"""Support for Centrometal Boiler System."""

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)

from .const import DOMAIN, WEB_BOILER_CLIENT


async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = []

    web_boiler_client = hass.data[DOMAIN][WEB_BOILER_CLIENT]
    for device in web_boiler_client.data.values():
        entities.append(WebBoilerWebsocketStatus(hass, web_boiler_client, device))
    async_add_entities(entities, True)


class WebBoilerWebsocketStatus(BinarySensorEntity):
    """Representation of Centrometal Boiler System websocket connection status."""

    def __init__(self, hass, web_boiler_client, device) -> None:
        """Initialize the binary sensor."""
        super().__init__()
        self.hass = hass
        self.web_boiler_client = web_boiler_client
        self.device = device
        self._serial = device["serial"]
        self._unique_id = self._serial + "_websocket_status"
        self._name = "Centrometal Boiler System connection"

    async def async_added_to_hass(self):
        """Subscribe to events."""
        self.web_boiler_client.set_connectivity_callback(self.update_callback)

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
        return self.web_boiler_client.is_websocket_connected()

    @property
    def should_poll(self) -> bool:
        """No polling needed for a sensor."""
        return False

    async def update_callback(self, status):
        """Call update for Home Assistant when the device is updated."""
        self.schedule_update_ha_state(True)

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY
