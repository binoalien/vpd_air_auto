"""Tests for option helpers and schemas."""

from __future__ import annotations

import pytest
import voluptuous as vol
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import (
    CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    CONF_ABSOLUTE_HUMIDITY_ICON,
    CONF_DEW_POINT_DISPLAY_NAME,
    CONF_DEW_POINT_ICON,
    CONF_DISPLAY_NAME,
    CONF_ENABLE_ABSOLUTE_HUMIDITY,
    CONF_ENABLE_AIR,
    CONF_ENABLE_DEW_POINT,
    CONF_ENABLE_LEAF,
    CONF_ICON,
    CONF_LEAF_DISPLAY_NAME,
    CONF_LEAF_ICON,
    CONF_LEAF_OFFSET,
    CONF_SCAN_INTERVAL,
    DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    DEFAULT_ABSOLUTE_HUMIDITY_ICON,
    DEFAULT_DEW_POINT_DISPLAY_NAME,
    DEFAULT_DEW_POINT_ICON,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_ENABLE_ABSOLUTE_HUMIDITY,
    DEFAULT_ENABLE_AIR,
    DEFAULT_ENABLE_DEW_POINT,
    DEFAULT_ENABLE_LEAF,
    DEFAULT_ICON,
    DEFAULT_LEAF_DISPLAY_NAME,
    DEFAULT_LEAF_ICON,
    DEFAULT_LEAF_OFFSET,
    DEFAULT_SCAN_INTERVAL,
    MAX_LEAF_OFFSET,
    MAX_SCAN_INTERVAL,
    MIN_LEAF_OFFSET,
    MIN_SCAN_INTERVAL,
)
from custom_components.vpd_air_auto.options import (
    build_schema,
    normalize_user_input,
    resolve_options,
    trimmed_nonempty_string,
    validated_leaf_offset,
)


def _valid_input() -> dict[str, object]:
    return {
        CONF_SCAN_INTERVAL: 600,
        CONF_ENABLE_AIR: True,
        CONF_ENABLE_LEAF: False,
        CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
        CONF_ENABLE_DEW_POINT: True,
        CONF_ICON: "  mdi:water-opacity ",
        CONF_DISPLAY_NAME: "  VPDair  ",
        CONF_LEAF_ICON: " mdi:leaf ",
        CONF_LEAF_DISPLAY_NAME: " Leaf VPD ",
        CONF_LEAF_OFFSET: -1.26,
        CONF_ABSOLUTE_HUMIDITY_ICON: " mdi:water ",
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: " Absolute Humidity ",
        CONF_DEW_POINT_ICON: " mdi:thermometer-water ",
        CONF_DEW_POINT_DISPLAY_NAME: " Dew Point ",
    }


def test_trimmed_nonempty_string_returns_trimmed_value() -> None:
    """Test trimmed nonempty string returns trimmed value."""
    assert trimmed_nonempty_string("  hello  ", "invalid") == "hello"


@pytest.mark.parametrize("value", [None, 123, "   ", ""])
def test_trimmed_nonempty_string_raises_for_invalid_values(value) -> None:
    """Test trimmed nonempty string raises for invalid values."""
    with pytest.raises(vol.Invalid, match="invalid_field"):
        trimmed_nonempty_string(value, "invalid_field")


def test_validated_leaf_offset_rounds_to_one_decimal() -> None:
    """Test validated leaf offset rounds to one decimal."""
    assert validated_leaf_offset(-1.26) == -1.3


@pytest.mark.parametrize(
    "value", [None, "abc", MIN_LEAF_OFFSET - 0.1, MAX_LEAF_OFFSET + 0.1]
)
def test_validated_leaf_offset_rejects_invalid_values(value) -> None:
    """Test validated leaf offset rejects invalid values."""
    with pytest.raises(vol.Invalid, match="invalid_leaf_offset"):
        validated_leaf_offset(value)


