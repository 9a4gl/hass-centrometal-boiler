"""Portal-confirmed PelTec II value decoding helpers.

The rules in this module come from the authenticated Centrometal portal
JavaScript/templates captured on 2026-07-04.  Keeping the rules free of Home
Assistant imports makes them easy to unit test and reuse from sensor and binary
sensor entities.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from .centrometal_web_boiler.parameter_filters import is_ignored_peltec2_parameter


INTERNET_ACCESS = {
    1: "Supervision",
    2: "Supervision + control",
}

STATUS_MARKS = {
    0: "None",
    1: "R",
    2: "B",
    3: "T",
    4: "G",
    5: "F",
}

STATUS_MARK_DETAILS = {
    0: {
        "meaning": "No special shutdown activity",
        "category": "None",
        "temporary_shutdown": False,
        "documentation": "PelTec II Lambda controller manual",
    },
    1: {
        "meaning": "Shutdown after loss of flame during operation",
        "category": "Temporary shutdown reason",
        "temporary_shutdown": True,
        "documentation": "PelTec II Lambda controller manual",
    },
    2: {
        "meaning": "Shutdown after excessive pellet feed tube bimetal temperature",
        "category": "Temporary shutdown reason",
        "temporary_shutdown": True,
        "documentation": "PelTec II Lambda controller manual",
    },
    3: {
        "meaning": "Shutdown so the turbulator / flue passage cleaner can operate",
        "category": "Temporary shutdown reason",
        "temporary_shutdown": True,
        "documentation": "PelTec II Lambda controller manual",
    },
    4: {
        "meaning": "Shutdown because burner grate cleaning is required",
        "category": "Temporary shutdown reason",
        "temporary_shutdown": True,
        "documentation": "PelTec II Lambda controller manual",
    },
    5: {
        "meaning": "Shutdown associated with pellet tank filling or refilling",
        "category": "Temporary shutdown reason",
        "temporary_shutdown": True,
        "documentation": "Related official Centrometal controller manual",
    },
}

START_TRANSITIONS = {
    0: "Idle",
    1: "Starting",
    2: "Stopping",
}

TANK_LEVELS = {
    0: "Empty",
    1: "Reserve",
    2: "Full",
}

# Zero-based B_KONF values from the controller configuration list. Optional
# DHW/buffer telemetry is meaningful only in configurations that contain the
# corresponding hydraulic component.
DHW_CONFIGURATIONS = frozenset({0, 2, 4, 6, 7, 8, 11, 14})
BUFFER_CONFIGURATIONS = frozenset({3, 4, 5, 6, 7, 8, 10, 13})


def _as_int(value: Any, *, base: int = 10) -> int | None:
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if not text:
            return None
        return int(text, base)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        return None


def parse_portal_hex(value: Any) -> int | None:
    """Decode values handled by the portal's ``parseInt(value, 16)`` filters."""
    if isinstance(value, int):
        # The server normally sends these as strings.  Preserve the portal's
        # semantics by treating an integer's decimal digits as a hex string.
        return _as_int(str(value), base=16)
    return _as_int(value, base=16)


def format_portal_hex(value: Any) -> str:
    parsed = parse_portal_hex(value)
    if parsed is None:
        return str(value)
    return f"0x{parsed:X}"


def portal_hex_bit_is_set(value: Any, bit: int) -> bool | None:
    parsed = parse_portal_hex(value)
    if parsed is None:
        return None
    return bool((parsed >> bit) & 1)


def decode_input_bitmask(value: Any) -> dict[str, Any]:
    parsed = parse_portal_hex(value)
    if parsed is None:
        return {
            "raw_hex": str(value),
            "decimal": None,
            "binary": None,
            "external_start": None,
        }
    return {
        "raw_hex": f"0x{parsed:X}",
        "decimal": parsed,
        "binary": f"{parsed:08b}",
        # Portal template uses zero-based bit 6.
        "external_start": bool((parsed >> 6) & 1),
    }


def decode_accessory_bitmask(value: Any) -> dict[str, Any]:
    parsed = parse_portal_hex(value)
    if parsed is None:
        return {
            "raw_hex": str(value),
            "decimal": None,
            "binary": None,
            "fuel_level_percentage_enabled": None,
        }
    return {
        "raw_hex": f"0x{parsed:X}",
        "decimal": parsed,
        "binary": f"{parsed:08b}",
        # Portal template shows B_razP only when bit 3 is set.
        "fuel_level_percentage_enabled": bool((parsed >> 3) & 1),
    }


