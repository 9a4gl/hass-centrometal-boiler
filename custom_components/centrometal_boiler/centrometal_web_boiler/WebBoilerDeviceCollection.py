"""Device / parameter state collection driven by HTTP snapshots and STOMP frames.

Design note on the dict inheritance
-----------------------------------
Both ``WebBoilerDevice`` and ``WebBoilerParameter`` deliberately inherit from
``dict``. A purely cosmetic refactor to ``@dataclass`` would *break the
integration*: the Home Assistant glue in ``custom_components/centrometal_boiler``
attaches per-entity wiring via ``device["__client"]``, ``device["__system"]``,
``device["__prefix"]``, ``device["__multi_device"]`` and similar bracket
assignments at runtime, and the sensor/switch entities read parameters via
``parameter["value"]`` / ``parameter["timestamp"]`` etc. across roughly fifty
call sites. So we keep the dict shape and add typing on top via the
``WebBoilerDeviceFields`` / ``WebBoilerParameterFields`` ``TypedDict``s — that
gives us static-analysis support and IDE autocomplete with zero runtime cost
and zero behaviour change.
"""

from __future__ import annotations

import datetime
import json
import logging
import time
from json import JSONDecodeError
from typing import Any, Awaitable, Callable, TypedDict

from .const import WEB_BOILER_STOMP_DEVICE_TOPIC
from .logging_utils import redact_account
from .parameter_filters import is_ignored_peltec2_parameter


class DeviceLookupError(LookupError):
    """Raised when a device cannot be found in the collection."""


class WebBoilerParameterFields(TypedDict, total=False):
    """Schema for a parameter dict. ``total=False`` reflects the lazy fill."""

    name: str
    value: Any
    timestamp: int | None
    used: bool


class WebBoilerDeviceFields(TypedDict, total=False):
    """Schema for a device dict — fields populated through the parse_* methods."""

    id: str | int
    serial: str
    place: str
    address: str
    type: str
    product: str
    country: str
    countryCode: str
    city: str
    parameters: dict[str, "WebBoilerParameter"]
    temperatures: dict[str, Any]
    errors: list[dict[str, Any]]
    circuits: dict[str, Any]


def _normalize_timestamp(timestamp: Any) -> int:
    if timestamp is None:
        return int(time.time())
    if isinstance(timestamp, (int, float)):
        return int(timestamp)

    value = str(timestamp).strip()
    if not value:
        return int(time.time())
    if value.isdigit():
        return int(value)

    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return int(parsed.timestamp())
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.datetime.strptime(value, fmt)
            return int(parsed.replace(tzinfo=datetime.timezone.utc).timestamp())
        except ValueError:
            continue

    return int(time.time())


def _decode_json_body(body: str) -> dict[str, Any]:
    cleaned = body.strip().rstrip("\x00")
    decoder = json.JSONDecoder()
    try:
        data, end = decoder.raw_decode(cleaned)
    except JSONDecodeError as first_err:
        # Corruption pattern: two STOMP frames merged (missing \x00 separator).
        # The JSON is valid up to a point, then garbled.  Try to salvage the
        # valid prefix so sensor values aren't dropped unnecessarily.
        data = _salvage_json_prefix(cleaned, first_err)
        if data is None:
            raise
        return data

    remainder = cleaned[end:].strip()
    if remainder:
        logging.getLogger(__name__).debug("Ignoring trailing realtime payload data after JSON body: %r", remainder)
    if not isinstance(data, dict):
        raise ValueError("Realtime payload must decode to a JSON object")
    return data


def _salvage_json_prefix(cleaned: str, original_err: JSONDecodeError) -> dict[str, Any] | None:
    """Try to recover a valid JSON object from the prefix of a corrupted body.

    When two STOMP frames are merged (the ``\\x00`` terminator between them is
    lost), the body looks like valid JSON up to a point, then contains garbage
    from the next frame's headers/body. We work backwards from the corruption
    point to find the last complete key-value pair and close the object there.
    """
    logger = logging.getLogger(__name__)
    pos = min(original_err.pos, len(cleaned)) if original_err.pos else len(cleaned)

    search_zone = cleaned[:pos]
    for cut in range(len(search_zone) - 1, 0, -1):
        if search_zone[cut] != ",":
            continue
        candidate = search_zone[:cut] + "}"
        try:
            obj = json.loads(candidate)
        except (JSONDecodeError, ValueError):
            continue
        if not isinstance(obj, dict) or len(obj) < 2:
            continue
        logger.info(
            "Salvaged %d key(s) from corrupted realtime payload (corruption at char %d, truncated at char %d)",
            len(obj),
            pos,
            cut,
        )
        return obj

    return None


