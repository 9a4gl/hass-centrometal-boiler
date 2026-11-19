"""Exercise real STOMP and parameter parsers with fake network boundaries."""

import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from centrometal_web_boiler.const import WEB_BOILER_STOMP_DEVICE_TOPIC

from custom_components.centrometal_boiler import (
    async_setup_entry,
    async_unload_entry,
    transport,
)
from custom_components.centrometal_boiler.binary_sensor import WebBoilerWebsocketStatus
from custom_components.centrometal_boiler.const import DOMAIN, WEB_BOILER_CLIENT
from custom_components.centrometal_boiler.sensors.WebBoilerGenericSensor import (
    WebBoilerGenericSensor,
)
from custom_components.centrometal_boiler.switches.WebBoilerCircuitSwitch import (
    WebBoilerCircuitSwitch,
)
from custom_components.centrometal_boiler.switches.WebBoilerPowerSwitch import (
    WebBoilerPowerSwitch,
)


def make_system(monkeypatch, installations=1):
    clock = SimpleNamespace(now=0)
    monkeypatch.setattr(transport, "monotonic", lambda: clock.now)
    system = transport.WebBoilerSystem("test@example.invalid", "private", "", True)
    system.data = transport.WebBoilerDeviceCollection(
        system.username, system._parameter_received
    )
    system.data.logger = transport._LIBRARY_LOGGER
    system.data.parse_installations(
        [
            {
                "label": f"test-{number}",
                "value": number,
                "place": "",
                "address": "",
                "type": "biopl",
                "product": "BioTec Plus",
            }
            for number in range(1, installations + 1)
        ]
    )
    system._ids = {str(device["id"]): device for device in system.data.values()}
    for device in system.data.values():
        device.logger = transport._LIBRARY_LOGGER
        for name in ("B_TMP", "B_STATE", "B_sng", "B_VER", "B_WifiVER"):
            device.create_parameter(name, "0")
        device_id = str(device["id"])
        system._available.add(device_id)
        system._last_data[device_id] = 0
    system.http_client = SimpleNamespace(
        get_installation_status_all=AsyncMock(),
        installation_status_all={},
        close_session=AsyncMock(),
    )
    system.http_helper = Mock()
    system.http_helper.get_all_devices_ids.return_value = list(
        range(1, installations + 1)
    )
    system.ws_client.client.send = AsyncMock()
    system.refresh = AsyncMock(return_value=True)
    system.relogin = AsyncMock(return_value=True)
    system._run_socket = AsyncMock()
    return system, clock


def snapshot(value, *ids):
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return {str(i): {"params": {"B_TMP": {"v": value, "ut": timestamp}}} for i in ids}


async def deliver(system, frame):
    """Pass frames through the installed library's STOMP message handler."""
    handler = system.ws_client.client.listeners["message"][-1]
    await handler(SimpleNamespace(data=frame))


async def live(system, value, number=1):
    body = json.dumps({"B_TMP": value})
    await deliver(
        system,
        f"MESSAGE\nsubscription:sub-1\n"
        f"destination:{WEB_BOILER_STOMP_DEVICE_TOPIC}biopl.test-{number}\n\n{body}\x00",
    )


async def connect(system):
    await deliver(system, "CONNECTED\nversion:1.2\n\n\x00")


def test_healthy_websocket_does_not_poll(monkeypatch):
    async def run():
        system, clock = make_system(monkeypatch)
        callback = AsyncMock()
        system._ids["1"].get_parameter("B_TMP").set_update_callback(callback)
        await system.tick()
        await connect(system)
        for clock.now in (30, 60, 90, 120):
            await live(system, "42")
            await system.tick()
        assert callback.await_count == 4
        assert system.is_websocket_connected()
        assert system._subscription == "receiving data"
        system.http_client.get_installation_status_all.assert_not_awaited()
        await system.stop()

    asyncio.run(run())


def test_stomp_error_enters_fallback_and_is_redacted(monkeypatch, caplog):
    async def run():
        system, _ = make_system(monkeypatch)
        await system.tick()
        await connect(system)
        assert system.is_websocket_connected()
        await deliver(system, "ERROR\nmessage:access_refused\n\nprivate test-1\x00")
        assert not system.is_websocket_connected()
        assert system._subscription == "rejected"
        system.http_client.installation_status_all = snapshot("42", 1)
        await system.tick()
        assert system._ids["1"].get_parameter("B_TMP")["value"] == "42"
        assert system.is_device_data_available(1)
        assert "HTTP fallback" in caplog.text
        for private in ("test-1", "test@example.invalid", "private"):
            assert private not in caplog.text
        await system.stop()

    with caplog.at_level("DEBUG"):
        asyncio.run(run())


