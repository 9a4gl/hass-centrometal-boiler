"""Parameter filters shared by HTTP and WebSocket ingestion."""

from __future__ import annotations


_PELTEC2_SCHEDULE_DBINDEXES = {"223", "224", "225", "226"}


def is_ignored_peltec2_parameter(name: str) -> bool:
    """Return whether a PelTec II parameter is schedule-only data.

    The Centrometal status snapshot and WebSocket stream include schedule
    selector/table values even when the client never opens the timetable UI.
    The integration intentionally does not store or expose those fields.
    """
    parts = name.split("_")
    return len(parts) >= 2 and parts[0] in {"PVAL", "PDEF", "PMIN", "PMAX"} and parts[1] in _PELTEC2_SCHEDULE_DBINDEXES
