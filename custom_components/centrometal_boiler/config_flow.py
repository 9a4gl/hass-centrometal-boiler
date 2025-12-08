"""Config flow for Centrometal boiler integration."""
from collections import OrderedDict
import logging

from centrometal_web_boiler import WebBoilerClient

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_ID, CONF_PASSWORD, CONF_PREFIX

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# pylint: disable=missing-function-docstring
# pylint: disable=broad-except


class CentrometalBoilerConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Centrometal boiler."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        errors = {}

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
        except Exception:
            _LOGGER.exception("Unexpected exception " + user_input[CONF_EMAIL])
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
    _LOGGER.debug(
        f"Trying to connect to Centrometal boiler server during setup {email}"
    )
    web_boiler_client = WebBoilerClient()
    loggedIn = await web_boiler_client.login(username=email, password=password)
    if not loggedIn:
        raise Exception(f"Login to Centrometal boiler server failed {email}")
    gotConfiguration = await web_boiler_client.get_configuration()
    if not gotConfiguration:
        raise Exception(
            f"Getting devices from Centrometal boiler server failed {email}"
        )
    if len(web_boiler_client.data) == 0:
        raise Exception(f"No device found on Centrometal boiler server {email}")
    await web_boiler_client.close_websocket()
    await web_boiler_client.http_client.close_session()
    _LOGGER.debug(f"Successfully connected to Centrometal boiler during setup {email}")
    return web_boiler_client.data