def test_resolve_options_prefers_entry_options_over_entry_data() -> None:
    """Test resolve options prefers entry options over entry data."""
    entry = MockConfigEntry(
        domain="vpd_air_auto",
        data={
            CONF_SCAN_INTERVAL: 300,
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: True,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: False,
            CONF_ENABLE_DEW_POINT: False,
            CONF_ICON: "mdi:data",
            CONF_DISPLAY_NAME: "Data Air",
            CONF_LEAF_ICON: "mdi:data-leaf",
            CONF_LEAF_DISPLAY_NAME: "Data Leaf",
            CONF_LEAF_OFFSET: -2.0,
            CONF_ABSOLUTE_HUMIDITY_ICON: "mdi:data-water",
            CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "Data Absolute",
            CONF_DEW_POINT_ICON: "mdi:data-dew",
            CONF_DEW_POINT_DISPLAY_NAME: "Data Dew",
        },
        options={
            CONF_SCAN_INTERVAL: 900,
            CONF_ENABLE_AIR: True,
            CONF_ENABLE_LEAF: False,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
            CONF_ENABLE_DEW_POINT: True,
            CONF_ICON: "mdi:option",
            CONF_DISPLAY_NAME: "Option Air",
            CONF_LEAF_ICON: "mdi:option-leaf",
            CONF_LEAF_DISPLAY_NAME: "Option Leaf",
            CONF_LEAF_OFFSET: -1.5,
            CONF_ABSOLUTE_HUMIDITY_ICON: "mdi:option-water",
            CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "Option Absolute",
            CONF_DEW_POINT_ICON: "mdi:option-dew",
            CONF_DEW_POINT_DISPLAY_NAME: "Option Dew",
        },
    )

    resolved = resolve_options(entry)

    assert resolved.scan_interval_seconds == 900
    assert resolved.enable_air is True
    assert resolved.enable_leaf is False
    assert resolved.enable_absolute_humidity is True
    assert resolved.enable_dew_point is True
    assert resolved.icon == "mdi:option"
    assert resolved.display_name == "Option Air"
    assert resolved.leaf_icon == "mdi:option-leaf"
    assert resolved.leaf_display_name == "Option Leaf"
    assert resolved.leaf_offset_c == -1.5
    assert resolved.absolute_humidity_icon == "mdi:option-water"
    assert resolved.absolute_humidity_display_name == "Option Absolute"
    assert resolved.dew_point_icon == "mdi:option-dew"
    assert resolved.dew_point_display_name == "Option Dew"


def test_resolve_options_falls_back_to_entry_data_and_defaults() -> None:
    """Test resolve options falls back to entry data and defaults."""
    entry = MockConfigEntry(
        domain="vpd_air_auto",
        data={CONF_SCAN_INTERVAL: 1200, CONF_ENABLE_AIR: False},
        options={},
    )

    resolved = resolve_options(entry)

    assert resolved.scan_interval_seconds == 1200
    assert resolved.enable_air is False
    assert resolved.enable_leaf is DEFAULT_ENABLE_LEAF
    assert resolved.enable_absolute_humidity is DEFAULT_ENABLE_ABSOLUTE_HUMIDITY
    assert resolved.enable_dew_point is DEFAULT_ENABLE_DEW_POINT
    assert resolved.icon == DEFAULT_ICON
    assert resolved.display_name == DEFAULT_DISPLAY_NAME
    assert resolved.leaf_icon == DEFAULT_LEAF_ICON
    assert resolved.leaf_display_name == DEFAULT_LEAF_DISPLAY_NAME
    assert resolved.leaf_offset_c == DEFAULT_LEAF_OFFSET
    assert resolved.absolute_humidity_icon == DEFAULT_ABSOLUTE_HUMIDITY_ICON
    assert (
        resolved.absolute_humidity_display_name
        == DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME
    )
    assert resolved.dew_point_icon == DEFAULT_DEW_POINT_ICON
    assert resolved.dew_point_display_name == DEFAULT_DEW_POINT_DISPLAY_NAME


