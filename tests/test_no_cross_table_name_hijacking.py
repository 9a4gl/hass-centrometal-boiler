"""Regression tests for a real naming bug found via a user's diagnostics
export: create_binary_state_entities() ran unconditionally for every device
type (no type gating) and claimed B_P1, B_gri, K1B_onOff, and K1B_P before
the device-family-specific tables (biotec/biotec_plus/cm_pelet_set) or the
generic per-circuit mechanism (WebBoilerHeatingCircuitSensor) ever got a
chance to -- entities are claimed on a first-created-wins basis via each
parameter's "used" flag, and create_binary_state_entities always ran first
in sensor.py's setup order.

Concretely, before the fix:
  - B_P1 on a BioTec/BioTec Plus boiler showed "Hot Water Flow" instead of
    that family's own "Boiler Pump".
  - B_gri on a CM Pelet Set boiler showed "Electric Heater" instead of that
    family's own "Heater State".
  - K1B_onOff/K1B_P on any PelTec-family boiler showed "DHW Pump
    Demand"/"DHW Pump State" instead of the generic, circuit-number-based
    "Circuit 1K Pump Demand"/"Circuit 1K Pump" that K2B_/K3B_/K4B_ already
    get via WebBoilerHeatingCircuitSensor -- baking in an installation-
    specific assumption (that circuit K1 is wired for DHW) into what is
    otherwise a purely generic, circuit-numbering convention.

These tests replicate sensor.py's actual entity-creation order (the bug
only manifests in that order -- each piece in isolation looks fine) and
assert the device-appropriate name wins.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.centrometal_boiler.sensors.WebBoilerBinaryOnOffSensor import (  # noqa: E402
    create_binary_state_entities,
)
from custom_components.centrometal_boiler.sensors.WebBoilerGenericSensor import (  # noqa: E402
    WebBoilerGenericSensor,
)
from custom_components.centrometal_boiler.sensors.WebBoilerHeatingCircuitSensor import (  # noqa: E402
    WebBoilerHeatingCircuitSensor,
)
from custom_components.centrometal_boiler.centrometal_web_boiler.WebBoilerDeviceCollection import (  # noqa: E402
    WebBoilerDevice,
)


def _make_device(device_type: str, product: str) -> WebBoilerDevice:
    device = WebBoilerDevice("user@example.com")
    device["id"] = 1
    device["serial"] = "SN"
    device["place"] = "P"
    device["address"] = "A"
    device["type"] = device_type
    device["product"] = product
    device["__client"] = None
    device["__system"] = None
    device["__prefix"] = ""
    device["__multi_device"] = False
    return device


def _run_sensor_setup_order(device) -> list:
    """Replicate sensor.py's actual creation order for the pieces relevant
    to this bug -- the conflict only exists in this specific order."""
    entities = []
    entities.extend(create_binary_state_entities(None, device))
    entities.extend(WebBoilerHeatingCircuitSensor.create_heating_circuits_entities(None, device))
    entities.extend(WebBoilerGenericSensor.create_conf_entities(None, device))
    return entities


def _name_for(entities, param_name: str) -> str | None:
    for e in entities:
        if getattr(e, "_param_name", None) == param_name:
            return e._name
    return None


def test_biotec_boiler_pump_keeps_its_own_name_not_hot_water_flow() -> None:
    device = _make_device("biotec", "BioTec")
    device.create_parameter("B_P1", 1)
    entities = _run_sensor_setup_order(device)
    name = _name_for(entities, "B_P1")
    assert name is not None
    assert "Boiler Pump" in name
    assert "Hot Water Flow" not in name


def test_biotec_plus_boiler_pump_keeps_its_own_name() -> None:
    device = _make_device("biopl", "BioTec Plus")
    device.create_parameter("B_P1", 1)
    entities = _run_sensor_setup_order(device)
    name = _name_for(entities, "B_P1")
    assert name is not None
    assert "Boiler Pump" in name


def test_cm_pelet_set_heater_keeps_its_own_name_not_generic_electric_heater() -> None:
    device = _make_device("cmpelet", "CM Pelet-Set")
    device.create_parameter("B_gri", 1)
    entities = _run_sensor_setup_order(device)
    name = _name_for(entities, "B_gri")
    assert name is not None
    assert "Heater State" in name


def test_peltec2_exposes_only_the_confirmed_k1_pump_state() -> None:
    device = _make_device("peltec2", "PelTec II Lambda")
    device.create_parameter("K1B_onOff", 1)
    device.create_parameter("K1B_P", 0)
    entities = _run_sensor_setup_order(device)

    assert _name_for(entities, "K1B_onOff") is None
    p_name = _name_for(entities, "K1B_P")
    assert p_name is not None
    assert "DHW" not in p_name
    assert "K1 Circuit Pump" in p_name
    p_entity = next(e for e in entities if e._param_name == "K1B_P")
    assert p_entity.native_value == "Off"


def test_only_confirmed_peltec2_circuit_fields_are_created() -> None:
    device = _make_device("peltec2", "PelTec II Lambda")
    for code, value in {
        "K1B_CircType": 5,
        "K1B_dayNight": 0,
        "K1B_kor": -7,
        "K1B_korN": -8,
        "K1B_korType": 0,
        "K1B_onOff": 1,
        "K1B_Prec": 0,
        "K1B_Tpol": 50,
        "K1B_Tsob": 20,
        "K1B_zahP": 0,
        "K1B_misC": 1,
        "K1B_misO": 0,
    }.items():
        device.create_parameter(code, value)
    device.create_parameter("K1B_P", 0)
    device.create_parameter("K1B_Tpol1", 53.7)
    device.create_parameter("K1B_Tsob1", -55)

    entities = _run_sensor_setup_order(device)
    exposed = {getattr(entity, "_param_name", None) for entity in entities}
    assert exposed & {
        "K1B_onOff",
        "K1B_P",
        "K1B_Tpol",
        "K1B_Tpol1",
        "K1B_Tsob",
        "K1B_Tsob1",
        "K1B_zahP",
    } == {
        "K1B_onOff",
        "K1B_P",
        "K1B_Tpol",
        "K1B_Tpol1",
        "K1B_Tsob",
        "K1B_Tsob1",
        "K1B_zahP",
    }
    assert exposed.isdisjoint(
        {
            "K1B_CircType",
            "K1B_dayNight",
            "K1B_kor",
            "K1B_korN",
            "K1B_korType",
            "K1B_Prec",
            "K1B_misC",
            "K1B_misO",
        }
    )