class WebBoilerParameter(dict):
    def __init__(self) -> None:
        super().__init__()
        self.update_callbacks: dict[str, Callable[..., Awaitable[None]]] = {}

    def set_update_callback(
        self,
        update_callback: Callable[..., Awaitable[None]] | None,
        update_key: str = "default",
    ) -> None:
        if update_callback is None:
            self.update_callbacks.pop(update_key, None)
        else:
            self.update_callbacks[update_key] = update_callback

    async def update(self, name: str, value: Any, timestamp: int | None = None) -> None:
        self["name"] = name
        self["value"] = value
        self["timestamp"] = timestamp
        await self.notify_updated()

    async def notify_updated(self) -> None:
        for callback in list(self.update_callbacks.values()):
            await callback(self)


class WebBoilerDevice(dict):
    def __init__(self, username: str) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.username = username
        self.log_account = redact_account(username)
        self["parameters"] = {}
        self["temperatures"] = {}
        self["errors"] = None
        self["circuits"] = {}

    def has_parameter(self, name: str) -> bool:
        return name in self["parameters"]

    def create_parameter(self, name: str, value: Any = "?") -> WebBoilerParameter:
        param = WebBoilerParameter()
        param["name"] = name
        param["value"] = value
        self["parameters"][name] = param
        return param

    def get_parameter(self, name: str) -> WebBoilerParameter:
        if name not in self["parameters"]:
            self.logger.debug(
                "WebBoilerDevice::get_parameter parameter %s does not exist, creating one (%s)",
                name,
                self.log_account,
            )
            return self.create_parameter(name)
        return self["parameters"][name]

    def get_or_create_parameter(self, name: str) -> WebBoilerParameter:
        if name not in self["parameters"]:
            return self.create_parameter(name)
        return self["parameters"][name]

    async def update_parameter(self, name: str, value: Any, timestamp: Any = None) -> WebBoilerParameter:
        normalized_timestamp = _normalize_timestamp(timestamp)
        parameter = self.get_or_create_parameter(name)
        await parameter.update(name, value, normalized_timestamp)
        return parameter