def test_connected_but_silent_polls_at_60_seconds_and_keeps_updating(monkeypatch):
    async def run():
        system, clock = make_system(monkeypatch)
        device = system._ids["1"]
        parameter = device.get_parameter("B_TMP")
        hass = SimpleNamespace(
            data={
                DOMAIN: {
                    system.username: {
                        WEB_BOILER_CLIENT: system,
                        "web_boiler_system": system,
                    },
                }
            }
        )
        entity = WebBoilerGenericSensor(
            hass, device, ["°C", None, None, "Temperature"], parameter
        )
        values = []
        entity.async_schedule_update_ha_state = Mock()
        entity.async_write_ha_state = lambda: values.append(entity.native_value)
        await entity.async_added_to_hass()
        await system.tick()
        await connect(system)
        await deliver(system, "\n")
        await live(system, "?")
        values.clear()
        clock.now = 59
        await system.tick()
        system.http_client.get_installation_status_all.assert_not_awaited()
        first = snapshot("41", 1)
        second = snapshot("42", 1)
        third = snapshot("43", 1)
        for clock.now, payload in (
            (60, first),
            (120, second),
            (180, second),
            (240, third),
        ):
            system.http_client.installation_status_all = payload
            await system.tick()
        assert values == ["41", "42", "43"]
        assert entity.available
        assert entity.parameter is parameter
        assert entity.unique_id == "test-1-B_TMP"
        assert entity.device_info["identifiers"] == {(DOMAIN, "test-1")}
        await system.stop()

    asyncio.run(run())


def test_multiple_installations_and_recovery_during_poll(monkeypatch):
    async def run():
        system, clock = make_system(monkeypatch, 2)
        await system.tick()
        await connect(system)
        clock.now = 60
        await live(system, "70", 1)
        system.http_client.installation_status_all = snapshot("40", 1, 2)
        await system.tick()
        system.http_client.get_installation_status_all.assert_awaited_once_with([1, 2])
        assert system._ids["1"].get_parameter("B_TMP")["value"] == "70"
        assert system._ids["2"].get_parameter("B_TMP")["value"] == "40"

        async def recovered(_ids):
            await live(system, "71", 1)
            await live(system, "72", 2)

        system.http_client.get_installation_status_all.side_effect = recovered
        clock.now = 120
        await system.tick()
        assert not system._fallback
        assert system._ids["2"].get_parameter("B_TMP")["value"] == "72"
        assert system.http_client.get_installation_status_all.await_count == 2
        clock.now = 179
        await system.tick()
        assert system.http_client.get_installation_status_all.await_count == 2
        await system.stop()

    asyncio.run(run())


def test_unchanged_old_snapshot_cannot_keep_an_installation_available(monkeypatch):
    async def run():
        system, clock = make_system(monkeypatch)
        device = system._ids["1"]
        await device.update_parameter("B_TMP", "42", "2020-01-01 00:00:00")
        system.http_client.installation_status_all = {
            "1": {"params": {"B_TMP": {"v": "42", "ut": "2020-01-01 00:00:00"}}}
        }
        clock.now = 60
        await system.tick()
        assert system._last_http is None
        clock.now = 180
        await system.tick()
        assert not system.is_device_data_available(1)
        assert device.get_parameter("B_TMP")["value"] == "42"
        clock.now = 420
        system.http_client.installation_status_all = snapshot("43", 1)
        await system.tick()
        assert system.is_device_data_available(1)
        assert device.get_parameter("B_TMP")["value"] == "43"
        await system.stop()

    asyncio.run(run())


@pytest.mark.parametrize("failure", ["401", "403", "redirect"])
def test_expired_session_reauthenticates_once(monkeypatch, failure):
    async def run():
        system, clock = make_system(monkeypatch)
        if failure == "redirect":
            try:
                json.loads("<html>private</html>")
            except ValueError as error:
                expired = RuntimeError("body with private credentials")
                expired.__context__ = error
        else:
            expired = RuntimeError(f"failed with http code: {failure}")
        request = system.http_client.get_installation_status_all
        request.side_effect = [expired, expired, None]
        system.http_client.installation_status_all = snapshot("44", 1)
        clock.now = 60
        await system.tick()
        assert system._http_error == "authentication"
        system.relogin.assert_awaited_once()
        assert request.await_count == 2
        clock.now = 180
        await system.tick()
        assert system.relogin.await_count == 2
        assert system._last_http is not None
        assert system._http_error is None
        await system.stop()

    asyncio.run(run())


