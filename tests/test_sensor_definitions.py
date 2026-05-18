"""Tests for declarative sensor definitions."""

from __future__ import annotations

from custom_components.vpd_air_auto.domain.enums import SensorKind
from custom_components.vpd_air_auto.domain.sensor_definitions import (
    SENSOR_DEFINITIONS,
    get_sensor_definition,
)
from custom_components.vpd_air_auto.models import DeviceSnapshot


def _snapshot() -> DeviceSnapshot:
    return DeviceSnapshot(
        device_id="device-1",
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


def test_all_sensor_kinds_have_definitions() -> None:
    """All supported sensor kinds should be defined."""
    assert set(SENSOR_DEFINITIONS) == set(SensorKind)


def test_sensor_definitions_expose_expected_metadata_and_snapshot_mapping() -> None:
    """Definitions should map metadata and snapshot fields correctly."""
    snapshot = _snapshot()

    air = get_sensor_definition(SensorKind.AIR)
    assert air.native_unit_of_measurement == "kPa"
    assert air.device_class is None
    assert air.snapshot_value_getter(snapshot) == 1.27

    leaf = get_sensor_definition(SensorKind.LEAF)
    assert leaf.native_unit_of_measurement == "kPa"
    assert leaf.device_class is None
    assert leaf.snapshot_value_getter(snapshot) == 1.58

    absolute_humidity = get_sensor_definition(SensorKind.ABSOLUTE_HUMIDITY)
    assert absolute_humidity.native_unit_of_measurement == "g/m³"
    assert absolute_humidity.device_class == "absolute_humidity"
    assert absolute_humidity.snapshot_value_getter(snapshot) == 13.8

    dew_point = get_sensor_definition(SensorKind.DEW_POINT)
    assert dew_point.native_unit_of_measurement == "°C"
    assert dew_point.device_class == "temperature"
    assert dew_point.snapshot_value_getter(snapshot) == 16.68


def test_leaf_definition_marks_leaf_offset_attribute() -> None:
    """Only leaf sensor definition should include leaf offset attribute."""
    assert get_sensor_definition(SensorKind.LEAF).include_leaf_offset_attribute is True
    assert get_sensor_definition(SensorKind.AIR).include_leaf_offset_attribute is False
    assert (
        get_sensor_definition(SensorKind.ABSOLUTE_HUMIDITY)
        .include_leaf_offset_attribute
        is False
    )
    assert (
        get_sensor_definition(SensorKind.DEW_POINT).include_leaf_offset_attribute
        is False
    )
