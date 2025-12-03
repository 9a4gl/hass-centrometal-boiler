import copy
from generic_sensors_peltec import PELTEC_SENSOR_TEMPERATURES, PELTEC_SENSOR_COUNTERS, PELTEC_SENSOR_MISC

# Make copies of the peltec sensors and remove those not returned by the API for the compact.
# I'm unsure of whether this is because of my configuration (37) or because those really do not exist for the compact.
_misc = copy.deepcopy(PELTEC_SENSOR_MISC)
_misc.pop("B_fan", None)
_misc.pop("B_fanB", None)
_misc.pop("B_FotV", None)
_misc.pop("B_misP", None)

_temps = copy.deepcopy(PELTEC_SENSOR_TEMPERATURES)
_temps.pop("B_Tptv1", None)

COMPACT_GENERIC_SENSORS = {
    **_temps,
    **PELTEC_SENSOR_COUNTERS,
    **_misc,
}
