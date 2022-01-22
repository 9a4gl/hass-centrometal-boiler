from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TIME_MINUTES,
)

BIOTEC_SENSOR_TEMPERATURES = {
    "B_Tak1_1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Temparature Up",
    ],
    "B_Tak2_1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Buffer Tank Temparature Down",
    ],
    "B_Tdpl1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Flue Gas",
    ],
    "B_Tpov1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Mixer Temperature",
    ],
    "B_Tk1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Boiler Temperature",
    ],
}

# B_Tlo1 - Firebox temperature
# B_priS - Air Flow Engine Primary
# B_secS - Air Flow Engine Secondary
# B_Tptv1 - Domestic Hot Water
# C1B_Tpol - Circuit 1 Target Temperature
# C1B_Tpol1 - Circuit 1 Measured Temperature
# C1B_Tsob - Room Target Temperature
# C1B_Tsob1 - Room Measured Temperature
# C1B_kor - Room Target Correction
# C1B_korType - Room Target Correction Type
# C1B_CircType, C1B_P, C1B_onOff ?

BIOTEC_SENSOR_COUNTERS = {
    "CNT_0": [TIME_MINUTES, "mdi:timer", None, "Burner Work"],
    "CNT_4": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Fan Working Time",
    ],
}

BIOTEC_SENSOR_MISC = {
    "B_fan": ["rpm", "mdi:fan", None, "Fan"],
    "B_Oxy1": ["% O2", "mdi:gas-cylinder", None, "Lambda Sensor"],
    "B_Tva1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Outdoor Temperature",
    ],
    "B_cm2k": ["", "mdi:state-machine", None, "CM2K Status"],
    "B_P1": ["", "mdi:pump", None, "Boiler Pump"],
    "B_zahP1": ["", "mdi:pump", None, "Boiler Pump Demand"],
}

BIOTEC_GENERIC_SENSORS = {
    **BIOTEC_SENSOR_TEMPERATURES,
    **BIOTEC_SENSOR_COUNTERS,
    **BIOTEC_SENSOR_MISC,
}
