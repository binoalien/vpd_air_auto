"""Translation and release QA tests."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EN_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "en.json"
DE_PATH = ROOT / "custom_components" / "vpd_air_auto" / "translations" / "de.json"


REQUIRED_OPTION_ERROR_KEYS = {
    "invalid_scope_id",
    "invalid_temperature_entity",
    "invalid_humidity_entity",
    "missing_source_override",
    "no_area_policies",
    "no_device_policies",
    "no_source_overrides",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_keys(prefix: str, value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            key = f"{prefix}.{k}" if prefix else k
            keys.add(key)
            keys.update(_walk_keys(key, v))
    return keys


def test_translation_key_parity_between_english_and_german() -> None:
    """English and German translation trees should expose the same key paths."""
    en = _load(EN_PATH)
    de = _load(DE_PATH)

    en_keys = _walk_keys("", en)
    de_keys = _walk_keys("", de)

    assert en_keys == de_keys


def test_required_option_error_keys_exist_in_both_languages() -> None:
    """Release-critical options-flow error keys must exist in EN and DE."""
    en = _load(EN_PATH)
    de = _load(DE_PATH)

    en_errors = set(en["options"]["error"].keys())
    de_errors = set(de["options"]["error"].keys())

    assert REQUIRED_OPTION_ERROR_KEYS <= en_errors
    assert REQUIRED_OPTION_ERROR_KEYS <= de_errors


def test_release_metadata_is_aligned_for_2_0_0() -> None:
    """Version metadata and release docs should be consistent for 2.0.0."""
    manifest = json.loads(
        (ROOT / "custom_components" / "vpd_air_auto" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert manifest["version"] == "2.0.0"
    assert "## 2.0.0 (unreleased)" in changelog
    assert "Current release line: **2.0.0**." in readme
    assert hacs["homeassistant"]
    assert hacs["hacs"]
