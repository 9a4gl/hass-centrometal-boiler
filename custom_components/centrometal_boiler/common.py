from datetime import datetime

from homeassistant.core import HomeAssistant
import homeassistant.util.dt as dt_util

from .const import DOMAIN, WEB_BOILER_CLIENT, WEB_BOILER_SYSTEM


def create_device_info(device) -> dict:
    param_power = device.get_parameter("B_sng")
    param_fw_ver = device.get_parameter("B_VER")
    power = param_power["value"] or "None"
    firmware_ver = param_fw_ver["value"] or "None"
    model = device["product"] + " " + power
    serial = device["serial"]
    name = "Centrometal Boiler " + model + " " + serial
    return {
        "identifiers": {(DOMAIN, device["serial"])},
        "name": name,
        "manufacturer": "Centrometal",
        "model": model,
        "sw_version": firmware_ver,
    }


def format_time(hass: HomeAssistant, timestamp, tzinfo=None):
    if tzinfo is None:
        tzinfo = dt_util.get_time_zone(hass.config.time_zone)
    dt = datetime.fromtimestamp(timestamp)
    return dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")


def format_name(hass: HomeAssistant, device, name) -> str:
    name = name.replace("GMX EASY", "biotec")
    username = device.username
    serial = device["serial"]
    web_boiler_client = hass.data[DOMAIN][username][WEB_BOILER_CLIENT]
    web_boiler_system = hass.data[DOMAIN][username][WEB_BOILER_SYSTEM]
    if len(web_boiler_client.data.values()) > 1:
        name = f"{serial} {name}"
    if len(web_boiler_system.prefix) > 0:
        return f"{web_boiler_system.prefix} {name}"
    return name
