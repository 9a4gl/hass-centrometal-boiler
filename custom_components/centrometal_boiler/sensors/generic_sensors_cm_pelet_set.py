from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS, TIME_MINUTES

CM_PELET_SET_SENSOR_TEMPERATURES = {
    "B_Tk1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Boiler Temperature",
    ],
    "B_Tak1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Up",
    ],
    "B_Tak2": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Down",
    ],
    "B_Tva1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Outdoor Temperature",
    ],
}

CM_PELET_SET_SENSOR_MISC = {
    "B_KONF_STR": [None, "mdi:information", None, "Setup"],
    "B_netMon": [None, "mdi:remote", None, "Remote Start Enabled"],
    "B_cmsr100": ["", "mdi:information", None, "Pellet Tank Level"],
    "B_Pk": [None, "mdi:pump", None, "Boiler Pump"],
    "B_fan": [None, "mdi:fan", None, "Heater Fan State"],
    "B_gri": [None, "mdi:fire", None, "Heater State"],
    "B_FotV": ["kOhm", "mdi:fire", None, "Fire Sensor"],
    "B_Add": [None, "mdi:note-plus", None, "Additional features"],
    "B_uklKot": [None, "mdi:information", None, "Boiler Operational"],
    "B_CP": [None, "mdi:information", None, "CentroPlus"],
    "CNT_0": [TIME_MINUTES, "mdi:timer", None, "Burner Work"],
    "B_freezEn": [None, "mdi:snowflake", None, "Freeze Guard"],
    "B_freezMon": [None, "mdi:snowflake", None, "Freeze Monitor"],
    "B_zlj": [None, "mdi:book-open", None, "Operation Mode"],
    "CNT_1": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Working DHW only",
    ],
    "CNT_2": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Freeze protection",
    ],
    "CNT_3": [
        "",
        "mdi:counter",
        None,
        "Number of Burner Start",
    ],
    "CNT_4": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Fan Working Time",
    ],
    "CNT_5": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Electric Heater Working Time",
    ],
    "CNT_6": [
        "",
        "mdi:counter",
        None,
        "Number of Electric Heater Start",
    ],
    "CNT_7": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Vacuum Turbine Working Time",
    ],
    "CNT_8": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Boiler pump",
    ],
}

CM_PELET_SET_GENERIC_SENSORS = {
    **CM_PELET_SET_SENSOR_TEMPERATURES,
    **CM_PELET_SET_SENSOR_MISC,
}
