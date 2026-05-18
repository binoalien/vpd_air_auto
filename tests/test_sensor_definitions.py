"""Tests for domain sensor definitions."""

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
from custom_components.vpd_air_auto.domain.sensor_definitions import SENSOR_DEFINITIONS
from custom_components.vpd_air_auto.models import DeviceSnapshot


def _snapshot() -> DeviceSnapshot:
    return DeviceSnapshot(
        device_id="dev-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.temp",
        humidity_entity_id="sensor.humidity",
        temperature_c=25.0,
        humidity_pct=60.0,
        leaf_offset_c=-2.0,
        leaf_temperature_c=23.0,
        dew_point_c=16.68,
        vpd_air_kpa=1.27,
        vpd_leaf_kpa=1.58,
        absolute_humidity_gm3=13.8,
    )


def test_sensor_kind_values_are_stable() -> None:
    """SensorKind values must remain compatible with V1 kind strings."""
    assert SensorKind.AIR.value == "air"
    assert SensorKind.LEAF.value == "leaf"
    assert SensorKind.ABSOLUTE_HUMIDITY.value == "absolute_humidity"
    assert SensorKind.DEW_POINT.value == "dew_point"


def test_sensor_definition_registry_covers_all_current_kinds() -> None:
    """Registry should contain all currently supported derived sensor kinds."""
    assert set(SENSOR_DEFINITIONS) == set(SensorKind)


def test_sensor_definition_metadata_matches_v1_defaults() -> None:
    """Definition metadata must match existing V1 constants."""
    assert SENSOR_DEFINITIONS[SensorKind.AIR].unique_id_suffix == UNIQUE_ID_SUFFIX_AIR
    assert SENSOR_DEFINITIONS[SensorKind.AIR].default_name == DEFAULT_DISPLAY_NAME
    assert SENSOR_DEFINITIONS[SensorKind.AIR].default_icon == DEFAULT_ICON
    assert SENSOR_DEFINITIONS[SensorKind.AIR].native_unit_of_measurement == UNIT_KPA

    assert SENSOR_DEFINITIONS[SensorKind.LEAF].unique_id_suffix == UNIQUE_ID_SUFFIX_LEAF
    assert SENSOR_DEFINITIONS[SensorKind.LEAF].default_name == DEFAULT_LEAF_DISPLAY_NAME
    assert SENSOR_DEFINITIONS[SensorKind.LEAF].default_icon == DEFAULT_LEAF_ICON
    assert SENSOR_DEFINITIONS[SensorKind.LEAF].native_unit_of_measurement == UNIT_KPA

    assert (
        SENSOR_DEFINITIONS[SensorKind.ABSOLUTE_HUMIDITY].unique_id_suffix
        == UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY
    )
    assert (
        SENSOR_DEFINITIONS[SensorKind.ABSOLUTE_HUMIDITY].default_name
        == DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME
    )
    assert (
        SENSOR_DEFINITIONS[SensorKind.ABSOLUTE_HUMIDITY].default_icon
        == DEFAULT_ABSOLUTE_HUMIDITY_ICON
    )
    assert (
        SENSOR_DEFINITIONS[SensorKind.ABSOLUTE_HUMIDITY].native_unit_of_measurement
        == UNIT_GM3
    )

    assert (
        SENSOR_DEFINITIONS[SensorKind.DEW_POINT].unique_id_suffix
        == UNIQUE_ID_SUFFIX_DEW_POINT
    )
    assert (
        SENSOR_DEFINITIONS[SensorKind.DEW_POINT].default_name
        == DEFAULT_DEW_POINT_DISPLAY_NAME
    )
    assert (
        SENSOR_DEFINITIONS[SensorKind.DEW_POINT].default_icon
        == DEFAULT_DEW_POINT_ICON
    )


def test_sensor_definition_snapshot_getters_map_to_current_snapshot_fields() -> None:
    """Snapshot getter mapping should match current DeviceSnapshot field usage."""
    snapshot = _snapshot()

    assert SENSOR_DEFINITIONS[SensorKind.AIR].snapshot_getter(snapshot) == 1.27
    assert SENSOR_DEFINITIONS[SensorKind.LEAF].snapshot_getter(snapshot) == 1.58
    assert (
        SENSOR_DEFINITIONS[SensorKind.ABSOLUTE_HUMIDITY].snapshot_getter(snapshot)
        == 13.8
    )
    assert SENSOR_DEFINITIONS[SensorKind.DEW_POINT].snapshot_getter(snapshot) == 16.68
