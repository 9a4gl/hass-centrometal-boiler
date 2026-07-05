"""Tests for suggested_display_precision.

Home Assistant's own sensor entity code treats ANY entity with
suggested_display_precision set as "must be numeric" and raises ValueError
on the next .state access if native_value isn't coercible to a number --
verified directly against homeassistant/components/sensor/__init__.py's
_numeric_state_expected() and state property, independent of unit or
state_class. So beyond checking the property's return value in isolation,
these tests also call the real .state property (the actual code path Home
Assistant runs on every update) for every text-returning parameter, to
prove none of them can ever hit that ValueError.

Note: while writing these tests, it turned out a real unit (or a
TEMPERATURE device class) ALREADY independently triggers the same
numeric-state requirement, with or without suggested_display_precision --
so the actual protection against a text-returning sensor crashing is that
no table entry for one has a unit or TEMPERATURE device class, not
anything suggested_display_precision's own logic does. That invariant is
covered directly below.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.centrometal_boiler.sensors.WebBoilerGenericSensor import (  # noqa: E402
    WebBoilerGenericSensor,
)
from custom_components.centrometal_boiler.sensors.generic_sensors_peltec import (  # noqa: E402
    PELTEC2_GENERIC_SENSORS,
    PELTEC_GENERIC_SENSORS,
)
from custom_components.centrometal_boiler.centrometal_web_boiler.WebBoilerDeviceCollection import (  # noqa: E402
    WebBoilerDevice,
)

# Minimal stand-in so SensorEntity.state's temperature-unit-conversion branch
# (self.hass.config.units.temperature_unit) doesn't crash on a bare `None`
# hass -- unrelated to what these tests actually check.
_FAKE_HASS = SimpleNamespace(config=SimpleNamespace(units=SimpleNamespace(temperature_unit="°C")))


def _make_device() -> WebBoilerDevice:
    device = WebBoilerDevice("t")
    device["id"] = 1
    device["serial"] = "SN"
    device["place"] = "P"
    device["address"] = "A"
    device["type"] = "peltec2"
    device["product"] = "PelTec II Lambda"
    device["__client"] = None
    device["__system"] = None
    device["__prefix"] = ""
    device["__multi_device"] = False
    return device


def _sensor_for(code: str, value) -> WebBoilerGenericSensor:
    device = _make_device()
    device.create_parameter(code, value)
    sensor_data = PELTEC2_GENERIC_SENSORS.get(code, PELTEC_GENERIC_SENSORS[code])
    return WebBoilerGenericSensor(_FAKE_HASS, device, sensor_data, device.get_parameter(code))


def test_peltec2_temperature_sensor_gets_one_decimal() -> None:
    assert _sensor_for("B_Tak1_1", 26.0).suggested_display_precision == 1


def test_peltec2_temperature_setpoint_has_no_measurement_state_class() -> None:
    device = _make_device()
    device.create_parameter("K1B_Tpol", 50)
    sensor_data = ["°C", "mdi:thermometer", "temperature", "K1 Flow Target Temperature"]
    sensor = WebBoilerGenericSensor(_FAKE_HASS, device, sensor_data, device.get_parameter("K1B_Tpol"))
    assert sensor.state_class is None


def test_signal_sensor_gets_zero_decimals() -> None:
    assert _sensor_for("B_signal", 0).suggested_display_precision == 0


def test_pellet_percentage_sensor_gets_zero_decimals() -> None:
    assert _sensor_for("B_razP", 87).suggested_display_precision == 0


def test_lambda_sensor_gets_one_decimal() -> None:
    assert _sensor_for("B_Oxy1", 12.5).suggested_display_precision == 1


def test_new_numeric_peltec2_sensors_use_expected_precision() -> None:
    assert _sensor_for("B_FotV", 1001).suggested_display_precision == 0
    assert _sensor_for("B_fan", 1200).suggested_display_precision == 0
    assert _sensor_for("B_misP", 12.5).suggested_display_precision == 1


def test_event_count_counter_gets_zero_decimals() -> None:
    assert _sensor_for("CNT_1", 12).suggested_display_precision == 0


def test_minute_duration_counter_also_gets_zero_decimals() -> None:
    # Diverges from the pasted proposal deliberately: a runtime-minutes
    # counter is just as much a whole number as an event count, so it gets
    # 0 decimals too, not 2.
    assert _sensor_for("CNT_3", 142).suggested_display_precision == 0


def test_text_returning_sensors_get_no_precision() -> None:
    text_returning_examples = {
        "B_fireS": 1,
        "B_gri": 1,
        "B_razina": 2,
        "B_SUP_TYPE": 1,
        "B_specG": 5,
        "B_start": 1,
        "B_puz": 1,
        "B_tur": 1,
    }
    for code, value in text_returning_examples.items():
        sensor = _sensor_for(code, value)
        assert sensor.suggested_display_precision is None, code


def test_status_sensor_without_unit_or_state_class_gets_no_precision() -> None:
    # A generic status-style sensor: no unit, no state class -> None.
    assert _sensor_for("B_FILE", "USR:PelTec II").suggested_display_precision is None


def test_no_text_returning_parameter_can_ever_trigger_ha_numeric_validation() -> None:
    """The actual safety net: call the real .state property (Home
    Assistant's own validation path) for every text-returning parameter and
    confirm none of them raise -- not just that suggested_display_precision
    returns None for them in isolation."""
    text_returning_params = (
        WebBoilerGenericSensor._YES_NO_PARAMS
        | WebBoilerGenericSensor._ON_OFF_PARAMS
        | WebBoilerGenericSensor._VALVE_PARAMS
        | {"B_razina", "B_SUP_TYPE"}
    )
    checked = 0
    for code in text_returning_params:
        if code not in PELTEC_GENERIC_SENSORS:
            continue
        sensor = _sensor_for(code, 1)
        sensor.state  # must not raise ValueError
        checked += 1
    assert checked > 0  # sanity check that this actually exercised something


def test_representative_numeric_sensors_state_property_does_not_raise() -> None:
    """Same real-code-path check for the numeric side: precision must not
    break normal numeric sensors either."""
    for code, value in {"B_Tak1_1": 26.0, "B_signal": -67, "CNT_1": 12, "CNT_3": 142}.items():
        sensor = _sensor_for(code, value)
        sensor.state  # must not raise


def test_no_text_returning_parameter_has_a_unit_or_temperature_class_in_any_table() -> None:
    """This is the invariant that actually matters, made permanent.

    Investigating a false lead while writing these tests turned up something
    more fundamental than a suggested_display_precision edge case: a unit
    (or a TEMPERATURE device class, which forces state_class via this file's
    own state_class property) ALREADY makes Home Assistant expect a numeric
    value, completely independent of suggested_display_precision --
    verified directly: giving a text-returning parameter a real unit still
    crashes .state even with suggested_display_precision correctly
    returning None for it. So the actual protection against a
    Yes/No/On/Off/Open-Closed sensor crashing isn't anything in
    suggested_display_precision's own logic -- it's that no table entry for
    a text-returning code has ever been given a unit or a TEMPERATURE
    device class. That was previously verified only ad hoc while writing
    the parameter-naming pass; this makes it a permanent, CI-enforced
    invariant instead of something that has to be re-checked by hand every
    time a table changes.
    """
    from custom_components.centrometal_boiler.sensors.generic_sensors_all import (
        GENERIC_SENSORS_COMMON,
    )
    from custom_components.centrometal_boiler.sensors.generic_sensors_biotec import (
        BIOTEC_GENERIC_SENSORS,
    )
    from custom_components.centrometal_boiler.sensors.generic_sensors_biotec_plus import (
        BIOTEC_PLUS_GENERIC_SENSORS,
    )
    from custom_components.centrometal_boiler.sensors.generic_sensors_cm_pelet_set import (
        CM_PELET_SET_GENERIC_SENSORS,
    )
    from custom_components.centrometal_boiler.sensors.generic_sensors_compact import (
        COMPACT_GENERIC_SENSORS,
    )
    from homeassistant.components.sensor import SensorDeviceClass

    text_returning_params = (
        WebBoilerGenericSensor._YES_NO_PARAMS
        | WebBoilerGenericSensor._ON_OFF_PARAMS
        | WebBoilerGenericSensor._VALVE_PARAMS
        | {"B_razina", "B_SUP_TYPE"}
    )
    tables = {
        "common": GENERIC_SENSORS_COMMON,
        "peltec": PELTEC_GENERIC_SENSORS,
        "biotec": BIOTEC_GENERIC_SENSORS,
        "biotec_plus": BIOTEC_PLUS_GENERIC_SENSORS,
        "cm_pelet_set": CM_PELET_SET_GENERIC_SENSORS,
        "compact": COMPACT_GENERIC_SENSORS,
    }

    checked = 0
    for table_name, table in tables.items():
        for code in text_returning_params:
            if code not in table:
                continue
            unit, _icon, device_class = table[code][0], table[code][1], table[code][2]
            checked += 1
            assert unit is None, (
                f"{table_name}:{code} is text-returning but has unit={unit!r} -- "
                "this WILL crash Home Assistant's numeric-state validation"
            )
            assert device_class != SensorDeviceClass.TEMPERATURE, (
                f"{table_name}:{code} is text-returning but has a TEMPERATURE "
                "device class, which forces state_class and WILL crash "
                "Home Assistant's numeric-state validation"
            )
    assert checked > 0  # sanity check that this actually exercised something
