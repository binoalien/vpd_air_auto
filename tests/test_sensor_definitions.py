"""Tests for declarative sensor definitions."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature

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


def test_registry_key_matches_definition_kind() -> None:
    """Each registry entry key must match the embedded definition kind."""
    for kind, definition in SENSOR_DEFINITIONS.items():
        assert definition.kind == kind


def test_sensor_definitions_align_with_v1_constants() -> None:
    """Definitions should remain aligned with current V1 constants."""
    expected_by_kind = {
        SensorKind.AIR: {
            "unique_id_suffix": UNIQUE_ID_SUFFIX_AIR,
            "default_name": DEFAULT_DISPLAY_NAME,
            "default_icon": DEFAULT_ICON,
            "native_unit_of_measurement": UNIT_KPA,
            "device_class": None,
            "expected_value": 1.27,
            "include_leaf_offset_attribute": False,
        },
        SensorKind.LEAF: {
            "unique_id_suffix": UNIQUE_ID_SUFFIX_LEAF,
            "default_name": DEFAULT_LEAF_DISPLAY_NAME,
            "default_icon": DEFAULT_LEAF_ICON,
            "native_unit_of_measurement": UNIT_KPA,
            "device_class": None,
            "expected_value": 1.58,
            "include_leaf_offset_attribute": True,
        },
        SensorKind.ABSOLUTE_HUMIDITY: {
            "unique_id_suffix": UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY,
            "default_name": DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
            "default_icon": DEFAULT_ABSOLUTE_HUMIDITY_ICON,
            "native_unit_of_measurement": UNIT_GM3,
            "device_class": SensorDeviceClass.ABSOLUTE_HUMIDITY,
            "expected_value": 13.8,
            "include_leaf_offset_attribute": False,
        },
        SensorKind.DEW_POINT: {
            "unique_id_suffix": UNIQUE_ID_SUFFIX_DEW_POINT,
            "default_name": DEFAULT_DEW_POINT_DISPLAY_NAME,
            "default_icon": DEFAULT_DEW_POINT_ICON,
            "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
            "device_class": SensorDeviceClass.TEMPERATURE,
            "expected_value": 16.68,
            "include_leaf_offset_attribute": False,
        },
    }

    snapshot = _snapshot()
    for kind, expected in expected_by_kind.items():
        definition = get_sensor_definition(kind)
        assert definition.kind == kind
        assert definition.unique_id_suffix == expected["unique_id_suffix"]
        assert definition.default_name == expected["default_name"]
        assert definition.default_icon == expected["default_icon"]
        assert (
            definition.native_unit_of_measurement
            == expected["native_unit_of_measurement"]
        )
        assert definition.device_class == expected["device_class"]
        assert definition.snapshot_value_getter(snapshot) == expected["expected_value"]
        assert (
            definition.include_leaf_offset_attribute
            == expected["include_leaf_offset_attribute"]
        )


def test_leaf_definition_marks_offset_attribute() -> None:
    """Leaf kind must flag leaf offset attr; all others must not."""
    for kind in SensorKind:
        expected = kind is SensorKind.LEAF
        assert get_sensor_definition(kind).include_leaf_offset_attribute is expected


def test_get_sensor_definition_accepts_sensor_kind_input() -> None:
    """Lookup should work when input is already a SensorKind."""
    assert get_sensor_definition(SensorKind.AIR) is SENSOR_DEFINITIONS[SensorKind.AIR]


def test_get_sensor_definition_accepts_string_input() -> None:
    """Lookup should work when input is the string form of a kind."""
    assert get_sensor_definition("leaf") is SENSOR_DEFINITIONS[SensorKind.LEAF]


def test_get_sensor_definition_raises_for_invalid_string() -> None:
    """Invalid string input should raise a clear ValueError."""
    try:
        get_sensor_definition("not_a_kind")
    except ValueError as err:
        message = str(err)
    else:
        raise AssertionError("Expected ValueError for invalid sensor kind")

    assert "Invalid sensor kind" in message
    assert "not_a_kind" in message
