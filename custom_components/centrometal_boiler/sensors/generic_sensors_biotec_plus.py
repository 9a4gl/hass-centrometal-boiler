from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TIME_MINUTES,
    PERCENTAGE,
)

BIOTEC_PLUS_SENSOR_TEMPERATURES = {
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
    "B_Tk1b": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Boiler Temperature Wood",
    ],
    "B_Tk1p": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Boiler Temperature Pellet",
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
    "B_Ths1": [
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        "Hydraulic Crossover Temperature",
    ],
}

BIOTEC_PLUS_SENSOR_COUNTERS = {
    "CNT_0": [TIME_MINUTES, "mdi:timer", None, "Operation Wood"],
    "CNT_1": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Operation Pellets",
    ],
    "CNT_2": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Pellets D6",
    ],
    "CNT_3": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Pellets D5",
    ],
    "CNT_4": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Pellets D4",
    ],
    "CNT_5": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Pellets D3",
    ],
    "CNT_6": [
        TIME_MINUTES,
        "mdi:timer",
        None,
        "Pellets D2",
    ],
    "CNT_7": [
        "",
        "mdi:counter",
        None,
        "Startup Wood",
    ],
    "CNT_8": ["", "mdi:counter", None, "Startup Pellets"],
    "CNT_9": [TIME_MINUTES, "mdi:timer", None, "DHW And Heating Time"],
    "CNT_10": [TIME_MINUTES, "mdi:timer", None, "DHW Only Time"],
    "CNT_11": [TIME_MINUTES, "mdi:timer", None, "Fan Time"],
    "CNT_12": [TIME_MINUTES, "mdi:timer", None, "Heater Time"],
    "CNT_13": ["", "mdi:counter", None, "Heater Start"],
    "CNT_14": [TIME_MINUTES, "mdi:timer", None, "Screw Feeder Time"],
    "CNT_15": [None, "mdi:counter", None, "Grate Cleaning"],
}

BIOTEC_PLUS_SENSOR_MISC = {
    "B_fan": ["rpm", "mdi:fan", None, "Fan"],
    "B_Oxy1": ["% O2", "mdi:gas-cylinder", None, "Lambda Sensor"],
    "B_FotV": ["kOhm", "mdi:fire", None, "Fire Sensor"],
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
    "B_priS": [PERCENTAGE, "mdi:air-filter", None, "Air Flow Engine Primary"],
    "B_secS": [PERCENTAGE, "mdi:air-filter", None, "Air Flow Engine Secondary"],
    "B_zar": [None, "mdi:campfire", None, "Glow"],
    "B_zlj": [None, "mdi:book-open", None, "Operation Mode"],
    "B_gri": [None, "mdi:fire-circle", None, "Electric Heater"],
    "B_puz": [None, "mdi:transfer-up", None, "Pellet Transporter"],
    "B_doz": [None, "mdi:transfer-up", None, "Pellet Dispenzer"],
    "B_pbs": [None, "mdi:pine-tree", None, "Wood Pellet Mode"],
    "B_scs": [None, "mdi:controller-classic", None, "Control Mode"],
}

BIOTEC_PLUS_GENERIC_SENSORS = {
    **BIOTEC_PLUS_SENSOR_TEMPERATURES,
    **BIOTEC_PLUS_SENSOR_COUNTERS,
    **BIOTEC_PLUS_SENSOR_MISC,
}
