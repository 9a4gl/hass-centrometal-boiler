from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime


PELTEC_SENSOR_TEMPERATURES = {
    "B_Tak1_1": [
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer",
        SensorDeviceClass.TEMPERATURE,
        "Buffer Tank Temperature (Upper)",
    ],
    "B_Tak2_1": [
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer",
        SensorDeviceClass.TEMPERATURE,
        "Buffer Tank Temperature (Lower)",
    ],
    "B_Tdpl1": [
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer",
        SensorDeviceClass.TEMPERATURE,
        "Flue Gas Temperature",
    ],
    "B_Tpov1": [
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer",
        SensorDeviceClass.TEMPERATURE,
        "Boiler Return Temperature",
    ],
    "B_Tk1": [
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer",
        SensorDeviceClass.TEMPERATURE,
        "Boiler Temperature",
    ],
    "B_Tkm1": [
        UnitOfTemperature.CELSIUS,
        "mdi:water-boiler",
        SensorDeviceClass.TEMPERATURE,
        "DHW Tank Temperature",
    ],
    "B_Ths1": [
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer",
        SensorDeviceClass.TEMPERATURE,
        "Hydraulic Crossover Temperature",
    ],
    "B_Tva1": [
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer-auto",
        SensorDeviceClass.TEMPERATURE,
        "Outside Temperature",
    ],
}


PELTEC_SENSOR_COUNTERS = {
    "CNT_0": [UnitOfTime.MINUTES, "mdi:timer", None, "Boiler Work + Standby Time"],
    "CNT_1": [None, "mdi:counter", None, "Number of Burner Starts"],
    "CNT_2": [UnitOfTime.MINUTES, "mdi:timer", None, "Feeder Screw Work"],
    "CNT_3": [UnitOfTime.MINUTES, "mdi:timer", None, "Flame Duration"],
    "CNT_4": [UnitOfTime.MINUTES, "mdi:timer", None, "Fan Working Time"],
    "CNT_5": [UnitOfTime.MINUTES, "mdi:timer", None, "Electric Heater Working Time"],
    "CNT_6": [UnitOfTime.MINUTES, "mdi:timer", None, "Vacuum Turbine Working Time"],
    "CNT_7": [None, "mdi:counter", None, "Vacuum Turbine Cycles"],
    "CNT_8": [UnitOfTime.MINUTES, "mdi:timer", None, "Time on D6"],
    "CNT_9": [UnitOfTime.MINUTES, "mdi:timer", None, "Time on D5"],
    "CNT_10": [UnitOfTime.MINUTES, "mdi:timer", None, "Time on D4"],
    "CNT_11": [UnitOfTime.MINUTES, "mdi:timer", None, "Time on D3"],
    "CNT_12": [UnitOfTime.MINUTES, "mdi:timer", None, "Time on D2"],
    "CNT_13": [UnitOfTime.MINUTES, "mdi:timer", None, "Time on D1"],
    "CNT_14": [UnitOfTime.MINUTES, "mdi:timer", None, "Time on D0"],
    "CNT_15": [UnitOfTime.MINUTES, "mdi:timer", None, "Boiler Work Time"],
}


# PelTec II entities are intentionally restricted to fields whose meaning and
# display rules are confirmed by the authenticated Centrometal portal capture.
# Helper fields such as B_addConf, B_Inp1 and B_cm2k are consumed internally
# but are not exposed as raw entities.
PELTEC2_PORTAL_SENSORS = {
    "B_Oxy1": [PERCENTAGE, "mdi:chart-bell-curve", None, "Lambda Probe"],
    "B_razP": [PERCENTAGE, "mdi:grain", None, "Pellet Level"],
    "B_signal": ["dB", "mdi:wifi", None, "WiFi Signal"],
    "B_FILE": [None, "mdi:file-cog", None, "Active File"],
    "B_fireS": [None, "mdi:fire", None, "Flame State"],
    "B_P1": [None, "mdi:pump", None, "P1 Pump"],
    "B_P2": [None, "mdi:pump", None, "P2 Pump"],
    "B_P3": [None, "mdi:pump", None, "P3 Pump"],
    "B_P4": [None, "mdi:pump", None, "P4 Pump"],
    "B_gri": [None, "mdi:radiator", None, "Electric Heater"],
    "B_zahPpwm": [None, "mdi:pump", None, "PWM Pump Demand"],
    "B_VAC_TUR": [None, "mdi:vacuum", None, "Vacuum Turbine"],
    "B_razina": [None, "mdi:basket-fill", None, "Fuel Level State"],
    "B_SUP_TYPE": [None, "mdi:lan-connect", None, "Internet Access"],
    "B_specG": [None, "mdi:alpha-s-circle", None, "Status Mark"],
    "B_start": [None, "mdi:play-pause", None, "Start / Stop Transition"],
    "B_FotV": ["kΩ", "mdi:fire-alert", None, "Photocell Resistance"],
    "B_fan": ["rpm", "mdi:fan", None, "Fan Speed"],
    "B_misP": [PERCENTAGE, "mdi:pipe-valve", None, "4-Way Mixing Valve Position"],
    "B_puz": [None, "mdi:transfer-up", None, "Feeder Screw"],
    "B_tur": [None, "mdi:fan-chevron-up", None, "Turbulator Cleaner"],
    "B_PTV_PRI": [None, "mdi:priority-high", None, "DHW Priority"],
    "B_bup": [None, "mdi:heat-wave", None, "Buffer Tank Heat Request"],
    "B_REC": [None, "mdi:autorenew", None, "DHW Recirculation Enabled"],
    "B_REO": [None, "mdi:pump", None, "DHW Recirculation Pump"],
}


