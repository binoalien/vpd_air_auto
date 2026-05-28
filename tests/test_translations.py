"""Tests for translation parity and release metadata readiness."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "en.json"
DE_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "de.json"
HACS_PATH = ROOT / "hacs.json"
MANIFEST_PATH = ROOT / "custom_components" / "vpd_air_auto" / "manifest.json"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _flatten_keys(node: object, prefix: str = "") -> set[str]:
    if not isinstance(node, dict):
        return set()
    keys: set[str] = set()
    for key, value in node.items():
        dotted = f"{prefix}.{key}" if prefix else key
        keys.add(dotted)
        keys |= _flatten_keys(value, dotted)
    return keys


def test_en_and_de_translation_key_parity() -> None:
    """English and German translation trees should have identical key sets."""
    en = _load_json(EN_PATH)
    de = _load_json(DE_PATH)

    en_keys = _flatten_keys(en)
    de_keys = _flatten_keys(de)

    assert en_keys == de_keys


def test_release_required_translation_error_keys_exist() -> None:
    """Release-critical options/config errors and abort reasons are present."""
    en = _load_json(EN_PATH)

    assert "single_instance_allowed" in en["config"]["abort"]

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

    assert required_error_keys.issubset(set(en["options"]["error"].keys()))


def test_release_version_metadata_is_consistent() -> None:
    """Release metadata should consistently target 2.0.0."""
    hacs = _load_json(HACS_PATH)
    manifest = _load_json(MANIFEST_PATH)

    assert manifest["version"] == "2.0.0"
    assert hacs["homeassistant"]
    assert hacs["hacs"]


def test_changelog_release_heading_is_not_unreleased() -> None:
    """Changelog release heading should be ready for 2.0.0 tagging."""
    changelog = CHANGELOG_PATH.read_text(encoding="utf-8")

    assert "## 2.0.0 (unreleased)" not in changelog
    assert "## 2.0.0" in changelog
