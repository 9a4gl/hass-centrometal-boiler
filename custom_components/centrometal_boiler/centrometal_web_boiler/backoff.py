"""Exponential backoff helper for retry cadences.

Deliberately dependency-free (stdlib only) so it lives in the framework-
agnostic ``centrometal_web_boiler`` layer alongside the rest of the testable
protocol/client code, rather than in the Home Assistant glue layer.

Used by ``WebBoilerSystem`` (in ``custom_components/centrometal_boiler``) to
space out relogin/reconnect attempts during a prolonged Centrometal outage
instead of retrying on a fixed cadence forever, which just adds load to a
service that is already struggling.
"""

from __future__ import annotations


def next_retry_delay(attempt: int, *, base: float, cap: float) -> float:
    """Return the delay in seconds before retry number ``attempt``.

    ``attempt`` is 0 for the first retry, 1 for the second, and so on. The
    delay doubles with each attempt until it reaches ``cap``.

    ``base`` and ``cap`` are clamped to sane minimums so a bad/zero config
    value can never collapse this into a zero-delay tight retry loop:
    ``base`` is at least 1 second, and ``cap`` is never below ``base``.
    """
    safe_base = max(float(base), 1.0)
    safe_cap = max(float(cap), safe_base)
    safe_attempt = max(int(attempt), 0)
    # Once base * 2**attempt would already dwarf cap, further growth cannot
    # change the (clamped) result. Bounding the exponent keeps this cheap even
    # if a caller passes an unbounded attempt count over a very long uptime.
    max_useful_attempt = 64
    safe_attempt = min(safe_attempt, max_useful_attempt)
    delay = safe_base * (2**safe_attempt)
    return min(delay, safe_cap)
