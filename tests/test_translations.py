"""Translation and release-readiness checks."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EN_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "en.json"
DE_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "de.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _flatten_keys(node: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in node.items():
        full = f"{prefix}.{key}" if prefix else key
        keys.add(full)
        if isinstance(value, dict):
            keys |= _flatten_keys(value, full)
    return keys


def test_en_de_translation_key_parity() -> None:
    """English and German translation files should have full key parity."""
    en = _load(EN_PATH)
    de = _load(DE_PATH)

    en_keys = _flatten_keys(en)
    de_keys = _flatten_keys(de)

    assert en_keys == de_keys


def test_required_options_error_keys_exist_in_both_languages() -> None:
    """Ensure all runtime-used options/config error keys are translated."""
    required_error_keys = {
        "invalid_icon",
        "invalid_display_name",
        "invalid_leaf_offset",
        "invalid_leaf_icon",
        "invalid_leaf_display_name",
        "invalid_absolute_humidity_icon",
        "invalid_absolute_humidity_display_name",
        "invalid_dew_point_icon",
        "invalid_dew_point_display_name",
        "invalid_scope_id",
        "invalid_temperature_entity",
        "invalid_humidity_entity",
        "missing_source_override",
    }

    en = _load(EN_PATH)
    de = _load(DE_PATH)

    assert required_error_keys.issubset(en["options"]["error"]) 
    assert required_error_keys.issubset(de["options"]["error"]) 


def test_release_metadata_versions_match_2_0_0_line() -> None:
    """Release metadata should remain aligned for the 2.0.0 release line."""
    manifest = json.loads(
        (ROOT / "custom_components" / "vpd_air_auto" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))

    assert manifest["version"] == "2.0.0"
    assert "2.0.0" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## 2.0.0 (unreleased)" in (
        ROOT / "CHANGELOG.md"
    ).read_text(encoding="utf-8")
    assert hacs["homeassistant"]
    assert hacs["hacs"]