def test_resolve_options_tolerates_malformed_stored_values() -> None:
    """Malformed stored values should gracefully fall back to defaults."""
    entry = MockConfigEntry(
        domain="vpd_air_auto",
        data={
            CONF_SCAN_INTERVAL: "nan",
            CONF_ENABLE_AIR: "false",
            CONF_ICON: "   ",
            CONF_LEAF_OFFSET: "bad",
        },
        options={
            CONF_ENABLE_LEAF: "true",
            CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: None,
        },
    )

    resolved = resolve_options(entry)

    assert resolved.scan_interval_seconds == DEFAULT_SCAN_INTERVAL
    assert resolved.enable_air is DEFAULT_ENABLE_AIR
    assert resolved.enable_leaf is DEFAULT_ENABLE_LEAF
    assert resolved.icon == DEFAULT_ICON
    assert resolved.leaf_offset_c == DEFAULT_LEAF_OFFSET
    assert (
        resolved.absolute_humidity_display_name
        == DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME
    )


def test_resolve_options_falls_back_to_data_when_options_invalid() -> None:
    """Malformed option values should fall back to valid entry.data values."""
    entry = MockConfigEntry(
        domain="vpd_air_auto",
        data={
            CONF_SCAN_INTERVAL: 750,
            CONF_LEAF_OFFSET: -1.1,
            CONF_DISPLAY_NAME: "Data Display",
        },
        options={
            CONF_SCAN_INTERVAL: "bad",
            CONF_LEAF_OFFSET: "inf",
            CONF_DISPLAY_NAME: "   ",
        },
    )

    resolved = resolve_options(entry)

    assert resolved.scan_interval_seconds == 750
    assert resolved.leaf_offset_c == -1.1
    assert resolved.display_name == "Data Display"


def test_resolve_options_uses_defaults_when_both_sources_invalid() -> None:
    """Defaults are used when both options and data values are invalid."""
    entry = MockConfigEntry(
        domain="vpd_air_auto",
        data={
            CONF_SCAN_INTERVAL: "nope",
            CONF_LEAF_OFFSET: "nan",
            CONF_DISPLAY_NAME: " ",
        },
        options={
            CONF_SCAN_INTERVAL: None,
            CONF_LEAF_OFFSET: "-inf",
            CONF_DISPLAY_NAME: None,
        },
    )

    resolved = resolve_options(entry)

    assert resolved.scan_interval_seconds == DEFAULT_SCAN_INTERVAL
    assert resolved.leaf_offset_c == DEFAULT_LEAF_OFFSET
    assert resolved.display_name == DEFAULT_DISPLAY_NAME


def test_resolve_options_leaf_offset_inf_falls_back_to_data() -> None:
    """Non-finite option leaf offset should use valid data leaf offset."""
    entry = MockConfigEntry(
        domain="vpd_air_auto",
        data={CONF_LEAF_OFFSET: -1.6},
        options={CONF_LEAF_OFFSET: "inf"},
    )

    resolved = resolve_options(entry)
    assert resolved.leaf_offset_c == -1.6


