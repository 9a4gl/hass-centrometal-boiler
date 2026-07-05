from __future__ import annotations

import contextlib
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_PREFIX
from homeassistant.core import callback
from homeassistant.helpers import selector

from .centrometal_web_boiler import HttpClientAuthError, HttpClientConnectionError, WebBoilerClient
from .const import (
    CONF_REFRESH_INTERVAL,
    CONF_RETRY_BASE_INTERVAL,
    CONF_RETRY_MAX_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    DEFAULT_RETRY_BASE_INTERVAL,
    DEFAULT_RETRY_MAX_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CentrometalBoilerConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CentrometalBoilerOptionsFlowHandler:
        return CentrometalBoilerOptionsFlowHandler()

    def _schema(self, *, email_default: str = "", prefix_default: str = "") -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_EMAIL, default=email_default): selector.TextSelector(),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Optional(CONF_PREFIX, default=prefix_default): selector.TextSelector(),
            }
        )

    async def _show_setup_form(self, errors=None, *, email_default: str = "", prefix_default: str = ""):
        return self.async_show_form(
            step_id="user",
            data_schema=self._schema(email_default=email_default, prefix_default=prefix_default),
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return await self._show_setup_form()

        errors = {}
        try:
            device_collection = await try_connection(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
        except InvalidAuth:
            errors["base"] = "invalid_auth"
            return await self._show_setup_form(
                errors,
                email_default=user_input[CONF_EMAIL],
                prefix_default=user_input.get(CONF_PREFIX, ""),
            )
        except CannotConnect:
            errors["base"] = "cannot_connect"
            return await self._show_setup_form(
                errors,
                email_default=user_input[CONF_EMAIL],
                prefix_default=user_input.get(CONF_PREFIX, ""),
            )
        except Exception:
            _LOGGER.exception("Unexpected exception during Centrometal setup")
            errors["base"] = "unknown"
            return await self._show_setup_form(
                errors,
                email_default=user_input[CONF_EMAIL],
                prefix_default=user_input.get(CONF_PREFIX, ""),
            )

        unique_id = user_input[CONF_EMAIL]
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        device = list(device_collection.values())[0]
        title = device["product"] + ": " + device["address"] + ", " + device["place"]
        return self.async_create_entry(
            title=title,
            data={
                CONF_EMAIL: user_input[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_PREFIX: user_input.get(CONF_PREFIX, ""),
            },
        )

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        entry = self._get_reauth_entry()
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_EMAIL, default=entry.data[CONF_EMAIL]): selector.TextSelector(),
                        vol.Required(CONF_PASSWORD): selector.TextSelector(
                            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                        ),
                        vol.Optional(
                            CONF_PREFIX,
                            default=entry.data.get(CONF_PREFIX, ""),
                        ): selector.TextSelector(),
                    }
                ),
                errors={},
            )

        try:
            await try_connection(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
        except InvalidAuth:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_EMAIL, default=user_input[CONF_EMAIL]): selector.TextSelector(),
                        vol.Required(CONF_PASSWORD): selector.TextSelector(
                            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                        ),
                        vol.Optional(
                            CONF_PREFIX,
                            default=user_input.get(CONF_PREFIX, entry.data.get(CONF_PREFIX, "")),
                        ): selector.TextSelector(),
                    }
                ),
                errors={"base": "invalid_auth"},
            )
        except CannotConnect:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_EMAIL, default=user_input[CONF_EMAIL]): selector.TextSelector(),
                        vol.Required(CONF_PASSWORD): selector.TextSelector(
                            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                        ),
                        vol.Optional(
                            CONF_PREFIX,
                            default=user_input.get(CONF_PREFIX, entry.data.get(CONF_PREFIX, "")),
                        ): selector.TextSelector(),
                    }
                ),
                errors={"base": "cannot_connect"},
            )

        await self.async_set_unique_id(user_input[CONF_EMAIL])
        self._abort_if_unique_id_mismatch(reason="wrong_account")
        return self.async_update_reload_and_abort(
            entry,
            data_updates={
                CONF_EMAIL: user_input[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_PREFIX: user_input.get(CONF_PREFIX, entry.data.get(CONF_PREFIX, "")),
            },
            reload_even_if_entry_is_unchanged=True,
        )


class CentrometalBoilerOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_REFRESH_INTERVAL,
                    default=options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=30,
                        max=3600,
                        step=10,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
                vol.Optional(
                    CONF_RETRY_BASE_INTERVAL,
                    default=options.get(CONF_RETRY_BASE_INTERVAL, DEFAULT_RETRY_BASE_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15,
                        max=600,
                        step=5,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
                vol.Optional(
                    CONF_RETRY_MAX_INTERVAL,
                    default=options.get(CONF_RETRY_MAX_INTERVAL, DEFAULT_RETRY_MAX_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=60,
                        max=86400,
                        step=30,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class CannotConnect(Exception):
    pass


class InvalidAuth(Exception):
    pass


async def try_connection(email, password):
    _LOGGER.debug("Trying to connect to Centrometal boiler server during setup")
    web_boiler_client = WebBoilerClient(None)
    try:
        await web_boiler_client.login(username=email, password=password)
        got_configuration = await web_boiler_client.get_configuration()
        if not got_configuration or len(web_boiler_client.data) == 0:
            raise CannotConnect
        return web_boiler_client.data
    except HttpClientAuthError as err:
        raise InvalidAuth from err
    except HttpClientConnectionError as err:
        raise CannotConnect from err
    finally:
        with contextlib.suppress(Exception):
            await web_boiler_client.close()
