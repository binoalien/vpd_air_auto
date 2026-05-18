"""Tests for declarative sensor definitions."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature

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
    """Ensure all declared kinds are present in the definition registry."""
    assert set(SENSOR_DEFINITIONS) == set(SensorKind)


def test_sensor_definitions_map_to_expected_units_and_device_classes() -> None:
    """Validate stable units and classes for each currently supported kind."""
    assert get_sensor_definition(SensorKind.AIR).native_unit_of_measurement == "kPa"
    assert get_sensor_definition(SensorKind.AIR).device_class is None

    assert get_sensor_definition(SensorKind.LEAF).native_unit_of_measurement == "kPa"
    assert get_sensor_definition(SensorKind.LEAF).device_class is None

    assert (
        get_sensor_definition(SensorKind.ABSOLUTE_HUMIDITY).native_unit_of_measurement
        == "g/m³"
    )
    assert (
        get_sensor_definition(SensorKind.ABSOLUTE_HUMIDITY).device_class
        == SensorDeviceClass.ABSOLUTE_HUMIDITY
    )

    assert (
        get_sensor_definition(SensorKind.DEW_POINT).native_unit_of_measurement
        == UnitOfTemperature.CELSIUS
    )
    assert (
        get_sensor_definition(SensorKind.DEW_POINT).device_class
        == SensorDeviceClass.TEMPERATURE
    )


def test_snapshot_value_getters_match_expected_fields() -> None:
    """Definition getters should map each kind to the expected snapshot field."""
    snapshot = _snapshot()

    assert (
        get_sensor_definition(SensorKind.AIR).snapshot_value_getter(snapshot) == 1.27
    )
    assert (
        get_sensor_definition(SensorKind.LEAF).snapshot_value_getter(snapshot) == 1.58
    )
    assert (
        get_sensor_definition(SensorKind.ABSOLUTE_HUMIDITY).snapshot_value_getter(
            snapshot
        )
        == 13.8
    )
    assert (
        get_sensor_definition(SensorKind.DEW_POINT).snapshot_value_getter(snapshot)
        == 16.68
    )


def test_leaf_definition_marks_offset_attribute() -> None:
    """Leaf kind must flag leaf offset attribute inclusion."""
    assert get_sensor_definition(SensorKind.LEAF).include_leaf_offset_attribute is True
    assert get_sensor_definition(SensorKind.AIR).include_leaf_offset_attribute is False
