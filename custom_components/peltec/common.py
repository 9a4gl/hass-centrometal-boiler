from .const import DOMAIN

import homeassistant.util.dt as dt_util
from datetime import datetime


def create_device_info(device):
    power = device["parameters"]["B_sng"]["value"] or "?"
    firmware_ver = device["parameters"]["B_VER"]["value"] or "?"
    wifi_ver = device["parameters"]["B_WifiVER"]["value"] or "?"
    name = "PelTec"
    model = device["product"] + " " + power
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


def formatTime(hass, timestamp, tzinfo=None):
    if tzinfo is None:
        tzinfo = dt_util.get_time_zone(hass.config.time_zone)
    dt = datetime.fromtimestamp(timestamp)
    return dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")
