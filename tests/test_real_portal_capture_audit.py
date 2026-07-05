"""End-to-end tests based on the authenticated PelTec II portal capture."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from dataclasses import dataclass
from types import SimpleNamespace

from custom_components.centrometal_boiler import binary_sensor as binary_sensor_platform
from custom_components.centrometal_boiler import sensor as sensor_platform
from custom_components.centrometal_boiler.centrometal_web_boiler.WebBoilerClient import WebBoilerClient
from custom_components.centrometal_boiler.centrometal_web_boiler.WebBoilerDeviceCollection import (
    WebBoilerDevice,
    WebBoilerDeviceCollection,
)
from custom_components.centrometal_boiler.sensors.WebBoilerConfigurationSensor import (
    WebBoilerConfigurationSensor,
)
from custom_components.centrometal_boiler.sensors.WebBoilerGenericSensor import WebBoilerGenericSensor

ROOT = Path(__file__).resolve().parents[1]
REAL_FIXTURE = ROOT / "tests" / "fixtures" / "peltec2_lambda_real_snapshot.json"
HTTP_FIXTURE = ROOT / "tests" / "fixtures" / "peltec2_lambda_http_snapshot.json"
SERIAL = "672E853E"
ENTRY_ID = "peltec2-test-entry"


@dataclass
class RegistryEntry:
    entity_id: str
    unique_id: str
    config_entry_id: str


class EntityRegistry:
    def __init__(self) -> None:
        self.entities: dict[str, RegistryEntry] = {}

    def async_remove(self, entity_id: str) -> None:
        self.entities.pop(entity_id, None)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def _make_device(snapshot: dict[str, object] | None = None) -> WebBoilerDevice:
    device = WebBoilerDevice("user@example.com")
    device.update(
        {
            "id": 7280,
            "serial": SERIAL,
            "place": "Boiler room",
            "address": "Test address",
            "type": "peltec2",
            "product": "PelTec II Lambda",
            "__client": None,
            "__system": None,
            "__prefix": "",
            "__multi_device": False,
        }
    )
    for code, value in (snapshot or {}).items():
        device.create_parameter(code, value)
    return device


def _make_client(device: WebBoilerDevice) -> WebBoilerClient:
    client = WebBoilerClient(None)
    client.data = WebBoilerDeviceCollection("user@example.com")
    client.data[SERIAL] = device
    client.websocket_connected = True
    device["__client"] = client
    return client


async def _run_sensor_setup(device: WebBoilerDevice, registry: EntityRegistry | None = None) -> list:
    client = _make_client(device)
    registry = registry or EntityRegistry()
    hass = SimpleNamespace(entity_registry=registry)
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(client=client),
        entry_id=ENTRY_ID,
    )
    added: list = []

    original_async_get = sensor_platform.er.async_get
    original_entries = sensor_platform.er.async_entries_for_config_entry
    sensor_platform.er.async_get = lambda _hass: registry
    sensor_platform.er.async_entries_for_config_entry = lambda reg, entry_id: [
        item for item in reg.entities.values() if item.config_entry_id == entry_id
    ]
    try:
        await sensor_platform.async_setup_entry(hass, entry, lambda entities, update=True: added.extend(entities))
    finally:
        sensor_platform.er.async_get = original_async_get
        sensor_platform.er.async_entries_for_config_entry = original_entries
    return added


async def _run_binary_setup(device: WebBoilerDevice) -> list:
    client = _make_client(device)
    entry = SimpleNamespace(runtime_data=SimpleNamespace(client=client), entry_id=ENTRY_ID)
    added: list = []
    await binary_sensor_platform.async_setup_entry(None, entry, lambda entities, update=True: added.extend(entities))
    return added


def _by_parameter(entities: list) -> dict[str, object]:
    return {entity._param_name: entity for entity in entities if getattr(entity, "_param_name", None) is not None}


def test_real_fixtures_have_expected_capture_sizes() -> None:
    assert len(_load(REAL_FIXTURE)) == 151
    assert len(_load(HTTP_FIXTURE)) == 231


def test_full_real_snapshot_creates_only_clean_peltec2_entities() -> None:
    device = _make_device(_load(REAL_FIXTURE))
    entities = asyncio.run(_run_sensor_setup(device))

    # Every exposed entity must be readable through the same native-value path
    # Home Assistant invokes on state writes.
    for entity in entities:
        entity.native_value

    names = [entity.name for entity in entities]
    assert all("(Hidden)" not in name for name in names)
    assert all("(unverified)" not in name.lower() for name in names)
    assert all("(raw)" not in name.lower() for name in names)
    assert all("B_" not in name for name in names)
    assert all("Weather" not in name for name in names)
    assert all("Schedule" not in name for name in names)
    assert all(entity.__class__.__name__ != "WebBoilerWorkingTableSensor" for entity in entities)


def test_exact_clutter_parameters_from_device_page_are_not_created() -> None:
    device = _make_device(_load(REAL_FIXTURE))
    entities = asyncio.run(_run_sensor_setup(device))
    exposed = set(_by_parameter(entities))

    forbidden = {
        "B_ashC",
        "B_ashSc",
        "B_bcl",
        "B_bim",
        "B_Inp1",  # decoded as a binary sensor, never exposed raw
        "B_Out1",
        "B_fanO",
        "B_puzOff",
        "B_puzOffO",
        "B_puzOn",
        "B_puzOnO",
        "B_sob",
        "B_sob2",
        "B_StsB1",
        "B_StsN1",
        "B_addConf",
        "B_cm2k",
        "B_zahPa",
        "B_zahK1_K2",
        "B_zahValve",
        "K1B_CircType",
        "K1B_dayNight",
        "K1B_kor",
        "K1B_korN",
        "K1B_korType",
        "K1B_Prec",
    }
    assert exposed.isdisjoint(forbidden)


def test_portal_confirmed_values_and_invalid_sentinels() -> None:
    device = _make_device(_load(REAL_FIXTURE))
    entities = asyncio.run(_run_sensor_setup(device))
    by_param = _by_parameter(entities)

    assert by_param["B_SUP_TYPE"].native_value == "Supervision + control"
    assert by_param["B_signal"].native_value is None
    assert by_param["B_signal"].available is False
    assert by_param["B_signal"].native_unit_of_measurement == "dB"
    assert by_param["B_signal"].state_class is None
    assert by_param["B_signal"].extra_state_attributes["Signal reported by controller"] is False
    assert by_param["B_specG"].native_value == "None"
    assert by_param["B_start"].native_value == "Idle"
    assert by_param["B_Oxy1"].native_value == 25.5
    assert by_param["B_Oxy1"].available is True
    assert by_param["B_Oxy1"].extra_state_attributes["Measurement active"] is False
    assert by_param["B_Oxy1"].extra_state_attributes["Flame detected"] is False
    assert by_param["B_Tk1"].native_value == 25.3
    assert by_param["B_Tk1"].name.endswith("Boiler Temperature")
    assert by_param["B_Ths1"].native_value is None
    assert by_param["B_Ths1"].available is False
    assert by_param["K1B_Tsob1"].native_value is None
    assert by_param["K1B_Tsob1"].available is False
    assert by_param["K1B_P"].native_value == "Off"
    assert by_param["K1B_Tpol1"].native_value == 53.7
    assert by_param["K1B_Tpol"].native_value == 50.0
    assert by_param["K1B_Tpol"].state_class is None
    assert by_param["K1B_Tsob"].native_value == 20.0
    assert by_param["K1B_Tsob"].state_class is None
    assert by_param["K1B_onOff"].native_value == "On"
    assert by_param["K1B_zahP"].native_value == "Off"
    assert by_param["B_P1"].native_value == "Off"
    assert by_param["B_P1"].name.endswith("P1 Pump")
    assert by_param["B_gri"].native_value == "Off"
    assert by_param["B_razina"].native_value == "Full"
    assert by_param["B_razP"].native_value == 99.0
    assert by_param["B_FILE"].name.endswith("Active File")
    assert by_param["B_sng"].native_value == 36.0
    assert by_param["B_sng"].native_unit_of_measurement == "kW"
    assert by_param["B_Tkm1"].name.endswith("DHW Tank Temperature")
    assert by_param["B_specG"].extra_state_attributes["Meaning"] == "No special shutdown activity"
    assert "B_PTV_PRI" not in by_param
    assert "B_bup" not in by_param
    assert "B_REC" not in by_param
    assert "B_REO" not in by_param



def test_optional_dhw_and_buffer_states_follow_controller_configuration() -> None:
    device = _make_device(
        {
            "B_KONF": 4,  # DHW || BUF
            "B_PTV_PRI": 1,
            "B_bup": 1,
            "B_REC": 0,
            "B_REO": 0,
        }
    )
    entities = asyncio.run(_run_sensor_setup(device))
    by_param = _by_parameter(entities)

    assert by_param["B_PTV_PRI"].native_value == "On"
    assert by_param["B_bup"].native_value == "On"
    assert by_param["B_REC"].native_value == "Off"
    assert by_param["B_REO"].native_value == "Off"

    no_dhw_or_buffer = _make_device(
        {
            "B_KONF": 12,  # DHC 2X
            "B_PTV_PRI": 1,
            "B_bup": 1,
            "B_REC": 0,
            "B_REO": 0,
        }
    )
    hidden = _by_parameter(asyncio.run(_run_sensor_setup(no_dhw_or_buffer)))
    assert {"B_PTV_PRI", "B_bup", "B_REC", "B_REO"}.isdisjoint(hidden)

def test_documented_screen_telemetry_from_full_http_snapshot() -> None:
    device = _make_device(_load(HTTP_FIXTURE))
    entities = asyncio.run(_run_sensor_setup(device))
    by_param = _by_parameter(entities)

    assert by_param["B_FotV"].native_value == 1001.0
    assert by_param["B_FotV"].extra_state_attributes["Over range"] is True
    assert by_param["B_fan"].native_value == 0.0
    assert by_param["B_misP"].native_value == 0.0
    assert by_param["B_puz"].native_value == "Off"
    assert by_param["B_tur"].native_value == "Off"
    assert by_param["B_resInd"].name.endswith("Burner Grate Position")
    assert by_param["B_resInd"].extra_state_attributes["Grate state"] == "Closed - ready to operate"



def test_corrected_counter_names_units_and_statistics() -> None:
    device = _make_device(_load(REAL_FIXTURE))
    entities = asyncio.run(_run_sensor_setup(device))
    by_param = _by_parameter(entities)

    assert by_param["CNT_0"].name.endswith("Boiler Work + Standby Time")
    assert by_param["CNT_0"].native_unit_of_measurement == "min"
    assert by_param["CNT_15"].name.endswith("Boiler Work Time")
    assert by_param["CNT_15"].native_unit_of_measurement == "min"
    assert by_param["CNT_15"].state_class == "total_increasing"

def test_lambda_entity_is_created_before_a_reading_exists_and_recovers() -> None:
    device = _make_device({"B_STATE": "OFF"})
    entities = asyncio.run(_run_sensor_setup(device))
    by_param = _by_parameter(entities)

    lambda_entity = by_param["B_Oxy1"]
    assert lambda_entity.native_value is None
    assert lambda_entity.available is False

    asyncio.run(device.update_parameter("B_Oxy1", "25.5"))
    assert lambda_entity.native_value == 25.5
    assert lambda_entity.available is True

    asyncio.run(device.update_parameter("B_Oxy1", "12.7"))
    assert lambda_entity.native_value == 12.7
    assert lambda_entity.available is True


def test_new_operation_stages_keep_existing_text_state_format() -> None:
    for raw, expected_group in (("S3-1", "ignition_startup"), ("S3-2", "ignition_startup"), ("S7", "shutdown")):
        device = _make_device({"B_STATE": raw})
        entities = asyncio.run(_run_sensor_setup(device))
        state = _by_parameter(entities)["B_STATE"]
        assert state.native_value.startswith(f"{raw}:")
        assert state.extra_state_attributes["Stage group"] == expected_group


def test_start_pause_override_is_portal_compatible() -> None:
    device = _make_device({"B_start": "1", "B_STATE": "S7-3"})
    entities = WebBoilerGenericSensor.create_conf_entities(None, device)
    entity = next(entity for entity in entities if entity._param_name == "B_start")
    assert entity.native_value == "Paused / standby"


def test_configuration_12_maps_to_portal_configuration_13() -> None:
    device = _make_device({"B_KONF": "12"})
    entity = WebBoilerConfigurationSensor.create_entities(None, device)[0]
    assert entity.native_value == "13. DHC 2X"


def test_external_start_is_decoded_without_a_raw_auxiliary_input_sensor() -> None:
    device = _make_device({"B_Inp1": "28"})
    binary_entities = asyncio.run(_run_binary_setup(device))
    external = next(entity for entity in binary_entities if entity.unique_id.endswith("B_Inp1-bit6"))
    assert external.is_on is False
    assert external.extra_state_attributes["raw_value"] == "28"

    sensor_entities = asyncio.run(_run_sensor_setup(device))
    assert "B_Inp1" not in _by_parameter(sensor_entities)


def test_schedule_values_are_dropped_during_http_ingestion() -> None:
    snapshot = _load(HTTP_FIXTURE)
    device = _make_device()
    collection = WebBoilerDeviceCollection("user@example.com")
    collection[SERIAL] = device
    payload = {
        str(device["id"]): {
            "installation": {"country": "Romania", "countryCode": "ro"},
            "params": {code: {"v": value, "ut": "2026-07-04 17:16:36"} for code, value in snapshot.items()},
        }
    }
    asyncio.run(collection.parse_installation_statuses(payload))

    assert not any(
        code.startswith(("PVAL_223_", "PVAL_224_", "PVAL_225_", "PVAL_226_")) for code in device["parameters"]
    )
    assert not any(code.startswith(("PDEF_223_", "PMIN_224_", "PMAX_224_")) for code in device["parameters"])
    assert "B_Tk1" in device["parameters"]


def test_schedule_values_are_dropped_during_websocket_ingestion() -> None:
    device = _make_device({"B_Tk1": "20"})
    collection = WebBoilerDeviceCollection("user@example.com")
    collection[SERIAL] = device
    frame = {
        "headers": {
            "subscription": "sub-1",
            "destination": f"/topic/cm.inst.peltec2.{SERIAL}",
        },
        "body": '{"PVAL_223_0":"1","PVAL_224_0":"33818","B_Tk1":"31.5"}',
    }
    asyncio.run(collection.parse_real_time_frame(frame))
    assert "PVAL_223_0" not in device["parameters"]
    assert "PVAL_224_0" not in device["parameters"]
    assert device.get_parameter("B_Tk1")["value"] == "31.5"


def test_weather_group_is_discarded_at_parameter_list_parse() -> None:
    device = _make_device()
    collection = WebBoilerDeviceCollection("user@example.com")
    collection[SERIAL] = device
    collection.parse_parameter_lists(
        {
            SERIAL: {
                "city": "Test",
                "parameters": [
                    {
                        "group": "Weather forecast",
                        "list": [{"naslov": "Monday", "forecast_min": 1, "forecast_max": 2}],
                    },
                    {
                        "group": "Temperatures",
                        "list": [{"dbindex": 67, "naslov": "Buffer tank temperature"}],
                    },
                ],
            }
        }
    )
    assert "weather" not in device
    assert not device.has_parameter("Weather_Forecast")
    assert 67 in device["temperatures"]


def test_obsolete_hidden_weather_and_schedule_registry_entries_are_removed() -> None:
    device = _make_device(_load(REAL_FIXTURE))
    registry = EntityRegistry()
    registry.entities = {
        "sensor.old_hidden": RegistryEntry("sensor.old_hidden", f"{SERIAL}-B_bcl", ENTRY_ID),
        "sensor.old_weather": RegistryEntry("sensor.old_weather", f"{SERIAL}-Weather_Forecast", ENTRY_ID),
        "sensor.old_schedule": RegistryEntry("sensor.old_schedule", f"{SERIAL}-working-table", ENTRY_ID),
        "sensor.keep": RegistryEntry("sensor.keep", f"{SERIAL}-B_Tk1", ENTRY_ID),
        "binary_sensor.keep": RegistryEntry("binary_sensor.keep", f"{SERIAL}-B_Inp1-bit6", ENTRY_ID),
        "sensor.other_integration": RegistryEntry("sensor.other_integration", "other-id", "another-entry"),
    }

    asyncio.run(_run_sensor_setup(device, registry))

    assert "sensor.old_hidden" not in registry.entities
    assert "sensor.old_weather" not in registry.entities
    assert "sensor.old_schedule" not in registry.entities
    assert "sensor.keep" in registry.entities
    assert "binary_sensor.keep" in registry.entities
    assert "sensor.other_integration" in registry.entities
