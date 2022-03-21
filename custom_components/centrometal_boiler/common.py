from .const import DOMAIN, WEB_BOILER_CLIENT, WEB_BOILER_SYSTEM

import homeassistant.util.dt as dt_util
from datetime import datetime


def create_device_info(device):
    param_power = device.get_parameter("B_sng")
    param_fw_ver = device.get_parameter("B_VER")
    param_wifi_ver = device.get_parameter("B_WifiVER")
    power = param_power["value"] or "?"
    firmware_ver = param_fw_ver["value"] or "?"
    wifi_ver = param_wifi_ver["value"] or "?"
    model = device["product"] + " " + power
    name = "Centrometal Boiler " + model
    sw_version = firmware_ver + " Wifi:" + wifi_ver
    return {
        "identifiers": {
            # Serial numbers are unique identifiers within a specific domain
            (DOMAIN, device["serial"])
        },
        "name": name,
        "manufacturer": "Centrometal",
        "model": model,
        "sw_version": sw_version,
    }


def format_time(hass, timestamp, tzinfo=None):
    if tzinfo is None:
        tzinfo = dt_util.get_time_zone(hass.config.time_zone)
    dt = datetime.fromtimestamp(timestamp)
    return dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")


def format_name(hass, device, name):
    username = device.username
    serial = device["serial"]
    web_boiler_client = hass.data[DOMAIN][username][WEB_BOILER_CLIENT]
    web_boiler_system = hass.data[DOMAIN][username][WEB_BOILER_SYSTEM]
    if len(web_boiler_client.data.values()) > 1:
        name = f"{serial} {name}"
    return f"{web_boiler_system.prefix} {name}"
