from __future__ import annotations

import datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
import homeassistant.util.dt as dt_util

from .const import DOMAIN


def create_device_info(device) -> DeviceInfo:
    param_power = device.get_parameter("B_sng")
    param_fw_ver = device.get_parameter("B_VER")
    power = param_power.get("value") or "None"
    firmware_ver = param_fw_ver.get("value") or "None"
    model = f"{device['product']} {power}"
    serial = device["serial"]
    name = f"Centrometal Boiler {model} {serial}"
    return DeviceInfo(
        identifiers={(DOMAIN, serial)},
        name=name,
        manufacturer="Centrometal",
        model=model,
        sw_version=firmware_ver,
        configuration_url="https://www.web-boiler.com",
    )


def format_time(hass: HomeAssistant, timestamp, tzinfo=None) -> str:
    if tzinfo is None:
        tzinfo = dt_util.get_time_zone(hass.config.time_zone)
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    return dt.astimezone(tzinfo).strftime("%d.%m.%Y %H:%M:%S")


def format_name(hass: HomeAssistant, device, name) -> str:
    name = name.replace("GMX EASY", "biotec")
    serial = device["serial"]
    if device.get("__multi_device"):
        name = f"{serial} {name}"
    prefix = device.get("__prefix", "")
    if prefix:
        return f"{prefix}{name}"
    return name
