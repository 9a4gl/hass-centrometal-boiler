"""Tests for the realtime JSON body decoding and salvage logic.

The salvage path matters because the upstream STOMP server occasionally drops
the ``\\x00`` separator between two frames, leaving us with a body that is
*almost* valid JSON followed by garbage from the next frame. Without salvage,
those packets used to drop *all* sensor updates in the frame; with salvage we
recover the leading complete key/value pairs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

from centrometal_web_boiler.WebBoilerDeviceCollection import (  # noqa: E402
    _decode_json_body,
    _salvage_json_prefix,
)


def test_clean_payload_decodes_directly() -> None:
    body = '{"B_TI":42,"B_PWR":1}'
    assert _decode_json_body(body) == {"B_TI": 42, "B_PWR": 1}


def test_trailing_null_terminator_is_stripped() -> None:
    body = '{"a":1}\x00'
    assert _decode_json_body(body) == {"a": 1}


def test_non_object_payload_raises_value_error() -> None:
    with pytest.raises(ValueError):
        _decode_json_body("[1, 2, 3]")


def test_truly_malformed_payload_raises() -> None:
    with pytest.raises(Exception):
        _decode_json_body('{"oops"')


def test_salvage_recovers_prefix_when_two_frames_merge() -> None:
    # Construct: valid JSON object, then more "json-looking" garbage from a
    # next frame whose \x00 terminator was dropped.
    corrupt = '{"B_TI":42,"B_PWR":1,"B_VER":"3.2.1",MESSAGE\nsub:foo\n}'
    decoded = _decode_json_body(corrupt)
    # We should have salvaged at least the first three keys.
    assert decoded["B_TI"] == 42
    assert decoded["B_PWR"] == 1
    assert decoded["B_VER"] == "3.2.1"


def test_salvage_returns_none_when_no_complete_pair_exists() -> None:
    from json import JSONDecodeError

    # Less than two complete key/value pairs - the salvage logic refuses
    # to return single-key dicts because they're more likely to be noise.
    cleaned = '{"a":1,garbage'
    try:
        import json

        json.loads(cleaned)
    except JSONDecodeError as err:
        result = _salvage_json_prefix(cleaned, err)
        assert result is None
