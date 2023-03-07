from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature

GENERIC_SENSORS_COMMON = {
    "B_STATE": [None, "mdi:state-machine", None, "Boiler State"],
    "B_CMD": [None, "mdi:state-machine", None, "Command Active"],
    "B_BRAND": [None, "mdi:information", None, "Brand"],
    "B_INST": [None, "mdi:information", None, "Installation"],
    "B_PRODNAME": [None, "mdi:information", None, "Product Name"],
    "B_VER": [None, "mdi:information", None, "Firmware Version"],
    "B_WifiVER": [None, "mdi:information", None, "Wifi Box Version"],
    "B_sng": [None, "mdi:information", None, "Nominal Power"],
}


def get_generic_temperature_settings_sensors(device):
    """Returns generic sensors"""
    temperature_settings = dict()
    for value in device["temperatures"].values():
        dbindex = value["dbindex"]
        value_param_name = f"PVAL_{dbindex}_0"
        default_param_name = f"PDEF_{dbindex}_0"
        min_param_name = f"PMIN_{dbindex}_0"
        max_param_name = f"PMAX_{dbindex}_0"
        value_param = (
            device.get_parameter(value_param_name)
            if device.has_parameter(value_param_name)
            else None
        )
        if value_param:
            attributes = dict()
            if device.has_parameter(default_param_name):
                attributes[default_param_name] = "Default"
            if device.has_parameter(min_param_name):
                attributes[min_param_name] = "Minimum"
            if device.has_parameter(max_param_name):
                attributes[max_param_name] = "Maximum"
            temperature_settings[value_param_name] = [
                UnitOfTemperature.CELSIUS,
                "mdi:thermometer",
                SensorDeviceClass.TEMPERATURE,
                value["naslov"],
                attributes,
            ]
    return temperature_settings
