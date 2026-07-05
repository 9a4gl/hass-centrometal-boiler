from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_has_required_custom_integration_keys() -> None:
    manifest = json.loads((ROOT / "custom_components/centrometal_boiler/manifest.json").read_text())

    for key in ("domain", "documentation", "issue_tracker", "codeowners", "name", "version"):
        assert key in manifest

    assert manifest["domain"] == "centrometal_boiler"
    assert manifest["version"] == "0.2.0.11"


def test_hacs_metadata_exists() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text())

    assert hacs["name"] == "Centrometal Boiler System"
    assert hacs["content_in_root"] is False


def test_hacs_metadata_uses_supported_keys_only() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert set(hacs) == {"name", "content_in_root", "homeassistant", "country"}
