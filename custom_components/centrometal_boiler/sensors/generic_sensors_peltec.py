from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE, UnitOfTime

PELTEC_SENSOR_TEMPERATURES = {
    "B_Tak1_1": [UnitOfTemperature.CELSIUS, "mdi:thermometer",      SensorDeviceClass.TEMPERATURE, "Puffer Upper"],
    "B_Tak2_1": [UnitOfTemperature.CELSIUS, "mdi:thermometer",      SensorDeviceClass.TEMPERATURE, "Puffer Lower"],
    "B_Tdpl1":  [UnitOfTemperature.CELSIUS, "mdi:thermometer",      SensorDeviceClass.TEMPERATURE, "Flue Gas Temperature"],
    "B_Tpov1":  [UnitOfTemperature.CELSIUS, "mdi:thermometer",      SensorDeviceClass.TEMPERATURE, "Return Flow Temperature"],
    "B_Tk1":    [UnitOfTemperature.CELSIUS, "mdi:thermometer",      SensorDeviceClass.TEMPERATURE, "Core Temperature"],
    "B_Tptv1":  [UnitOfTemperature.CELSIUS, "mdi:water-thermometer", SensorDeviceClass.TEMPERATURE, "DHW Flow Temperature"],
    "B_Tkm1":   [UnitOfTemperature.CELSIUS, "mdi:water-boiler",     SensorDeviceClass.TEMPERATURE, "DHW Boiler Temperature"],
    "B_Ths1":   [UnitOfTemperature.CELSIUS, "mdi:thermometer",      SensorDeviceClass.TEMPERATURE, "Hydraulic Crossover Temperature"],
    "B_Tva1":   [UnitOfTemperature.CELSIUS, "mdi:thermometer-auto", SensorDeviceClass.TEMPERATURE, "Outside Temperature"],
}

PELTEC_SENSOR_COUNTERS = {
    "CNT_0":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Burner Work"],
    "CNT_1":  [None,               "mdi:counter", None, "Number of Burner Starts"],
    "CNT_2":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Feeder Screw Work"],
    "CNT_3":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Flame Duration"],
    "CNT_4":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Fan Working Time"],
    "CNT_5":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Electric Heater Working Time"],
    "CNT_6":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Vacuum Turbine Working Time"],
    "CNT_7":  [None,               "mdi:counter", None, "Vacuum Turbine Cycles Number"],
    "CNT_8":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Time on D6"],
    "CNT_9":  [UnitOfTime.MINUTES, "mdi:timer",   None, "Time on D5"],
    "CNT_10": [UnitOfTime.MINUTES, "mdi:timer",   None, "Time on D4"],
    "CNT_11": [UnitOfTime.MINUTES, "mdi:timer",   None, "Time on D3"],
    "CNT_12": [UnitOfTime.MINUTES, "mdi:timer",   None, "Time on D2"],
    "CNT_13": [UnitOfTime.MINUTES, "mdi:timer",   None, "Time on D1"],
    "CNT_14": [UnitOfTime.MINUTES, "mdi:timer",   None, "Time on D0"],
    "CNT_15": [None,               "mdi:counter", None, "Reserve Counter"],
}

PELTEC_SENSOR_MISC = {
    "B_fan":    ["rpm",      "mdi:fan",           None, "Fan Speed"],
    "B_fanB":   ["rpm",      "mdi:fan",           None, "Fan B Speed"],
    "B_Oxy1":   [PERCENTAGE, "mdi:chart-bell-curve", None, "Lambda Probe Reading"],
    "B_FotV":   ["kOhm",    "mdi:fire-alert",     None, "Fire Sensor"],
    "B_misP":   [PERCENTAGE, "mdi:pipe-valve",    None, "Mixing Valve"],
    "B_razP":   [PERCENTAGE, "mdi:grain",         None, "Pelet Level"],
    "B_signal": [PERCENTAGE, "mdi:wifi",          None, "WiFi Signal"],
    "B_puz":    [None, "mdi:transfer-up",         None, "Pellet Transporter"],
    "B_cm2k":   [None, "mdi:state-machine",       None, "CM2K Status"],
    "B_addConf":[None, "mdi:note-plus",           None, "Accessories"],
    "B_korNum": [None, "mdi:counter",             None, "Working Phase"],
    "B_zlj":    [None, "mdi:book-open",           None, "Operation Mode"],
    "B_FILE":   [None, "mdi:file-cog",            None, "Firmware File"],
    "B_fireS":  [None, "mdi:fire",                None, "Flame State"],
    "B_zahPa":  [None, "mdi:pump",                None, "Additional Pump Active"],
    "B_Valve":  [None, "mdi:pipe-valve",          None, "Valve State"],
    "B_P2":     [None, "mdi:pump",                None, "Pump 2"],
    "B_P3":     [None, "mdi:pump",                None, "Pump 3"],
    "B_P4":     [None, "mdi:pump",                None, "Pump 4"],
    "B_Paku":   [None, "mdi:pump",                None, "Accumulator Pump"],
    "B_Pk1_k2": [None, "mdi:pump",               None, "K1/K2 Pump"],
    "B_VAC_STS":[None, "mdi:vacuum",             None, "Vacuum Status"],
    "B_VAC_TUR":[None, "mdi:vacuum",             None, "Vacuum Turbine"],
    "B_razina": [None, "mdi:basket-fill",         None, "Tank Level"],
    "B_SUP_TYPE":[None, "mdi:view-list",          None, "Supply Type"],
    "B_PTV/GRI":[None, "mdi:fire",               None, "DHW / Heater"],
    "B_PTV/GRI_SEL":[None, "mdi:view-list",      None, "DHW / Heater Select"],
    "B_dop":    [None, "mdi:plus-circle",         None, "Additional Heating"],
    "B_doz":    [None, "mdi:fuel",                None, "Fuel Dosing"],
    "B_specG":  [None, "mdi:fire-circle",         None, "Special Combustion"],
    "B_start":  [None, "mdi:play-circle",         None, "Start Signal"],
    "B_ODRTMP": [UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE, "Defrost Temperature"],
}

PELTEC_GENERIC_SENSORS = {
    **PELTEC_SENSOR_TEMPERATURES,
    **PELTEC_SENSOR_COUNTERS,
    **PELTEC_SENSOR_MISC,
}
