from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
)

CM_PELET_SET_SENSOR_TEMPERATURES = {
    "C2B_Tpol1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Circuit Flow 1 Temperature",
    ],
    "B_Tak1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Temparature Up",
    ],
    "B_Tak2": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Temparature Down",
    ],
    "B_Tva1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Outdoor Temperature",
    ],
}


CM_PELET_SET_SENSOR_MISC = {
    "B_KONF_STR": ["", "mdi:information", None, "Setup"],
    "C1B_CircType": ["", "mdi:information", None, "Heating type"],
    "B_Pk": ["", "mdi:pump", None, "Boiler Pump"],
}

CM_PELET_SET_GENERIC_SENSORS = {
    **CM_PELET_SET_SENSOR_TEMPERATURES,
    **CM_PELET_SET_SENSOR_MISC,
}