# Legacy PelTec mappings retained for non-PelTec-II installations. These are
# not used to create entities for PelTec II.
PELTEC_LEGACY_EXTRA_SENSORS = {
    "B_cm2k": [None, "mdi:counter", None, "CM2K Module Count"],
    "B_addConf": [None, "mdi:code-braces", None, "Accessory Bitmask"],
    "B_Inp1": [None, "mdi:code-braces", None, "Input Bitmask"],
    "B_zahPa": [None, "mdi:pump", None, "Additional Pump Demand"],
    "B_zahK1_K2": [None, "mdi:pump", None, "K1/K2 Pump Demand"],
    "B_zahValve": [None, "mdi:pipe-valve", None, "Valve Demand"],
    "B_fan": [None, "mdi:fan", None, "Fan Speed"],
    "B_fanB": [None, "mdi:fan", None, "Fan B Speed"],
    "B_FotV": [None, "mdi:fire-alert", None, "Fire Sensor"],
    "B_misP": [None, "mdi:pipe-valve", None, "Mixing Valve"],
    "B_puz": [None, "mdi:transfer-up", None, "Pellet Transporter"],
    "B_Paku": [None, "mdi:pump", None, "Accumulator Pump"],
    "B_Pk1_k2": [None, "mdi:pump", None, "K1/K2 Pump"],
    "B_Valve": [None, "mdi:pipe-valve", None, "Valve State"],
    "B_VAC_STS": [None, "mdi:vacuum", None, "Vacuum Status"],
    "B_PTV/GRI": [None, "mdi:fire", None, "DHW / Heater"],
    "B_dop": [None, "mdi:plus-circle", None, "Additional Heating"],
    "B_doz": [None, "mdi:fuel", None, "Fuel Dosing"],
    "B_ODRTMP": [None, "mdi:thermometer", None, "Defrost Temperature"],
    "B_Tptv1": [None, "mdi:water-thermometer", None, "DHW Temperature"],
    "B_REC": [None, "mdi:autorenew", None, "DHW Recirculation Active"],
    "B_REO": [None, "mdi:pump", None, "DHW Recirculation Pump"],
    "B_tur": [None, "mdi:fan-chevron-up", None, "Turbulator"],
    "B_vanjS": [None, "mdi:thermometer-lines", None, "Outdoor Sensor Connected"],
    "B_Out1": [None, "mdi:export", None, "Auxiliary Output 1"],
    "B_bim": [None, "mdi:thermometer-alert", None, "Bimetal Overheat Sensor"],
    "B_MPC": [None, "mdi:gauge", None, "Configured Maximum Power"],
    "B_MPO": [None, "mdi:gauge-full", None, "Output Maximum Power"],
    "B_HS_AKU": [None, "mdi:valve", None, "Hydraulic Separator / Buffer Config"],
    "B_pres": [None, "mdi:gauge", None, "Pressure Sensor"],
    "B_ashC": [None, "mdi:tray-alert", None, "Ash Screw Active"],
    "B_ashSc": [None, "mdi:calendar-clock", None, "Ash Cleaner"],
    "B_bup": [None, "mdi:pump", None, "Buffer Tank Heat Request"],
    "B_rpm": [None, "mdi:speedometer", None, "Motor Speed"],
    "B_PTV_PRI": [None, "mdi:priority-high", None, "DHW Priority"],
    "B_PTV/GRI_SEL": [None, "mdi:view-list", None, "DHW / Heater Select"],
    "B_korNum": [None, "mdi:counter", None, "Working Phase"],
    "B_zlj": [None, "mdi:book-open", None, "Log"],
}


# Backward-compatible legacy misc table used by the Compact boiler mapping.
PELTEC_SENSOR_MISC = {
    **PELTEC2_PORTAL_SENSORS,
    **PELTEC_LEGACY_EXTRA_SENSORS,
}


PELTEC2_GENERIC_SENSORS = {
    **PELTEC_SENSOR_TEMPERATURES,
    **PELTEC_SENSOR_COUNTERS,
    **PELTEC2_PORTAL_SENSORS,
}


PELTEC_GENERIC_SENSORS = {
    **PELTEC2_GENERIC_SENSORS,
    **PELTEC_LEGACY_EXTRA_SENSORS,
}
