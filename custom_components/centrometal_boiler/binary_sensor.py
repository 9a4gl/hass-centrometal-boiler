import logging
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import CONF_EMAIL

from .common import format_name
from .const import DOMAIN, WEB_BOILER_CLIENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    entities = []
    unique_id = config_entry.data[CONF_EMAIL]
    web_boiler_client = hass.data[DOMAIN][unique_id][WEB_BOILER_CLIENT]
    for device in web_boiler_client.data.values():
        entities.append(WebBoilerWebsocketStatus(hass, web_boiler_client, device))
    async_add_entities(entities, True)


class WebBoilerWebsocketStatus(BinarySensorEntity):
    def __init__(self, hass: HomeAssistant, web_boiler_client, device) -> None:
        super().__init__()
        self.hass = hass
        self.web_boiler_client = web_boiler_client
        self.device = device
        self._serial = device["serial"]
        self._unique_id = f"{self._serial}_websocket_status"
        self._name = format_name(hass, device, "Centrometal Boiler System connection")

    async def async_added_to_hass(self):
        self.web_boiler_client.set_connectivity_callback(self.update_callback)

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool:
        return self.web_boiler_client.is_websocket_connected()

    @property
    def should_poll(self) -> bool:
        return False

    async def update_callback(self, status):
        self.async_write_ha_state()

    @property
    def device_class(self):
        return BinarySensorDeviceClass.CONNECTIVITY
