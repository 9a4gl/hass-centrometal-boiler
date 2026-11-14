"""Set up the Centrometal Boiler System integration."""

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PREFIX,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, WEB_BOILER_CLIENT, WEB_BOILER_SYSTEM
from .transport import WebBoilerSystem

PLATFORMS = ["sensor", "switch", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Initialize integration storage."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Load the existing account and set up its entities."""
    username = entry.data[CONF_EMAIL]
    system = WebBoilerSystem(
        username,
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_PREFIX, ""),
        entry.data.get("product_prefix", True),
    )
    accounts = hass.data.setdefault(DOMAIN, {})
    accounts[username] = {WEB_BOILER_SYSTEM: system, WEB_BOILER_CLIENT: system}
    try:
        if not await system.load_configuration():
            raise ConfigEntryNotReady("Centrometal configuration could not be loaded")
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except (Exception, asyncio.CancelledError):
        await system.stop()
        accounts.pop(username, None)
        raise

    async def stop_on_shutdown(_event):
        await system.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_on_shutdown)
    )
    system.start_monitoring()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Stop updates before removing entities and close the account session."""
    accounts = hass.data[DOMAIN]
    username = entry.data[CONF_EMAIL]
    system = accounts[username][WEB_BOILER_SYSTEM]
    await system.pause()
    try:
        unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    except Exception:
        system.start_monitoring()
        raise

    if unloaded:
        await system.stop()
        accounts.pop(username)
    else:
        system.start_monitoring()
    return unloaded
