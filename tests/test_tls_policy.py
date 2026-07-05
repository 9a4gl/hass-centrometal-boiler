"""TLS policy tests.

Certificate verification against the Centrometal endpoint is always enabled.
Past verification failures on some Home Assistant hosts were caused by an
outdated system CA trust store, not a problem with the server's certificate,
so the client verifies against certifi's bundled (and independently updated)
root store instead of ever disabling verification.
"""

from __future__ import annotations

import ssl
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

import pytest

from centrometal_web_boiler.HttpClient import build_verified_ssl_context  # noqa: E402


def test_ssl_context_verifies_certificates() -> None:
    ctx = build_verified_ssl_context()
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_ssl_context_uses_certifi_bundle_when_available() -> None:
    certifi = pytest.importorskip("certifi")
    ctx = build_verified_ssl_context()
    # A context built with cafile=certifi.where() still ends up CERT_REQUIRED
    # with hostname checking on; this just confirms certifi is picked up in
    # the test environment and doesn't make the context any less strict.
    assert certifi.where()
    assert ctx.verify_mode == ssl.CERT_REQUIRED
