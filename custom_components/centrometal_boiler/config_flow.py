"""Config flow for Centrometal boiler integration."""
from collections import OrderedDict
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_ID, CONF_PASSWORD, CONF_PREFIX

from .const import DOMAIN
from .transport import WebBoilerSystem

_LOGGER = logging.getLogger(__name__)

# pylint: disable=missing-function-docstring
# pylint: disable=broad-except


class CentrometalBoilerConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Centrometal boiler."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        fields = OrderedDict()
        fields[vol.Required(CONF_EMAIL)] = str
        fields[vol.Required(CONF_PASSWORD)] = str
        fields[vol.Optional(CONF_PREFIX)] = str
        fields[vol.Optional('product_prefix')] = bool

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return await self._show_setup_form()

        errors = {}
        deviceCollection = None
        try:
            deviceCollection = await try_connection(
                user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
        except Exception as error:
            _LOGGER.debug("Centrometal connection check failed (%s)", type(error).__name__)
            errors["base"] = "unknown"
            return await self._show_setup_form(errors)

        unique_id = user_input[CONF_EMAIL]

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        device = list(deviceCollection.values())[0]
        title = device["product"] + ": " + device["address"] + ", " + device["place"]

        return self.async_create_entry(
            title=title,
            data={
                CONF_ID: unique_id,
                CONF_EMAIL: user_input[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_PREFIX: user_input.get(CONF_PREFIX, ""),
                'product_prefix': user_input.get('product_prefix', ""),
            },
        )


async def try_connection(email, password):
    system = WebBoilerSystem(email, password, "", True)
    try:
        if not await system.load_configuration():
            raise ConnectionError("Centrometal configuration could not be loaded")
        return system.data
    finally:
        await system.stop()
