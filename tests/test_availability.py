"""Tests for the entity-availability signal and telemetry timestamps on
WebBoilerClient. These methods are read by every sensor and switch's
``available`` property, so a regression silently breaks every entity in HA.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

from centrometal_web_boiler.WebBoilerClient import WebBoilerClient  # noqa: E402


def _make_client() -> WebBoilerClient:
    return WebBoilerClient(hass=None)


def test_has_fresh_data_false_when_never_connected() -> None:
    c = _make_client()
    c.last_successful_http_refresh = None
    c.websocket_connected = False
    assert c.has_fresh_data() is False


def test_has_fresh_data_true_when_websocket_connected() -> None:
    c = _make_client()
    c.last_successful_http_refresh = None
    c.websocket_connected = True
    assert c.has_fresh_data() is True


def test_has_fresh_data_true_with_recent_http_refresh() -> None:
    c = _make_client()
    c.websocket_connected = False
    c.last_successful_http_refresh = time.monotonic() - 30  # 30s ago
    assert c.has_fresh_data(max_age=300) is True


def test_has_fresh_data_false_with_stale_http_refresh() -> None:
    c = _make_client()
    c.websocket_connected = False
    c.last_successful_http_refresh = time.monotonic() - 1000  # >5min ago
    assert c.has_fresh_data(max_age=300) is False


def test_websocket_disconnected_for_zero_when_connected() -> None:
    c = _make_client()
    c.websocket_connected = True
    c.disconnected_since = None
    assert c.websocket_disconnected_for() == 0.0


def test_websocket_disconnected_for_returns_elapsed() -> None:
    c = _make_client()
    c.websocket_connected = False
    c.disconnected_since = time.monotonic() - 60
    elapsed = c.websocket_disconnected_for()
    assert 50 < elapsed < 70  # ~60s, allowing for execution time
