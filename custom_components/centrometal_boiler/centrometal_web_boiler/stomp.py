from __future__ import annotations

from typing import List


def connect(login: str, passcode: str, host: str = "/", heartbeats: tuple[int, int] = (90000, 60000)) -> str:
    return (
        "CONNECT\n"
        "accept-version:1.1\n"
        f"host:{host}\n"
        f"login:{login}\n"
        f"passcode:{passcode}\n"
        f"heart-beat:{heartbeats[0]},{heartbeats[1]}\n"
        "\n\x00"
    )


def subscribe(destination: str, subscription_id: str, ack: str = "auto") -> str:
    return f"SUBSCRIBE\nid:{subscription_id}\ndestination:{destination}\nack:{ack}\n\n\x00"


def _parse_single_frame(payload: str) -> dict:
    if payload == "\n" or not payload.strip("\n"):
        return {"cmd": "HEARTBEAT", "headers": {}, "body": ""}

    payload = payload.lstrip("\n")
    parts = payload.split("\n\n", 1)
    header_block = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    lines = header_block.split("\n")
    cmd = lines[0].strip()
    headers = {}
    for line in lines[1:]:
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        headers[k] = v

    # STOMP bodies can end with trailing newlines before the frame terminator.
    body = body.rstrip("\n")
    return {"cmd": cmd, "headers": headers, "body": body}


def extract_complete_frames(data: str, buffer: str = "") -> tuple[List[dict], str]:
    """Return complete STOMP frames plus any incomplete remainder.

    Websocket message boundaries do not always match STOMP frame boundaries, so
    callers should carry the returned remainder into the next invocation.
    """
    if data is None:
        return [], buffer

    combined = f"{buffer}{data}"
    frames: list[dict] = []

    # Heartbeat-only payloads have no frame terminator and should not be buffered.
    if combined == "\n" or (not combined.strip("\n") and "\x00" not in combined):
        return ([{"cmd": "HEARTBEAT", "headers": {}, "body": ""}] if combined else []), ""

    parts = combined.split("\x00")
    remainder = parts.pop()

    for chunk in parts:
        if not chunk:
            continue
        if chunk == "\n" or not chunk.strip("\n"):
            frames.append({"cmd": "HEARTBEAT", "headers": {}, "body": ""})
            continue
        frames.append(_parse_single_frame(chunk))

    return frames, remainder


def unpack_frame(data: str) -> dict:
    frames = unpack_frames(data)
    return frames[0] if frames else {"cmd": "HEARTBEAT", "headers": {}, "body": ""}


def unpack_frames(data: str) -> List[dict]:
    """Parse one websocket payload into one or more STOMP frames.

    This helper only returns frames that are complete within the provided data.
    Use ``extract_complete_frames`` when the caller needs to keep incomplete
    fragments between websocket messages.
    """
    frames, _ = extract_complete_frames(data)
    return frames