def decode_internet_access(value: Any) -> str:
    parsed = _as_int(value)
    if parsed is None:
        return str(value)
    return INTERNET_ACCESS.get(parsed, f"Unknown ({parsed})")


def decode_status_mark(value: Any) -> str:
    parsed = _as_int(value)
    if parsed is None:
        return str(value)
    return STATUS_MARKS.get(parsed, f"Unknown ({parsed})")


def decode_status_mark_details(value: Any) -> dict[str, Any]:
    """Return the documented meaning for a PelTec II status mark."""
    parsed = _as_int(value)
    if parsed is None:
        return {
            "raw_value": value,
            "code": str(value),
            "meaning": "Unknown status mark",
            "category": "Unknown",
            "temporary_shutdown": None,
            "documentation": None,
        }
    details = STATUS_MARK_DETAILS.get(parsed)
    if details is None:
        return {
            "raw_value": parsed,
            "code": f"Unknown ({parsed})",
            "meaning": "Unknown status mark",
            "category": "Unknown",
            "temporary_shutdown": None,
            "documentation": None,
        }
    return {
        "raw_value": parsed,
        "code": STATUS_MARKS[parsed],
        **details,
    }


def decode_start_transition(value: Any, boiler_state: Any = None) -> str:
    if str(boiler_state).strip() == "S7-3":
        return "Paused / standby"
    parsed = _as_int(value)
    if parsed is None:
        return str(value)
    return START_TRANSITIONS.get(parsed, f"Unknown ({parsed})")


def decode_tank_level(value: Any) -> str:
    parsed = _as_int(value)
    if parsed is None:
        return str(value)
    return TANK_LEVELS.get(parsed, f"Unknown ({parsed})")


def configuration_has_dhw(value: Any) -> bool:
    """Return whether the controller configuration contains a DHW tank."""
    parsed = _as_int(value)
    return parsed in DHW_CONFIGURATIONS if parsed is not None else False


def configuration_has_buffer(value: Any) -> bool:
    """Return whether the controller configuration contains a buffer tank."""
    parsed = _as_int(value)
    return parsed in BUFFER_CONFIGURATIONS if parsed is not None else False


def valid_temperature(parameter: str, value: Any) -> float | None:
    """Return a portal-valid PelTec II temperature, otherwise ``None``.

    The portal uses -45/145 for water, room, buffer and outside temperatures,
    while flue gas is allowed up to 300.  These are strict bounds in the
    portal templates.
    """
    numeric = _as_float(value)
    if numeric is None:
        return None
    upper = 300.0 if parameter == "B_Tdpl1" else 145.0
    if not (-45.0 < numeric < upper):
        return None
    if parameter in {"B_Tdpl1", "B_Tpov1"} and numeric == 0:
        return None
    return numeric


def valid_lambda(value: Any) -> float | None:
    """Return the numeric Lambda/O2 value supplied by the controller portal.

    Older releases passed this value through unchanged.  Do not treat 0, 25.4
    or 25.5 as Home Assistant availability sentinels: the controller may publish
    those values while combustion is inactive and later replace them with a live
    measurement.  Only missing or non-finite values are unavailable.
    """
    numeric = _as_float(value)
    if numeric is None or not isfinite(numeric):
        return None
    return numeric


def valid_signal_db(value: Any) -> float | None:
    """Return a numeric Wi-Fi signal reading, or ``None`` when not reported.

    The controller's local Software Info screen labels this value in dB and
    displays ``---dB`` when no RSSI is available.  The portal represents that
    missing reading as zero, so zero must not be exposed as a real signal.
    """
    numeric = _as_float(value)
    if numeric is None or not isfinite(numeric) or numeric == 0:
        return None
    return numeric


def valid_percentage(value: Any) -> float | None:
    numeric = _as_float(value)
    if numeric is None or numeric < 0 or numeric > 100:
        return None
    return numeric


def valid_nonnegative_measurement(value: Any, *, maximum: float | None = None) -> float | None:
    """Return a finite non-negative numeric measurement within an optional maximum."""
    numeric = _as_float(value)
    if numeric is None or not isfinite(numeric) or numeric < 0:
        return None
    if maximum is not None and numeric > maximum:
        return None
    return numeric
