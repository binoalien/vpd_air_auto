"""Translation and release-readiness tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "en.json"
DE_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "de.json"
HACS_PATH = ROOT / "hacs.json"
MANIFEST_PATH = ROOT / "custom_components" / "vpd_air_auto" / "manifest.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _flatten_keys(obj: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in obj.items():
        full = f"{prefix}.{key}" if prefix else key
        keys.add(full)
        if isinstance(value, dict):
            keys |= _flatten_keys(value, full)
    return keys


def test_en_de_translation_keys_are_identical() -> None:
    """English and German translation trees must expose the same keys."""
    en = _load(EN_PATH)
    de = _load(DE_PATH)

    en_keys = _flatten_keys(en)
    de_keys = _flatten_keys(de)

    assert en_keys == de_keys


def test_required_flow_error_and_abort_keys_exist() -> None:
    """Expected flow errors/abort reasons for 2.0.0 docs UX must be present."""
    en = _load(EN_PATH)

    assert "single_instance_allowed" in en["config"]["abort"]

    required_error_keys = {
        "invalid_scope_id",
        "missing_source_override",
        "invalid_temperature_entity",
        "invalid_humidity_entity",
    }
    assert required_error_keys.issubset(set(en["options"]["error"].keys()))


def test_release_metadata_versions_are_consistent() -> None:
    """hacs.json and manifest.json should both reflect the 2.0.0 line."""
    hacs = _load(HACS_PATH)
    manifest = _load(MANIFEST_PATH)

    assert manifest["version"] == "2.0.0"
    assert hacs["homeassistant"]
    assert hacs["hacs"]
