"""Pure regression tests for rules captured from the PelTec II portal."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.centrometal_boiler.centrometal_web_boiler.parameter_filters import (
    is_ignored_peltec2_parameter,
)
from custom_components.centrometal_boiler import peltec2


def test_portal_hex_and_input_bitmask() -> None:
    decoded = peltec2.decode_input_bitmask("28")
    assert decoded == {
        "raw_hex": "0x28",
        "decimal": 40,
        "binary": "00101000",
        "external_start": False,
    }
    assert peltec2.portal_hex_bit_is_set("40", 6) is True


def test_accessory_bitmask_controls_pellet_percentage() -> None:
    assert peltec2.decode_accessory_bitmask("8")["fuel_level_percentage_enabled"] is True
    assert peltec2.decode_accessory_bitmask("0")["fuel_level_percentage_enabled"] is False


def test_portal_enums() -> None:
    assert peltec2.decode_internet_access("1") == "Supervision"
    assert peltec2.decode_internet_access("2") == "Supervision + control"
    assert peltec2.decode_internet_access("0") == "Unknown (0)"
    assert peltec2.decode_status_mark("0") == "None"
    assert peltec2.decode_status_mark("5") == "F"
    details = peltec2.decode_status_mark_details("4")
    assert details["code"] == "G"
    assert details["temporary_shutdown"] is True
    assert "grate cleaning" in details["meaning"]
    assert peltec2.decode_start_transition("0", "OFF") == "Idle"
    assert peltec2.decode_start_transition("1", "S1") == "Starting"
    assert peltec2.decode_start_transition("2", "S9") == "Stopping"
    assert peltec2.decode_start_transition("1", "S7-3") == "Paused / standby"
    assert peltec2.decode_tank_level("2") == "Full"


def test_temperature_validity_matches_portal_bounds() -> None:
    assert peltec2.valid_temperature("B_Tk1", "25.3") == 25.3
    assert peltec2.valid_temperature("B_Tk1", "-55") is None
    assert peltec2.valid_temperature("B_Tk1", "-45") is None
    assert peltec2.valid_temperature("B_Tk1", "145") is None
    assert peltec2.valid_temperature("B_Tpov1", "0") is None
    assert peltec2.valid_temperature("B_Tdpl1", "0") is None
    assert peltec2.valid_temperature("B_Tdpl1", "299.9") == 299.9
    assert peltec2.valid_temperature("B_Tdpl1", "300") is None


def test_lambda_signal_and_percentage_validity() -> None:
    assert peltec2.valid_lambda("12.5") == 12.5
    assert peltec2.valid_lambda("0") == 0.0
    assert peltec2.valid_lambda("25.4") == 25.4
    assert peltec2.valid_lambda("25.5") == 25.5
    assert peltec2.valid_lambda("nan") is None
    assert peltec2.valid_signal_db("0") is None
    assert peltec2.valid_signal_db("-67") == -67.0
    assert peltec2.valid_signal_db("nan") is None
    assert peltec2.valid_percentage("99") == 99.0
    assert peltec2.valid_percentage("101") is None
    assert peltec2.valid_nonnegative_measurement("1001", maximum=1001) == 1001.0
    assert peltec2.valid_nonnegative_measurement("1002", maximum=1001) is None
    assert peltec2.valid_nonnegative_measurement("nan") is None


def test_schedule_parameter_filter_covers_all_tables_and_metadata() -> None:
    for family in ("PVAL", "PDEF", "PMIN", "PMAX"):
        for dbindex in (223, 224, 225, 226):
            assert is_ignored_peltec2_parameter(f"{family}_{dbindex}_0") is True
    assert is_ignored_peltec2_parameter("PVAL_272_0") is False
    assert is_ignored_peltec2_parameter("B_Tk1") is False


def test_full_http_snapshot_fixture_matches_audited_capture() -> None:
    fixture = Path(__file__).resolve().parent / "fixtures" / "peltec2_lambda_http_snapshot.json"
    snapshot = json.loads(fixture.read_text())
    assert len(snapshot) == 231
    assert snapshot["B_SUP_TYPE"] == "2"
    assert snapshot["B_Inp1"] == "28"
    assert snapshot["B_addConf"] == "8"
    assert snapshot["B_Oxy1"] == "25.5"
    assert snapshot["B_Ths1"] == "-55"
    assert snapshot["K1B_Tsob1"] == "-55"
    assert snapshot["PVAL_223_0"] == "0"
    assert snapshot["PVAL_224_0"] == "33818"
    assert snapshot["PVAL_224_69"] == "1440"


def test_wifi_zero_is_missing_but_nonzero_db_is_valid() -> None:
    from custom_components.centrometal_boiler.peltec2 import valid_signal_db

    assert valid_signal_db(0) is None
    assert valid_signal_db("0") is None
    assert valid_signal_db(-35) == -35.0


def test_configuration_component_helpers() -> None:
    assert peltec2.configuration_has_dhw(4) is True
    assert peltec2.configuration_has_buffer(4) is True
    assert peltec2.configuration_has_dhw(12) is False
    assert peltec2.configuration_has_buffer(12) is False
