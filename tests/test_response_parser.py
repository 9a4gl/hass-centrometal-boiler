"""Tests for the command-response success parser used by ``turn`` and
``turn_circuit`` in WebBoilerClient.

The parser must:
- accept the documented success shapes the Centrometal API returns
- accept obvious one-level envelopes
- *reject* random nested success markers inside otherwise-failing responses
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

from centrometal_web_boiler.WebBoilerClient import _response_is_success  # noqa: E402


def test_top_level_status_success() -> None:
    assert _response_is_success({"status": "success"}) is True
    assert _response_is_success({"status": "ok"}) is True
    assert _response_is_success({"status": "DONE"}) is True


def test_top_level_success_or_ok_flag() -> None:
    assert _response_is_success({"success": True}) is True
    assert _response_is_success({"ok": True}) is True


def test_envelope_under_result_or_data() -> None:
    assert _response_is_success({"result": {"status": "success"}}) is True
    assert _response_is_success({"data": {"ok": True}}) is True


def test_explicit_failure_is_rejected() -> None:
    assert _response_is_success({"status": "error"}) is False
    assert _response_is_success({"success": False}) is False
    assert _response_is_success({"status": "failed", "message": "bad"}) is False


def test_unrelated_payload_is_rejected() -> None:
    assert _response_is_success({}) is False
    assert _response_is_success({"foo": "bar"}) is False
    assert _response_is_success(None) is False
    assert _response_is_success("ok") is False
    assert _response_is_success(123) is False


def test_deep_success_marker_does_not_falsely_pass() -> None:
    # A failure response that happens to contain a success marker buried two
    # levels deep must NOT be treated as success — the parser intentionally
    # does not do a recursive walk.
    payload = {
        "status": "error",
        "details": {"history": [{"status": "success"}]},
    }
    assert _response_is_success(payload) is False


def test_bare_true_is_accepted() -> None:
    assert _response_is_success(True) is True
    assert _response_is_success(False) is False


def test_explicit_top_level_failure_wins_over_success_envelope() -> None:
    assert _response_is_success({"status": "error", "result": {"status": "success"}}) is False
    assert _response_is_success({"success": False, "data": {"ok": True}}) is False
