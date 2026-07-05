"""Tests for the lightweight HTML parsing helpers in HttpClient.

These replaced the lxml-based extractor; they're small but they sit on the
critical login path so a unit test on representative markup is worth having.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

from centrometal_web_boiler.HttpClient import (  # noqa: E402
    _extract_csrf_token,
    _login_succeeded,
)


def test_csrf_token_extracted_from_minimal_form() -> None:
    html_text = (
        '<html><body><form action="/login_check">'
        '<input name="_csrf_token" value="ABC-123-token" />'
        '<input name="_username" />'
        "</form></body></html>"
    )
    assert _extract_csrf_token(html_text) == "ABC-123-token"


def test_csrf_token_handles_double_quotes_and_spacing() -> None:
    html_text = '<input  type="hidden"  name="_csrf_token"  value="x.y_Z-9"  />'
    assert _extract_csrf_token(html_text) == "x.y_Z-9"


def test_csrf_token_returns_none_when_missing() -> None:
    html_text = '<form><input name="_username" value="me" /></form>'
    assert _extract_csrf_token(html_text) is None


def test_login_succeeded_detects_loading_div() -> None:
    html_text = '<html><body><div id="id-loading-screen-blackout"></div></body></html>'
    assert _login_succeeded(html_text) is True


def test_login_succeeded_returns_false_without_loading_div() -> None:
    html_text = '<html><body><form action="/login_check"></form></body></html>'
    assert _login_succeeded(html_text) is False
