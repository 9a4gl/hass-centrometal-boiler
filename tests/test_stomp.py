"""Tests for the STOMP frame extraction helpers.

These tests pin down the behaviour of ``extract_complete_frames`` because it
is on the realtime path: every STOMP message that drives sensor updates passes
through it, and websocket messages do not always align with STOMP frame
boundaries (the function is the buffer that hides the difference).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

from centrometal_web_boiler import stomp  # noqa: E402


def test_heartbeat_frame_is_recognized() -> None:
    frames, remainder = stomp.extract_complete_frames("\n", "")
    assert remainder == ""
    assert len(frames) == 1
    assert frames[0]["cmd"] == "HEARTBEAT"


def test_single_complete_frame_is_parsed() -> None:
    payload = 'MESSAGE\nsubscription:sub-1\ndestination:/topic/cm.inst.peltec.SN123\n\n{"B_TI":42}\x00'
    frames, remainder = stomp.extract_complete_frames(payload, "")
    assert remainder == ""
    assert len(frames) == 1
    frame = frames[0]
    assert frame["cmd"] == "MESSAGE"
    assert frame["headers"]["subscription"] == "sub-1"
    assert frame["headers"]["destination"] == "/topic/cm.inst.peltec.SN123"
    assert frame["body"] == '{"B_TI":42}'


def test_two_frames_in_one_payload_split_correctly() -> None:
    f1 = "MESSAGE\nsubscription:sub-1\ndestination:x\n\nA\x00"
    f2 = "MESSAGE\nsubscription:sub-2\ndestination:y\n\nB\x00"
    frames, remainder = stomp.extract_complete_frames(f1 + f2, "")
    assert remainder == ""
    assert len(frames) == 2
    assert frames[0]["body"] == "A"
    assert frames[1]["body"] == "B"


def test_chunked_frame_is_buffered_until_terminator_arrives() -> None:
    full = "MESSAGE\nsubscription:sub-1\ndestination:x\n\nABC\x00"
    chunk_a, chunk_b = full[:20], full[20:]

    frames, buffer = stomp.extract_complete_frames(chunk_a, "")
    assert frames == []
    # Anything before \x00 must be buffered, not dropped.
    assert chunk_a in buffer

    frames, buffer = stomp.extract_complete_frames(chunk_b, buffer)
    assert buffer == ""
    assert len(frames) == 1
    assert frames[0]["body"] == "ABC"


def test_trailing_remainder_is_returned_as_buffer() -> None:
    f1 = "MESSAGE\nsubscription:sub-1\ndestination:x\n\nA\x00"
    partial = "MESSAGE\nsubscription:sub-2\ndestination:"
    frames, remainder = stomp.extract_complete_frames(f1 + partial, "")
    assert len(frames) == 1
    assert remainder == partial


def test_connect_frame_format() -> None:
    frame = stomp.connect("user", "pass", "/", (10000, 10000))
    assert frame.startswith("CONNECT\n")
    assert "login:user" in frame
    assert "passcode:pass" in frame
    assert frame.endswith("\n\x00")


def test_subscribe_frame_format() -> None:
    frame = stomp.subscribe("/topic/x", "sub-7", "auto")
    assert "SUBSCRIBE\n" in frame
    assert "id:sub-7" in frame
    assert "destination:/topic/x" in frame
    assert "ack:auto" in frame