class WebBoilerDeviceCollection(dict):
    def __init__(
        self,
        username: str,
        on_update_callback: Callable[..., Awaitable[None]] | None = None,
        update_key: str = "default",
    ) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.username = username
        self.log_account = redact_account(username)
        self.on_update_callbacks: dict[str, Callable[..., Awaitable[None]]] = {}
        self.set_on_update_callback(on_update_callback, update_key)

    def set_on_update_callback(
        self,
        on_update_callback: Callable[..., Awaitable[None]] | None,
        update_key: str = "default",
    ) -> None:
        if on_update_callback is None:
            self.on_update_callbacks.pop(update_key, None)
        else:
            self.on_update_callbacks[update_key] = on_update_callback

    async def notify_all_updated(self) -> None:
        for on_update_callback in list(self.on_update_callbacks.values()):
            for device in self.values():
                parameters = device["parameters"]
                for parameter in list(parameters.values()):
                    await on_update_callback(device, parameter, True)
                    await parameter.notify_updated()

    def get_device_by_id(self, id: str | int) -> WebBoilerDevice:
        target = str(id)
        for device in self.values():
            if str(device["id"]) == target:
                return device
        raise DeviceLookupError(f"No device with id {id!r}")

    def get_device_by_serial(self, serial: str) -> WebBoilerDevice:
        target = str(serial)
        for device in self.values():
            if str(device["serial"]) == target:
                return device
        raise DeviceLookupError(f"No device with serial {serial!r}")

    def parse_installations(self, installations: list[dict[str, Any]]) -> None:
        for device in installations:
            serial = device["label"]
            self.logger.info("Creating device %s (%s)", serial, self.log_account)
            new_device = WebBoilerDevice(self.log_account)
            new_device["id"] = device["value"]
            new_device["serial"] = device["label"]
            new_device["place"] = device["place"]
            new_device["address"] = device["address"]
            new_device["type"] = device["type"]
            new_device["product"] = device["product"]
            self[serial] = new_device

    async def parse_installation_statuses(self, installation_status_all: dict[str, Any]) -> None:
        for device_id, value in installation_status_all.items():
            device = self.get_device_by_id(device_id)
            for group, data in value.items():
                if group == "installation":
                    device["country"] = data["country"]
                    device["countryCode"] = data["countryCode"]
                elif group == "params":
                    for param_id, param_data in data.items():
                        if device.get("type") == "peltec2" and is_ignored_peltec2_parameter(param_id):
                            continue
                        parameter = await device.update_parameter(param_id, param_data.get("v"), param_data.get("ut"))
                        # Without this, an HTTP refresh updated the cache
                        # but HA entities did not re-render until the next
                        # websocket message arrived. Fire the same callback
                        # path the websocket uses so refresh() is enough.
                        for on_update_callback in list(self.on_update_callbacks.values()):
                            await on_update_callback(device, parameter)
                else:
                    self.logger.warning(
                        "Unknown group in installation_status_all group:%s (%s) - skipping",
                        group,
                        self.log_account,
                    )

    def parse_parameter_lists(self, parameter_list: dict[str, Any]) -> list[WebBoilerParameter]:
        updated_metadata: list[WebBoilerParameter] = []
        for serial, device_data in parameter_list.items():
            device = self.get_device_by_serial(serial)
            for data_id, data_value in device_data.items():
                if data_id == "city":
                    device["city"] = data_value
                elif data_id == "parameters":
                    for data_value_item in data_value:
                        group = data_value_item["group"]
                        if group == "Temperatures":
                            for list_item in data_value_item["list"]:
                                index = list_item["dbindex"]
                                device["temperatures"][index] = list_item
                        elif group == "Info":
                            # Static portal display metadata is not used to
                            # create entities; do not retain it.
                            continue
                        elif group == "Weather forecast":
                            # Weather is intentionally not stored or exposed.
                            continue
                        elif group == "Heating circuits":
                            for list_item in data_value_item["list"]:
                                index = list_item["naslov"]
                                device["circuits"][index] = list_item
                        else:
                            self.logger.warning(
                                "Unknown group in parameter_list group:%s (%s) - skipping",
                                group,
                                self.log_account,
                            )
                else:
                    self.logger.warning(
                        "Unknown data_id in parameter_list data_id:%s (%s) - skipping",
                        data_id,
                        self.log_account,
                    )
        return updated_metadata

    def parse_errors_lists(self, errors_lists: dict[str, Any]) -> list[WebBoilerParameter]:
        updated_metadata: list[WebBoilerParameter] = []
        for device_id, payload in errors_lists.items():
            device = self.get_device_by_id(device_id)
            columns = [col.get("id") for col in payload.get("cols", [])]
            events: list[dict[str, Any]] = []
            for row in payload.get("rows", []):
                if isinstance(row, list):
                    events.append({columns[i]: row[i] for i in range(min(len(columns), len(row)))})
            device["errors"] = events
            parameter = device.get_or_create_parameter("Errors_History")
            parameter["name"] = "Errors_History"
            if events:
                latest = events[-1]
                parameter["value"] = latest.get("description") or latest.get("received_parameter") or "Event"
            else:
                parameter["value"] = "No events"
            parameter["timestamp"] = int(time.time())
            updated_metadata.append(parameter)
        return updated_metadata

    async def _update_device_with_real_time_data(self, device: WebBoilerDevice, body: str) -> None:
        try:
            data = _decode_json_body(body)
        except (JSONDecodeError, ValueError) as err:
            self.logger.warning(
                "Skipping malformed realtime JSON payload for device %s (%s): %s body=%r",
                device.get("serial"),
                self.log_account,
                err,
                body[:300],
            )
            return
        for param_id, value in data.items():
            if device.get("type") == "peltec2" and is_ignored_peltec2_parameter(param_id):
                continue
            parameter = await device.update_parameter(param_id, value)
            for on_update_callback in list(self.on_update_callbacks.values()):
                await on_update_callback(device, parameter)

    async def parse_real_time_frame(self, stomp_frame: dict[str, Any]) -> None:
        if "headers" not in stomp_frame or "body" not in stomp_frame:
            return

        headers = stomp_frame["headers"]
        body = stomp_frame["body"]
        if "subscription" not in headers or "destination" not in headers:
            return

        subscription = headers["subscription"]
        destination = headers["destination"]

        if destination.startswith(WEB_BOILER_STOMP_DEVICE_TOPIC):
            dotpos = destination.rfind(".")
            serial = destination[dotpos + 1 :]
            try:
                device = self.get_device_by_serial(serial)
            except DeviceLookupError:
                self.logger.warning(
                    "Unexpected realtime message for unknown serial: %s (%s) - skipping",
                    serial,
                    self.log_account,
                )
                return
            await self._update_device_with_real_time_data(device, body)
        else:
            self.logger.warning(
                "Unexpected message for destination: %s (subscription %s, %s) - skipping",
                destination,
                subscription,
                self.log_account,
            )
