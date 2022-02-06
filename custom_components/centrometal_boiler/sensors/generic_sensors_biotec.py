from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TIME_MINUTES,
    PERCENTAGE,
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
    "B_Tlo1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Firebox Temperature",
    ],
    "B_Tptv1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Domestic Hot Water",
    ],
    "C1B_Tpol": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Circuit 1 Target Temperature",
    ],
    "C1B_Tpol1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Circuit 1 Measured Temperature",
    ],
    "C1B_Tsob": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Room Target Temperature",
    ],
    "C1B_Tsob1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Room Measured Temperature",
    ],
    "C1B_kor": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Room Target Correction",
    ],
}

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
    "B_cm2k": [None, "mdi:state-machine", None, "CM2K Status"],
    "B_P1": [None, "mdi:pump", None, "Boiler Pump"],
    "B_zahP1": [None, "mdi:pump", None, "Boiler Pump Demand"],
    "B_P2": [None, "mdi:pump", None, "Second Pump"],
    "B_zahP2": [None, "mdi:pump", None, "Second Pump Demand"],
    "B_P3": [None, "mdi:pump", None, "Third Pump"],
    "B_zahP3": [None, "mdi:pump", None, "Third Pump Demand"],
    "C1B_P": [None, "mdi:pump", None, "Circuit 1 Pump"],
    "C1B_onOff": [None, "mdi:pump", None, "Circuit 1 Pump Demand"],
    "B_priS": [PERCENTAGE, "mdi:air-filter", None, "Air Flow Engine Primary"],
    "B_secS": [PERCENTAGE, "mdi:air-filter", None, "Air Flow Engine Secondary"],
    "B_zar": [None, "mdi:campfire", None, "Glow"],
    "C1B_CircType": [None, "mdi:view-list", None, "Circuit 1 Type"],
    "C1B_korType": [None, "mdi:view-list", None, "Circuit 1 Correction Type"],
    "C1B_dayNight": [None, "mdi:view-list", None, "Circuit 1 Day Night Mode"],
    "B_korNum": [None, "mdi:counter", None, "Accessories Value"],
    "B_zlj": [None, "mdi:book-open", None, "Operation Mode"],
}

BIOTEC_GENERIC_SENSORS = {
    **BIOTEC_SENSOR_TEMPERATURES,
    **BIOTEC_SENSOR_COUNTERS,
    **BIOTEC_SENSOR_MISC,
}
