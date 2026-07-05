import logging
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .common import format_name, create_device_info
from .peltec2 import portal_hex_bit_is_set

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    entities = []
    web_boiler_client = config_entry.runtime_data.client
    for device in web_boiler_client.data.values():
        entities.append(WebBoilerWebsocketStatus(hass, web_boiler_client, device))
        if device.get("type") == "peltec2" and device.has_parameter("B_Inp1"):
            entities.append(WebBoilerExternalStartInput(hass, device))
    async_add_entities(entities, True)


class WebBoilerWebsocketStatus(BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "websocket_status"

    def __init__(self, hass: HomeAssistant, web_boiler_client, device) -> None:
        super().__init__()
        self.hass = hass
        self.web_boiler_client = web_boiler_client
        self.device = device
        self._serial = device["serial"]
        self._unique_id = f"{self._serial}_websocket_status"
        self._name = format_name(hass, device, "Centrometal Boiler System connection")
        self._callback_key = self._unique_id

    async def async_added_to_hass(self):
        self.web_boiler_client.set_connectivity_callback(self.update_callback, self._callback_key)

    async def async_will_remove_from_hass(self) -> None:
        self.web_boiler_client.set_connectivity_callback(None, self._callback_key)

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

    @property
    def device_info(self):
        return create_device_info(self.device)


class WebBoilerExternalStartInput(BinarySensorEntity):
    """Portal-confirmed bit 6 of the hexadecimal B_Inp1 input mask."""

    def __init__(self, hass: HomeAssistant, device) -> None:
        super().__init__()
        self.hass = hass
        self.device = device
        self.web_boiler_client = device["__client"]
        self.parameter = device.get_parameter("B_Inp1")
        self._unique_id = f"{device['serial']}-B_Inp1-bit6"
        self._name = format_name(hass, device, f"{device['product']} External Start Input")
        self._callback_key = f"{self._unique_id}-binary"

    async def async_added_to_hass(self):
        self.parameter.set_update_callback(self.update_callback, self._callback_key)

    async def async_will_remove_from_hass(self) -> None:
        self.parameter.set_update_callback(None, self._callback_key)

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_on(self) -> bool | None:
        return portal_hex_bit_is_set(self.parameter.get("value"), 6)

    @property
    def available(self) -> bool:
        return (
            self.web_boiler_client.has_fresh_data()
            and portal_hex_bit_is_set(self.parameter.get("value"), 6) is not None
        )

    @property
    def icon(self) -> str:
        return "mdi:import"

    @property
    def extra_state_attributes(self):
        return {
            "raw_value": self.parameter.get("value"),
            "source_parameter": "B_Inp1",
            "bit": 6,
        }

    async def update_callback(self, _parameter):
        self.async_write_ha_state()

    @property
    def device_info(self):
        return create_device_info(self.device)