def test_timeout_backoff_is_bounded(monkeypatch):
    async def run():
        system, clock = make_system(monkeypatch)
        monkeypatch.setattr(transport, "REQUEST_TIMEOUT", 0)

        async def never_returns(_ids):
            await asyncio.Future()

        request = system.http_client.get_installation_status_all
        request.side_effect = never_returns
        clock.now = 60
        for delay in (120, 240, 300, 300):
            await system.tick()
            assert system._http_error == "TimeoutError"
            assert system._next_poll == clock.now + delay
            clock.now += delay - 1
            count = request.await_count
            await system.tick()
            assert request.await_count == count
            clock.now += 1
        system.relogin.assert_not_awaited()
        await system.stop()

    asyncio.run(run())


def test_no_overlap_and_stop_cancels_poll_and_socket(monkeypatch):
    async def run():
        system, clock = make_system(monkeypatch)
        started = asyncio.Event()
        cancelled = asyncio.Event()
        socket_cancelled = asyncio.Event()

        async def pending(_ids):
            started.set()
            try:
                await asyncio.Future()
            finally:
                cancelled.set()

        async def socket():
            try:
                await asyncio.Future()
            finally:
                socket_cancelled.set()

        system._run_socket.side_effect = socket
        await system.tick()
        await asyncio.sleep(0)
        clock.now = 60
        system.http_client.get_installation_status_all.side_effect = pending
        system._monitor = asyncio.create_task(system.tick())
        await started.wait()
        await system.tick()
        http = system.http_client
        http.get_installation_status_all.assert_awaited_once()
        await asyncio.gather(system.stop(), system.stop())
        assert cancelled.is_set()
        assert socket_cancelled.is_set()
        http.close_session.assert_awaited_once()

    asyncio.run(run())


@pytest.mark.parametrize("explicit_prefix", [False, True])
def test_existing_entry_ids_and_unload(monkeypatch, explicit_prefix):
    async def run():
        system, _ = make_system(monkeypatch)
        entry = Mock()
        entry.entry_id = "retained-config-entry"
        entry.unique_id = system.username
        entry.data = {
            "email": system.username,
            "password": "private",
            "id": system.username,
        }
        if explicit_prefix:
            entry.data["prefix"] = "My boiler"
            entry.data["product_prefix"] = False
        old_config = entry.data.copy()
        shutdown = Mock()
        hass = SimpleNamespace(
            data={},
            bus=Mock(),
            config_entries=SimpleNamespace(
                async_forward_entry_setups=AsyncMock(),
                async_unload_platforms=AsyncMock(return_value=True),
            ),
        )
        hass.bus.async_listen_once.return_value = shutdown
        system.load_configuration = AsyncMock(return_value=True)

        def existing_account(username, password, prefix, product_prefix):
            assert (username, password) == (system.username, "private")
            assert prefix == ("My boiler" if explicit_prefix else "")
            assert product_prefix is not explicit_prefix
            system.prefix = f"{prefix} " if prefix else ""
            system.product_prefix = product_prefix
            return system

        monkeypatch.setattr(
            "custom_components.centrometal_boiler.WebBoilerSystem", existing_account
        )
        assert await async_setup_entry(hass, entry)
        device = system._ids["1"]
        sensor = WebBoilerGenericSensor(
            hass,
            device,
            ["°C", None, None, "Temperature"],
            device.get_parameter("B_TMP"),
        )
        assert sensor.unique_id == "test-1-B_TMP"
        assert sensor.name == (
            "My boiler  Temperature" if explicit_prefix else "BioTec Plus Temperature"
        )
        assert WebBoilerPowerSwitch(hass, device).unique_id == "test-1"
        assert (
            WebBoilerCircuitSwitch(hass, device, "Circuit", 3).unique_id
            == "test-1_switch_3"
        )
        assert (
            WebBoilerWebsocketStatus(hass, system, device).unique_id
            == "test-1_websocket_status"
        )
        assert sensor.device_info["identifiers"] == {("centrometal_boiler", "test-1")}
        assert entry.entry_id == "retained-config-entry"
        assert entry.data == old_config
        entry.async_on_unload.assert_called_once_with(shutdown)
        http = system.http_client
        assert await async_unload_entry(hass, entry)
        assert hass.data[DOMAIN] == {}
        assert system._monitor is None
        http.close_session.assert_awaited_once()

    asyncio.run(run())