def test_build_schema_applies_defaults_and_validates_scan_interval_bounds() -> None:
    """Test build schema applies defaults and validates scan interval bounds."""
    options = resolve_options(
        MockConfigEntry(domain="vpd_air_auto", data={}, options={})
    )
    schema = build_schema(options)

    normalized: dict = schema({})  # type: ignore[assignment]
    assert normalized[CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL
    assert normalized[CONF_ENABLE_AIR] is DEFAULT_ENABLE_AIR
    assert normalized[CONF_ENABLE_LEAF] is DEFAULT_ENABLE_LEAF
    assert normalized[CONF_ENABLE_ABSOLUTE_HUMIDITY] is DEFAULT_ENABLE_ABSOLUTE_HUMIDITY
    assert normalized[CONF_ENABLE_DEW_POINT] is DEFAULT_ENABLE_DEW_POINT
    assert normalized[CONF_ICON] == DEFAULT_ICON
    assert normalized[CONF_DISPLAY_NAME] == DEFAULT_DISPLAY_NAME
    assert normalized[CONF_LEAF_ICON] == DEFAULT_LEAF_ICON
    assert normalized[CONF_LEAF_DISPLAY_NAME] == DEFAULT_LEAF_DISPLAY_NAME
    assert normalized[CONF_LEAF_OFFSET] == DEFAULT_LEAF_OFFSET
    assert normalized[CONF_ABSOLUTE_HUMIDITY_ICON] == DEFAULT_ABSOLUTE_HUMIDITY_ICON
    assert (
        normalized[CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME]
        == DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME
    )
    assert normalized[CONF_DEW_POINT_ICON] == DEFAULT_DEW_POINT_ICON
    assert normalized[CONF_DEW_POINT_DISPLAY_NAME] == DEFAULT_DEW_POINT_DISPLAY_NAME

    with pytest.raises(vol.Invalid):
        schema({CONF_SCAN_INTERVAL: MIN_SCAN_INTERVAL - 1})
    with pytest.raises(vol.Invalid):
        schema({CONF_SCAN_INTERVAL: MAX_SCAN_INTERVAL + 1})


def test_normalize_user_input_returns_trimmed_and_rounded_values() -> None:
    """Test normalize user input returns trimmed and rounded values."""
    normalized, errors = normalize_user_input(_valid_input())

    assert not errors
    assert normalized[CONF_ICON] == "mdi:water-opacity"
    assert normalized[CONF_DISPLAY_NAME] == "VPDair"
    assert normalized[CONF_LEAF_ICON] == "mdi:leaf"
    assert normalized[CONF_LEAF_DISPLAY_NAME] == "Leaf VPD"
    assert normalized[CONF_LEAF_OFFSET] == -1.3
    assert normalized[CONF_ABSOLUTE_HUMIDITY_ICON] == "mdi:water"
    assert normalized[CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME] == "Absolute Humidity"
    assert normalized[CONF_DEW_POINT_ICON] == "mdi:thermometer-water"
    assert normalized[CONF_DEW_POINT_DISPLAY_NAME] == "Dew Point"


def test_normalize_user_input_collects_all_field_errors() -> None:
    """Test normalize user input collects all field errors."""
    invalid = _valid_input()
    invalid[CONF_ICON] = "  "
    invalid[CONF_DISPLAY_NAME] = None
    invalid[CONF_LEAF_ICON] = ""
    invalid[CONF_LEAF_DISPLAY_NAME] = 123
    invalid[CONF_LEAF_OFFSET] = MAX_LEAF_OFFSET + 1
    invalid[CONF_ABSOLUTE_HUMIDITY_ICON] = "   "
    invalid[CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME] = ""
    invalid[CONF_DEW_POINT_ICON] = "  "
    invalid[CONF_DEW_POINT_DISPLAY_NAME] = None

    normalized, errors = normalize_user_input(invalid)

    assert normalized[CONF_SCAN_INTERVAL] == 600
    assert errors == {
        CONF_ICON: "invalid_icon",
        CONF_DISPLAY_NAME: "invalid_display_name",
        CONF_LEAF_ICON: "invalid_leaf_icon",
        CONF_LEAF_DISPLAY_NAME: "invalid_leaf_display_name",
        CONF_LEAF_OFFSET: "invalid_leaf_offset",
        CONF_ABSOLUTE_HUMIDITY_ICON: "invalid_absolute_humidity_icon",
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "invalid_absolute_humidity_display_name",
        CONF_DEW_POINT_ICON: "invalid_dew_point_icon",
        CONF_DEW_POINT_DISPLAY_NAME: "invalid_dew_point_display_name",
    }
