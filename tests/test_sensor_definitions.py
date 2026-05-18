"""Tests for declarative sensor definitions."""

from __future__ import annotations

from custom_components.vpd_air_auto.const import (
    DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    DEFAULT_ABSOLUTE_HUMIDITY_ICON,
    DEFAULT_DEW_POINT_DISPLAY_NAME,
    DEFAULT_DEW_POINT_ICON,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_ICON,
    DEFAULT_LEAF_DISPLAY_NAME,
    DEFAULT_LEAF_ICON,
    UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY,
    UNIQUE_ID_SUFFIX_AIR,
    UNIQUE_ID_SUFFIX_DEW_POINT,
    UNIQUE_ID_SUFFIX_LEAF,
    UNIT_GM3,
    UNIT_KPA,
)
from custom_components.vpd_air_auto.domain.enums import SensorKind
from custom_components.vpd_air_auto.domain.sensor_definitions import (
    SENSOR_DEFINITIONS,
    definition_for,
)
from custom_components.vpd_air_auto.models import DeviceSnapshot


def _snapshot() -> DeviceSnapshot:
    return DeviceSnapshot(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.temp",
        humidity_entity_id="sensor.hum",
        temperature_c=25.0,
        humidity_pct=60.0,
        leaf_offset_c=-2.0,
        leaf_temperature_c=23.0,
        dew_point_c=16.68,
        vpd_air_kpa=1.27,
        vpd_leaf_kpa=1.58,
        absolute_humidity_gm3=13.8,
    )


def test_sensor_definitions_cover_all_sensor_kinds() -> None:
    """Every SensorKind must have a declarative definition."""
    assert set(SENSOR_DEFINITIONS) == set(SensorKind)


def test_air_definition_defaults_and_value_getter() -> None:
    """Air definition maps to current V1 constants and snapshot field."""
    definition = definition_for(SensorKind.AIR)

    assert definition.kind == SensorKind.AIR
    assert definition.unique_id_suffix == UNIQUE_ID_SUFFIX_AIR
    assert definition.default_name == DEFAULT_DISPLAY_NAME
    assert definition.default_icon == DEFAULT_ICON
    assert definition.native_unit_of_measurement == UNIT_KPA
    assert definition.device_class is None
    assert definition.value_getter(_snapshot()) == 1.27


def test_leaf_definition_defaults_and_value_getter() -> None:
    """Leaf definition maps to current V1 constants and snapshot field."""
    definition = definition_for(SensorKind.LEAF)

    assert definition.kind == SensorKind.LEAF
    assert definition.unique_id_suffix == UNIQUE_ID_SUFFIX_LEAF
    assert definition.default_name == DEFAULT_LEAF_DISPLAY_NAME
    assert definition.default_icon == DEFAULT_LEAF_ICON
    assert definition.native_unit_of_measurement == UNIT_KPA
    assert definition.device_class is None
    assert definition.value_getter(_snapshot()) == 1.58


def test_absolute_humidity_definition_defaults_and_value_getter() -> None:
    """Absolute humidity definition maps to current V1 constants and snapshot field."""
    definition = definition_for(SensorKind.ABSOLUTE_HUMIDITY)

    assert definition.kind == SensorKind.ABSOLUTE_HUMIDITY
    assert definition.unique_id_suffix == UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY
    assert definition.default_name == DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME
    assert definition.default_icon == DEFAULT_ABSOLUTE_HUMIDITY_ICON
    assert definition.native_unit_of_measurement == UNIT_GM3
    assert definition.device_class == "absolute_humidity"
    assert definition.value_getter(_snapshot()) == 13.8


def test_dew_point_definition_defaults_and_value_getter() -> None:
    """Dew point definition maps to current V1 constants and snapshot field."""
    definition = definition_for(SensorKind.DEW_POINT)

    assert definition.kind == SensorKind.DEW_POINT
    assert definition.unique_id_suffix == UNIQUE_ID_SUFFIX_DEW_POINT
    assert definition.default_name == DEFAULT_DEW_POINT_DISPLAY_NAME
    assert definition.default_icon == DEFAULT_DEW_POINT_ICON
    assert definition.native_unit_of_measurement == "°C"
    assert definition.device_class == "temperature"
    assert definition.value_getter(_snapshot()) == 16.68
