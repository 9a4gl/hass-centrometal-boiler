"""Tests for the relogin/reconnect exponential backoff helper."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

from centrometal_web_boiler.backoff import next_retry_delay  # noqa: E402


def test_first_attempt_is_base_delay() -> None:
    assert next_retry_delay(0, base=60, cap=1800) == 60


def test_delay_doubles_each_attempt() -> None:
    assert next_retry_delay(1, base=60, cap=1800) == 120
    assert next_retry_delay(2, base=60, cap=1800) == 240
    assert next_retry_delay(3, base=60, cap=1800) == 480


def test_delay_is_clamped_to_cap() -> None:
    assert next_retry_delay(10, base=60, cap=1800) == 1800
    assert next_retry_delay(1000, base=60, cap=1800) == 1800


def test_negative_attempt_treated_as_zero() -> None:
    assert next_retry_delay(-5, base=60, cap=1800) == 60


def test_base_is_floored_to_one_second() -> None:
    # A misconfigured (zero or negative) base can never produce a zero-delay
    # tight retry loop.
    assert next_retry_delay(0, base=0, cap=1800) == 1
    assert next_retry_delay(0, base=-30, cap=1800) == 1


def test_cap_never_below_base() -> None:
    # If cap is misconfigured smaller than base, base still wins as the floor.
    assert next_retry_delay(0, base=60, cap=10) == 60
    assert next_retry_delay(5, base=60, cap=10) == 60


def test_very_large_attempt_count_stays_cheap_and_clamped() -> None:
    assert next_retry_delay(10_000_000, base=60, cap=1800) == 1800
