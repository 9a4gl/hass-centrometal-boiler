from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TIME_MINUTES,
    PERCENTAGE,
)

PELTEC_SENSOR_TEMPERATURES = {
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
    "B_Tptv1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Domestic Hot Water",
    ],
    "B_Ths1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Hydraulic Crossover Temperature",
    ],
}

PELTEC_SENSOR_COUNTERS = {
    "CNT_0": [TIME_MINUTES, "mdi:timer", None, "Burner Work"],
    "CNT_1": [
        "",
        "mdi:counter",
        None,
        "Number of Burner Start",
    ],
    "CNT_2": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Feeder Screw Work",
    ],
    "CNT_3": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Flame Duration",
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
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Vacuum Turbine Working Time",
    ],
    "CNT_7": [
        "",
        "mdi:counter",
        None,
        "Vacuum Turbine Cycles Number",
    ],
    "CNT_8": [TIME_MINUTES, "mdi:timer", None, "Time on D6"],
    "CNT_9": [TIME_MINUTES, "mdi:timer", None, "Time on D5"],
    "CNT_10": [TIME_MINUTES, "mdi:timer", None, "Time on D4"],
    "CNT_11": [TIME_MINUTES, "mdi:timer", None, "Time on D3"],
    "CNT_12": [TIME_MINUTES, "mdi:timer", None, "Time on D2"],
    "CNT_13": [TIME_MINUTES, "mdi:timer", None, "Time on D1"],
    "CNT_14": [TIME_MINUTES, "mdi:timer", None, "Time on D0"],
    "CNT_15": [None, "mdi:counter", None, "Reserve Counter"],
}

PELTEC_SENSOR_MISC = {
    "B_fan": ["rpm", "mdi:fan", None, "Fan"],
    "B_fanB": ["rpm", "mdi:fan", None, "Fan B"],
    "B_Oxy1": ["% O2", "mdi:gas-cylinder", None, "Lambda Sensor"],
    "B_FotV": ["kOhm", "mdi:fire", None, "Fire Sensor"],
    "B_Tva1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Outdoor Temperature",
    ],
    "B_cm2k": [None, "mdi:state-machine", None, "CM2K Status"],
    "B_misP": [PERCENTAGE, "mdi:pipe-valve", None, "Mixing Valve"],
    "B_P1": [None, "mdi:pump", None, "Boiler Pump"],
    "B_zahP1": [None, "mdi:pump", None, "Boiler Pump Demand"],
    "B_gri": [None, "mdi:fire-circle", None, "Electric Heater"],
    "B_puz": [None, "mdi:transfer-up", None, "Pellet Transporter"],
    "B_addConf": [None, "mdi:note-plus", None, "Accessories"],
    "B_korNum": [None, "mdi:counter", None, "Accessories Value"],
    "B_zlj": [None, "mdi:book-open", None, "Operation Mode"],
}

PELTEC_GENERIC_SENSORS = {
    **PELTEC_SENSOR_TEMPERATURES,
    **PELTEC_SENSOR_COUNTERS,
    **PELTEC_SENSOR_MISC,
}
